"""release_eval.py - Held-out evaluation on the speaker-disjoint release split.

Split: model/data/splits/release_speakers.json (validation P12/P14/P20/P22, test P3/P8/P18/P19,
all other speakers train). Text input: archived Indic ASR transcripts (offline_asr_predictions.json).

Systems (all trained on ASR text of training speakers; selection on validation speakers only):
  B0 majority class
  B1 v1 router: char TF-IDF + LR, hard consensus labels (what the deployed image used, but on ASR text)
  P  v2 router (router_v2.IntentRouter): cleaned text, char TF-IDF + chunk + opening embeddings, soft labels
The candidate with the higher VALIDATION macro-F1 is declared the release router BEFORE the test
split is scored; the test split is then scored once and the access is appended to TEST_SET_LOG.md.
Also evaluates the learned language router (train+val speakers -> test speakers).

Output: model/results/release_eval.json
Usage:  python model/src/evaluation/release_eval.py
"""
import csv
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code" / "a2_part_d_deployment"))
from router_v2 import Embedder, IntentRouter, LangRouter, clean_text, route_label  # noqa: E402


def load():
    gold = {c["clip_id"]: c for c in json.loads((ROOT / "final_annotation/consensus_gold_182.json").read_text())["clips"]}
    asr = {p["uuid"]: p["transcription"] for p in json.loads((ROOT / "model/data/reports/offline_asr_predictions.json").read_text())["predictions"]}
    split = json.loads((ROOT / "model/data/splits/release_speakers.json").read_text())
    rows = {"train": [], "validation": [], "test": []}
    with open(ROOT / "model/data/metadata/metadata_182.csv", encoding="utf-8-sig") as f:
        for m in csv.DictReader(f):
            g = gold[m["original_clip_id"]]
            spk = m["original_speaker_id"]
            part = "test" if spk in split["test"] else "validation" if spk in split["validation"] else "train"
            rows[part].append({"uuid": m["uuid"], "speaker": spk, "text": asr[m["uuid"]], "intent": g["gold_intent"],
                               "a1": g["a1_intent"], "a2": g["a2_intent"], "languages": g["languages"],
                               "language": "Code-mixed" if len(g["languages"]) > 1 else g["languages"][0]})
    for k in rows:
        rows[k].sort(key=lambda r: r["uuid"])
    return rows


def scores(y, p, spk, n=2000):
    y, p, spk = np.array(y), np.array(p), np.array(spk)
    rng = np.random.default_rng(42); u = np.unique(spk); acc, f1 = [], []
    for _ in range(n):
        ii = np.concatenate([np.where(spk == s)[0] for s in rng.choice(u, len(u))])
        acc.append(accuracy_score(y[ii], p[ii])); f1.append(f1_score(y[ii], p[ii], average="macro", zero_division=0))
    return {"n": int(len(y)), "accuracy": float(accuracy_score(y, p)), "macro_f1": float(f1_score(y, p, average="macro", zero_division=0)),
            "accuracy_ci95_speaker_bootstrap": [float(np.percentile(acc, 2.5)), float(np.percentile(acc, 97.5))],
            "macro_f1_ci95_speaker_bootstrap": [float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5))]}


