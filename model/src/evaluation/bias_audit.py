"""bias_audit.py - Label, data, ASR and model bias audit for the 182-clip final corpus.

Sections of the output (model/results/bias_audit.json):
  1. annotator_bias   A1 vs A2 label marginals, Stuart-Maxwell test of marginal homogeneity,
                      which annotator the expert sided with on the 47 disagreements.
  2. data_bias        intent x language and intent x speaker association (chi-square, Cramer's V),
                      speaker concentration (top-5 share, Gini), duration by language/intent.
  3. shortcut_risk    how well SPEAKER ID alone predicts intent under clip-grouped CV; this is the
                      leakage that inflated the earlier clip-grouped "unseen speaker" number.
  4. asr_bias         per-language ASR output rate (words/s), repetition-loop rate, empty outputs.
  5. model_bias       per-language and per-speaker accuracy of the speaker-disjoint router, with
                      the gap between best and worst group.
  6. label_noise      clips whose human label the cross-validated model finds least probable,
                      ranked for human re-listening (never relabelled automatically).

Usage: python model/src/evaluation/bias_audit.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import chi2, chi2_contingency

ROOT = Path(__file__).resolve().parents[3]
FA = ROOT / "final_annotation"
REPORTS = ROOT / "model" / "data" / "reports"
RESULTS = ROOT / "model" / "results"
CLASSES = ["admissions", "hostel_mess", "it_support", "student_services"]


def export_labels(path):
    out = {}
    for t in json.loads(Path(path).read_text()):
        res = t["annotations"][0]["result"]
        d = {r["from_name"]: r["value"]["choices"] for r in res}
        out[t["data"]["clip_id"]] = {"intent": d.get("intent", [None])[0], "languages": sorted(d.get("languages", []))}
    return out


def stuart_maxwell(a, b, cats):
    k = len(cats)
    n = np.zeros((k, k))
    for x, y in zip(a, b):
        n[cats.index(x), cats.index(y)] += 1
    d = (n.sum(1) - n.sum(0))[:-1]
    S = np.zeros((k - 1, k - 1))
    for i in range(k - 1):
        for j in range(k - 1):
            S[i, j] = (n[i].sum() + n[:, i].sum() - 2 * n[i, i]) if i == j else -(n[i, j] + n[j, i])
    stat = float(d @ np.linalg.pinv(S) @ d)
    return stat, float(chi2.sf(stat, k - 1)), n.astype(int).tolist()


def cramers_v(table):
    table = np.asarray(table)
    c2, p, dof, _ = chi2_contingency(table)
    n = table.sum(); r, c = table.shape
    return float(np.sqrt(c2 / (n * (min(r, c) - 1)))), float(p), int(dof)


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def main():
    gold = json.loads((FA / "consensus_gold_182.json").read_text())["clips"]
    a1 = export_labels(FA / "annotator_1" / "annotator_1_export.json")
    a2 = export_labels(FA / "annotator_2" / "annotator_2_export.json")
    ids = [g["clip_id"] for g in gold]
    out = {}

    # 1. annotator bias ------------------------------------------------------------
    A = [a1[i]["intent"] for i in ids]; B = [a2[i]["intent"] for i in ids]
    stat, p, table = stuart_maxwell(A, B, CLASSES)
    sided = Counter()
    for g in gold:
        if g["resolution_source"] != "concordant_double_annotation":
            fin = g["gold_intent"]
            sided["A1" if fin == g["a1_intent"] else "A2" if fin == g["a2_intent"] else "neither"] += 1
    out["annotator_bias"] = {
        "a1_marginals": dict(Counter(A)), "a2_marginals": dict(Counter(B)),
        "stuart_maxwell_chi2": stat, "stuart_maxwell_p": p, "a1_rows_a2_cols": table,
        "expert_sided_with_on_disagreements": dict(sided),
        "language_tag_exact_match": float(np.mean([a1[i]["languages"] == a2[i]["languages"] for i in ids])),
    }

    # 2. data bias -----------------------------------------------------------------
    lang = ["Code-mixed" if len(g["languages"]) > 1 else g["languages"][0] for g in gold]
    intent = [g["gold_intent"] for g in gold]
    spk = [g["speaker_id"] for g in gold]
    langs = sorted(set(lang)); spks = sorted(set(spk), key=lambda s: int(s[1:]))
    t_li = [[sum(1 for l, y in zip(lang, intent) if l == L and y == c) for c in CLASSES] for L in langs]
    t_si = [[sum(1 for s, y in zip(spk, intent) if s == S and y == c) for c in CLASSES] for S in spks]
    v_li, p_li, _ = cramers_v(t_li); v_si, p_si, _ = cramers_v(t_si)
    sc = Counter(spk)
    asr = {p_["original_clip_id"]: p_ for p_ in json.loads((REPORTS / "offline_asr_predictions.json").read_text())["predictions"]}
    dur = np.array([asr[i]["audio_duration_sec"] for i in ids])
    out["data_bias"] = {
        "intent_by_language": {L: dict(zip(CLASSES, row)) for L, row in zip(langs, t_li)},
        "intent_language_cramers_v": v_li, "intent_language_chi2_p": p_li,
        "intent_by_speaker": {S: dict(zip(CLASSES, row)) for S, row in zip(spks, t_si)},
        "intent_speaker_cramers_v": v_si, "intent_speaker_chi2_p": p_si,
        "speakers_with_single_intent": [S for S, row in zip(spks, t_si) if sum(1 for x in row if x) == 1],
        "clips_per_speaker": dict(sc), "top5_speaker_share": sum(c for _, c in sc.most_common(5)) / len(spk),
        "speaker_gini": gini(list(sc.values())),
        "duration_sec_median_by_language": {L: float(np.median(dur[np.array(lang) == L])) for L in langs},
        "duration_sec_median_by_intent": {c: float(np.median(dur[np.array(intent) == c])) for c in CLASSES},
        "clips_under_15s": int((dur < 15).sum()),
    }

    # 3. shortcut risk: speaker identity alone, clip-grouped vs speaker-grouped -----
    rng = np.random.default_rng(42)
    acc_clip = []
    for _ in range(20):
        perm = rng.permutation(len(ids)); folds = np.array_split(perm, 5); hits = 0
        for te in folds:
            tr = np.setdiff1d(perm, te)
            maj = {}
            for S in spks:
                lab = [intent[i] for i in tr if spk[i] == S]
                maj[S] = Counter(lab).most_common(1)[0][0] if lab else Counter(intent[i] for i in tr).most_common(1)[0][0]
            hits += sum(maj[spk[i]] == intent[i] for i in te)
        acc_clip.append(hits / len(ids))
    out["shortcut_risk"] = {
        "speaker_id_only_accuracy_clip_grouped_cv": float(np.mean(acc_clip)),
        "speaker_id_only_accuracy_speaker_grouped_cv": "= majority class (speaker unseen)",
        "majority_class_rate": Counter(intent).most_common(1)[0][1] / len(intent),
        "note": "A model that only memorises who is speaking beats chance under clip-grouped folds; "
                "this is why the earlier fold_1 'unseen speaker' 75% was optimistic.",
    }

    # 4. ASR bias ----------------------------------------------------------------
    def loop(t):
        s = [x.strip().lower() for x in re.split(r"[.?!।]+", t) if x.strip()]
        return len(s) >= 3 and Counter(s).most_common(1)[0][1] >= 3
    ab = {}
    for L in langs:
        rows = [asr[i] for i, l in zip(ids, lang) if l == L]
        ab[L] = {
            "n": len(rows),
            "words_per_sec_median": float(np.median([len(r["transcription"].split()) / r["audio_duration_sec"] for r in rows])),
            "repetition_loop_rate": float(np.mean([loop(r["transcription"]) for r in rows])),
            "empty_rate": float(np.mean([not r["transcription"].strip() for r in rows])),
        }
    out["asr_bias_hybrid"] = ab
    xs = REPORTS / "asr_crosscheck_whisper_small.json"
    if xs.exists():
        rows = json.loads(xs.read_text())["predictions"]
        out["asr_bias_whisper_small"] = {
            L: {"n": len(r_), "rtf_median": float(np.median([r["decode_sec"] / r["audio_duration_sec"] for r in r_])),
                "words_per_sec_median": float(np.median([len(r["transcription"].split()) / r["audio_duration_sec"] for r in r_]))}
            for L in langs if (r_ := [r for r in rows if ("Code-mixed" if len(r["languages"]) > 1 else r["languages"][0]) == L])
        }

    # 5/6. model bias and label noise from the speaker-disjoint ablation -------------
    abl = RESULTS / "intent_v2_ablation_asr_hybrid.json"
    if abl.exists():
        d = json.loads(abl.read_text())
        best = max(d["results"], key=lambda k: d["results"][k]["fold_f1_mean"])
        pred = dict(zip(d["uuids"], d["oof_seed42"][best]))
        man = {m["original_clip_id"]: m["uuid"] for m in json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]}
        hit = np.array([pred[man[i]] == y for i, y in zip(ids, intent)])
        lg = np.array(lang); sp = np.array(spk)
        per_lang = {L: float(hit[lg == L].mean()) for L in langs}
        per_spk = {S: {"n": int((sp == S).sum()), "acc": float(hit[sp == S].mean())} for S in spks}
        big = {S: v for S, v in per_spk.items() if v["n"] >= 5}
        out["model_bias"] = {
            "model": best, "per_language_acc": per_lang,
            "language_gap": max(per_lang.values()) - min(per_lang.values()),
            "per_speaker_acc": per_spk,
            "speaker_gap_n>=5": max(v["acc"] for v in big.values()) - min(v["acc"] for v in big.values()),
            "concordant_label_acc": float(hit[[g["resolution_source"] == "concordant_double_annotation" for g in gold]].mean()),
            "adjudicated_label_acc": float(hit[[g["resolution_source"] != "concordant_double_annotation" for g in gold]].mean()),
        }
        out["label_noise_review_queue"] = [
            {"clip_id": i, "speaker": s, "gold": y, "model": pred[man[i]], "a1": g["a1_intent"], "a2": g["a2_intent"],
             "adjudicated": g["resolution_source"] != "concordant_double_annotation"}
            for i, s, y, g in zip(ids, spk, intent, gold)
            if pred[man[i]] != y and (g["a1_intent"] != g["a2_intent"] or pred[man[i]] in (g["a1_intent"], g["a2_intent"]))
        ]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "bias_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k not in ("label_noise_review_queue",)}, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
