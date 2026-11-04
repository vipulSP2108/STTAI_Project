# ============================================================
# Part D: Active Learning Publication Plot Generator
# CS203 Assignment 1 - Project 5: Voice Helpdesk ASR
#
# Plots empirical learning curve comparing Uncertainty Sampling (AL)
# vs Random Selection with +/- 1 sigma confidence intervals.
# All annotations are computed directly from the empirical results JSON —
# no numbers are hard-coded.
#
# Usage: python code/part_d_augmentation/plot_learning_curve.py
# ============================================================

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_FILE = Path("supporting_files/plots/active_learning_results.json")
OUT_FILE_1 = Path("supporting_files/plots/active_learning_curve.png")
OUT_FILE_2 = Path("report/figures/active_learning_curve.png")

TARGET_ACC = 0.90


def find_budget_at_target(budgets, means, target):
    """Return the first budget where mean accuracy >= target, or None."""
    for b, m in zip(budgets, means):
        if m >= target:
            return int(b)
    return None


def main():
    if not RESULTS_FILE.exists():
        print(f"Results file not found: {RESULTS_FILE}")
        return

    with open(RESULTS_FILE) as f:
        results = json.load(f)

    budgets   = np.array([r["budget"]              for r in results])
    al_means  = np.array([r["al_accuracy_mean"]    for r in results])
    al_stds   = np.array([r["al_accuracy_std"]     for r in results])
    rand_means = np.array([r["random_accuracy_mean"] for r in results])
    rand_stds  = np.array([r["random_accuracy_std"]  for r in results])

    # ---- Empirically derive crossing budgets for the 90% target line ----
    al_90   = find_budget_at_target(budgets, al_means,   TARGET_ACC)
    rand_90 = find_budget_at_target(budgets, rand_means, TARGET_ACC)

    # Build human-readable annotation from the data
    if al_90 is not None and rand_90 is not None and rand_90 > al_90:
        pct_gain = round(100 * (rand_90 - al_90) / rand_90)
        annot_text = (
            f"AL reaches {int(TARGET_ACC*100)}% at B={al_90}\n"
            f"Random reaches {int(TARGET_ACC*100)}% at B={rand_90}\n"
            f"({pct_gain}% fewer labels needed)"
        )
        annot_xy = (al_90, TARGET_ACC)
        annot_xytext = (al_90 + 3, TARGET_ACC - 0.14)
    elif al_90 is not None:
        annot_text = (
            f"AL reaches {int(TARGET_ACC*100)}% at B={al_90}\n"
            f"Random did not reach {int(TARGET_ACC*100)}% in budget"
        )
        annot_xy = (al_90, TARGET_ACC)
        annot_xytext = (al_90 + 3, TARGET_ACC - 0.14)
    else:
        annot_text = None

    style = "seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default"
    plt.style.use(style)
    fig, ax = plt.subplots(figsize=(8.5, 5.4), dpi=300)

    # ---- Active learning curve with ±1σ band ----
    ax.plot(budgets, al_means, "o-", color="#1f77b4",
            linewidth=2.5, markersize=7, label="Active Learning (Uncertainty Sampling)")
    ax.fill_between(
        budgets,
        np.clip(al_means - al_stds, 0, 1),
        np.clip(al_means + al_stds, 0, 1),
        color="#1f77b4", alpha=0.18, label="AL $\\pm 1\\sigma$ Band"
    )

    # ---- Random baseline curve with ±1σ band ----
    ax.plot(budgets, rand_means, "s--", color="#d62728",
            linewidth=2.2, markersize=6.5, label="Random Selection Baseline")
    ax.fill_between(
        budgets,
        np.clip(rand_means - rand_stds, 0, 1),
        np.clip(rand_means + rand_stds, 0, 1),
        color="#d62728", alpha=0.15, label="Random $\\pm 1\\sigma$ Band"
    )

    # ---- 90% target line ----
    ax.axhline(TARGET_ACC, color="#2ca02c", linestyle=":", linewidth=1.8,
               label=f"{int(TARGET_ACC*100)}% Accuracy Target")

    # ---- Annotate empirical crossing point (computed, not hard-coded) ----
    if annot_text and al_90 is not None:
        ax.axvline(al_90, color="#1f77b4", linestyle=":", linewidth=1.1, alpha=0.55)
        if rand_90 is not None:
            ax.axvline(rand_90, color="#d62728", linestyle=":", linewidth=1.1, alpha=0.55)
        ax.annotate(
            annot_text,
            xy=annot_xy,
            xytext=annot_xytext,
            arrowprops=dict(facecolor="#2ca02c", shrink=0.06, width=1.4, headwidth=7),
            fontsize=9.5, fontweight="bold", color="#1b5e20",
            bbox=dict(boxstyle="round,pad=0.4", fc="#e8f5e9", ec="#2ca02c", lw=1.2)
        )

    # ---- Note on dataset saturation at high budgets ----
    ax.text(
        0.98, 0.07,
        ("Note: TF-IDF + Logistic Regression on this 4-class corpus (n=249)\n"
         "saturates near perfect accuracy at higher budgets."),
        transform=ax.transAxes, fontsize=8.5, ha="right", va="bottom",
        color="#555555", style="italic",
        bbox=dict(boxstyle="round,pad=0.3", fc="#f9f9f9", ec="#cccccc", lw=0.8)
    )

    ax.set_xlabel("Annotation Budget $B$ (Number of Query Clips)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Intent Classification Accuracy (5-Fold CV)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Active Learning vs. Random Sampling — Label Efficiency\n"
        "(IITGN Voice Helpdesk Corpus · TF-IDF + Logistic Regression · 5-Fold CV)",
        fontsize=12, fontweight="bold", pad=12
    )
    ax.set_xticks(budgets)
    ax.set_ylim(0.30, 1.05)
    ax.legend(loc="lower right", fontsize=9.5, frameon=True, framealpha=0.92)
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    OUT_FILE_1.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUT_FILE_1), dpi=300, bbox_inches="tight")
    OUT_FILE_2.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUT_FILE_2), dpi=300, bbox_inches="tight")
    print(f"Learning curve saved to:\n  - {OUT_FILE_1}\n  - {OUT_FILE_2}")
    if al_90 or rand_90:
        print(f"\n  Empirical 90% crossing: AL={al_90}, Random={rand_90}")


if __name__ == "__main__":
    main()
