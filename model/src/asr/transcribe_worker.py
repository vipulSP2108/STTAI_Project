#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""transcribe_worker.py - High-Throughput Accelerated ASR Worker (Reverse Queue).

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Uses faster-whisper (CTranslate2) with 4 CPU threads.
2. Processes files in reverse order, skipping any already transcribed files.
3. Merges seamlessly with the forward worker.
"""

import os
import sys
import time
from pathlib import Path
from faster_whisper import WhisperModel

os.environ["PATH"] = f"/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:{os.environ.get('PATH', '')}"

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
AUDIO_DIR = MODEL_DIR / "data" / "audio"
TEXT_DIR = MODEL_DIR / "data" / "text"

DOMAIN_PROMPT = "Campus student helpdesk query regarding hostel, mess, admissions, IT support, or student services."

def is_already_transcribed(text_path: Path) -> bool:
    if not text_path.exists():
        return False
    content = text_path.read_text()
    for line in content.splitlines():
        if line.startswith("Transcript:"):
            val = line.replace("Transcript:", "").strip()
            return len(val) > 0
    return False

def run_reverse_worker():
    print("=" * 70)
    print("ACCELERATED REVERSE ASR WORKER (Model: faster-whisper-base)")
    print("=" * 70)

    model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
    print("Worker loaded faster-whisper-base model checkpoint.")

    audio_files = sorted(list(AUDIO_DIR.glob("*.wav")), reverse=True)
    print(f"Total candidate audio files: {len(audio_files)} (Reverse order)")

    transcribed_count = 0
    for idx, audio_path in enumerate(audio_files, start=1):
        sample_uuid = audio_path.stem
        text_path = TEXT_DIR / f"{sample_uuid}.txt"

        if is_already_transcribed(text_path):
            continue

        t0 = time.time()
        try:
            segments, info = model.transcribe(
                str(audio_path),
                condition_on_previous_text=False,
                initial_prompt=DOMAIN_PROMPT
            )
            transcript_text = " ".join([s.text for s in segments]).strip()
            detected_lang = info.language
            duration_s = time.time() - t0

            # Double check in case forward worker just wrote it
            if is_already_transcribed(text_path):
                continue

            if text_path.exists():
                lines = text_path.read_text().splitlines()
                meta = {}
                for line in lines:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()

                updated_content = f"""UUID: {sample_uuid}
Transcript: {transcript_text}
Detected_Language: {detected_lang}
Target_Label: {meta.get('Target_Label', '')}
Spoken_Languages: {meta.get('Spoken_Languages', '')}
Reference_Notes: {meta.get('Reference_Notes', '')}
"""
                text_path.write_text(updated_content.strip() + "\n")
                transcribed_count += 1
                print(f"[REV {transcribed_count:3d}] Transcribed {sample_uuid}.wav ({duration_s:.2f}s) | Lang: {detected_lang:2s} | Words: {len(transcript_text.split()):2d}")

        except Exception as e:
            print(f"[REV ERROR] {sample_uuid}.wav: {e}")

    print(f"Reverse worker completed. Transcribed {transcribed_count} files.")

if __name__ == "__main__":
    run_reverse_worker()
