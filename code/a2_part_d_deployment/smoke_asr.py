"""Run a real CPU decode from a WAV staged outside the Git checkout."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--sha256", required=True, help="SHA-256 from the data manifest")
    args = parser.parse_args()

    audio_hash = hashlib.sha256(args.audio.read_bytes()).hexdigest()
    if audio_hash != args.sha256.lower():
        parser.error(f"audio SHA-256 mismatch: {audio_hash}")

    model = WhisperModel("/opt/whisper-base", device="cpu", compute_type="int8", cpu_threads=2)
    start = perf_counter()
    segments, info = model.transcribe(str(args.audio), beam_size=1)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    elapsed = perf_counter() - start
    if not transcript or info.duration <= 0:
        raise SystemExit("ASR smoke test failed: no transcription for the input WAV")

    print(json.dumps({
        "status": "pass",
        "test": "cpu_asr_smoke",
        "model": "Systran/faster-whisper-base",
        "audio_sha256": audio_hash,
        "language": info.language,
        "audio_seconds": round(info.duration, 3),
        "decode_seconds": round(elapsed, 3),
        "real_time_factor": round(elapsed / info.duration, 3),
        "transcript_characters": len(transcript),
    }, indent=2))


if __name__ == "__main__":
    main()
