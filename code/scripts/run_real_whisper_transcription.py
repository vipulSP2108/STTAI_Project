# ============================================================
# Assignment 2: Real Whisper Base Offline Audio Transcription Engine
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Transcribes audio clips using OpenAI Whisper base model.
# Extracts real ASR transcripts, decoder log-probabilities,
# no-speech probabilities, and waveform SNR statistics.
# Results are cached to data/processed/whisper_base_eval_cache.json
# ============================================================

import argparse
import json
import math
import os
import time
import wave
import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from normalisation import normalise_text, detect_repetition

DATA_DIR = Path("data")
AUDIO_DIR = DATA_DIR / "raw" / "audio"
CACHE_JSON = DATA_DIR / "processed" / "whisper_base_eval_cache.json"
CACHE_CSV = DATA_DIR / "processed" / "whisper_base_eval_cache.csv"
CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)

def compute_audio_snr(wav_path):
    """Computes empirical signal-to-noise ratio in dB from audio waveform."""
    try:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            dtype = np.int16 if wf.getsampwidth() == 2 else np.uint8
            audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
            if len(audio) == 0:
                return 15.0
            
            # Divide into frames of 20ms
            frame_len = int(wf.getframerate() * 0.02)
            if frame_len <= 0 or len(audio) < frame_len:
                return 15.0
            num_frames = len(audio) // frame_len
            frame_energies = [np.mean(audio[i*frame_len : (i+1)*frame_len]**2) for i in range(num_frames)]
            frame_energies = [e for e in frame_energies if not np.isnan(e) and e > 1e-6]
            if len(frame_energies) < 2:
                return 15.0
            
            frame_energies.sort()
            noise_floor = np.mean(frame_energies[:max(1, int(len(frame_energies)*0.1))])
            signal_floor = np.mean(frame_energies[int(len(frame_energies)*0.2):])
            
            if noise_floor <= 0:
                return 25.0
            snr = 10.0 * math.log10(signal_floor / noise_floor)
            return round(float(np.clip(snr, 5.0, 35.0)), 2)
    except Exception:
        return 15.0

def get_audio_duration(wav_path):
    try:
        with wave.open(str(wav_path), "rb") as wf:
            return round(float(wf.getnframes() / wf.getframerate()), 2)
    except Exception:
        return 2.0

def load_cache():
    if CACHE_JSON.exists():
        with open(CACHE_JSON, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_JSON, "w") as f:
        json.dump(cache, f, indent=2)
    rows = list(cache.values())
    if rows:
        pd.DataFrame(rows).to_csv(CACHE_CSV, index=False)

def run_transcription(splits=["gold", "val", "test", "cohort_b"], force=False):
    print(f"=== Running Real Safe Whisper Base Transcription on Splits: {splits} ===")
    import whisper

    cache = load_cache() if not force else {}
    print(f"Loaded existing cache with {len(cache)} entries (force={force}).")

    clip_ids = []
    for s in splits:
        if s == "gold":
            p = DATA_DIR / "gold_test_set.csv"
        elif s == "val":
            p = DATA_DIR / "splits" / "val.csv"
        elif s == "test":
            p = DATA_DIR / "splits" / "test.csv"
        elif s == "cohort_b":
            p = DATA_DIR / "splits" / "cohort_b_shifted.csv"
        elif s == "train":
            p = DATA_DIR / "splits" / "train.csv"
        else:
            continue
        if p.exists():
            df = pd.read_csv(p)
            clip_ids.extend(df["clip_id"].tolist())

    unique_cids = list(dict.fromkeys(clip_ids))
    missing_cids = unique_cids if force else [cid for cid in unique_cids if cid not in cache]
    print(f"Total unique clips requested: {len(unique_cids)}, to transcribe: {len(missing_cids)}")

    if not missing_cids:
        print("All requested clips are already cached! No transcription needed.")
        return cache

    print(f"Loading Whisper base model on CPU...")
    model = whisper.load_model("base", device="cpu")

    t0_all = time.time()
    repetition_flags = 0
    for idx, cid in enumerate(missing_cids):
        wav_path = AUDIO_DIR / f"{cid}.wav"
        if not wav_path.exists():
            print(f"Warning: Audio file not found: {wav_path}")
            continue

        t0 = time.time()
        # Safe decoding per Guide Section 3.0.1: No prompt loop, greedy beam=1
        res = model.transcribe(
            str(wav_path),
            fp16=False,
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=2.0,
            no_speech_threshold=0.6,
            beam_size=1
        )
        latency_sec = time.time() - t0

        raw_tx = res.get("text", "").strip()
        has_loop = detect_repetition(raw_tx)
        if has_loop:
            repetition_flags += 1
        tx = normalise_text(raw_tx)

        avg_logprob = -1.0
        no_speech_prob = 0.0
        if "segments" in res and res["segments"]:
            avg_logprob = float(np.mean([s.get("avg_logprob", -1.0) for s in res["segments"]]))
            no_speech_prob = float(np.mean([s.get("no_speech_prob", 0.0) for s in res["segments"]]))

        snr = compute_audio_snr(wav_path)
        duration = get_audio_duration(wav_path)

        cache[cid] = {
            "clip_id": cid,
            "pred_transcript": tx,
            "raw_transcript": raw_tx,
            "avg_logprob": round(avg_logprob, 4),
            "no_speech_prob": round(no_speech_prob, 4),
            "snr_db": snr,
            "duration_sec": duration,
            "transcribe_latency_sec": round(latency_sec, 3),
            "repetition_flagged": has_loop
        }

        if (idx + 1) % 5 == 0 or idx == len(missing_cids) - 1:
            save_cache(cache)
            elapsed = time.time() - t0_all
            print(f"[{idx+1}/{len(missing_cids)}] Transcribed {cid} ({latency_sec:.2f}s) | Repetitions: {repetition_flags} | Elapsed: {elapsed:.1f}s")

    save_cache(cache)
    print(f"\nTranscription complete! Saved {len(cache)} entries to {CACHE_JSON}")
    print(f"Total prompt-induced repetition loops caught and filtered: {repetition_flags}")
    return cache

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", nargs="+", default=["gold", "val", "test", "cohort_b"])
    parser.add_argument("--force", action="store_true", help="Force re-transcription of all clips")
    args = parser.parse_args()
    run_transcription(args.splits, force=args.force)
