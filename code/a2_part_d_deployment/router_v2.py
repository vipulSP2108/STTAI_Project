"""router_v2.py - Deployed language router + intent router (version indic-v2).

Shared by the Docker image (revised_release.py) and the offline release evaluation
(model/src/evaluation/release_eval.py) so both use exactly the same code.

Language router: logistic regression on Whisper-base's 99-language log-probabilities
(mean over <= 3 x 30 s windows) -> {en, hi, gu}; see model/results/lid_router.json.

Intent router (ablation variant B7, model/results/intent_v2_ablation_asr_hybrid_soft.json):
  * text cleaning: collapse ASR repetition loops, strip greeting boilerplate;
  * char 2-5-gram TF-IDF on the cleaned text;
  * paraphrase-multilingual-MiniLM-L12-v2 mean embedding over 40-word windows (whole query);
  * separate embedding of the opening 40 words (guideline rule 5.1: opening topic decides);
  * labels: the final consensus intent (A1=A2 agreement, or the expert's decision on the 47
    disagreements). label_mode="soft" (A1 and A2 at weight 0.5 each) is kept only as an ablation;
  * C chosen on validation speakers only, then refit on train + validation speakers.
Training text is ASR output of the training clips (model/data/reports/offline_asr_predictions.json),
never the withdrawn curated references.
"""
from __future__ import annotations

import os
import re
from collections import Counter

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

WIN = 40
C_GRID = [0.1, 0.3, 1.0, 3.0, 10.0]
GREETING = re.compile(
    r"\b(hello|hi|namaste|namaskar|good (morning|afternoon|evening)|sir|madam|iitgn|iit gandhi ?nagar|"
    r"voice help ?desk|help ?desk|query|thank you|thanks)\b|नमस्ते|नमस्कार|हैलो|हेलो|नमस्ती|"
    r"નમસ્તે|નમસ્કાર|હેલો|આઈઆઈટીજીએન|હેલ્પડેસ્ક", re.I)


def route_label(langs):
    return "gu" if "Gujarati" in langs else "hi" if "Hindi" in langs else "en"


def clean_text(t: str) -> str:
    sents = [s.strip() for s in re.split(r"[.?!।\n]+", t or "") if s.strip()]
    seen, out = Counter(), []
    for s in sents:
        seen[s.lower()] += 1
        if seen[s.lower()] == 1:
            out.append(s)
    words = " ".join(out).split()
    for n in range(6, 0, -1):
        i, res = 0, []
        while i < len(words):
            res.extend(words[i:i + n]); j = i + n
            while j + n <= len(words) and words[j:j + n] == words[i:i + n]:
                j += n
            i = j
        words = res
    return re.sub(r"\s+", " ", GREETING.sub(" ", " ".join(words))).strip()


def windows(t: str):
    w = t.split()
    return [" ".join(w[i:i + WIN]) for i in range(0, len(w), WIN)] or [""]


class Embedder:
    def __init__(self, path=None):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer(path or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                                     revision=None if path else "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
                                     device="cpu")

    def dense(self, cleaned):
        flat, owner = [], []
        for i, t in enumerate(cleaned):
            for w in windows(t):
                flat.append(w); owner.append(i)
        E = self.m.encode(flat, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        owner = np.array(owner)
        chunk = np.vstack([E[owner == i].mean(0) for i in range(len(cleaned))])
        chunk /= np.linalg.norm(chunk, axis=1, keepdims=True) + 1e-9
        opening = self.m.encode([windows(t)[0] for t in cleaned], normalize_embeddings=True, show_progress_bar=False)
        return np.hstack([chunk, opening])


class IntentRouter:
    def __init__(self, embedder: Embedder, label_mode: str = "expert"):
        self.emb = embedder
        self.label_mode = label_mode
        self.vec = self.clf = None
        self.C = None

    def _X(self, cleaned, dense):
        return sparse.hstack([self.vec.transform(cleaned), sparse.csr_matrix(dense)]).tocsr()

    def _fit(self, cleaned, dense, rows, C):
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True).fit(cleaned)
        X = self._X(cleaned, dense)
        self.clf = LogisticRegression(C=C, max_iter=4000, class_weight="balanced", random_state=42)
        if self.label_mode == "soft":
            y = np.concatenate([[r["a1"] for r in rows], [r["a2"] for r in rows]])
            self.clf.fit(sparse.vstack([X, X]).tocsr(), y, sample_weight=np.full(2 * len(rows), 0.5))
        else:  # expert-final consensus label
            self.clf.fit(X, [r["intent"] for r in rows])
        self.C = C
        return self

    def select_and_fit(self, train, val):
        """train/val: lists of dicts with text, a1, a2, intent. C picked by validation macro-F1."""
        ct = [clean_text(r["text"]) for r in train]; cv = [clean_text(r["text"]) for r in val]
        dt, dv = self.emb.dense(ct), self.emb.dense(cv)
        scores = {}
        for C in C_GRID:
            self._fit(ct, dt, train, C)
            p = self.clf.predict(self._X(cv, dv))
            scores[C] = float(f1_score([r["intent"] for r in val], p, average="macro", zero_division=0))
        best = max(C_GRID, key=lambda c: (scores[c], -abs(np.log10(c))))
        self._fit(ct + cv, np.vstack([dt, dv]), train + val, best)
        return {"validation_macro_f1_by_C": scores, "selected_C": best, "label_mode": self.label_mode}

    def predict_proba(self, texts):
        cleaned = [clean_text(t) for t in texts]
        P = self.clf.predict_proba(self._X(cleaned, self.emb.dense(cleaned)))
        return self.clf.classes_, P

    def __getstate__(self):  # the embedder is reloaded from disk, not pickled
        d = dict(self.__dict__); d["emb"] = None
        return d


class LangRouter:
    def __init__(self):
        self.clf = self.keys = None

    def fit(self, feats: dict, rows):
        self.keys = sorted(next(iter(feats.values())))
        X = np.array([[feats[r["uuid"]][k] for k in self.keys] for r in rows])
        y = [route_label(r["languages"]) for r in rows]
        self.clf = LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced").fit(X, y)
        return self

    @staticmethod
    def features(whisper_base, audio, sr=16000):
        vecs = []
        for s in range(0, min(len(audio), 90 * sr), 30 * sr):
            win = audio[s:s + 30 * sr]
            if len(win) < 2 * sr and vecs:
                break
            vecs.append(dict(whisper_base.detect_language(win)[2]))
        keys = sorted(vecs[0])
        return {k: float(np.mean([np.log(v[k] + 1e-9) for v in vecs])) for k in keys}

    def predict(self, f: dict):
        x = np.array([[f.get(k, np.log(1e-9)) for k in self.keys]])
        p = self.clf.predict_proba(x)[0]
        return str(self.clf.classes_[p.argmax()]), {str(c): round(float(v), 4) for c, v in zip(self.clf.classes_, p)}
