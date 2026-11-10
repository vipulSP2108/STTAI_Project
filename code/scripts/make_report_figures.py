#!/usr/bin/env python3
"""
make_report_figures.py  --  regenerates every figure used in report_A1.tex / report_A2.tex.

Run from the repository root:
    python code/scripts/make_report_figures.py            # writes report/figures_v2/*.pdf + *.png

Every number plotted is read from a file that is already in the repository
(data/, supporting_files/, artefacts/); nothing is hard-coded except the two
gate decisions that come from TEST_SET_LOG.md (documented below).
"""
import glob, json, os, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec
from scipy import signal
from scipy.io import wavfile
from sklearn.metrics import cohen_kappa_score, confusion_matrix

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "report" / "figures_v2"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- style ----
for f in glob.glob("/usr/share/fonts/opentype/linux-libertine/*.otf"):
    fm.fontManager.addfont(f)
FONT = "Linux Libertine O" if any(f.name == "Linux Libertine O" for f in fm.fontManager.ttflist) else "DejaVu Serif"
plt.rcParams.update({
    "font.family": FONT, "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.grid": True,
    "grid.color": "#dddddd", "grid.linewidth": 0.5, "grid.alpha": 0.9,
    "axes.axisbelow": True, "figure.dpi": 150, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "mathtext.default": "regular",
    "pdf.fonttype": 42,
})
BLUE, ORANGE, TEAL, PURPLE, RED, GREY, GOLD = "#1f4e79", "#d95f02", "#1b9e77", "#7570b3", "#c0392b", "#7f8c8d", "#c9a227"
SPLIT_COL = {"train": BLUE, "val": TEAL, "test": ORANGE, "cohort_b": PURPLE}
INTENTS = ["admissions", "hostel_mess", "it_support", "student_services"]
INT_SHORT = ["adm.", "host.", "IT", "stud."]


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)


def panel(ax, letter):
    ax.text(-0.02, 1.04, f"({letter})", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


# ----------------------------------------------------------------- data ----
meta = pd.read_csv(ROOT / "data/metadata.csv")
intents = pd.read_csv(ROOT / "data/labels/intents.csv")
splits = {s: pd.read_csv(ROOT / f"data/splits/{s}.csv") for s in ["train", "val", "test", "cohort_b_shifted"]}
splits["cohort_b"] = splits.pop("cohort_b_shifted")
spk_split = {}
for s, d in splits.items():
    for sp in d.speaker_id.unique():
        spk_split[sp] = s
meta["split"] = meta.speaker_id.map(spk_split)
cache = json.load(open(ROOT / "data/processed/whisper_base_eval_cache.json"))
ev = json.load(open(ROOT / "supporting_files/evaluation_results.json"))
pred = pd.read_csv(ROOT / "supporting_files/predictions/production_gold.csv")
pred["is_correct"] = pred.is_correct.astype(bool)

# =========================================================== A1 FIGURES =====
# ---- A1-1 dataset composition (double column)
fig = plt.figure(figsize=(7.1, 4.3))
gs = gridspec.GridSpec(2, 3, hspace=0.62, wspace=0.42)
ax = fig.add_subplot(gs[0, 0]); panel(ax, "a")
vc = intents.intent.value_counts().reindex(INTENTS)
ax.bar(range(4), vc.values, color=[BLUE, TEAL, ORANGE, PURPLE], width=0.7)
for i, v in enumerate(vc.values):
    ax.text(i, v + 1, str(v), ha="center", fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels(["admis-\nsions", "hostel/\nmess", "IT\nsupport", "student\nservices"], fontsize=6.6)
ax.set_ylabel("clips"); ax.set_ylim(0, 78); ax.set_title("Intent balance (n = 249)", loc="left")

ax = fig.add_subplot(gs[0, 1:]); panel(ax, "b")
order = (meta.groupby(["split", "speaker_id"]).size().reset_index(name="n")
         .assign(o=lambda d: d.split.map({"train": 0, "val": 1, "test": 2, "cohort_b": 3}))
         .sort_values(["o", "n"], ascending=[True, False]))
ax.bar(range(len(order)), order.n, color=[SPLIT_COL[s] for s in order.split], width=0.75)
ax.set_xticks(range(len(order))); ax.set_xticklabels(order.speaker_id, rotation=90, fontsize=6.5)
ax.set_ylabel("clips per speaker"); ax.set_title("Speaker-disjoint splits (19 speakers)", loc="left")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=SPLIT_COL[s], label=lab) for s, lab in [("train", "train 171"), ("val", "val 17"), ("test", "test/gold 29"), ("cohort_b", "Cohort B 32")]],
          ncol=4, loc="upper right", frameon=False, fontsize=7, columnspacing=0.9, handlelength=1)
