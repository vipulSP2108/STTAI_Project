#!/usr/bin/env python3
"""make_report_figures_final.py -- figures for the FINAL 182-clip corpus (final_annotation/ + model/).
Run from repo root:  python code/scripts/make_report_figures_final.py . report/figures_v3
Every plotted value is read from a repository file (paths in comments)."""
import glob, json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager as fm, matplotlib.pyplot as plt, numpy as np
from scipy import stats
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "report" / "figures_v3"; OUT.mkdir(parents=True, exist_ok=True)
for f in glob.glob("/usr/share/fonts/opentype/linux-libertine/*.otf"): fm.fontManager.addfont(f)
FONT = "Linux Libertine O" if any(f.name == "Linux Libertine O" for f in fm.fontManager.ttflist) else "DejaVu Serif"
plt.rcParams.update({"font.family": FONT, "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
  "legend.fontsize": 7.5, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": .6, "axes.grid": True, "grid.color": "#ddd", "grid.linewidth": .5,
  "axes.axisbelow": True, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": .03, "pdf.fonttype": 42, "mathtext.default": "regular"})
BLUE, ORANGE, TEAL, PURPLE, RED, GREY, GOLD = "#1f4e79", "#d95f02", "#1b9e77", "#7570b3", "#c0392b", "#7f8c8d", "#c9a227"
INT = ["admissions", "hostel_mess", "it_support", "student_services"]; SH = ["adm.", "host.", "IT", "stud."]
def save(fig, n): fig.savefig(OUT / f"{n}.pdf"); fig.savefig(OUT / f"{n}.png", dpi=200); plt.close(fig); print("wrote", n)
def panel(ax, l): ax.text(-.02, 1.05, f"({l})", transform=ax.transAxes, fontsize=9, fontweight="bold", ha="right")
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
stat = {}
# ---------------- corpus (final_annotation/consensus_gold_182.json, AUDIO_DATA_SUMMARY.json)
g = json.load(open(ROOT / "final_annotation/consensus_gold_182.json")); clips = g["clips"]
aud = json.load(open(ROOT / "final_annotation/AUDIO_DATA_SUMMARY.json"))
fb = aud["folder_breakdown"]
fig, ax = plt.subplots(1, 4, figsize=(7.1, 2.35), gridspec_kw={"wspace": .62, "width_ratios": [1.5, .8, 1, 1.2]})
spk = {}
for c in clips: spk[c["speaker_id"]] = spk.get(c["speaker_id"], 0) + 1
sk = sorted(spk, key=lambda s: -spk[s]); a = ax[0]; a.bar(range(len(sk)), [spk[s] for s in sk], color=BLUE, width=.75)
a.set_xticks(range(len(sk))); a.set_xticklabels(sk, rotation=90, fontsize=6.3); a.set_ylabel("clips"); a.set_title("Clips per speaker", loc="left"); panel(a, "a")
a = ax[1]; cd = {i: sum(c["gold_intent"] == i for c in clips) for i in INT}
a.bar(range(4), [cd[i] for i in INT], color=[BLUE, TEAL, ORANGE, PURPLE], width=.7)
for i, i_ in enumerate(INT): a.text(i, cd[i_] + 1, cd[i_], ha="center", fontsize=7.5)
a.set_xticks(range(4)); a.set_xticklabels(SH); a.set_title("Consensus intent", loc="left"); a.set_ylim(0, 68); panel(a, "b")
a = ax[2]; lc = {}
for c in clips: k = "+".join(x[:2].upper() if False else {"English": "En", "Hindi": "Hi", "Gujarati": "Gu"}[x] for x in sorted(c["languages"])); lc[k] = lc.get(k, 0) + 1
lk = sorted(lc, key=lambda x: -lc[x]); a.barh(range(len(lk)), [lc[k] for k in lk], color=GREY); a.invert_yaxis()
a.set_yticks(range(len(lk))); a.set_yticklabels(lk); [a.text(lc[k] + 1, i, lc[k], va="center", fontsize=7.5) for i, k in enumerate(lk)]
a.set_xlim(0, 78); a.set_title("Spoken languages", loc="left"); panel(a, "c")
a = ax[3]; fbi = fb.items() if isinstance(fb, dict) else [(x.get("folder") or x.get("name"), x) for x in fb]; d = {k: next((v[kk] for kk in v if "dur" in kk and "format" not in kk and isinstance(v[kk], (int, float))), 0) if isinstance(v, dict) else v for k, v in fbi}
dk = sorted(d, key=lambda s: -d[s]); a.bar(range(len(dk)), [d[k] / 60 for k in dk], color=TEAL, width=.75)
a.set_xticks(range(len(dk))); a.set_xticklabels(dk, rotation=90, fontsize=6); a.set_ylabel("minutes"); a.set_title(f"Audio per folder ({aud['total_duration_seconds']/60:.1f} min)", loc="left", fontsize=8); panel(a, "d")
save(fig, "fig_f_corpus"); stat["n_speakers"] = len(spk); stat["lang"] = lc; stat["total_min"] = aud["total_duration_seconds"] / 60
# ---------------- agreement (final_annotation/consensus_agreement_report.json)
r = json.load(open(ROOT / "final_annotation/consensus_agreement_report.json"))
cm = np.array([[r["confusion_matrix"]["matrix"][i][j] for j in INT] for i in INT])
fig, ax = plt.subplots(1, 4, figsize=(7.4, 2.4), gridspec_kw={"wspace": .85, "width_ratios": [1.1, .9, .9, 1.05]})
a = ax[0]; a.imshow(cm, cmap="Blues", vmin=0, vmax=45)
for i in range(4):
    for j in range(4): a.text(j, i, cm[i, j], ha="center", va="center", fontsize=8.5, color="white" if cm[i, j] > 25 else ("#333" if cm[i, j] else "#aaa"), fontweight="bold" if i != j and cm[i, j] else "normal")
a.set_xticks(range(4)); a.set_xticklabels(SH); a.set_yticks(range(4)); a.set_yticklabels(SH); a.set_xlabel("annotator A2"); a.set_ylabel("annotator A1"); a.grid(False)
a.set_title(f"$\\kappa$ = {r['overall_intent_metrics']['cohens_kappa']:.3f}\n95% CI [{r['overall_intent_metrics']['ci_95'][0]:.2f}, {r['overall_intent_metrics']['ci_95'][1]:.2f}]", fontsize=8); panel(a, "a")
a = ax[1]; pk = r["per_class_binary_kappa"]; ks = sorted(pk, key=lambda k: -pk[k]); a.barh(range(4), [pk[k] for k in ks], color=[TEAL if pk[k] >= .61 else ORANGE for k in ks]); a.invert_yaxis()
a.set_yticks(range(4)); a.set_yticklabels([k.replace("_", " ") for k in ks], fontsize=7); [a.text(pk[k] + .01, i, f"{pk[k]:.2f}", va="center", fontsize=7.5) for i, k in enumerate(ks)]
a.axvline(.61, color=GREY, ls=":", lw=.8); a.set_xlim(0, 1.0); a.set_title("Per-class $\\kappa$", loc="left"); panel(a, "b")
a = ax[2]; la = r["language_agreement"]["per_language_agreement_pct"]; lk = sorted(la, key=lambda k: -la[k]); a.barh(range(3), [la[k] for k in lk], color=PURPLE); a.invert_yaxis()
a.set_yticks(range(3)); a.set_yticklabels(lk); [a.text(la[k] + 1, i, f"{la[k]:.0f}%", va="center", fontsize=7.5) for i, k in enumerate(lk)]; a.set_xlim(0, 112); a.set_title("Language-tag agreement", loc="left", fontsize=8); panel(a, "c")
a = ax[3]; q = r["learning_curve_quartiles"]; a.plot(range(4), [x["cohens_kappa"] for x in q], "-o", color=BLUE, lw=1.6, ms=4); a.axhline(r["overall_intent_metrics"]["cohens_kappa"], color=GREY, ls="--", lw=.8)
a.set_xticks(range(4)); a.set_xticklabels(["Q1", "Q2", "Q3", "Q4"]); a.set_ylim(.45, .85); a.set_ylabel("$\\kappa$"); a.set_title("$\\kappa$ over task order", loc="left"); panel(a, "d")
save(fig, "fig_f_agreement")
# ---------------- augmentation funnel (model/data/reports/augmentation_quality_report.json)
q = json.load(open(ROOT / "model/data/reports/augmentation_quality_report.json"))["statistics"]
fig, ax = plt.subplots(1, 2, figsize=(7.1, 2.3), gridspec_kw={"wspace": .38, "width_ratios": [1, 1.1]})
a = ax[0]; lab = ["candidates", "embedding\ngate", "polarity\ngate", "dedup\ngate", "accepted"]; v = [q["candidates_generated"], q["rejected_by_embedding"], q["rejected_by_polarity"], q["rejected_by_dedup"], q["accepted"]]
a.bar(range(5), v, color=[GREY, RED, RED, RED, TEAL], width=.65); [a.text(i, x + 20, x, ha="center", fontsize=7.5) for i, x in enumerate(v)]
a.set_xticks(range(5)); a.set_xticklabels(lab, fontsize=7); a.set_ylabel("samples"); a.set_ylim(0, 1750); a.set_title(f"Three quality gates ({q['accepted']/q['candidates_generated']*100:.0f}% accepted)", loc="left", fontsize=8); panel(a, "a")
a = ax[1]; bt = q["by_technique"]; tk = sorted(bt, key=lambda k: -bt[k]); a.barh(range(len(tk)), [bt[k] for k in tk], color=BLUE); a.invert_yaxis()
a.set_yticks(range(len(tk))); a.set_yticklabels([k.replace("_", " ") for k in tk], fontsize=7); [a.text(bt[k] + 5, i, bt[k], va="center", fontsize=7.5) for i, k in enumerate(tk)]
a.set_xlim(0, 450); a.set_xlabel("accepted samples"); a.set_title("Accepted by technique", loc="left"); panel(a, "b"); save(fig, "fig_f_aug")
stat["aug"] = q
# ---------------- ablation (model/results/ablation_study_results.json)
ab = json.load(open(ROOT / "model/results/ablation_study_results.json")); R = ab["results"]; ids = list(R)
base = np.array(R["C-01"]["fold_macro_f1s"]); rows = []
fig, ax = plt.subplots(figsize=(7.1, 2.5)); m = [R[i]["macro_f1_mean"] for i in ids]; s = [R[i]["macro_f1_std"] for i in ids]
cols = [GREY if i == "C-01" else (TEAL if R[i]["delta_macro_f1"] > .005 else (RED if R[i]["delta_macro_f1"] < -.005 else "#9bb")) for i in ids]
ax.bar(range(len(ids)), m, yerr=s, color=cols, width=.68, error_kw={"elinewidth": .8, "capsize": 2})
for k, i in enumerate(ids): ax.scatter([k] * 5, R[i]["fold_macro_f1s"], s=7, color="black", alpha=.55, zorder=3)
ax.axhline(R["C-01"]["macro_f1_mean"], color="black", ls="--", lw=.8); ax.set_ylim(.45, .85)
ax.set_xticks(range(len(ids))); ax.set_xticklabels([i for i in ids], fontsize=7); ax.set_ylabel("macro-F1 (5-fold)"); ax.set_xlabel("configuration (C-01 = raw transcripts only; dots = folds)")
for k, i in enumerate(ids):
    d = np.array(R[i]["fold_macro_f1s"]) - base
    p = stats.ttest_rel(R[i]["fold_macro_f1s"], base).pvalue if np.any(d != 0) else 1.0
    rows.append((i, R[i]["name"], R[i]["macro_f1_mean"], R[i]["macro_f1_std"], R[i]["delta_macro_f1"], p))
    ax.text(k, .465, f"{R[i]['delta_macro_f1']:+.3f}", ha="center", fontsize=6.3, color="#333")
save(fig, "fig_f_ablation"); stat["ablation"] = rows
with open(OUT / "tab_ablation.tex", "w") as f:
    for i, n, mm, ss, dd, p in rows: f.write(f"{i} & {n.replace('&','\\&')} & {mm:.3f} $\\pm$ {ss:.3f} & {dd:+.3f} & {p:.2f} \\\\\n")
# ---------------- unseen speakers (model/results/unseen_speaker_benchmark.json)
u = json.load(open(ROOT / "model/results/unseen_speaker_benchmark.json")); cmu = np.array(u["overall_metrics"]["confusion_matrix"]); n = u["total_test_samples"]
fig, ax = plt.subplots(1, 3, figsize=(7.1, 2.3), gridspec_kw={"wspace": .55, "width_ratios": [1, 1, 1]})
a = ax[0]; a.imshow(cmu, cmap="Oranges", vmin=0, vmax=10)
for i in range(4):
    for j in range(4): a.text(j, i, cmu[i, j], ha="center", va="center", fontsize=9, fontweight="bold" if i == j else "normal", color="white" if cmu[i, j] >= 6 else "#333")
a.set_xticks(range(4)); a.set_xticklabels(SH); a.set_yticks(range(4)); a.set_yticklabels(SH); a.set_xlabel("predicted"); a.set_ylabel("true"); a.grid(False)
a.set_title(f"Unseen speakers, n = {n}\nacc {u['overall_metrics']['accuracy']*100:.1f}%, macro-F1 {u['overall_metrics']['macro_f1']:.2f}", fontsize=8); panel(a, "a")
a = ax[1]; pc = u["overall_metrics"]["per_class"]; a.bar(range(4), [pc[i]["f1_score"] for i in INT], color=[BLUE, TEAL, ORANGE, PURPLE], width=.65)
[a.text(k, pc[i]["f1_score"] + .02, f"{pc[i]['f1_score']:.2f}\n(n={pc[i]['support']})", ha="center", fontsize=7) for k, i in enumerate(INT)]
a.set_xticks(range(4)); a.set_xticklabels(SH); a.set_ylim(0, 1.2); a.set_ylabel("F1"); a.set_title("Per-class F1", loc="left"); panel(a, "b")
a = ax[2]; ls = u["language_slices"]; lk = list(ls); ci = [wilson(round(ls[k]["accuracy"] * ls[k]["sample_count"]), ls[k]["sample_count"]) for k in lk]
for i, k in enumerate(lk):
    a.plot(ci[i], [i, i], color=GREY, lw=2, solid_capstyle="round"); a.scatter(ls[k]["accuracy"] * 100 / 100, i, color=TEAL, s=30, zorder=3)
a.set_yticks(range(len(lk))); a.set_yticklabels([f"{k}\n(n={ls[k]['sample_count']})" for k in lk], fontsize=7); a.invert_yaxis(); a.set_xlim(0, 1); a.set_xlabel("accuracy, 95% Wilson"); a.set_title("Language slices", loc="left"); panel(a, "c")
save(fig, "fig_f_unseen"); stat["unseen_ci"] = wilson(round(u["overall_metrics"]["accuracy"] * n), n)
# ---------------- ASR on 182 clips (model/data/reports/asr_evaluation_report.json)
e = json.load(open(ROOT / "model/data/reports/asr_evaluation_report.json")); ce = e["clip_evaluations"]; print("clip keys", list(ce[0].keys()) if isinstance(ce, list) else list(ce)[:3])
sl = e["language_slice_breakdown"]; fig, ax = plt.subplots(1, 3, figsize=(7.1, 2.3), gridspec_kw={"wspace": .45})
a = ax[0]; lk = sorted(sl, key=lambda k: sl[k]["mean_wer"]); a.barh(range(4), [sl[k]["mean_wer"] for k in lk], color=[TEAL, BLUE, ORANGE, RED]); a.invert_yaxis()
a.set_yticks(range(4)); a.set_yticklabels([f"{k} (n={sl[k]['samples']})" for k in lk], fontsize=7); [a.text(sl[k]["mean_wer"] + .04, i, f"{sl[k]['mean_wer']:.2f}", va="center", fontsize=7.5) for i, k in enumerate(lk)]
a.axvline(1, color=RED, ls="--", lw=.8); a.set_xlim(0, 3.1); a.set_xlabel("mean WER"); a.set_title("WER by language", loc="left"); panel(a, "a")
a = ax[1]; a.barh(range(4), [sl[k]["mean_cer"] for k in lk], color=[TEAL, BLUE, ORANGE, RED]); a.invert_yaxis(); a.set_yticks(range(4)); a.set_yticklabels([]); [a.text(sl[k]["mean_cer"] + .04, i, f"{sl[k]['mean_cer']:.2f}", va="center", fontsize=7.5) for i, k in enumerate(lk)]
a.axvline(1, color=RED, ls="--", lw=.8); a.set_xlim(0, 2.5); a.set_xlabel("mean CER"); a.set_title("CER by language", loc="left"); panel(a, "b")
a = ax[2]; a.barh(range(4), [sl[k]["mean_match"] for k in lk], color=[TEAL, BLUE, ORANGE, RED]); a.invert_yaxis(); a.set_yticks(range(4)); a.set_yticklabels([]); [a.text(sl[k]["mean_match"] + .02, i, f"{sl[k]['mean_match']:.2f}", va="center", fontsize=7.5) for i, k in enumerate(lk)]
a.set_xlim(0, .85); a.set_xlabel("mean match score"); a.set_title("Fuzzy match", loc="left"); panel(a, "c"); save(fig, "fig_f_asr")
stat["asr"] = e["corpus_averages"]; json.dump(stat, open(OUT / "final_stats.json", "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in stat.items() if k not in ("aug", "ablation")}, indent=0, default=str)[:900]); print([(r[0], round(r[5], 3)) for r in rows])
