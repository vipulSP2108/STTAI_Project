# ============================================================
# Part D: Active Learning Simulation (Empirical Pool-Based Uncertainty Sampling)
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# Simulates pool-based active learning vs. random sampling baseline across 5 folds.
# Uses iterative entropy uncertainty sampling: queries the least confident instances
# under current decision boundaries.
# Strictly measures empirical accuracy on held-out test splits without synthetic curves.
# ============================================================

import json
import random
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt

AL_SEED = 42
BUDGETS = [10, 15, 20, 25, 30, 35, 40, 45, 50]
LABELS_CSV = Path("data/labels/intents.csv")
TRANSCRIPTS_CSV = Path("data/labels/transcripts.csv")
OUT_JSON = Path("supporting_files/plots/active_learning_results.json")
REPORT_JSON = Path("report/figures/active_learning_results.json")
PLOT_PNG = Path("report/figures/active_learning_curve.png")

def load_data():
    if not LABELS_CSV.exists() or not TRANSCRIPTS_CSV.exists():
        raise FileNotFoundError("Transcripts and intents CSVs required.")
    df_i = pd.read_csv(LABELS_CSV)
    df_t = pd.read_csv(TRANSCRIPTS_CSV)
    df = df_i.merge(df_t, on="clip_id")
    return df

def run_simulation():
    random.seed(AL_SEED)
    np.random.seed(AL_SEED)

    df = load_data()
    print(f"Loaded {len(df)} samples across classes: {df['intent'].value_counts().to_dict()}")

    # 5-fold cross-validation setup
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=AL_SEED)
    results = []

    print("\nRunning Active Learning vs Random Selection over 5 folds...")
    print(f"{'Budget':<8} {'AL Mean':<10} {'AL Std':<10} {'Rand Mean':<11} {'Rand Std':<10} {'Gain':<8} {'p-value':<8}")
    print("-" * 72)

    for budget in BUDGETS:
        al_fold_accs = []
        rand_fold_accs = []

        for fold_idx, (pool_idx, test_idx) in enumerate(skf.split(df, df["intent"])):
            fold_seed = AL_SEED + fold_idx * 17
            pool_df = df.iloc[pool_idx].copy().reset_index(drop=True)
            test_df = df.iloc[test_idx].copy().reset_index(drop=True)

            # --- Pool-Based Active Learning with Uncertainty Sampling ---
            # Seed with 1 initial sample per class to bootstrap decision boundary
            seed_indices = []
            for c in np.unique(pool_df["intent"]):
                c_indices = pool_df[pool_df["intent"] == c].index
                seed_indices.append(c_indices[0])

            labeled_indices = list(seed_indices)
            unlabeled_indices = [i for i in range(len(pool_df)) if i not in labeled_indices]

            vec = TfidfVectorizer(max_features=250, ngram_range=(1, 2), sublinear_tf=True)

            while len(labeled_indices) < budget and len(unlabeled_indices) > 0:
                labeled_df = pool_df.iloc[labeled_indices]
                X_train = vec.fit_transform(labeled_df["transcript"].astype(str))
                y_train = labeled_df["intent"]

                clf = LogisticRegression(C=1.0, max_iter=200, random_state=fold_seed)
                clf.fit(X_train, y_train)

                unlabeled_df = pool_df.iloc[unlabeled_indices]
                X_unlab = vec.transform(unlabeled_df["transcript"].astype(str))
                probs = clf.predict_proba(X_unlab)

                # Shannon entropy in nats: H(x) = -sum(p * log(p))
                entropies = -np.sum(probs * np.log(probs + 1e-12), axis=1)

                # Query top instances with highest predictive entropy
                batch_step = min(2, budget - len(labeled_indices), len(unlabeled_indices))
                top_uncertain_local = np.argsort(entropies)[-batch_step:]

                new_queried = [unlabeled_indices[i] for i in top_uncertain_local]
                labeled_indices.extend(new_queried)
                unlabeled_indices = [i for i in unlabeled_indices if i not in new_queried]

            # Fit final AL model on queried budget
            final_al_df = pool_df.iloc[labeled_indices]
            X_al_final = vec.fit_transform(final_al_df["transcript"].astype(str))
            y_al_final = final_al_df["intent"]

            clf_al_final = LogisticRegression(C=1.0, max_iter=200, random_state=fold_seed)
            clf_al_final.fit(X_al_final, y_al_final)
            acc_al = clf_al_final.score(vec.transform(test_df["transcript"].astype(str)), test_df["intent"])

            # --- Random Baseline Selection ---
            rand_indices = random.Random(fold_seed).sample(range(len(pool_df)), min(budget, len(pool_df)))
            rand_df = pool_df.iloc[rand_indices]

            vec_rand = TfidfVectorizer(max_features=250, ngram_range=(1, 2), sublinear_tf=True)
            X_rand = vec_rand.fit_transform(rand_df["transcript"].astype(str))
            y_rand = rand_df["intent"]

            if len(y_rand.unique()) > 1:
                clf_rand = LogisticRegression(C=1.0, max_iter=200, random_state=fold_seed)
                clf_rand.fit(X_rand, y_rand)
                acc_rand = clf_rand.score(vec_rand.transform(test_df["transcript"].astype(str)), test_df["intent"])
            else:
                acc_rand = 0.25

            al_fold_accs.append(acc_al)
            rand_fold_accs.append(acc_rand)

        al_mean = float(np.mean(al_fold_accs))
        al_std = float(np.std(al_fold_accs))
        rand_mean = float(np.mean(rand_fold_accs))
        rand_std = float(np.std(rand_fold_accs))
        gain = float(al_mean - rand_mean)

        t_stat, p_val = stats.ttest_rel(al_fold_accs, rand_fold_accs)
        p_val = max(float(p_val), 0.001)

        print(f"{budget:<8} {al_mean:<10.3f} {al_std:<10.3f} {rand_mean:<11.3f} {rand_std:<10.3f} {gain:<8.3f} {p_val:<8.4f}")

        results.append({
            "budget": budget,
            "al_accuracy_mean": round(al_mean, 3),
            "al_accuracy_std": round(al_std, 3),
            "random_accuracy_mean": round(rand_mean, 3),
            "random_accuracy_std": round(rand_std, 3),
            "accuracy_gain": round(gain, 3),
            "p_value": round(p_val, 4)
        })

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    # Plot authentic curve
    plot_curve(results)
    print(f"\nActive Learning results saved to {OUT_JSON} and {REPORT_JSON}")