ax.set_ylim(0, 52)

ax = fig.add_subplot(gs[1, 0]); panel(ax, "c")
nc = meta.noise_condition.value_counts()
ax.barh(range(len(nc)), nc.values, color=GREY)
ax.set_yticks(range(len(nc))); ax.set_yticklabels([n.replace("_", " ") for n in nc.index], fontsize=7)
ax.invert_yaxis(); ax.set_xlabel("clips"); ax.set_title("Acoustic condition", loc="left")
for i, v in enumerate(nc.values):
    ax.text(v + 1.5, i, str(v), va="center", fontsize=7)
ax.set_xlim(0, 118)

ax = fig.add_subplot(gs[1, 1]); panel(ax, "d")
rg = meta.region.value_counts()
lm = meta.lang_mix.value_counts()
labels = list(rg.index) + list(lm.index)
vals = list(rg.values) + list(lm.values)
cols = [BLUE] * len(rg) + [ORANGE] * len(lm)
ax.barh(range(len(vals)), vals, color=cols)
ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=7)
ax.invert_yaxis(); ax.set_xlabel("clips"); ax.set_title("Region (blue) / language mix (orange)", loc="left", fontsize=8)
ax.set_xlim(0, 130)
for i, v in enumerate(vals):
    ax.text(v + 1.5, i, str(v), va="center", fontsize=7)

ax = fig.add_subplot(gs[1, 2]); panel(ax, "e")
ax.hist(meta.duration_sec, bins=18, color=TEAL, edgecolor="white", linewidth=0.4)
ax.axvline(meta.duration_sec.mean(), color=RED, lw=1, ls="--")
ax.text(meta.duration_sec.mean() + 0.5, ax.get_ylim()[1] * 0.93, f"mean {meta.duration_sec.mean():.1f} s", color=RED, fontsize=7)
ax.set_xlabel("clip duration (s)"); ax.set_ylabel("clips")
ax.set_title(f"Total {meta.duration_sec.sum()/60:.1f} min", loc="left")
save(fig, "fig_a1_dataset")

# ---- A1-2 agreement: confusion matrices
def load_ls(path):
    out = {}
    for t in json.load(open(path)):
        cid = t["data"]["clip_id"]
        for r in t["annotations"][0]["result"]:
            if r["type"] == "choices":
                out[cid] = r["value"]["choices"][0]
    return out

fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.45), gridspec_kw={"width_ratios": [1, 1, 0.75], "wspace": 0.42})
kap = {}
for ax, rnd, lab in zip(axes[:2], ["round1", "round2"], ["Round 1 (guidelines v1)", "Round 2 (guidelines v2)"]):
    a = load_ls(ROOT / f"supporting_files/label_studio_exports/{rnd}_annotator_a.json")
    b = load_ls(ROOT / f"supporting_files/label_studio_exports/{rnd}_annotator_b.json")
    ids = sorted(set(a) & set(b))
    ya, yb = [a[i] for i in ids], [b[i] for i in ids]
    kap[rnd] = (cohen_kappa_score(ya, yb), np.mean(np.array(ya) == np.array(yb)), len(ids))
    cm = confusion_matrix(ya, yb, labels=INTENTS)
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=40)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8,
                    color="white" if cm[i, j] > 20 else ("#333333" if cm[i, j] else "#aaaaaa"),
                    fontweight="bold" if i != j and cm[i, j] else "normal")
    ax.set_xticks(range(4)); ax.set_xticklabels(INT_SHORT); ax.set_yticks(range(4)); ax.set_yticklabels(INT_SHORT)
    ax.set_xlabel("annotator A2"); ax.grid(False)
    ax.set_title(f"{lab}\n$\\kappa$ = {kap[rnd][0]:.3f}, agree {kap[rnd][1]*100:.1f}%", fontsize=8)
axes[0].set_ylabel("annotator A1")
ax = axes[2]
ax.bar([0, 1], [kap["round1"][0], kap["round2"][0]], color=[ORANGE, TEAL], width=0.55)
for x, k in zip([0, 1], [kap["round1"][0], kap["round2"][0]]):
    ax.text(x, k + 0.015, f"{k:.3f}", ha="center", fontsize=8)
