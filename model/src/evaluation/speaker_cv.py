"""speaker_cv.py - Speaker-disjoint intent evaluation on the 182-clip final corpus.

Why this exists
---------------
The earlier folds (group_splitter.py) grouped by *clip*, so every validation speaker was also
in training, and the "unseen speaker" benchmark reused fold-1 speakers. This script groups by
*speaker*, so no speaker ever appears on both sides of a split.

Protocol
--------
* Labels: consensus intent (final_annotation/consensus_gold_182.json; human double annotation
  plus expert adjudication).
* Inputs (one text source per run, chosen with --source):
    asr_hybrid  archived Indic hybrid ASR (model/data/reports/offline_asr_predictions.json)
    asr_small   independent faster-whisper-small pass (asr_crosscheck_whisper_small.json)
    asr_indic_v2 prompt-free Indic decode, temperature 0, VAD (asr_indic_v2_confidence.json)
    curated     hard-coded curated references; DIAGNOSTIC ONLY (provenance unverified)
    human       human transcripts, once data/labels/human_transcripts.csv exists
* Outer loop: StratifiedGroupKFold(5, groups=speaker), repeated over 5 seeds.
* Inner loop: hyper-parameter C chosen by GroupKFold(3) on the outer-training speakers only,
  so no test speaker influences model selection.
* Reported: mean +/- s.d. over the 25 outer folds, pooled out-of-fold accuracy and macro-F1
  with speaker-cluster bootstrap 95% CIs, paired comparisons against the best baseline,
  per-language / per-speaker slices, and leave-one-speaker-out (LOSO) accuracy per speaker.

Usage:
    python model/src/evaluation/speaker_cv.py --source asr_hybrid
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import binomtest, wilcoxon
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "final_annotation" / "consensus_gold_182.json"
MANIFEST = ROOT / "model" / "data" / "metadata" / "internal_manifest.json"
REPORTS = ROOT / "model" / "data" / "reports"
RESULTS = ROOT / "model" / "results"
EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMB_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
SEEDS = [42, 43, 44, 45, 46]
C_GRID = [0.1, 1.0, 10.0]
CLASSES = ["admissions", "hostel_mess", "it_support", "student_services"]


def load_corpus(source: str):
    manifest = json.loads(MANIFEST.read_text())["manifest"]
    by_clip = {m["original_clip_id"]: m for m in manifest}
    gold = json.loads(GOLD.read_text())["clips"]
    if source == "asr_hybrid":
        rows = json.loads((REPORTS / "offline_asr_predictions.json").read_text())["predictions"]
        text = {r["uuid"]: r["transcription"] for r in rows}
    elif source == "asr_small":
        rows = json.loads((REPORTS / "asr_crosscheck_whisper_small.json").read_text())["predictions"]
        text = {r["uuid"]: r["transcription"] for r in rows}
    elif source == "asr_indic_v2":
        rows = json.loads((REPORTS / "asr_indic_v2_confidence.json").read_text())["clips"]
        text = {r["uuid"]: r["transcription"] for r in rows}
    elif source == "curated":
        rows = json.loads((ROOT / "model/data/metadata/gold_transcripts_manifest.json").read_text())["manifest"]
        text = {r["uuid"]: r["transcript"] for r in rows}
    elif source == "human":
        import csv
        with open(ROOT / "data" / "labels" / "human_transcripts.csv", newline="", encoding="utf-8") as f:
            text = {r["uuid"]: r["transcript"] for r in csv.DictReader(f)}
    else:
        raise SystemExit(f"unknown source {source}")

    items = []
    for g in gold:
        m = by_clip[g["clip_id"]]
        if m["uuid"] not in text:
            continue
        langs = g["languages"]
        items.append({
            "uuid": m["uuid"],
            "clip_id": g["clip_id"],
            "speaker": g["speaker_id"],
            "intent": g["gold_intent"],
            "language": langs[0] if len(langs) == 1 else "Code-mixed",
            "resolution": g["resolution_source"],
            "a1": g.get("a1_intent"), "a2": g.get("a2_intent"),
            "text": text[m["uuid"]] or "",
        })
    return items


def embed(texts):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMB_MODEL, revision=EMB_REVISION, device="cpu")
    return model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)


class Majority:
    def fit(self, X, y, groups):
        self.label = Counter(y).most_common(1)[0][0]
        return self

    def predict(self, X):
        return np.array([self.label] * X.shape[0])


def make_features(kind, train_idx, test_idx, texts, emb):
    if kind == "word":
        # whitespace tokens: the default regex splits Devanagari/Gujarati words at vowel signs
        v = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True,
                            tokenizer=lambda t: re.sub(r"[^\w\s\u0900-\u0AFF]", " ", t).split(),
                            token_pattern=None, lowercase=True)
    elif kind in ("char", "char+emb"):
        v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
    if kind == "emb":
        return emb[train_idx], emb[test_idx]
    tr = v.fit_transform([texts[i] for i in train_idx])
    te = v.transform([texts[i] for i in test_idx])
    if kind == "char+emb":
        tr = sparse.hstack([tr, sparse.csr_matrix(emb[train_idx])]).tocsr()
        te = sparse.hstack([te, sparse.csr_matrix(emb[test_idx])]).tocsr()
    return tr, te


def fit_predict(kind, train_idx, test_idx, texts, emb, y, groups, seed):
    """Nested selection of C on training speakers only, then refit and predict."""
    if kind == "majority":
        clf = Majority().fit(None, y[train_idx], None)
        return clf.predict(np.zeros((len(test_idx), 1))), None
    inner = GroupKFold(n_splits=3)
    best_c, best_f1 = C_GRID[0], -1.0
    for c in C_GRID:
        scores = []
        for itr, iva in inner.split(train_idx, y[train_idx], groups[train_idx]):
            a, b = train_idx[itr], train_idx[iva]
            Xa, Xb = make_features(kind, a, b, texts, emb)
            m = LogisticRegression(C=c, max_iter=3000, class_weight="balanced", random_state=seed)
            m.fit(Xa, y[a])
            scores.append(f1_score(y[b], m.predict(Xb), average="macro", zero_division=0))
        if np.mean(scores) > best_f1:
            best_c, best_f1 = c, float(np.mean(scores))
    Xtr, Xte = make_features(kind, train_idx, test_idx, texts, emb)
    m = LogisticRegression(C=best_c, max_iter=3000, class_weight="balanced", random_state=seed)
    m.fit(Xtr, y[train_idx])
    return m.predict(Xte), best_c


def cluster_bootstrap(y, p, groups, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    spk = np.unique(groups)
    idx_by = {s: np.where(groups == s)[0] for s in spk}
    accs, f1s = [], []
    for _ in range(n):
        pick = rng.choice(spk, size=len(spk), replace=True)
        ii = np.concatenate([idx_by[s] for s in pick])
        accs.append(accuracy_score(y[ii], p[ii]))
        f1s.append(f1_score(y[ii], p[ii], average="macro", zero_division=0))
    return [float(np.percentile(accs, 2.5)), float(np.percentile(accs, 97.5))], \
           [float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="asr_hybrid")
    ap.add_argument("--models", default="majority,word,char,emb,char+emb")
    args = ap.parse_args()

    items = load_corpus(args.source)
    texts = [it["text"] for it in items]
    y = np.array([it["intent"] for it in items])
    groups = np.array([it["speaker"] for it in items])
    langs = np.array([it["language"] for it in items])
    emb = embed(texts)
    kinds = args.models.split(",")
    t0 = time.time()

    # ---- repeated speaker-grouped CV -------------------------------------------------
    fold_scores = {k: {"acc": [], "f1": []} for k in kinds}
    oof = {k: {s: np.empty(len(y), dtype=object) for s in SEEDS} for k in kinds}
    chosen_c = defaultdict(list)
    fold_audit = []
    for seed in SEEDS:
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        for f, (tr, te) in enumerate(sgkf.split(texts, y, groups)):
            overlap = set(groups[tr]) & set(groups[te])
            assert not overlap, f"speaker leakage {overlap}"
            fold_audit.append({"seed": seed, "fold": f, "n_train": int(len(tr)), "n_test": int(len(te)),
                               "test_speakers": sorted(set(groups[te].tolist())), "speaker_overlap": 0})
            for k in kinds:
                p, c = fit_predict(k, tr, te, texts, emb, y, groups, seed)
                oof[k][seed][te] = p
                if c is not None:
                    chosen_c[k].append(c)
                fold_scores[k]["acc"].append(accuracy_score(y[te], p))
                fold_scores[k]["f1"].append(f1_score(y[te], p, average="macro", zero_division=0))

    summary = {}
    for k in kinds:
        p = oof[k][SEEDS[0]].astype(str)
        acc_ci, f1_ci = cluster_bootstrap(y, p, groups)
        per_lang = {}
        for lg in sorted(set(langs)):
            m = langs == lg
            per_lang[lg] = {"n": int(m.sum()), "acc": float(accuracy_score(y[m], p[m]))}
        summary[k] = {
            "fold_acc_mean": float(np.mean(fold_scores[k]["acc"])),
            "fold_acc_sd": float(np.std(fold_scores[k]["acc"])),
            "fold_f1_mean": float(np.mean(fold_scores[k]["f1"])),
            "fold_f1_sd": float(np.std(fold_scores[k]["f1"])),
            "pooled_seed42_acc": float(accuracy_score(y, p)),
            "pooled_seed42_acc_ci95_speaker_bootstrap": acc_ci,
            "pooled_seed42_macro_f1": float(f1_score(y, p, average="macro", zero_division=0)),
            "pooled_seed42_macro_f1_ci95_speaker_bootstrap": f1_ci,
            "per_language_seed42": per_lang,
            "chosen_C_counts": dict(Counter(chosen_c[k])) if chosen_c[k] else None,
        }

    # ---- paired comparisons vs majority and vs char ----------------------------------
    paired = {}
    ref_models = [m for m in ("char", "majority") if m in kinds]
    for ref in ref_models:
        for k in kinds:
            if k == ref:
                continue
            a = np.array(fold_scores[k]["f1"]); b = np.array(fold_scores[ref]["f1"])
            try:
                w = wilcoxon(a, b, zero_method="zsplit")
                wp = float(w.pvalue)
            except ValueError:
                wp = 1.0
            pk = oof[k][SEEDS[0]].astype(str); pr = oof[ref][SEEDS[0]].astype(str)
            k_right = (pk == y) & (pr != y); r_right = (pr == y) & (pk != y)
            n_disc = int(k_right.sum() + r_right.sum())
            mc = float(binomtest(int(k_right.sum()), n_disc, 0.5).pvalue) if n_disc else 1.0
            paired[f"{k}_vs_{ref}"] = {
                "mean_fold_f1_delta": float(np.mean(a - b)),
                "wilcoxon_p_25_folds": wp,
                "mcnemar_exact_p_seed42": mc,
                "discordant": [int(k_right.sum()), int(r_right.sum())],
            }

    # ---- leave-one-speaker-out for the best model: per-speaker bias -----------------
    best = max((k for k in kinds if k != "majority"), key=lambda k: summary[k]["fold_f1_mean"])
    loso_pred = np.empty(len(y), dtype=object)
    for tr, te in LeaveOneGroupOut().split(texts, y, groups):
        p, _ = fit_predict(best, tr, te, texts, emb, y, groups, 42)
        loso_pred[te] = p
    loso_pred = loso_pred.astype(str)
    per_speaker = {}
    for s in sorted(set(groups), key=lambda s: int(s[1:])):
        m = groups == s
        per_speaker[s] = {"n": int(m.sum()), "acc": float(accuracy_score(y[m], loso_pred[m])),
                          "languages": dict(Counter(langs[m].tolist()))}

    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": args.source,
        "n_clips": len(y),
        "n_speakers": int(len(set(groups))),
        "class_counts": dict(Counter(y.tolist())),
        "protocol": "StratifiedGroupKFold(5, groups=speaker) x seeds " + str(SEEDS)
                    + "; inner GroupKFold(3) on training speakers selects C from " + str(C_GRID),
        "embedding_model": f"{EMB_MODEL}@{EMB_REVISION}",
        "runtime_sec": round(time.time() - t0, 1),
        "summary": summary,
        "paired_tests": paired,
        "loso_model": best,
        "loso_accuracy": float(accuracy_score(y, loso_pred)),
        "loso_macro_f1": float(f1_score(y, loso_pred, average="macro", zero_division=0)),
        "loso_per_speaker": per_speaker,
        "fold_audit": fold_audit,
        "oof_predictions_seed42": [
            {"uuid": it["uuid"], "speaker": it["speaker"], "language": it["language"], "true": it["intent"],
             **{k: str(oof[k][42][i]) for k in kinds}, "loso_" + best: str(loso_pred[i])}
            for i, it in enumerate(items)
        ],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"speaker_cv_intent_{args.source}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {path.relative_to(ROOT)}")
    for k in kinds:
        s = summary[k]
        print(f"{k:10s} acc {s['fold_acc_mean']:.3f}±{s['fold_acc_sd']:.3f}  F1 {s['fold_f1_mean']:.3f}±{s['fold_f1_sd']:.3f}"
              f"  pooled acc {s['pooled_seed42_acc']:.3f} CI {[round(x,3) for x in s['pooled_seed42_acc_ci95_speaker_bootstrap']]}")
    print("LOSO", best, round(out["loso_accuracy"], 3))


if __name__ == "__main__":
    main()
