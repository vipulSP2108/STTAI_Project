"""english_view.py - Build an English "view" of every clip for the intent router.

  English clips          archived hybrid ASR text as is
  Hindi / code-mixed     archived hybrid ASR text -> Helsinki-NLP/opus-mt-hi-en (MarianMT, CPU)
  Gujarati               audio -> faster-whisper-base task="translate" (no gu->en MT model cached)

Language routing uses the language detected from audio by faster-whisper-base restricted to
{en, hi, gu} (deployable), and records the annotators' tag next to it for auditing.
Inputs never include intent labels. Output: model/data/reports/english_view.json (resumable).
"""
import json
import os
import re
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "model" / "data" / "reports"
OUT = R / "english_view.json"
MT = "Helsinki-NLP/opus-mt-hi-en"


def sentences(t, max_words=60):
    parts = [p.strip() for p in re.split(r"(?<=[.?!।])\s+", t) if p.strip()]
    out = []
    for p in parts:  # long unpunctuated ASR runs are cut into 60-word pieces
        w = p.split()
        out += [" ".join(w[i:i + max_words]) for i in range(0, len(w), max_words)]
    return out or [""]


def main():
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio
    from transformers import MarianMTModel, MarianTokenizer

    hyb = json.loads((R / "offline_asr_predictions.json").read_text())["predictions"]
    done = {r["uuid"]: r for r in json.loads(OUT.read_text())["clips"]} if OUT.exists() else {}
    tok = MarianTokenizer.from_pretrained(MT); mt = MarianMTModel.from_pretrained(MT)
    wb = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)

    def lid(path):
        audio = decode_audio(path)
        lang, prob, all_probs = wb.detect_language(audio)
        sub = {k: v for k, v in all_probs if k in ("en", "hi", "gu")}
        return max(sub, key=sub.get), sub

    for i, p in enumerate(hyb, 1):
        u = p["uuid"]
        if u in done:
            continue
        wav = str(ROOT / "model" / "data" / "audio" / f"{u}.wav")
        lang, probs = lid(wav)
        if lang == "en":
            en, how = p["transcription"], "asr_en"
        elif lang == "hi":
            sents = sentences(p["transcription"])
            outs = []
            for k in range(0, len(sents), 8):
                b = tok(sents[k:k + 8], return_tensors="pt", padding=True, truncation=True, max_length=256)
                outs += tok.batch_decode(mt.generate(**b, num_beams=2, max_new_tokens=200), skip_special_tokens=True)
            en, how = " ".join(outs), "asr_hi->opus-mt"
        else:
            segs, _ = wb.transcribe(wav, task="translate", language="gu", beam_size=1,
                                    condition_on_previous_text=False, vad_filter=True)
            en, how = " ".join(s.text.strip() for s in segs), "whisper-base translate(gu)"
        done[u] = {"uuid": u, "annotator_languages": p["languages"], "lid": lang,
                   "lid_probs": {k: round(v, 4) for k, v in probs.items()}, "method": how, "english": en}
        print(f"[{i}/{len(hyb)}] {u} {lang} {how} {len(en.split())}w", flush=True)
        OUT.write_text(json.dumps({"mt_model": MT, "lid_model": "faster-whisper-base (en/hi/gu shortlist)",
                                   "clips": list(done.values())}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