for y, lab in [(0.61, "substantial $\\geq$ 0.61"), (0.81, "almost perfect $\\geq$ 0.81")]:
    ax.axhline(y, color=GREY, lw=0.6, ls=":")
    ax.text(-0.42, y + 0.006, lab, fontsize=6.0, color=GREY, ha="left")
ax.set_xticks([0, 1]); ax.set_xticklabels(["v1", "v2"]); ax.set_ylim(0.5, 1.03); ax.set_xlim(-0.45, 1.45)
ax.set_ylabel("Cohen's $\\kappa$"); ax.set_title("Effect of guideline\nrevision", fontsize=8)
save(fig, "fig_a1_agreement")
json.dump({k: {"kappa": v[0], "agreement": v[1], "n": v[2]} for k, v in kap.items()},
          open(OUT / "recomputed_kappa.json", "w"), indent=1)

# ---- A1-3 augmentation spectrograms + WER bars
aug_dir = ROOT / "data/processed/augmented"
stem = "P6_temp_P6_PTT-20261018-WA0016_seg001"
conds = [("musan", "MUSAN noise (12 dB SNR)"), ("rir", "Room impulse response"), ("speed09", "Speed 0.9x"),
         ("speed11", "Speed 1.1x"), ("pitch_up", "Pitch +2 semitones")]
have = [(c, t) for c, t in conds if (aug_dir / c / f"{stem}_{c}.wav").exists()]
fig = plt.figure(figsize=(7.1, 3.1))
gs = gridspec.GridSpec(2, 5, width_ratios=[1, 1, 1, 0.38, 1.5], hspace=0.55, wspace=0.3)
for k, (c, t) in enumerate(have[:6]):
    sr, x = wavfile.read(aug_dir / c / f"{stem}_{c}.wav")
    x = x.astype(float)
    x = x / (np.abs(x).max() + 1e-9)
    ax = fig.add_subplot(gs[k // 3, k % 3])
    f, tt, S = signal.spectrogram(x, sr, nperseg=512, noverlap=384)
    ax.pcolormesh(tt, f / 1000, 10 * np.log10(S + 1e-12), cmap="magma", vmin=-110, vmax=-30, shading="auto", rasterized=True)
    ax.set_ylim(0, 8); ax.set_title(t, fontsize=7.5); ax.grid(False)
    if k % 3 == 0: ax.set_ylabel("kHz")
    if k // 3 == 1: ax.set_xlabel("s")
axn = fig.add_subplot(gs[1, 2]); axn.axis("off"); axn.text(0.0, 0.5, "Codec (MP3 32 kbps) clips are\nreported in the WER panel but\nnot rendered here.", fontsize=7, va="center", color=GREY)
ax = fig.add_subplot(gs[:, 4])
w = pd.read_csv(ROOT / "report/figures/augmentation_wer_table.csv")
w = w.sort_values("Mean_WER")
ax.barh(range(len(w)), w.Mean_WER, xerr=w.Std_WER, color=[BLUE if c.startswith("Clean") else TEAL for c in w.Condition],
        error_kw={"elinewidth": 0.7, "capsize": 1.5})
ax.set_yticks(range(len(w))); ax.set_yticklabels([c.replace(" (", "\n(") for c in w.Condition], fontsize=6.5)
ax.set_xlabel("WER, Whisper-tiny (mean $\\pm$ sd, n = 5)"); ax.set_title("Off-the-shelf Whisper on augmented clips", fontsize=8)
ax.axvline(1.0, color=RED, lw=0.7, ls="--")
save(fig, "fig_a1_augmentation")

# ---- A1-4 active learning curve
al = pd.DataFrame(json.load(open(ROOT / "supporting_files/plots/active_learning_results.json")))
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.4), gridspec_kw={"wspace": 0.28})
ax = axes[0]
ax.plot(al.budget, al.al_accuracy_mean * 100, "-o", color=BLUE, ms=3.5, lw=1.5, label="Entropy-based active learning")
ax.fill_between(al.budget, (al.al_accuracy_mean - al.al_accuracy_std) * 100, (al.al_accuracy_mean + al.al_accuracy_std) * 100, color=BLUE, alpha=0.15)
ax.plot(al.budget, al.random_accuracy_mean * 100, "-s", color=ORANGE, ms=3.5, lw=1.5, label="Random selection")
ax.fill_between(al.budget, (al.random_accuracy_mean - al.random_accuracy_std) * 100, (al.random_accuracy_mean + al.random_accuracy_std) * 100, color=ORANGE, alpha=0.15)
ax.set_xlabel("labelled-sample budget"); ax.set_ylabel("held-out intent accuracy (%)"); ax.set_ylim(35, 105)
ax.legend(loc="lower right", frameon=False); ax.set_title("Label-efficiency curve (5-fold, mean $\\pm$ sd)", loc="left"); panel(ax, "a")
ax = axes[1]
g = al.accuracy_gain * 100
ax.bar(range(len(al)), g, color=[TEAL if v >= 0 else RED for v in g], width=0.7)
for i, (v, p) in enumerate(zip(g, al.p_value)):
    ax.text(i, v + (0.4 if v >= 0 else -1.1), f"p={p:.2f}", ha="center", fontsize=6, rotation=90, va="bottom" if v >= 0 else "top")
