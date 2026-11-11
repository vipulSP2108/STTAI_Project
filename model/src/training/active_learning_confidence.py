"""active_learning_confidence.py - Decoder-confidence active learning vs random (A1 Part D, A2 Part E).

Question: if only B clips can be sent to annotators, does choosing the clips the ASR is LEAST
confident about (lowest duration-weighted avg_logprob, as the brief prescribes for Project 5)
give a better intent router than choosing clips at random?

Protocol (speaker-disjoint):
  outer StratifiedGroupKFold(5, groups=speaker) x seeds 42..46 -> held-out test speakers;
  the pool is every clip of the training speakers; budgets B = 20, 40, 60, 80, all;
  strategies: random | low_confidence | high_confidence (control) | model_entropy (uncertainty
  sampling with the router itself, batches of 10, seeded with 10 random clips);
  model: char TF-IDF + multilingual embedding logistic regression (C = 1, balanced).
The ASR text used as input is the prompt-free Indic decode (asr_indic_v2_confidence.json); the
labels are the consensus intents. Output: model/results/active_learning_confidence.json and
supporting_files/plots/active_learning_confidence.png.
"""
import json
import os
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import wilcoxon
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[3]
BUDGETS = [20, 40, 60, 80]
SEEDS = [42, 43, 44, 45, 46]


def main():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    conf = {r["uuid"]: r for r in json.loads((ROOT / "model/data/reports/asr_indic_v2_confidence.json").read_text())["clips"]}
    gold = {c["clip_id"]: c for c in json.loads((ROOT / "final_annotation/consensus_gold_182.json").read_text())["clips"]}
    man = sorted(json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"], key=lambda r: r["uuid"])
    man = [m for m in man if m["uuid"] in conf]
    texts = [conf[m["uuid"]]["transcription"] for m in man]
    y = np.array([gold[m["original_clip_id"]]["gold_intent"] for m in man])
    g = np.array([m["original_speaker_id"] for m in man])
    lp = np.array([conf[m["uuid"]]["avg_logprob"] for m in man])
    E = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            revision="e8f8c211226b894fcb81acc59f3b34ba3efd5f42", device="cpu").encode(texts, normalize_embeddings=True)

    def fit_score(tr, te, proba_on=None):
        v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, sublinear_tf=True).fit([texts[i] for i in tr])
        X = lambda idx: sparse.hstack([v.transform([texts[i] for i in idx]), sparse.csr_matrix(E[idx])]).tocsr()
        m = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced").fit(X(tr), y[tr])
        f1 = f1_score(y[te], m.predict(X(te)), average="macro", zero_division=0)
        P = m.predict_proba(X(proba_on)) if proba_on is not None and len(proba_on) else None
        return f1, P

    curves = {s: {b: [] for b in BUDGETS + ["all"]} for s in ("random", "low_confidence", "high_confidence", "model_entropy")}
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(texts, y, g):
            assert not set(g[tr]) & set(g[te])
            full, _ = fit_score(tr, te)
            for s in curves:
                curves[s]["all"].append(full)
            order = {"random": rng.permutation(tr),
                     "low_confidence": tr[np.argsort(lp[tr])],
                     "high_confidence": tr[np.argsort(-lp[tr])]}
            for s, o in order.items():
                for b in BUDGETS:
                    sel = o[:b]
                    curves[s][b].append(fit_score(sel, te)[0] if len(set(y[sel])) > 1 else 0.0)
            # uncertainty sampling with the router (entropy), batches of 10
            labelled = list(rng.choice(tr, 10, replace=False))
            for b in BUDGETS:
                while len(labelled) < b:
                    pool = np.array([i for i in tr if i not in set(labelled)])
                    if len(set(y[labelled])) < 2:
                        labelled += list(rng.choice(pool, 10, replace=False)); continue
                    _, P = fit_score(np.array(labelled), te, proba_on=pool)
                    ent = -(P * np.log(P + 1e-12)).sum(1)
                    labelled += list(pool[np.argsort(-ent)[:min(10, b - len(labelled))]])
                curves["model_entropy"][b].append(fit_score(np.array(labelled), te)[0])

    out = {"protocol": __doc__.split("Protocol")[1].split("Output")[0].strip(), "budgets": BUDGETS, "n_runs": len(SEEDS) * 5,
           "mean_macro_f1": {s: {str(b): float(np.mean(v)) for b, v in c.items()} for s, c in curves.items()},
           "sd_macro_f1": {s: {str(b): float(np.std(v)) for b, v in c.items()} for s, c in curves.items()},
           "paired_vs_random": {}}
    for s in ("low_confidence", "high_confidence", "model_entropy"):
        out["paired_vs_random"][s] = {}
        for b in BUDGETS:
            d = np.array(curves[s][b]) - np.array(curves["random"][b])
            try:
                p = float(wilcoxon(d, zero_method="zsplit").pvalue)
            except ValueError:
                p = 1.0
            out["paired_vs_random"][s][str(b)] = {"mean_delta": float(d.mean()), "wilcoxon_p": p}
    out["raw"] = {s: {str(b): [float(x) for x in v] for b, v in c.items()} for s, c in curves.items()}
    (ROOT / "model/results/active_learning_confidence.json").write_text(json.dumps(out, indent=1))

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    for s, c in [("random", "#666666"), ("low_confidence", "#1f77b4"), ("model_entropy", "#2ca02c"), ("high_confidence", "#d62728")]:
        m = [out["mean_macro_f1"][s][str(b)] for b in BUDGETS]; sd = [out["sd_macro_f1"][s][str(b)] for b in BUDGETS]
        ax.errorbar(BUDGETS, m, yerr=np.array(sd) / np.sqrt(len(SEEDS) * 5), label=s.replace("_", " "), color=c, marker="o", capsize=3)
    ax.axhline(out["mean_macro_f1"]["random"]["all"], ls="--", color="k", lw=0.8, label="all training clips")
    ax.set_xlabel("labelled clips (budget)"); ax.set_ylabel("macro-F1 on held-out speakers"); ax.legend(fontsize=8)
    ax.set_title("Active learning: decoder confidence vs random (25 runs, ±SE)")
    fig.tight_layout(); (ROOT / "supporting_files/plots").mkdir(parents=True, exist_ok=True)
    fig.savefig(ROOT / "supporting_files/plots/active_learning_confidence.png", dpi=150)
    print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=1))


if __name__ == "__main__":
    main()