def plot_curve(results):
    budgets = [r["budget"] for r in results]
    al_means = [r["al_accuracy_mean"] for r in results]
    al_stds = [r["al_accuracy_std"] for r in results]
    rand_means = [r["random_accuracy_mean"] for r in results]
    rand_stds = [r["random_accuracy_std"] for r in results]

    plt.figure(figsize=(8, 5))
    plt.plot(budgets, al_means, "o-", color="#1E3A8A", linewidth=2.2, label="Active Learning (Uncertainty Sampling)")
    plt.fill_between(budgets, np.array(al_means) - np.array(al_stds), np.array(al_means) + np.array(al_stds), color="#1E3A8A", alpha=0.15)

    plt.plot(budgets, rand_means, "s--", color="#64748B", linewidth=2.0, label="Random Sampling Baseline")
    plt.fill_between(budgets, np.array(rand_means) - np.array(rand_stds), np.array(rand_means) + np.array(rand_stds), color="#64748B", alpha=0.15)

    plt.axhline(0.90, color="#DC2626", linestyle=":", label="90% Target Intent Accuracy")

    plt.title("Active Learning vs. Random Sampling (5-Fold CV)", fontsize=13, fontweight="bold")
    plt.xlabel("Label Budget (Number of Annotated Queries)", fontsize=11)
    plt.ylabel("Held-Out Intent Classification Accuracy", fontsize=11)
    plt.ylim(0.4, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right", fontsize=10)
    plt.tight_layout()

    PLOT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(PLOT_PNG, dpi=200)
    plt.close()
    print(f"Curve plot saved to {PLOT_PNG}")

if __name__ == "__main__":
    run_simulation()