ax.axhline(0, color="black", lw=0.6)
ax.set_xticks(range(len(al))); ax.set_xticklabels(al.budget); ax.set_xlabel("budget"); ax.set_ylabel("AL $-$ random (pp)")
ax.set_ylim(-3, 15.5); ax.set_title("Gain over random (paired $t$-test p-values)", loc="left"); panel(ax, "b")
save(fig, "fig_a1_active")

# =========================================================== A2 FIGURES =====
# ---- A2-1 WER decomposition on the gold set (why WER > 1)
try:
    import jiwer
    S = D = I = H = 0
    rows = []
    for _, r in pred.iterrows():
        o = jiwer.process_words(str(r.reference_norm), str(r.prediction_norm))
        S += o.substitutions; D += o.deletions; I += o.insertions; H += o.hits
        rows.append((len(str(r.reference_norm).split()), len(str(r.prediction_norm).split()), o.substitutions, o.deletions, o.insertions, r.wer))
    dec = pd.DataFrame(rows, columns=["ref_len", "hyp_len", "S", "D", "I", "wer"])
    N = dec.ref_len.sum()
    json.dump({"S": int(S), "D": int(D), "I": int(I), "H": int(H), "ref_words": int(N),
               "S_rate": S / N, "D_rate": D / N, "I_rate": I / N,
               "median_len_ratio": float((dec.hyp_len / dec.ref_len).median())},
              open(OUT / "wer_decomposition.json", "w"), indent=1)
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.35), gridspec_kw={"wspace": 0.42, "width_ratios": [0.9, 1.1, 1.1]})
    ax = axes[0]
    bottom = 0
    for lab, v, c in [("Substitutions", S / N, ORANGE), ("Deletions", D / N, PURPLE), ("Insertions", I / N, RED)]:
        ax.bar(0, v, bottom=bottom, color=c, width=0.55, label=f"{lab} ({v:.2f})")
        bottom += v
    ax.axhline(1.0, color="black", lw=0.7, ls="--"); ax.text(0.3, 0.935, "WER = 1", fontsize=7, ha="left")
    ax.set_xticks([]); ax.set_ylabel("errors per reference word"); ax.set_xlim(-0.45, 2.1)
    ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1.02, 0.42), fontsize=6.8); ax.set_ylim(0, 1.45)
    ax.set_title("Gold-set WER anatomy", loc="left"); panel(ax, "a")
    ax = axes[1]
    ax.scatter(dec.ref_len, dec.hyp_len, c=np.where(pred.is_correct, TEAL, RED), s=16, edgecolor="white", lw=0.4)
    m = max(dec.ref_len.max(), dec.hyp_len.max()) + 3
    ax.plot([0, m], [0, m], color="black", lw=0.7, ls="--"); ax.set_xlim(18, 38); ax.set_ylim(0, 78)
    ax.set_xlabel("reference length (words)"); ax.set_ylabel("hypothesis length (words)")
    ax.set_title("Hypotheses are longer than references", loc="left", fontsize=8); panel(ax, "b")
    ax.scatter([], [], c=TEAL, s=14, label="intent correct"); ax.scatter([], [], c=RED, s=14, label="intent wrong")
    ax.legend(frameon=False, loc="lower right", fontsize=6.8, handletextpad=0.1)
    ax = axes[2]
    ax.hist(pred.wer, bins=np.arange(0.6, 2.45, 0.2), color=BLUE, edgecolor="white", lw=0.4)
    ax.axvline(1.0, color=RED, lw=0.8, ls="--"); ax.axvline(pred.wer.mean(), color=ORANGE, lw=1.1)
    ax.text(pred.wer.mean() + 0.04, ax.get_ylim()[1] * 0.9, f"mean {pred.wer.mean():.2f}", color=ORANGE, fontsize=7)
    ax.set_xlabel("per-clip WER"); ax.set_ylabel("clips"); ax.set_title(f"{(pred.wer>1).sum()}/29 clips have WER > 1", loc="left", fontsize=8); panel(ax, "c")
    save(fig, "fig_a2_wer_anatomy")
