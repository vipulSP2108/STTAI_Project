"""lid_router.py - Learned language routing for the Indic ASR (en / hi / gu).

Problem: faster-whisper-base language ID, even restricted to {en, hi, gu}, recognises few
Gujarati clips (it says hi, mr or bn), so Gujarati audio is sent to the wrong ASR model.
Fix: use the FULL 99-language probability vector from Whisper-base's language detector on up to
three 30-second windows (mean of log-probabilities) as features, and train a logistic regression
whose target is the routing language derived from the annotators' language tags:
    gu if Gujarati was tagged, else hi if Hindi was tagged, else en.
Evaluated speaker-disjoint (StratifiedGroupKFold by speaker, 5 folds x 5 seeds) against the
restricted-argmax baseline. Output: model/results/lid_router.json; features cached in
model/data/reports/lid_features.json.

Usage: python model/src/asr/lid_router.py [--fit-final]
"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[3]
FEAT = ROOT / "model/data/reports/lid_features.json"
SR = 16000


def route_label(langs):
    return "gu" if "Gujarati" in langs else "hi" if "Hindi" in langs else "en"


def extract():
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio
    m = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
    man = json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]
    out = json.loads(FEAT.read_text()) if FEAT.exists() else {}
    for i, r in enumerate(man, 1):
        if r["uuid"] in out:
            continue
        a = decode_audio(str(ROOT / "model/data/audio" / f"{r['uuid']}.wav"))
        vecs = []
        for s in range(0, min(len(a), 90 * SR), 30 * SR):
            win = a[s:s + 30 * SR]
            if len(win) < 2 * SR:
                break
            _, _, probs = m.detect_language(win)
            vecs.append(dict(probs))
        keys = sorted(vecs[0])
        out[r["uuid"]] = {k: float(np.mean([np.log(v[k] + 1e-9) for v in vecs])) for k in keys}
        if i % 20 == 0:
            print(f"{i}/{len(man)}", flush=True)
            FEAT.write_text(json.dumps(out))
    FEAT.write_text(json.dumps(out))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fit-final", action="store_true"); a = ap.parse_args()
    feats = extract()
    man = json.loads((ROOT / "model/data/metadata/internal_manifest.json").read_text())["manifest"]
    keys = sorted(next(iter(feats.values())))
    X = np.array([[feats[r["uuid"]][k] for k in keys] for r in man])
    y = np.array([route_label(r["languages"]) for r in man])
    g = np.array([r["original_speaker_id"] for r in man])
    idx = {k: i for i, k in enumerate(keys)}
    base = np.array(["en", "hi", "gu"])[np.argmax(X[:, [idx["en"], idx["hi"], idx["gu"]]], 1)]

    accs, accs_base, oof = [], [], np.empty(len(y), dtype=object)
    for seed in [42, 43, 44, 45, 46]:
        for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(X, y, g):
            assert not set(g[tr]) & set(g[te])
            clf = LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced").fit(X[tr], y[tr])
            p = clf.predict(X[te])
            accs.append(accuracy_score(y[te], p)); accs_base.append(accuracy_score(y[te], base[te]))
            if seed == 42:
                oof[te] = p
    oof = oof.astype(str)
    labs = ["en", "hi", "gu"]
    res = {
        "n": len(y), "label_counts": {l: int((y == l).sum()) for l in labs},
        "restricted_argmax_acc": float(accuracy_score(y, base)),
        "restricted_argmax_per_lang": {l: float((base[y == l] == l).mean()) for l in labs},
        "restricted_argmax_confusion_en_hi_gu": confusion_matrix(y, base, labels=labs).tolist(),
        "learned_fold_acc_mean": float(np.mean(accs)), "learned_fold_acc_sd": float(np.std(accs)),
        "baseline_fold_acc_mean": float(np.mean(accs_base)),
        "learned_oof_acc_seed42": float(accuracy_score(y, oof)),
        "learned_per_lang_seed42": {l: float((oof[y == l] == l).mean()) for l in labs},
        "learned_confusion_en_hi_gu": confusion_matrix(y, oof, labels=labs).tolist(),
        "protocol": "StratifiedGroupKFold(5, groups=speaker) x 5 seeds; features = mean log-prob over <=3 30s windows, 99 languages",
    }
    (ROOT / "model/results/lid_router.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    if a.fit_final:
        clf = LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced").fit(X, y)
        with open(ROOT / "model/models/lid_router.pkl", "wb") as f:
            pickle.dump({"clf": clf, "keys": keys}, f)


if __name__ == "__main__":
    main()
