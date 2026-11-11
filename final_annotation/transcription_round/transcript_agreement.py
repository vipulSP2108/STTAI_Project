"""transcript_agreement.py - Inter-annotator WER/CER for Round T and the human transcript table.

Inputs (raw Label Studio JSON exports, saved unchanged, one per annotator):
    final_annotation/transcription_round/exports/A1.json, A2.json
    The 100 shared clips are identified from order_manifest.json; the rest are single-annotated.
Outputs:
    final_annotation/transcription_round/transcript_agreement_report.json
    data/labels/human_transcripts.csv   (uuid, clip_id, transcript, source)

Agreement is reported on the 100 double clips: corpus WER/CER of A2 against A1 (and the symmetric
mean), per language, with a speaker-cluster bootstrap 95% CI. Normalisation (lower-case, strip
punctuation and [NOISE]/[MUSIC]/[UNK] tags) is applied identically to both sides. For the final
reference, the double clips use A1's text unless the adjudicator file
exports/adjudicated.json supplies a correction.

Usage: python final_annotation/transcription_round/transcript_agreement.py
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

import jiwer
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXP = HERE / "exports"


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t or "")
    t = re.sub(r"\[(NOISE|MUSIC|UNK)\]", " ", t, flags=re.I)
    t = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in t.lower())
    return re.sub(r"\s+", " ", t).strip()


def load(path):
    out = {}
    if not path.exists():
        return out
    for t in json.loads(path.read_text()):
        ann = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not ann:
            continue
        res = {r["from_name"]: r["value"] for r in ann[-1]["result"]}
        text = res.get("transcript", {}).get("text", [""])
        out[t["data"]["clip_id"]] = {
            "text": " ".join(text) if isinstance(text, list) else text,
            "intent": res.get("intent", {}).get("choices", [None])[0],
            "quality": res.get("transcript_quality", {}).get("choices", [None])[0],
            "created_at": ann[-1].get("created_at"),
            "lead_time": ann[-1].get("lead_time"),
        }
    return out


def corpus_err(refs, hyps, fn):
    pairs = [(r, h) for r, h in zip(refs, hyps) if r]
    return float(fn([r for r, _ in pairs], [h for _, h in pairs])) if pairs else None


def main():
    gold = {c["clip_id"]: c for c in json.loads((ROOT / "final_annotation/consensus_gold_182.json").read_text())["clips"]}
    man = {m["original_clip_id"]: m["uuid"] for m in json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]}
    shared = set(json.loads((HERE / "order_manifest.json").read_text())["double_100_order"])
    full1, full2 = load(EXP / "A1.json"), load(EXP / "A2.json")
    a1 = {c: v for c, v in full1.items() if c in shared}
    a2 = {c: v for c, v in full2.items() if c in shared}
    both = sorted(set(a1) & set(a2))
    if not both:
        raise SystemExit("No shared clips annotated by both: export exports/A1.json and exports/A2.json first")
    r1 = [norm(a1[c]["text"]) for c in both]; r2 = [norm(a2[c]["text"]) for c in both]
    lang = ["Code-mixed" if len(gold[c]["languages"]) > 1 else gold[c]["languages"][0] for c in both]
    spk = np.array([gold[c]["speaker_id"] for c in both])

    rng = np.random.default_rng(42); boots = []
    for _ in range(1000):
        pick = rng.choice(np.unique(spk), len(np.unique(spk)))
        idx = [i for s in pick for i in np.where(spk == s)[0]]
        boots.append(corpus_err([r1[i] for i in idx], [r2[i] for i in idx], jiwer.wer))
    per_lang = {}
    for L in sorted(set(lang)):
        ii = [i for i, l in enumerate(lang) if l == L]
        per_lang[L] = {"n": len(ii), "wer": corpus_err([r1[i] for i in ii], [r2[i] for i in ii], jiwer.wer),
                       "cer": corpus_err([r1[i] for i in ii], [r2[i] for i in ii], jiwer.cer)}
    report = {
        "n_double": len(both),
        "wer_A2_vs_A1": corpus_err(r1, r2, jiwer.wer),
        "wer_A1_vs_A2": corpus_err(r2, r1, jiwer.wer),
        "cer_A2_vs_A1": corpus_err(r1, r2, jiwer.cer),
        "wer_ci95_speaker_bootstrap": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
        "per_language": per_lang,
        "note": "Round T has a single level (transcript); intents are final from Round I + expert adjudication.",
        "per_clip": [{"clip_id": c, "language": l, "wer": float(jiwer.wer(x, y)) if x else None, "A1": a1[c]["text"], "A2": a2[c]["text"]}
                     for c, l, x, y in zip(both, lang, r1, r2)],
    }
    (HERE / "transcript_agreement_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))

    adj = json.loads((EXP / "adjudicated.json").read_text()) if (EXP / "adjudicated.json").exists() else {}
    singles = {**{c: v for c, v in full1.items() if c not in shared}, **{c: v for c, v in full2.items() if c not in shared}}
    out = ROOT / "data" / "labels" / "human_transcripts.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["uuid", "clip_id", "transcript", "source"])
        for c in sorted(gold):
            if c in adj:
                w.writerow([man[c], c, adj[c], "adjudicated"])
            elif c in a1 and c in a2:
                w.writerow([man[c], c, a1[c]["text"], "double_A1"])
            elif c in singles:
                w.writerow([man[c], c, singles[c]["text"], "single_asr_draft_corrected"])
    print(json.dumps({k: v for k, v in report.items() if k != "per_clip"}, indent=1))
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