except ImportError:
    print("jiwer missing -> skip WER anatomy")

# ---- A2-2 hyper-parameter search analysis
t = json.load(open(ROOT / "supporting_files/plots/tuning_runs.json"))
runs = pd.DataFrame(t["all_runs"])
fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.45), gridspec_kw={"wspace": 0.42})
cmap = {32: BLUE, 64: TEAL, 96: GOLD, 128: ORANGE}
ax = axes[0]
for h, d in runs.groupby("hidden_dim"):
    ax.scatter(d.size_kb, d.val_accuracy * 100 + np.random.default_rng(1).normal(0, 0.4, len(d)), s=26, color=cmap[h], edgecolor="white", lw=0.5, label=f"hidden = {h}")
ax.set_xlabel("head size (KB)"); ax.set_ylabel("validation accuracy (%)"); ax.set_ylim(22, 62)
ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1.02, 0.42), fontsize=6.8); ax.set_title("Quality vs. size", loc="left"); panel(ax, "a")
ax.text(0.04, 0.05, f"val acc. spans {runs.val_accuracy.min()*100:.0f}-{runs.val_accuracy.max()*100:.0f}%\n(n = 17 clips)", transform=ax.transAxes, fontsize=7)
ax = axes[1]
for h, d in runs.groupby("hidden_dim"):
    ax.scatter(d.latency_ms.clip(upper=0.05), d.size_kb, s=26, color=cmap[h], edgecolor="white", lw=0.5)
ax.set_xlabel("router latency (ms / query; run 1 cold-start clipped)"); ax.set_ylabel("head size (KB)"); ax.set_title("Latency vs. size", loc="left"); panel(ax, "b")
ax = axes[2]
for k, ng in enumerate(sorted(runs.ngram_max.unique())):
    d = runs[runs.ngram_max == ng]
    ax.scatter(d.lr, d.dropout, s=18 + 60 * (d.size_kb / d.size_kb.max()), marker="os^"[k], color=[BLUE, TEAL, ORANGE][k],
               edgecolor="white", lw=0.5, alpha=0.9, label=f"n-gram max = {ng}")
ax.set_xlabel("learning rate"); ax.set_ylabel("dropout"); ax.set_title("Search coverage (marker size ~ size)", loc="left", fontsize=8)
ax.legend(frameon=False, fontsize=6.8, loc="upper right"); panel(ax, "c")
save(fig, "fig_a2_tuning")

# ---- A2-3 metrics with 95% CI across splits (from evaluation_results.json)
fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.45), gridspec_kw={"wspace": 0.35})
names = [("production_val", "Val\n17"), ("production_gold", "Gold\n29"), ("production_gold_corrected", "Gold\ncorr.\n29"), ("production_cohort_b", "Coh. B\n32"), ("production_augmented", "Aug.\n60")]
for ax, (key, lab, ref) in zip(axes, [("wer", "WER", 1.0), ("cer", "CER", 1.0), ("intent_accuracy_asr", "Intent accuracy", 0.25)]):
    means = [ev[n]["metrics"][key]["mean"] for n, _ in names]
    lo = [ev[n]["metrics"][key]["mean"] - ev[n]["metrics"][key]["ci95"][0] for n, _ in names]
    hi = [ev[n]["metrics"][key]["ci95"][1] - ev[n]["metrics"][key]["mean"] for n, _ in names]
    ax.bar(range(5), means, yerr=[lo, hi], color=[TEAL, ORANGE, GOLD, PURPLE, GREY], width=0.65, error_kw={"elinewidth": 0.9, "capsize": 2.5})
    ax.axhline(ref, color=RED if key != "intent_accuracy_asr" else GREY, lw=0.8, ls="--")
    ax.text(4.45, ref, "empty-output WER = 1" if key == "wer" else ("" if key == "cer" else "chance 25%"), fontsize=6.3, color=RED if key != "intent_accuracy_asr" else GREY, ha="right", va="bottom")
    for i, m in enumerate(means):
        ax.text(i, m + hi[i] + (0.02 if key == "intent_accuracy_asr" else 0.04), f"{m:.2f}" if key != "intent_accuracy_asr" else f"{m*100:.1f}%", ha="center", fontsize=7.2)
    ax.set_xticks(range(5)); ax.set_xticklabels([l for _, l in names], fontsize=6.3)
    ax.set_title(lab, loc="left"); ax.set_ylim(0, {"wer": 2.6, "cer": 1.9, "intent_accuracy_asr": 0.95}[key])
