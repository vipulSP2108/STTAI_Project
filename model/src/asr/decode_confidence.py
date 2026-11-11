"""decode_confidence.py - Re-decode all 182 clips with the deployed Indic routing, no prompt,
and keep the decoder-confidence signals used by active learning (A1 Part D) and monitoring (A2 Part E).

Routing: language from the annotators' tag (gu -> whisper-gujarati-ct2, hi -> whisper-hindi-ct2,
en -> faster-whisper-base), same as offline_asr_predictions.json, but WITHOUT the domain prompt
that produced copy loops, and with VAD. Per clip: transcript, duration-weighted mean avg_logprob,
min segment avg_logprob, mean no_speech_prob, mean compression ratio, decode time.

Output: model/data/reports/asr_indic_v2_confidence.json (resumable)
"""
import json
import time
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "model/data/reports/asr_indic_v2_confidence.json"


def route(langs):
    return "gu" if "Gujarati" in langs else "hi" if "Hindi" in langs else "en"


def main():
    models = {"hi": WhisperModel(str(ROOT / "model/models/whisper-hindi-ct2"), device="cpu", compute_type="int8", cpu_threads=6),
              "gu": WhisperModel(str(ROOT / "model/models/whisper-gujarati-ct2"), device="cpu", compute_type="int8", cpu_threads=6),
              "en": WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=6)}
    man = sorted(json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"], key=lambda r: r["uuid"])
    done = {r["uuid"]: r for r in json.loads(OUT.read_text())["clips"]} if OUT.exists() else {}
    for i, r in enumerate(man, 1):
        if r["uuid"] in done:
            continue
        lang = route(r["languages"]); t0 = time.time()
        segs, info = models[lang].transcribe(str(ROOT / "model/data/audio" / f"{r['uuid']}.wav"), language=lang, beam_size=1, temperature=0.0,
                                             condition_on_previous_text=False, vad_filter=True)
        segs = list(segs)
        dur = np.array([max(s.end - s.start, 1e-3) for s in segs]) if segs else np.array([1.0])
        lp = np.array([s.avg_logprob for s in segs]) if segs else np.array([-5.0])
        done[r["uuid"]] = {
            "uuid": r["uuid"], "speaker": r["original_speaker_id"], "languages": r["languages"], "route": lang,
            "transcription": " ".join(s.text.strip() for s in segs).strip(),
            "avg_logprob": float((lp * dur).sum() / dur.sum()), "min_logprob": float(lp.min()),
            "no_speech_prob": float(np.mean([s.no_speech_prob for s in segs])) if segs else 1.0,
            "compression_ratio": float(np.mean([s.compression_ratio for s in segs])) if segs else 0.0,
            "n_segments": len(segs), "audio_sec": float(info.duration), "decode_sec": round(time.time() - t0, 2),
        }
        print(f"[{i}/{len(man)}] {r['uuid']} {lang} lp={done[r['uuid']]['avg_logprob']:.2f}", flush=True)
        OUT.write_text(json.dumps({"engine": "Indic routing by annotator tag, greedy (temperature 0, no fallback), VAD, no prompt",
                                   "clips": list(done.values())}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
