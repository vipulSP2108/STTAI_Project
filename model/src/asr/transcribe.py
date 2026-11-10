#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""transcribe.py - Production Offline ASR Transcription Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. 100% Offline local execution on Apple Silicon Mac / CPU with int8 quantization.
2. Indic-Specialized Tri-Engine Architecture:
   - Gujarati engine: Offline CTranslate2 model (model/models/whisper-gujarati-ct2)
   - Hindi engine: Offline CTranslate2 model (model/models/whisper-hindi-ct2, vasista22/whisper-hindi-small)
   - English engine: faster-whisper base (int8, fast RTF 0.06 - 0.12)
3. Transcribes all 182 audio files in model/data/audio/<uuid>.wav.
4. Normalizes text, eliminates token repetition loops, strips cross-script Urdu bleeding, records latency & RTF.
5. Saves predictions to model/data/reports/offline_asr_predictions.json.
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
import soundfile as sf
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
AUDIO_DIR = MODEL_DIR / "data" / "audio"
METADATA_DIR = MODEL_DIR / "data" / "metadata"
REPORTS_DIR = MODEL_DIR / "data" / "reports"
GU_MODEL_DIR = MODEL_DIR / "models" / "whisper-gujarati-ct2"
HI_MODEL_DIR = MODEL_DIR / "models" / "whisper-hindi-ct2"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def clean_repetition(text: str) -> str:
    """Removes degenerate ASR repetition loops and stray non-native characters."""
    if not text:
        return ""
    # 1. Collapse repeating words/tokens (e.g. 'word word word' or 'डॉक्यूमेंट डॉक्यूमेंट')
    text = re.sub(r'(\S+)(?:\s+\1)+', r'\1', text)
    # 2. Collapse repeating characters (e.g. 'aaaa' -> 'a', 'dddd' -> 'd')
    text = re.sub(r'(.)\1{3,}', r'\1', text)
    # 3. Strip any stray Urdu/Perso-Arabic tokens if bleeding occurs
    text = re.sub(r'[\u0600-\u06FF\u0750-\u077F]', '', text)
    # 4. Strip unicode replacement characters
    text = text.replace('\ufffd', '')
    # 5. Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_transcription(cpu_threads: int = 4, max_clips: int = None):
    print("=" * 70)
    print("OFFLINE MULTILINGUAL ASR ENGINE (100% Local Inference)")
    print("=" * 70)

    manifest_path = METADATA_DIR / "internal_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest = manifest_data["manifest"]

    if max_clips:
        manifest = manifest[:max_clips]

    print(f"Total clips to transcribe: {len(manifest)}")

    # Load offline models
    print("\n[1/3] Loading offline CTranslate2 Gujarati model...")
    t0 = time.time()
    gu_model = WhisperModel(str(GU_MODEL_DIR), device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    print(f"  Loaded Gujarati model in {time.time() - t0:.2f}s")

    print("[2/3] Loading offline CTranslate2 Hindi model (vasista22/whisper-hindi-small)...")
    t0 = time.time()
    hi_model = WhisperModel(str(HI_MODEL_DIR), device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    print(f"  Loaded Hindi model in {time.time() - t0:.2f}s")

    print("[3/3] Loading offline faster-whisper base model (English)...")
    t0 = time.time()
    base_model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    print(f"  Loaded English base model in {time.time() - t0:.2f}s")

    predictions = []
    total_audio_duration = 0.0
    total_transcription_time = 0.0

    print("\nStarting offline transcription pipeline...")
    for idx, item in enumerate(manifest, start=1):
        u = item["uuid"]
        audio_path = BASE_DIR / item["audio_path"]
        langs = item.get("languages", [])
        gold_intent = item.get("gold_intent", "")

        # Get audio duration
        info = sf.info(str(audio_path))
        dur_sec = info.duration
        total_audio_duration += dur_sec

        t_clip_start = time.time()
        
        # Route model based on language
        is_gujarati = "Gujarati" in langs and len(langs) == 1
        is_english = "English" in langs and len(langs) == 1
        is_hindi = "Hindi" in langs and not is_gujarati
        
        try:
            common_kwargs = dict(
                temperature=0.0,
                beam_size=1,
                condition_on_previous_text=False,
                vad_filter=True
            )
            if is_gujarati:
                segments, a_info = gu_model.transcribe(
                    str(audio_path),
                    language="gu",
                    initial_prompt="નમસ્તે, આઈઆઈટી ગાંધીનગર વોઇસ હેલ્પડેસ્ક.",
                    **common_kwargs
                )
                detected_lang = "gu"
            elif is_english:
                segments, a_info = base_model.transcribe(
                    str(audio_path),
                    language="en",
                    initial_prompt="Hello IITGN Voice Helpdesk query.",
                    **common_kwargs
                )
                detected_lang = "en"
            elif is_hindi:
                segments, a_info = hi_model.transcribe(
                    str(audio_path),
                    language="hi",
                    **common_kwargs
                )
                detected_lang = "hi"
            else:
                # Code-mixed
                if "Gujarati" in langs:
                    segments, a_info = gu_model.transcribe(str(audio_path), **common_kwargs)
                    detected_lang = "gu"
                else:
                    segments, a_info = hi_model.transcribe(str(audio_path), **common_kwargs)
                    detected_lang = "hi"

            raw_text = " ".join([seg.text.strip() for seg in segments])
            pred_text = clean_repetition(raw_text)

        except Exception as e:
            pred_text = f"[TRANSCRIPTION_ERROR: {str(e)}]"
            detected_lang = "error"

        clip_latency = time.time() - t_clip_start
        total_transcription_time += clip_latency
        rtf = clip_latency / dur_sec if dur_sec > 0 else 0.0

        predictions.append({
            "uuid": u,
            "original_clip_id": item["original_clip_id"],
            "original_speaker_id": item["original_speaker_id"],
            "languages": langs,
            "gold_intent": gold_intent,
            "audio_duration_sec": round(dur_sec, 2),
            "latency_sec": round(clip_latency, 2),
            "rtf": round(rtf, 3),
            "detected_language": detected_lang,
            "transcription": pred_text
        })

        if idx % 20 == 0 or idx == len(manifest):
            print(f"[{idx:3d}/{len(manifest):3d}] UUID: {u} | {dur_sec:5.1f}s audio -> {clip_latency:4.2f}s (RTF: {rtf:.2f}) | {pred_text[:65]}...")

    # Overall metrics
    overall_rtf = total_transcription_time / total_audio_duration if total_audio_duration > 0 else 0.0

    output_path = REPORTS_DIR / "offline_asr_predictions.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "Offline Indic Hybrid ASR (whisper-gujarati-ct2 + whisper-hindi-ct2 + faster-whisper-base)",
            "total_clips": len(predictions),
            "total_audio_duration_sec": round(total_audio_duration, 2),
            "total_transcription_time_sec": round(total_transcription_time, 2),
            "overall_rtf": round(overall_rtf, 3),
            "predictions": predictions
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("OFFLINE TRANSCRIPTION COMPLETE")
    print(f"Total audio processed: {total_audio_duration / 60:.1f} minutes")
    print(f"Total compute time   : {total_transcription_time / 60:.1f} minutes")
    print(f"Overall RTF          : {overall_rtf:.3f} (< 1.0 real-time threshold)")
    print(f"Predictions saved to : {output_path}")
    print("=" * 70)
    return output_path

if __name__ == "__main__":
    run_transcription()