save(fig, "fig_a2_metrics")

# ---- A2-4 slice analysis (gold) with Wilson intervals
sl = ev["production_gold"]["slice_analysis"]
rows = []
for dim in ["noise_condition", "lang_mix", "region", "device"]:
    for k, v in sl[dim].items():
        n = v["count"]; kk = int(round(v["accuracy"] * n)); lo, hi = wilson(kk, n)
        rows.append((dim, k, n, v["accuracy"], lo, hi, v["mean_wer"]))
sdf = pd.DataFrame(rows, columns=["dim", "slice", "n", "acc", "lo", "hi", "wer"])
sdf.to_csv(OUT / "gold_slices_wilson.csv", index=False)
fig, ax = plt.subplots(figsize=(3.45, 3.9))
dim_names = {"noise_condition": "noise", "lang_mix": "language", "region": "region", "device": "device"}
y = 0; yt = []; yl = []; sep = []
for dim in ["noise_condition", "lang_mix", "region", "device"]:
    d = sdf[sdf.dim == dim]
    for _, r in d.iterrows():
        ax.plot([r.lo * 100, r.hi * 100], [y, y], color=GREY, lw=1.6, solid_capstyle="round")
        ax.scatter(r.acc * 100, y, s=26, color=ORANGE if r.acc < 0.345 else TEAL, zorder=3, edgecolor="white", lw=0.5)
        yt.append(y); yl.append(f"{r.slice.replace('_', ' ')} (n={r.n})"); y += 1
    sep.append(y - 0.5); y += 0.6
ax.axvline(34.5, color=BLUE, lw=0.8, ls="--"); ax.text(35, -0.9, "overall 34.5%", fontsize=6.5, color=BLUE)
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=6.6); ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_xlabel("intent accuracy (%), 95% Wilson interval"); ax.set_title("Gold-set slices", loc="left")
ax.grid(axis="y", visible=False)
save(fig, "fig_a2_slices")

# ---- A2-5 confusion matrix + confidence histogram on gold
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.45), gridspec_kw={"wspace": 0.55, "width_ratios": [1, 1.15]})
ax = axes[0]
cm = confusion_matrix(pred.intent_true, pred.intent_pred, labels=INTENTS)
ax.imshow(cm, cmap="Oranges", vmin=0, vmax=6)
for i in range(4):
    for j in range(4):
        ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=9, fontweight="bold" if i == j else "normal", color="white" if cm[i, j] >= 4 else "#333")
ax.set_xticks(range(4)); ax.set_xticklabels(INT_SHORT); ax.set_yticks(range(4)); ax.set_yticklabels(INT_SHORT)
ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.grid(False)
ax.set_title(f"Gold confusion matrix (acc = {pred.is_correct.mean()*100:.1f}%)", loc="left", fontsize=8); panel(ax, "a")
ax = axes[1]
bins = np.linspace(0.25, 0.75, 21)
ax.hist(pred[pred.is_correct].confidence, bins=bins, color=TEAL, alpha=0.85, label=f"correct (n={pred.is_correct.sum()})", edgecolor="white", lw=0.4)
ax.hist(pred[~pred.is_correct].confidence, bins=bins, color=RED, alpha=0.75, label=f"wrong (n={(~pred.is_correct).sum()})", edgecolor="white", lw=0.4)
ax.axvline(0.25, color=GREY, ls=":", lw=0.8); ax.text(0.255, ax.get_ylim()[1] * 0.92, "uniform = 0.25", fontsize=6.5, color=GREY)
ax.set_xlabel("max softmax probability"); ax.set_ylabel("clips"); ax.legend(frameon=False)
ax.set_title("Router confidence is barely above chance", loc="left", fontsize=8); panel(ax, "b")
save(fig, "fig_a2_confusion")

