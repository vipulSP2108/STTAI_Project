"""finetune_whisper.py - Fine-tune a Whisper-small/base checkpoint on human transcripts of
TRAINING speakers only, with an MLflow-logged hyper-parameter grid (A2 Parts A/B).

Requires data/labels/human_transcripts.csv (produced by the Round T transcription pass, see
final_annotation/transcription_round/README.md). Curated/ASR text is never used as a target.

Split: model/data/splits/release_speakers.json (validation and test speakers held out; every
other speaker is training). Only clips <= 30 s are used as training targets because Whisper
sees 30-second windows; longer clips are evaluated with chunked decoding.

Search grid (validation WER/CER only; test speakers are never decoded here):
    --lr        1e-5, 3e-5
    --freeze    encoder | none          (freeze the whole encoder, or train everything)
    --base      vasista22/whisper-hindi-small | openai/whisper-small | vasista22/whisper-gujarati-base

Hardware: run on a GPU (free Colab T4 is enough: ~10 min per run at 4 epochs). CPU works but is slow.
    pip install "transformers==4.46.3" "datasets==3.1.0" "accelerate==1.1.1" jiwer mlflow librosa
    python model/src/asr/finetune_whisper.py --base vasista22/whisper-hindi-small --lr 1e-5 --freeze encoder
Conversion for serving (CTranslate2 int8, same format as model/models/whisper-*-ct2):
    ct2-transformers-converter --model <out_dir> --output_dir model/models/<name>-ct2 --quantization int8
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from pathlib import Path

import jiwer
import librosa
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
AUDIO = ROOT / "model" / "data" / "audio"
SPLIT = json.loads((ROOT / "model/data/splits/release_speakers.json").read_text())
LANG = {"Hindi": "hi", "Gujarati": "gu", "English": "en"}


def rows():
    man = {m["uuid"]: m for m in json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]}
    with open(ROOT / "data/labels/human_transcripts.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m = man[r["uuid"]]
            spk = m["original_speaker_id"]
            role = "val" if spk in SPLIT["validation"] else "test" if spk in SPLIT["test"] else "train"
            langs = m["languages"]
            yield {"uuid": r["uuid"], "text": r["transcript"], "role": role, "speaker": spk,
                   "lang": LANG.get(langs[0]) if len(langs) == 1 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="vasista22/whisper-hindi-small")
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--freeze", choices=["encoder", "none"], default="encoder")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)

    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    proc = WhisperProcessor.from_pretrained(a.base)
    model = WhisperForConditionalGeneration.from_pretrained(a.base)
    if a.freeze == "encoder":
        for p in model.model.encoder.parameters():
            p.requires_grad = False
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev)

    data = list(rows())
    train = [r for r in data if r["role"] == "train"]
    val = [r for r in data if r["role"] == "val"]

    def load(u):
        return librosa.load(AUDIO / f"{u}.wav", sr=16000)[0]

    train = [r for r in train if len(load(r["uuid"])) <= 30 * 16000]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.01)

    def batch(rs):
        feats = proc.feature_extractor([load(r["uuid"]) for r in rs], sampling_rate=16000, return_tensors="pt").input_features
        labels = []
        for r in rs:
            proc.tokenizer.set_prefix_tokens(language=r["lang"] or "hi", task="transcribe")
            labels.append(proc.tokenizer(r["text"]).input_ids)
        L = max(map(len, labels))
        lab = torch.full((len(labels), L), -100)
        for i, l in enumerate(labels):
            lab[i, :len(l)] = torch.tensor(l)
        return feats.to(dev), lab.to(dev)

    t0 = time.time(); model.train(); losses = []
    for ep in range(a.epochs):
        random.shuffle(train)
        for i in range(0, len(train), 4):
            x, y = batch(train[i:i + 4])
            loss = model(input_features=x, labels=y).loss
            loss.backward(); opt.step(); opt.zero_grad(); losses.append(float(loss))
        print(f"epoch {ep + 1} loss {np.mean(losses[-max(1, len(train) // 4):]):.3f}", flush=True)
    train_sec = time.time() - t0

    model.eval(); hyps, refs = [], []
    for r in val:
        audio = load(r["uuid"]); out = []
        for s in range(0, len(audio), 30 * 16000):
            f = proc.feature_extractor(audio[s:s + 30 * 16000], sampling_rate=16000, return_tensors="pt").input_features.to(dev)
            with torch.no_grad():
                ids = model.generate(f, language=r["lang"], task="transcribe", max_new_tokens=220)
            out.append(proc.batch_decode(ids, skip_special_tokens=True)[0])
        hyps.append(" ".join(out)); refs.append(r["text"])
    metrics = {"val_wer": float(jiwer.wer(refs, hyps)), "val_cer": float(jiwer.cer(refs, hyps)),
               "n_train": len(train), "n_val": len(val), "train_sec": round(train_sec, 1)}
    out = Path(a.out or ROOT / "model" / "models" / f"ft_{a.base.split('/')[-1]}_lr{a.lr}_{a.freeze}")
    model.save_pretrained(out); proc.save_pretrained(out)
    digest = hashlib.sha256((out / "model.safetensors").read_bytes()).hexdigest()
    (out / "val_predictions.json").write_text(json.dumps([{"uuid": r["uuid"], "ref": r["text"], "hyp": h} for r, h in zip(val, hyps)],
                                                          ensure_ascii=False, indent=1))
    try:
        import mlflow
        mlflow.set_experiment("whisper_finetune")
        with mlflow.start_run(run_name=out.name):
            mlflow.log_params({"base": a.base, "lr": a.lr, "freeze": a.freeze, "epochs": a.epochs, "seed": a.seed,
                               "device": dev, "weights_sha256": digest})
            mlflow.log_metrics(metrics)
            mlflow.log_artifact(str(out / "val_predictions.json"))
    except Exception as e:  # MLflow is optional on Colab
        print("mlflow skipped:", e)
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
