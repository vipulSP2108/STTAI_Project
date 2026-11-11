"""make_figures_v2.py - Report figures for the speaker-disjoint evaluation, bias and language routing.

Reads only result files under model/results/ and writes PDFs next to the report sources.
Usage: python code/report_figures/make_figures_v2.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "model/results"
OUT = ROOT / "STTAI_reports/report_final/report"
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
BLUE, GREY, RED, GREEN = "#2b6cb0", "#9aa5b1", "#c53030", "#2f855a"


def speaker_figure():
    a = json.loads((RES / "intent_v2_ablation_asr_hybrid.json").read_text())["results"]
    soft = json.loads((RES / "intent_v2_ablation_asr_hybrid_soft.json").read_text())["results"]
    cv = json.loads((RES / "speaker_cv_intent_asr_hybrid.json").read_text())["summary"]
    lid = json.loads((RES / "lid_router.json").read_text())
    bias = json.loads((RES / "bias_audit.json").read_text())
    rows = [("Majority", cv["majority"])] + [(k.split("_")[0], v) for k, v in a.items()] + \
           [(k.split("_")[0], v) for k, v in soft.items() if k.startswith("B7")]
    fig, ax = plt.subplots(1, 4, figsize=(7.2, 1.9))
    names = [r[0] for r in rows]
    m = [r[1]["fold_acc_mean"] * 100 for r in rows]; sd = [r[1]["fold_acc_sd"] * 100 for r in rows]
    ax[0].bar(names, m, yerr=sd, color=[GREY] + [BLUE] * (len(rows) - 2) + [GREEN], capsize=2)
    ax[0].set_title("(a) ablation (acc. %)"); ax[0].tick_params(axis="x", rotation=60)

    langs = ["English", "Hindi", "Gujarati", "Code-mixed"]
    b0 = a["B0_char+emb(raw)"]["per_language_seed42"]; b7 = soft["B7_B3+soft_labels"]["per_language_seed42"]
    x = np.arange(4)
    ax[1].bar(x - 0.2, [b0[l] * 100 for l in langs], 0.4, color=GREY, label="B0")
    ax[1].bar(x + 0.2, [b7[l] * 100 for l in langs], 0.4, color=GREEN, label="B7")
    ax[1].set_xticks(x, ["En", "Hi", "Gu", "Mix"]); ax[1].set_title("(b) by language (%)"); ax[1].set_ylim(0, 105); ax[1].legend(frameon=False, loc="upper center", ncol=2, fontsize=6)

    ll = ["en", "hi", "gu"]
    ax[2].bar(x[:3] - 0.2, [lid["restricted_argmax_per_lang"][l] * 100 for l in ll], 0.4, color=GREY, label="argmax")
    ax[2].bar(x[:3] + 0.2, [lid["learned_per_lang_seed42"][l] * 100 for l in ll], 0.4, color=BLUE, label="learned")
    ax[2].set_xticks(x[:3], ["En", "Hi", "Gu"]); ax[2].set_title("(c) routing (%)"); ax[2].set_ylim(0, 118); ax[2].set_yticks([0, 25, 50, 75, 100]); ax[2].legend(frameon=False, loc="upper center", ncol=2, fontsize=6)

    ps = bias["model_bias"]["per_speaker_acc"]
    n = np.array([v["n"] for v in ps.values()]); acc = np.array([v["acc"] for v in ps.values()]) * 100
    ax[3].scatter(n, acc, s=12, color=RED)
    for s_, v in ps.items():
        if v["n"] >= 14:
            ax[3].annotate(s_, (v["n"], v["acc"] * 100), fontsize=6)
    ax[3].set_xlabel("clips from speaker"); ax[3].set_title("(d) per speaker (%)")
    fig.tight_layout(); fig.savefig(OUT / "fig_f_speaker.pdf"); plt.close(fig)


def al_figure():
    p = RES / "active_learning_confidence.json"
    if not p.exists():
        return
    d = json.loads(p.read_text()); B = d["budgets"]
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    for s, c in [("random", GREY), ("low_confidence", BLUE), ("model_entropy", GREEN), ("high_confidence", RED)]:
        m = np.array([d["mean_macro_f1"][s][str(b)] for b in B]); se = np.array([d["sd_macro_f1"][s][str(b)] for b in B]) / np.sqrt(d["n_runs"])
        ax.errorbar(B, m, yerr=se, label=s.replace("_", " "), color=c, marker="o", ms=3, capsize=2)
    ax.axhline(d["mean_macro_f1"]["random"]["all"], ls="--", color="k", lw=0.7)
    ax.set_xlabel("labelled clips"); ax.set_ylabel("macro-F1 (unseen speakers)"); ax.legend(frameon=False, fontsize=6)
    fig.tight_layout(); fig.savefig(OUT / "fig_f_al_conf.pdf"); plt.close(fig)


def robustness_figure():
    p = RES / "audio_robustness.json"
    if not p.exists() or "summary" not in json.loads(p.read_text()):
        return
    d = json.loads(p.read_text())["summary"]
    names = list(d); langs = sorted(next(iter(d.values()))["by_language"])
    fig, ax = plt.subplots(figsize=(3.4, 2.1)); x = np.arange(len(names)); w = 0.8 / len(langs)
    for k, L in enumerate(langs):
        ax.bar(x + k * w - 0.4 + w / 2, [d[n]["by_language"][L] for n in names], w, label=L)
    ax.set_xticks(x, [n.split("_")[0] for n in names]); ax.set_ylabel("median drift WER vs clean"); ax.legend(frameon=False, fontsize=6)
    fig.tight_layout(); fig.savefig(OUT / "fig_f_robust.pdf"); plt.close(fig)


if __name__ == "__main__":
    speaker_figure(); al_figure(); robustness_figure()
    print("figures written to", OUT.relative_to(ROOT))
