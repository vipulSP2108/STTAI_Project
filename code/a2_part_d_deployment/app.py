# ============================================================
# Assignment 2 - Part D: FastAPI REST Service & Telemetry
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Provides:
# - POST /predict: audio file -> real Whisper ASR transcript,
#   neural intent classification, softmax confidence, and latency
# - GET /health: system status, memory usage, CPU load
# - GET /version: git commit, model registry alias, gold test hash
# - Non-PII request and performance logging
# ============================================================

import os
import pickle
import platform
import tempfile
import time
import psutil
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

app = FastAPI(
    title="IITGN Voice Helpdesk ASR & Intent API",
    description="Local offline service for code-mixed speech recognition and intent routing",
    version="2.0.0"
)

GIT_COMMIT = os.environ.get("GIT_COMMIT", "a2-final")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "production")
LOG_PATH = Path("supporting_files/api_access.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
MODELS_DIR = Path("artefacts/models")

INTENT_MAP = {"admissions": 0, "hostel_mess": 1, "it_support": 2, "student_services": 3}
REV_INTENT_MAP = {v: k for k, v in INTENT_MAP.items()}

PROMPT = "IIT Gandhinagar student voice helpdesk query: admissions, hostel mess, IT support, student affairs, fees, wifi."

class PredictionResponse(BaseModel):
    transcript: str
    intent: str
    confidence: float
    latency_ms: float
    model_version: str
    git_commit: str

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    cpu_percent: float
    memory_mb: float
    hardware: str

class VersionResponse(BaseModel):
    model_version: str
    git_commit: str
    gold_set_sha256: str
    pipeline_stage: str

START_TIME = time.time()

# Global model holders for fast in-memory inference
whisper_model = None
vectorizer = None
intent_head = None

def get_models():
    global whisper_model, vectorizer, intent_head
    if whisper_model is None:
        import whisper
        whisper_model = whisper.load_model("base", device="cpu")

    if vectorizer is None:
        vec_path = MODELS_DIR / "proposed_vectorizer.pkl"
        with open(vec_path, "rb") as f:
            vectorizer = pickle.load(f)

    if intent_head is None:
        in_dim = len(vectorizer.get_feature_names_out())
        head = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 4)
        )
        head_path = MODELS_DIR / "production_v1_head.pt"
        if head_path.exists():
            sd = torch.load(head_path, weights_only=True)
            cleaned_sd = {k.replace("net.", ""): v for k, v in sd.items()}
            head.load_state_dict(cleaned_sd)
        head.eval()
        intent_head = head

    return whisper_model, vectorizer, intent_head

@app.on_event("startup")
def startup_event():
    # Warm up models on startup
    try:
        get_models()
    except Exception as e:
        print(f"Startup warmup notice: {e}")

@app.post("/predict", response_model=PredictionResponse)
async def predict_audio(file: UploadFile = File(...)):
    t0 = time.time()
    filename = file.filename.lower() if file.filename else "query.wav"

    if not filename.endswith((".wav", ".mp3", ".ogg", ".m4a", ".opus")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    # Write temporarily to disk for Whisper decoding
    suffix = Path(filename).suffix if Path(filename).suffix else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        w_model, vec, head = get_models()
        res = w_model.transcribe(
            tmp_path,
            fp16=False,
            initial_prompt=PROMPT,
            temperature=0.0,
            condition_on_previous_text=False
        )
        transcript = res.get("text", "").strip()
        if not transcript:
            transcript = "institute helpdesk query"

        # Intent classification
        X_text = vec.transform([transcript]).toarray()
        with torch.no_grad():
            logits = head(torch.tensor(X_text, dtype=torch.float32))
            probs = torch.softmax(logits, dim=1).numpy()[0]

        pred_idx = int(np.argmax(probs))
        intent = REV_INTENT_MAP[pred_idx]
        confidence = round(float(np.max(probs)), 4)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    latency_ms = (time.time() - t0) * 1000.0

    # Non-PII telemetry logging
    log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] model={MODEL_VERSION} intent={intent} conf={confidence:.3f} lat_ms={latency_ms:.2f}\n"
    with open(LOG_PATH, "a") as f:
        f.write(log_entry)

    return PredictionResponse(
        transcript=transcript,
        intent=intent,
        confidence=confidence,
        latency_ms=round(latency_ms, 2),
        model_version=MODEL_VERSION,
        git_commit=GIT_COMMIT
    )

@app.get("/health", response_model=HealthResponse)
def health_check():
    process = psutil.Process()
    mem_info = process.memory_info()
    return HealthResponse(
        status="HEALTHY",
        uptime_seconds=round(time.time() - START_TIME, 2),
        cpu_percent=psutil.cpu_percent(),
        memory_mb=round(mem_info.rss / (1024 * 1024), 2),
        hardware=f"{platform.system()} {platform.machine()} ({platform.processor()})"
    )

@app.get("/version", response_model=VersionResponse)
def get_version():
    return VersionResponse(
        model_version=MODEL_VERSION,
        git_commit=GIT_COMMIT,
        gold_set_sha256="64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9",
        pipeline_stage="production"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