def main():
    rows = load()
    tr, va, te = rows["train"], rows["validation"], rows["test"]
    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "sizes": {k: len(v) for k, v in rows.items()},
           "speakers": {k: sorted({r["speaker"] for r in v}) for k, v in rows.items()}}
    assert not ({r["speaker"] for r in tr} & {r["speaker"] for r in te}) and not ({r["speaker"] for r in va} & {r["speaker"] for r in te})

    # ---- selection on validation only ----------------------------------------------
    maj = Counter(r["intent"] for r in tr).most_common(1)[0][0]
    best_v1, v1_scores = None, {}
    for C in [0.1, 0.3, 1.0, 3.0, 10.0]:
        m = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
                          LogisticRegression(C=C, max_iter=3000, class_weight="balanced", random_state=42))
        m.fit([r["text"] for r in tr], [r["intent"] for r in tr])
        v1_scores[C] = float(f1_score([r["intent"] for r in va], m.predict([r["text"] for r in va]), average="macro", zero_division=0))
    c1 = max(v1_scores, key=v1_scores.get)
    v1 = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
                       LogisticRegression(C=c1, max_iter=3000, class_weight="balanced", random_state=42))
    v1.fit([r["text"] for r in tr + va], [r["intent"] for r in tr + va])

    emb = Embedder()
    # validation scores come from train-only fits (comparable to v1); the model is then refit on train+val
    v2 = IntentRouter(emb, label_mode="expert")            # team decision: train on the expert-final labels
    sel = v2.select_and_fit(tr, va)
    soft_val = IntentRouter(emb, label_mode="soft").select_and_fit(tr, va)   # validation-only comparison
    out["selection"] = {"v1_validation_macro_f1_by_C": v1_scores, "v1_selected_C": c1,
                        "v2_validation_macro_f1_by_C": sel["validation_macro_f1_by_C"], "v2_selected_C": sel["selected_C"],
                        "v2_label_mode": "expert",
                        "soft_label_validation_macro_f1_by_C (not tested)": soft_val["validation_macro_f1_by_C"]}
    release = "v2" if max(sel["validation_macro_f1_by_C"].values()) >= max(v1_scores.values()) else "v1"
    out["release_router_chosen_on_validation"] = release

    # ---- single test evaluation -------------------------------------------------------
    y = [r["intent"] for r in te]; spk = [r["speaker"] for r in te]
    p0 = [maj] * len(te)
    p1 = list(v1.predict([r["text"] for r in te]))
    cls, P = v2.predict_proba([r["text"] for r in te]); p2 = list(cls[P.argmax(1)])
    out["test"] = {"B0_majority": scores(y, p0, spk), "B1_v1_char": scores(y, p1, spk), "P_v2": scores(y, p2, spk)}
    a = np.array(p2) == np.array(y); b = np.array(p1) == np.array(y)
    out["test"]["mcnemar_v2_vs_v1"] = {"v2_only_right": int((a & ~b).sum()), "v1_only_right": int((b & ~a).sum()),
                                       "exact_p": float(binomtest(int((a & ~b).sum()), int((a ^ b).sum()), 0.5).pvalue) if (a ^ b).any() else 1.0}
    out["test"]["per_language_v2"] = {L: float(np.mean([pp == r["intent"] for pp, r in zip(p2, te) if r["language"] == L]))
                                      for L in sorted({r["language"] for r in te})}
    out["test"]["confidence_v2"] = {"mean_when_right": float(P.max(1)[a].mean()), "mean_when_wrong": float(P.max(1)[~a].mean()) if (~a).any() else None}
    out["test"]["predictions"] = [{"uuid": r["uuid"], "speaker": r["speaker"], "true": r["intent"], "v1": q1, "v2": q2,
                                   "v2_confidence": float(pr.max())} for r, q1, q2, pr in zip(te, p1, p2, P)]

    # ---- language router: train+val speakers -> test speakers -------------------------
    feats = json.loads((ROOT / "model/data/reports/lid_features.json").read_text())
    lr = LangRouter().fit(feats, tr + va)
    lid_pred = [lr.predict(feats[r["uuid"]])[0] for r in te]
    lid_true = [route_label(r["languages"]) for r in te]
    keys = ["en", "hi", "gu"]
    base = [max(keys, key=lambda k: feats[r["uuid"]][k]) for r in te]
    out["test"]["language_router"] = {"learned_acc": float(np.mean(np.array(lid_pred) == np.array(lid_true))),
                                      "restricted_argmax_acc": float(np.mean(np.array(base) == np.array(lid_true))),
                                      "counts": dict(Counter(lid_true))}

    (ROOT / "model/results/release_eval.json").write_text(json.dumps(out, indent=1))
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    with open(ROOT / "TEST_SET_LOG.md", "a") as f:
        f.write(f"| `REL-{time.strftime('%Y%m%d-%H%M')}` | {time.strftime('%Y-%m-%dT%H:%M:%S')} | `{commit}`+working tree | "
                f"router {release} expert-label (re-run after team switched from soft to expert labels) | release test split, 40 clips, speakers P3/P8/P18/P19; "
                f"text = archived Indic ASR | n/a (not the pilot gold) | - | {out['test']['P_v2']['accuracy']:.3f} | **EVALUATED ONCE** |\n")
    print(json.dumps({k: v for k, v in out.items() if k != "test"}, indent=1))
    print(json.dumps({k: v for k, v in out["test"].items() if k != "predictions"}, indent=1))


if __name__ == "__main__":
    main()
