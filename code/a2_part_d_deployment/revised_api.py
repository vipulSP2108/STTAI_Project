"""FastAPI endpoints for the revised-corpus CPU image."""

from contextlib import asynccontextmanager
from io import BytesIO
import json
import logging

from av.error import FFmpegError
from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper.audio import decode_audio

from revised_release import get_models, predict, version


MAX_WAV_BYTES = 12 * 1024 * 1024
LOGGER = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_app):
    get_models()
    yield


app = FastAPI(title="Revised Voice Helpdesk", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "HEALTHY"}


@app.get("/version")
def model_version():
    return version()


@app.post("/predict")
def predict_upload(file: UploadFile):
    if not (file.filename or "").lower().endswith(".wav"):
        raise HTTPException(400, "Upload a .wav audio file")
    data = file.file.read(MAX_WAV_BYTES + 1)
    if not data or len(data) > MAX_WAV_BYTES:
        raise HTTPException(400, "WAV payload is empty or exceeds 12 MiB")
    if data[:4] not in (b"RIFF", b"RF64", b"RIFX") or data[8:12] != b"WAVE":
        raise HTTPException(400, "The file does not contain WAV audio")
    try:
        audio = decode_audio(BytesIO(data), sampling_rate=16000)
    except (FFmpegError, ValueError, EOFError) as error:
        raise HTTPException(400, "Could not decode the WAV audio") from error
    if not audio.size:
        raise HTTPException(400, "The WAV contains no audio")
    result = predict(audio)
    LOGGER.info("prediction %s", json.dumps({key: result[key] for key in ("model_version", "intent", "confidence", "latency_ms")}))
    return result
