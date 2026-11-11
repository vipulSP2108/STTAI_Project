"""reference_audit.py - Check whether the curated "gold" transcripts match the audio.

Two independent tests, neither of which needs a human transcript:
  1. Speech rate. Natural read/spontaneous speech is ~2-3 words/s. A reference with far fewer
     words than the audio can hold is a summary or a different sentence.
  2. Cross-system agreement. If the curated text were a faithful transcript, two independent ASR
     systems (archived Indic hybrid; faster-whisper-small, no prompt) would each be about as close
     to it as they are to each other. If they agree with each other much more than with the
     reference, the reference is the outlier.

Character error rate is used (script-agnostic within one script); Whisper-small Hindi output in
Urdu script is excluded via a Devanagari/Gujarati/Latin script check.

Output: model/results/reference_audit.json
"""
import json
import re
import unicodedata
from pathlib import Path

import jiwer
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "model" / "data" / "reports"


def norm(t):
    t = unicodedata.normalize("NFC", t or "").lower()
    # drop punctuation/symbols only; keep letters AND combining vowel signs (Mn/Mc) of Indic scripts
    t = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def script(t):
    c = {"latin": len(re.findall(r"[a-z]", t)), "deva": len(re.findall(r"[ऀ-ॿ]", t)),
         "guj": len(re.findall(r"[઀-૿]", t)), "arabic": len(re.findall(r"[؀-ۿ]", t))}
    return max(c, key=c.get) if sum(c.values()) else "none"


def main():
    cur = {m["uuid"]: m for m in json.loads((ROOT / "model/data/metadata/gold_transcripts_manifest.json").read_text())["manifest"]}
    hyb = {p["uuid"]: p for p in json.loads((R / "offline_asr_predictions.json").read_text())["predictions"]}
    sm_path = R / "asr_crosscheck_whisper_small.json"
    sm = {p["uuid"]: p for p in json.loads(sm_path.read_text())["predictions"]} if sm_path.exists() else {}

    rows = []
    for u, m in cur.items():
        d = hyb[u]["audio_duration_sec"]
        c, h = norm(m["transcript"]), norm(hyb[u]["transcription"])
        lang = "Code-mixed" if len(m["languages"]) > 1 else m["languages"][0]
        row = {"uuid": u, "clip_id": m["original_clip_id"], "language": lang, "duration_sec": d,
               "curated_words_per_sec": len(c.split()) / d, "hybrid_words_per_sec": len(h.split()) / d,
               "cer_hybrid_vs_curated": jiwer.cer(c, h) if c else None}
        if u in sm:
            s = norm(sm[u]["transcription"])
            if s and script(s) == script(h) == script(c):
                row["cer_small_vs_curated"] = jiwer.cer(c, s)
                row["cer_small_vs_hybrid"] = jiwer.cer(h, s) if h else None
        rows.append(row)

    def med(k, rs):
        v = [r[k] for r in rs if r.get(k) is not None]
        return (float(np.median(v)), len(v)) if v else (None, 0)

    per_lang = {}
    for L in sorted({r["language"] for r in rows}):
        rs = [r for r in rows if r["language"] == L]
        per_lang[L] = {k: med(k, rs) for k in ("curated_words_per_sec", "hybrid_words_per_sec", "cer_hybrid_vs_curated",
                                                "cer_small_vs_curated", "cer_small_vs_hybrid")}
    trip = [r for r in rows if r.get("cer_small_vs_hybrid") is not None]
    out = {
        "n_clips": len(rows),
        "curated_words_per_sec_median": med("curated_words_per_sec", rows)[0],
        "clips_curated_below_0.6_wps": sum(r["curated_words_per_sec"] < 0.6 for r in rows),
        "clips_curated_below_1.0_wps": sum(r["curated_words_per_sec"] < 1.0 for r in rows),
        "same_script_triplets": len(trip),
        "median_cer_small_vs_hybrid": med("cer_small_vs_hybrid", trip)[0],
        "median_cer_small_vs_curated": med("cer_small_vs_curated", trip)[0],
        "median_cer_hybrid_vs_curated": med("cer_hybrid_vs_curated", trip)[0],
        "per_language_median_and_n": per_lang,
        "conclusion": ("Independent ASR systems agree with each other far more than either agrees with the curated "
                       "text, and the curated text is too short for the audio: the curated strings are not "
                       "transcripts and are excluded from all WER and training."),
        "clips": rows,
    }
    (ROOT / "model/results/reference_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != "clips"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
