"""asr_wer_human.py - WER/CER of the ASR systems against the Round T human transcripts.

References: data/labels/human_transcripts.csv (A1's text on the 76 double clips, annotator-corrected
ASR drafts on single clips). Single-clip references started from the indic-v2 ASR draft, so WER of
that same system on them is optimistically biased; we therefore report the shared clips (typed
from scratch, no draft: 76 double + shared clips done by one annotator) as the primary set and the single clips separately.

Systems: asr_indic_v2 (deployed decode: Indic routing, greedy, VAD, no prompt) and the archived
hybrid decode (domain prompt). Normalisation: NFC, lower-case, punctuation/symbols removed,
[NOISE]/[UNK] tags removed; a script-normalised variant maps Gujarati letters to Devanagari.
Output: model/results/asr_wer_human.json
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

import jiwer

ROOT = Path(__file__).resolve().parents[3]


def norm(t):
    t = unicodedata.normalize("NFC", t or "")
    t = re.sub(r"\[(NOISE|MUSIC|UNK)\]", " ", t, flags=re.I)
    t = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in t.lower())
    return re.sub(r"\s+", " ", t).strip()


def script_norm(t):
    return "".join(chr(ord(ch) - 0x180) if "઀" <= ch <= "૿" else ch for ch in t)


def main():
    rows = list(csv.DictReader(open(ROOT / "data/labels/human_transcripts.csv", encoding="utf-8")))
    systems = {
        "asr_indic_v2": {r["uuid"]: r["transcription"] for r in json.loads((ROOT / "model/data/reports/asr_indic_v2_confidence.json").read_text())["clips"]},
        "asr_hybrid_prompted": {r["uuid"]: r["transcription"] for r in json.loads((ROOT / "model/data/reports/offline_asr_predictions.json").read_text())["predictions"]},
    }
    out = {"references": "data/labels/human_transcripts.csv", "n_total": len(rows), "results": {}}
    for sname, hyp in systems.items():
        res = {}
        for subset, keep in (("from_scratch_no_draft", lambda r: r["source"] in ("double_A1", "shared_one_annotator")),
                             ("single_draft_corrected", lambda r: r["source"] == "single_asr_draft_corrected")):
            sub = [r for r in rows if keep(r) and norm(r["transcript"])]
            block = {}
            for lang in ["all", "English", "Hindi", "Gujarati", "code-mixed"]:
                rr = [r for r in sub if lang == "all" or (lang == "code-mixed" and "+" in r["languages"]) or r["languages"] == lang]
                if not rr:
                    continue
                ref = [norm(r["transcript"]) for r in rr]; hy = [norm(hyp.get(r["uuid"], "")) for r in rr]
                block[lang] = {"n": len(rr), "wer": float(jiwer.wer(ref, hy)), "cer": float(jiwer.cer(ref, hy)),
                               "wer_script_normalised": float(jiwer.wer([script_norm(x) for x in ref], [script_norm(x) for x in hy]))}
            res[subset] = block
        out["results"][sname] = res
    (ROOT / "model/results/asr_wer_human.json").write_text(json.dumps(out, indent=1))
    for s, r in out["results"].items():
        for sub, b in r.items():
            print(s, sub, {k: (v["n"], round(v["wer"], 3), round(v["cer"], 3)) for k, v in b.items()})


if __name__ == "__main__":
    main()
