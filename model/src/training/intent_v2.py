"""intent_v2.py - Improved intent router + feature ablation under speaker-disjoint CV.

Diagnosis that motivated each component (see model/results/intent_v2_ablation_*.json):
  * clean     ASR loops ("IITGN Voice Helpdesk." x 30) and greeting boilerplate dominate some
              transcripts -> collapse repeated sentences / n-grams and strip greetings.
  * chunk     MiniLM truncates at 128 word pieces, but clips run 30-97 s (100-250 words) ->
              embed 40-word windows and average, so the whole query is seen.
  * opening   Guideline rule 5.1: when a call spans two topics, the OPENING topic decides the
              label -> separate embedding of the first 40 content words.
  * proto     Similarity to the class definitions written in GUIDELINES.md section 4 (English,
              Hindi and Gujarati keyword lines). A zero-shot prior that does not use any
              training clip, so it helps most for the rare/short classes.
  * multiasr  Training-time augmentation: each training clip contributes one row per ASR system
              (hybrid Indic + Whisper-small). Same audio, same human label -> label-preserving.
              At test time the probabilities of both views are averaged.
  * bt        Training-time back-translation (en<->hi with Helsinki-NLP opus-mt) of training rows.

Evaluation reuses speaker_cv.py: StratifiedGroupKFold(5, groups=speaker) x 5 seeds, C chosen by
inner GroupKFold(3) on training speakers only. Test speakers never influence any choice.

Usage:
    python model/src/training/intent_v2.py --ablation         # all feature sets
    python model/src/training/intent_v2.py --fit-final        # train on all 182, save bundle
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "model" / "src" / "evaluation"))
from speaker_cv import CLASSES, EMB_MODEL, EMB_REVISION, cluster_bootstrap, load_corpus  # noqa: E402

RESULTS = ROOT / "model" / "results"
ONLY: list = []
CACHE = ROOT / "model" / "data" / "cache"
SEEDS = [42, 43, 44, 45, 46]
C_GRID = [0.1, 1.0, 10.0]
WIN = 40

# Class definitions paraphrased from final_annotation/GUIDELINES.md section 4 (scope + keywords).
PROTOTYPES = {
    "admissions": [
        "admission process, eligibility, cutoff, JEE or GATE score, counselling, seat acceptance and document verification for a new candidate",
        "my son or daughter wants to take admission in engineering, what is the fee structure and admission procedure",
        "एडमिशन की प्रक्रिया, प्रवेश, कटऑफ, सीट, काउंसलिंग, दस्तावेज़ सत्यापन, बीटेक में दाखिला",
        "એડમિશન પ્રક્રિયા, પ્રવેશ, કટઓફ, સીટ, કાઉન્સેલિંગ, દસ્તાવેજ ચકાસણી",
    ],
    "hostel_mess": [
        "hostel room, mess food, warden, caretaker, room allocation, laundry, water cooler, mess rebate, guest room",
        "the food in the mess is bad and the hostel room fan or geyser is broken",
        "हॉस्टल का कमरा, मेस का खाना, वार्डन, केयरटेकर, पानी, कमरा आवंटन, भोजन की व्यवस्था",
        "હોસ્ટેલ રૂમ, મેસનું જમવાનું, વોર્ડન, કેરટેકર, પાણી, રૂમ ફાળવણી",
    ],
    "it_support": [
        "wifi not connecting, password reset, institute email, VPN, LDAP login, laptop, printer, portal login error, internet",
        "my laptop cannot connect to the campus network and the portal login fails",
        "वाईफाई नहीं चल रहा, पासवर्ड रीसेट, ईमेल, लॉगिन, इंटरनेट, लैपटॉप, पोर्टल",
        "વાઇફાઇ કનેક્ટ નથી થતું, પાસવર્ડ રીસેટ, ઈમેલ, લોગિન, ઇન્ટરનેટ, લેપટોપ",
    ],
    "student_services": [
        "library, health centre, doctor, ambulance, shuttle bus, ID card, bonafide certificate, scholarship, grade card, transcript, sports, gym",
        "I need a bonafide certificate and information about scholarship disbursement and the campus shuttle",
        "लाइब्रेरी, डॉक्टर, स्वास्थ्य केंद्र, बस, आईडी कार्ड, प्रमाण पत्र, छात्रवृत्ति, स्कॉलरशिप, खेल",
        "લાઇબ્રેરી, ડોક્ટર, આરોગ્ય કેન્દ્ર, બસ, આઈડી કાર્ડ, પ્રમાણપત્ર, શિષ્યવૃત્તિ, રમતગમત",
    ],
}

GREETING = re.compile(
    r"\b(hello|hi|namaste|namaskar|good (morning|afternoon|evening)|sir|madam|iitgn|iit gandhi ?nagar|"
    r"voice help ?desk|help ?desk|query|thank you|thanks)\b|नमस्ते|नमस्कार|हैलो|हेलो|नमस्ती|"
    r"નમસ્તે|નમસ્કાર|હેલો|આઈઆઈટીજીએન|હેલ્પડેસ્ક", re.I)


def clean_text(t: str) -> str:
    """Collapse ASR repetition loops and strip greeting boilerplate."""
    sents = [s.strip() for s in re.split(r"[.?!।\n]+", t) if s.strip()]
    out, seen = [], Counter()
    for s in sents:
        key = s.lower()
        seen[key] += 1
        if seen[key] <= 1:
            out.append(s)
    t = " ".join(out)
    words = t.split()
    for n in range(6, 0, -1):          # collapse word n-grams repeated back-to-back
        i, res = 0, []
        while i < len(words):
            res.extend(words[i:i + n])
            j = i + n
            while words[j:j + n] == words[i:i + n] and n > 0 and j + n <= len(words):
                j += n
            i = j if j > i + n else i + n
        words = res
    t = " ".join(words)
    t = GREETING.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def windows(t: str, size: int = WIN):
    w = t.split()
    if not w:
        return [""]
    return [" ".join(w[i:i + size]) for i in range(0, len(w), size)]


class Encoder:
    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer(EMB_MODEL, revision=EMB_REVISION, device="cpu")
        self.protos = {c: self.enc(v) for c, v in PROTOTYPES.items()}

    def enc(self, texts):
        return self.m.encode(list(texts), batch_size=32, normalize_embeddings=True, show_progress_bar=False)

    def features(self, texts, clean=True):
        """Return dict of dense feature blocks for a list of transcripts."""
        cl = [clean_text(t) if clean else t for t in texts]
        flat, owner = [], []
        for i, t in enumerate(cl):
            for w in windows(t):
                flat.append(w); owner.append(i)
        E = self.enc(flat); owner = np.array(owner)
        chunk = np.vstack([E[owner == i].mean(0) for i in range(len(cl))])
        chunk /= np.linalg.norm(chunk, axis=1, keepdims=True) + 1e-9
        opening = self.enc([windows(t)[0] for t in cl])
        trunc = self.enc(cl)
        proto = []
        for i in range(len(cl)):
            Ei = E[owner == i]
            row = []
            for c in CLASSES:
                P = self.protos[c]
                row.append(float((Ei @ P.T).max()))          # best window vs any definition
                row.append(float((opening[i] @ P.T).max()))  # opening vs definition
            proto.append(row)
        proto = np.array(proto)
        proto = (proto - proto.mean(1, keepdims=True)) * 5.0     # relative similarity per clip
        return {"clean": cl, "trunc": trunc, "chunk": chunk, "opening": opening, "proto": proto}


FEATURE_SETS = {
    "B0_char+emb(raw)":        dict(clean=False, dense=["trunc"]),
    "B1_+clean":               dict(clean=True, dense=["trunc"]),
    "B2_+chunk":               dict(clean=True, dense=["chunk"]),
    "B3_+chunk+opening":       dict(clean=True, dense=["chunk", "opening"]),
    "B4_+chunk+opening+proto": dict(clean=True, dense=["chunk", "opening", "proto"]),
    "B5_proto_only(zero-shot)": dict(clean=True, dense=["proto"], no_char=True),
    "B7_B3+soft_labels":       dict(clean=True, dense=["chunk", "opening"], soft=True),
    "B8_B4+soft_labels":       dict(clean=True, dense=["chunk", "opening", "proto"], soft=True),
}


def build(F, idx, dense, vec=None, no_char=False):
    blocks = []
    if not no_char:
        texts = [F["text"][i] for i in idx]
        if vec is None:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True).fit(texts)
        blocks.append(vec.transform(texts))
    for d in dense:
        blocks.append(sparse.csr_matrix(F[d][idx]))
    return sparse.hstack(blocks).tocsr(), vec


SOFT = {}   # filled by prepare(): index -> (a1_label, a2_label)


def fit_eval(Fviews, y, groups, tr, te, spec, seed):
    """Train on all views of training clips, average probabilities over views at test time.
    With spec['soft'], each training clip contributes its A1 and A2 labels at weight 0.5 each
    (identical labels collapse to weight 1); test labels are always the adjudicated consensus."""
    def train(idx_rows, c):
        Xs, ys, ws, vec = [], [], [], None
        allt = [F["text"][i] for F in Fviews for i in idx_rows]
        if not spec.get("no_char"):
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True).fit(allt)
        for F in Fviews:
            X, _ = build(F, idx_rows, spec["dense"], vec, spec.get("no_char"))
            if spec.get("soft"):
                for k in (0, 1):
                    Xs.append(X); ys.append(np.array([SOFT[i][k] for i in idx_rows])); ws.append(np.full(len(idx_rows), 0.5))
            else:
                Xs.append(X); ys.append(y[idx_rows]); ws.append(np.ones(len(idx_rows)))
        m = LogisticRegression(C=c, max_iter=4000, class_weight="balanced", random_state=seed)
        m.fit(sparse.vstack(Xs).tocsr(), np.concatenate(ys), sample_weight=np.concatenate(ws))
        return m, vec

    def predict(m, vec, idx_rows):
        P = 0
        for F in Fviews:
            X, _ = build(F, idx_rows, spec["dense"], vec, spec.get("no_char"))
            P = P + m.predict_proba(X)
        return m.classes_[np.argmax(P, 1)], P / len(Fviews)

    best_c, best = C_GRID[0], -1
    for c in C_GRID:
        sc = []
        for a, b in GroupKFold(3).split(tr, y[tr], groups[tr]):
            m, vec = train(tr[a], c)
            sc.append(f1_score(y[tr[b]], predict(m, vec, tr[b])[0], average="macro", zero_division=0))
        if np.mean(sc) > best:
            best, best_c = np.mean(sc), c
    m, vec = train(tr, best_c)
    pred, prob = predict(m, vec, te)
    return pred, prob, best_c


def prepare(sources):
    enc = Encoder()
    items_by = {s: {it["uuid"]: it for it in load_corpus(s)} for s in sources}
    uu = sorted(set.intersection(*[set(v) for v in items_by.values()]))
    base = items_by[sources[0]]
    y = np.array([base[u]["intent"] for u in uu])
    groups = np.array([base[u]["speaker"] for u in uu])
    langs = np.array([base[u]["language"] for u in uu])
    SOFT.clear(); SOFT.update({i: (base[u]["a1"], base[u]["a2"]) for i, u in enumerate(uu)})
    views = {}
    for s in sources:
        raw = [items_by[s][u]["text"] for u in uu]
        for clean in (False, True):
            f = enc.features(raw, clean=clean)
            f["text"] = f["clean"] if clean else raw
            views[(s, clean)] = f
    return uu, y, groups, langs, views


def ablation(sources, tag):
    uu, y, groups, langs, views = prepare(sources)
    res, oof = {}, {}
    sets = {k: v for k, v in FEATURE_SETS.items() if not ONLY or any(k.startswith(o) for o in ONLY)}
    if len(sources) > 1 and (not ONLY or "B6" in ONLY):
        sets["B6_full+multiasr"] = dict(clean=True, dense=["chunk", "opening", "proto"], multi=True)
    for name, spec in sets.items():
        t0 = time.time()
        use = sources if spec.get("multi") else sources[:1]
        Fviews = [views[(s, spec["clean"])] for s in use]
        accs, f1s, p42 = [], [], np.empty(len(y), dtype=object)
        for seed in SEEDS:
            for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(uu, y, groups):
                assert not set(groups[tr]) & set(groups[te])
                pred, _, _ = fit_eval(Fviews, y, groups, tr, te, spec, seed)
                accs.append(accuracy_score(y[te], pred))
                f1s.append(f1_score(y[te], pred, average="macro", zero_division=0))
                if seed == 42:
                    p42[te] = pred
        p42 = p42.astype(str)
        aci, fci = cluster_bootstrap(y, p42, groups)
        res[name] = {
            "fold_acc_mean": float(np.mean(accs)), "fold_acc_sd": float(np.std(accs)),
            "fold_f1_mean": float(np.mean(f1s)), "fold_f1_sd": float(np.std(f1s)),
            "fold_f1_all": [float(x) for x in f1s],
            "pooled_seed42_acc": float(accuracy_score(y, p42)), "pooled_acc_ci95": aci,
            "pooled_seed42_f1": float(f1_score(y, p42, average="macro", zero_division=0)), "pooled_f1_ci95": fci,
            "per_language_seed42": {lg: float(accuracy_score(y[langs == lg], p42[langs == lg])) for lg in sorted(set(langs))},
            "per_class_recall_seed42": {c: float(np.mean(p42[y == c] == c)) for c in CLASSES},
            "sec": round(time.time() - t0, 1),
        }
        oof[name] = p42.tolist()
        r = res[name]
        print(f"{name:28s} acc {r['fold_acc_mean']:.3f}±{r['fold_acc_sd']:.3f} F1 {r['fold_f1_mean']:.3f}±{r['fold_f1_sd']:.3f} "
              f"pooled {r['pooled_seed42_acc']:.3f} {[round(v, 3) for v in aci]}", flush=True)
    from scipy.stats import wilcoxon
    ref = res.get("B0_char+emb(raw)", next(iter(res.values())))["fold_f1_all"]
    for name in res:
        if name.startswith("B0"):
            continue
        d = np.array(res[name]["fold_f1_all"]) - np.array(ref)
        try:
            p = float(wilcoxon(d, zero_method="zsplit").pvalue)
        except ValueError:
            p = 1.0
        res[name]["delta_f1_vs_B0"] = float(d.mean()); res[name]["wilcoxon_p_vs_B0"] = p
    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "sources": sources, "n": len(y),
           "protocol": "StratifiedGroupKFold(5, groups=speaker) x 5 seeds, inner GroupKFold(3) selects C",
           "results": res, "uuids": uu, "true": y.tolist(), "oof_seed42": oof}
    path = RESULTS / f"intent_v2_ablation_{tag}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("wrote", path.relative_to(ROOT))


def fit_final(sources):
    """Train the selected configuration on all 182 clips and save a servable bundle."""
    uu, y, groups, langs, views = prepare(sources)
    spec = dict(clean=True, dense=["chunk", "opening", "proto"])
    Fviews = [views[(s, True)] for s in sources]
    allidx = np.arange(len(y))
    # C chosen by speaker-grouped CV on all data (no separate test set is touched here).
    _, _, c = fit_eval(Fviews, y, groups, allidx, allidx[:1], spec, 42)
    allt = [F["text"][i] for F in Fviews for i in allidx]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True).fit(allt)
    X = sparse.vstack([build(F, allidx, spec["dense"], vec)[0] for F in Fviews]).tocsr()
    m = LogisticRegression(C=c, max_iter=4000, class_weight="balanced", random_state=42).fit(X, np.tile(y, len(Fviews)))
    out = ROOT / "model" / "models" / "intent_v2"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "router.pkl", "wb") as f:
        pickle.dump({"vectorizer": vec, "clf": m, "C": c, "spec": spec, "sources": sources,
                     "embedding_model": f"{EMB_MODEL}@{EMB_REVISION}", "prototypes": PROTOTYPES}, f)
    print("saved", out / "router.pkl", "C =", c)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="asr_hybrid")
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--fit-final", action="store_true")
    ap.add_argument("--only", default="", help="comma list of variant prefixes, e.g. B0,B7")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ONLY[:] = [o for o in a.only.split(",") if o]
    srcs = a.sources.split(",")
    if a.ablation:
        ablation(srcs, "+".join(srcs) + (f"_{a.tag}" if a.tag else ""))
    if a.fit_final:
        fit_final(srcs)