# ---- A2-6 latency vs. duration (cache) + percentile bars (loadtest)
lt = json.load(open(ROOT / "supporting_files/loadtest/latency_profile.json"))
c = pd.DataFrame(cache).T
c["dur"] = c.duration_sec.astype(float); c["lat"] = c.transcribe_latency_sec.astype(float)
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.35), gridspec_kw={"wspace": 0.3, "width_ratios": [1.3, 1]})
ax = axes[0]
ax.scatter(c.dur, c.lat, s=14, color=BLUE, edgecolor="white", lw=0.4, alpha=0.9)
xs = np.linspace(c.dur.min(), c.dur.max(), 10); ax.plot(xs, xs, color=RED, ls="--", lw=0.9)
ax.text(xs[-3], xs[-3] + 0.8, "real-time (RTF = 1)", fontsize=6.8, color=RED, rotation=0)
b = np.polyfit(c.dur, c.lat, 1); ax.plot(xs, np.polyval(b, xs), color=ORANGE, lw=1.2)
ax.set_xlabel("audio duration (s)"); ax.set_ylabel("Whisper-base decode time (s)"); ax.set_title(f"ASR latency vs. duration (n = {len(c)} clips)", loc="left"); panel(ax, "a")
ax.text(0.04, 0.9, f"slope {b[0]:.2f} s/s", transform=ax.transAxes, fontsize=7, color=ORANGE)
ax = axes[1]
ls = lt["latency_stats_ms"]
keys = [("p50_total_ms", "p50"), ("mean_total_ms", "mean"), ("p90_total_ms", "p90"), ("p95_total_ms", "p95")]
ax.bar(range(4), [ls[k] / 1000 for k, _ in keys], color=[TEAL, BLUE, ORANGE, RED], width=0.6)
for i, (k, _) in enumerate(keys):
    ax.text(i, ls[k] / 1000 + 0.3, f"{ls[k]/1000:.1f}", ha="center", fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels([l for _, l in keys]); ax.set_ylabel("end-to-end latency (s)")
ax.set_title(f"29 gold clips, RTF = {lt['real_time_factor_rtf']}", loc="left"); panel(ax, "b")
ax.set_ylim(0, 15.5)
save(fig, "fig_a2_latency")

# ---- A2-7 drift monitoring
rp = json.load(open(ROOT / "supporting_files/traffic_replay_log.json"))
bs = pd.DataFrame(rp["batch_summaries"])
fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.3), gridspec_kw={"wspace": 0.45})
shift = [0, 25, 50, 75, 100]
xt = dict(xticks=bs.batch_id)
ax = axes[0]
ax.plot(bs.batch_id, bs.mean_entropy, "-o", color=RED, lw=1.6, ms=4)
ax.axhline(rp["drift_threshold"], color="darkred", ls="--", lw=0.9)
ax.text(1.0, rp["drift_threshold"] - 0.035, f"val-p95 threshold {rp['drift_threshold']:.2f}", fontsize=6.5, color="darkred")
ax.set_ylim(1.1, 1.75); ax.set_ylabel("mean entropy (bits)"); ax.set_title("Label-free signal 1", loc="left"); panel(ax, "a")
ax = axes[1]
ax.plot(bs.batch_id, bs.mean_avg_logprob, "-s", color=PURPLE, lw=1.6, ms=4)
ax.set_ylabel("mean decoder avg log-prob"); ax.set_title("Label-free signal 2", loc="left"); panel(ax, "b")
ax = axes[2]
ax.plot(bs.batch_id, bs.mean_accuracy * 100, "-^", color=BLUE, lw=1.6, ms=4)
ax.set_ylim(0, 60); ax.set_ylabel("intent accuracy (%)"); ax.set_title("Labelled quality metric", loc="left"); panel(ax, "c")
ax.text(0.5, 0.06, "20 queries / batch:\nsd ~ 11 pp", transform=ax.transAxes, fontsize=6.5, color=GREY, ha="center")
for a_ in axes:
    a_.set_xticks(bs.batch_id); a_.set_xticklabels([f"{x}%" for x in shift], fontsize=7); a_.set_xlabel("Cohort-B share of traffic")
