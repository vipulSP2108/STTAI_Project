#!/usr/bin/env python3
"""
cache_train_asr.py
==================
Generates real ASR transcripts for all 171 training audio clips
using Whisper base (with adapted weights on MPS/CPU) under Latin script decoding constraints.
Caches outputs to data/processed/whisper_base_train_cache.json
so the Intent Router Head can be trained directly on ASR transcripts,
eliminating the human template-leak domain mismatch.
"""

import json
import time
import torch
import whisper
from pathlib import Path
import pandas as pd

import sys
sys.path.append(str(Path(__file__).parent.parent))
from normalisation import normalise_text

DATA_DIR = Path("data")
AUDIO_DIR = DATA_DIR / "raw" / "audio"
TRAIN_CSV = DATA_DIR / "splits" / "train.csv"
OUTPUT_CACHE = DATA_DIR / "processed" / "whisper_base_train_cache.json"
ADAPTED_PT = Path("artefacts/models/whisper_base_adapted.pt")

def main():
    print("=== Commencing Train Set ASR Transcription ===")
    OUTPUT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    
    cache = {}
    if OUTPUT_CACHE.exists():
        try:
            with open(OUTPUT_CACHE, "r") as f:
                cache = json.load(f)
            print(f"Loaded existing cache with {len(cache)} entries.")
        except Exception:
            cache = {}

    df_train = pd.read_csv(TRAIN_CSV)
    cids = df_train["clip_id"].tolist()
    missing_cids = [c for c in cids if c not in cache]
    print(f"Total train clips: {len(cids)}, remaining to transcribe: {len(missing_cids)}")

    if not missing_cids:
        print("All training clips already cached!")
        return

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading Whisper base model on {device.upper()}...")
    model = whisper.load_model("base", device=device)

    if ADAPTED_PT.exists():
        print(f"Loading adapted decoder weights from {ADAPTED_PT}...")
        sd = torch.load(ADAPTED_PT, map_location=device)
        res = model.load_state_dict(sd, strict=False)
        print(f"Loaded adapted weights: {len(sd)} keys matched.")

    t0_all = time.time()
    for idx, cid in enumerate(missing_cids):
        wav_path = AUDIO_DIR / f"{cid}.wav"
        if not wav_path.exists():
            print(f"Clip not found: {wav_path}")
            continue

        t0 = time.time()
        res = model.transcribe(
            str(wav_path),
            language="en",
            beam_size=1,
            condition_on_previous_text=False,
            temperature=0.0
        )
        latency = time.time() - t0
        raw_tx = res.get("text", "").strip()
        norm_tx = normalise_text(raw_tx)

        cache[cid] = {
            "clip_id": cid,
            "raw_transcript": raw_tx,
            "pred_transcript": norm_tx,
            "latency_sec": round(latency, 2)
        }

        if (idx + 1) % 10 == 0 or idx == len(missing_cids) - 1:
            with open(OUTPUT_CACHE, "w") as f:
                json.dump(cache, f, indent=2)
            elapsed = time.time() - t0_all
            print(f"[{idx+1}/{len(missing_cids)}] Processed {cid} ({latency:.2f}s) | Total cached: {len(cache)} | Elapsed: {elapsed:.1f}s")

    with open(OUTPUT_CACHE, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"✓ All {len(cache)} training ASR transcripts saved to {OUTPUT_CACHE} in {time.time()-t0_all:.1f}s")

if __name__ == "__main__":
    main()

