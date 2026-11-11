"""crosscheck_asr.py - Independent second-model ASR pass used to audit reference transcripts.

Runs faster-whisper "small" (Systran/faster-whisper-small, CTranslate2 int8, CPU) over every
final-corpus clip with NO domain prompt, so its output is independent of the deployed hybrid
ASR and of the curated references. The language is forced from the annotators' language tag
when the clip is monolingual, and auto-detected for code-mixed clips.

Output: model/data/reports/asr_crosscheck_whisper_small.json (one row per clip, resumable).

Usage:
    python model/src/asr/crosscheck_asr.py [--limit N]
"""
import argparse
import json
import time
from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[3]
AUDIO_DIR = ROOT / "model" / "data" / "audio"
MANIFEST = ROOT / "model" / "data" / "metadata" / "internal_manifest.json"
OUT = ROOT / "model" / "data" / "reports" / "asr_crosscheck_whisper_small.json"
LANG_CODE = {"Hindi": "hi", "Gujarati": "gu", "English": "en"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model", default="small")
    ap.add_argument("--beam", type=int, default=1)
    args = ap.parse_args()

    rows = json.loads(MANIFEST.read_text())["manifest"]
    rows = sorted(rows, key=lambda r: r["uuid"])[: args.limit]
    done = {}
    if OUT.exists():
        done = {r["uuid"]: r for r in json.loads(OUT.read_text())["predictions"]}

    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=6)
    for i, r in enumerate(rows, 1):
        if r["uuid"] in done:
            continue
        langs = r["languages"]
        forced = LANG_CODE[langs[0]] if len(langs) == 1 else None
        t0 = time.time()
        segs, info = model.transcribe(
            str(AUDIO_DIR / f"{r['uuid']}.wav"),
            language=forced,
            beam_size=args.beam,
            condition_on_previous_text=False,
            vad_filter=True,
        )
        segs = list(segs)
        text = " ".join(s.text.strip() for s in segs).strip()
        avg_lp = sum(s.avg_logprob for s in segs) / len(segs) if segs else None
        done[r["uuid"]] = {
            "uuid": r["uuid"],
            "original_clip_id": r["original_clip_id"],
            "languages": langs,
            "forced_language": forced,
            "detected_language": info.language,
            "audio_duration_sec": round(info.duration, 3),
            "decode_sec": round(time.time() - t0, 2),
            "avg_logprob": avg_lp,
            "transcription": text,
        }
        print(f"[{i}/{len(rows)}] {r['uuid']} {forced or 'auto'}->{info.language} {len(text.split())} words", flush=True)
        OUT.write_text(json.dumps({
            "engine": f"faster-whisper-{args.model} (int8, beam {args.beam}, VAD, no prompt)",
            "predictions": list(done.values()),
        }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