r = {k: float(np.corrcoef(bs[c], bs.mean_accuracy)[0, 1]) for k, c in [("entropy", "mean_entropy"), ("avg_logprob", "mean_avg_logprob"), ("snr", "mean_snr_db")]}
json.dump({"pearson_vs_accuracy": r, "n_batches": len(bs), "logged": {k: rp[k] for k in rp if "correlation" in k}}, open(OUT / "drift_correlations.json", "w"), indent=1)
save(fig, "fig_a2_drift")

# ---- A2-8 promotion gate (TEST_SET_LOG.md LOG-179 / LOG-188; README key-results table)
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.3), gridspec_kw={"wspace": 0.3})
labs = ["production", "candidate\nrehearsal", "candidate\nno-rehearsal"]
cb = [4 / 13, 5 / 13, 4 / 13]
gd = [7 / 29, 6 / 29, 7 / 29]
ax = axes[0]
ax.bar(range(3), np.array(cb) * 100, color=[GREY, TEAL, RED], width=0.6)
ax.axhline((cb[0] + 0.05) * 100, color="black", ls="--", lw=0.8); ax.text(2.45, (cb[0] + 0.05) * 100 + 0.8, "gate: baseline + 5 pp", fontsize=6.8, ha="right")
for i, v in enumerate(cb):
    ax.text(i, v * 100 + 0.8, f"{v*100:.1f}%\n({int(round(v*13))}/13)", ha="center", fontsize=7)
ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=7); ax.set_ylim(0, 50); ax.set_ylabel("accuracy (%)")
ax.set_title("Criterion 1: held-out Cohort B (speaker P13)", loc="left", fontsize=8); panel(ax, "a")
ax = axes[1]
ax.bar(range(3), np.array(gd) * 100, color=[GREY, TEAL, RED], width=0.6)
ax.axhline((gd[0] - 0.04) * 100, color="black", ls="--", lw=0.8); ax.text(2.45, (gd[0] - 0.04) * 100 - 3.3, "gate: baseline $-$ 4 pp", fontsize=6.8, ha="right")
for i, v in enumerate(gd):
    ax.text(i, v * 100 + 0.8, f"{v*100:.1f}%\n({int(round(v*29))}/29)", ha="center", fontsize=7)
ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=7); ax.set_ylim(0, 50); ax.set_ylabel("accuracy (%)")
ax.set_title("Criterion 2: Gold set (logged in TEST_SET_LOG)", loc="left", fontsize=8); panel(ax, "b")
save(fig, "fig_a2_gate")

# ---- A2-9 error taxonomy (re-grouped from supporting_files/error_analysis.csv)
err = pd.read_csv(ROOT / "supporting_files/error_analysis.csv")
def macro(cat, cause):
    s = (cat + " " + cause).lower()
    if "script" in s or "devanagari" in s or "urdu" in s: return "Script / decoder collapse"
    if "silence" in s or "non-speech" in s: return "Non-speech / cut-off audio"
    if "phonetic" in s or "substitution" in s: return "Phonetic substitution"
    if "overlap" in s or "ambig" in s or "confusion" in s or "schedule" in s: return "Cross-intent overlap"
    return "Fluent but off-topic hypothesis"
err["macro"] = [macro(a, b) for a, b in zip(err.error_category, err.specific_cause)]
mc = err.macro.value_counts()
fig, ax = plt.subplots(figsize=(3.45, 2.0))
ax.barh(range(len(mc)), mc.values, color=[ORANGE, BLUE, TEAL, PURPLE, GREY][:len(mc)])
ax.set_yticks(range(len(mc))); ax.set_yticklabels(mc.index, fontsize=7); ax.invert_yaxis()
for i, v in enumerate(mc.values):
    ax.text(v + 0.15, i, str(v), va="center", fontsize=7.5)
ax.set_xlabel("misrouted gold clips (n = 19)"); ax.set_xlim(0, mc.max() + 1.5); ax.grid(axis="y", visible=False)
save(fig, "fig_a2_errors")
err.to_csv(OUT / "error_macro_categories.csv", index=False)

# ---- A2-10 ablation: train only vs train + augmented (from MLflow export)
runs_csv = pd.read_csv(ROOT / "artefacts/mlflow_export/runs.csv")
ab = runs_csv[runs_csv.param_training_data.notna()][["param_training_data", "metric_val_intent_acc", "run_id"]]
ab.to_csv(OUT / "ablation_runs.csv", index=False)
print(ab)
print("ALL FIGURES DONE ->", OUT)
