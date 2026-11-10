#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""models.py - Multilingual Intent Classification Model Architectures.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Architectures:
1. CalibratedMultilingualClassifier:
   - Word n-gram TF-IDF (1, 2) for domain-specific technical campus keywords
   - Subword character n-gram TF-IDF (char_wb, 3, 6) for morphological inflections and ASR phonetic variants
   - Dense multilingual semantic embeddings (all-MiniLM-L6-v2) for cross-lingual intent representation
   - Probability calibrated linear classifier with balanced class weights
"""

from typing import List, Dict, Tuple
import numpy as np
import torch
import torch.nn as nn
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import FeatureUnion
from sentence_transformers import SentenceTransformer

from model.src.training.dataset import INTENT_CLASSES, INTENT2ID, ID2INTENT

_SHARED_EMBEDDER = None
_EMB_CACHE = {}

def get_shared_embedder():
    global _SHARED_EMBEDDER
    if _SHARED_EMBEDDER is None:
        _SHARED_EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    return _SHARED_EMBEDDER

def get_cached_embeddings(texts: List[str]) -> np.ndarray:
    global _EMB_CACHE
    embedder = get_shared_embedder()
    missing = [t for t in texts if t not in _EMB_CACHE]
    if missing:
        embs = embedder.encode(missing, show_progress_bar=False, normalize_embeddings=True, batch_size=64)
        for t, emb in zip(missing, embs):
            _EMB_CACHE[t] = emb
    return np.array([_EMB_CACHE[t] for t in texts])

class CalibratedMultilingualClassifier:
    """Robust Hybrid Subword + Dense Embedding Classifier for Code-Mixed & Multilingual Speech."""
    def __init__(self, c_reg: float = 2.0, seed: int = 42, use_dense_embeddings: bool = True):
        self.c_reg = c_reg
        self.seed = seed
        self.use_dense_embeddings = use_dense_embeddings
        
        # Word + Subword Char_wb n-gram feature union
        self.vectorizer = FeatureUnion([
            ("word_ngram", TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                max_features=6000,
                token_pattern=r'(?u)\b\w+\b',
                min_df=1
            )),
            ("subword_char_wb", TfidfVectorizer(
                ngram_range=(3, 6),
                analyzer="char_wb",
                sublinear_tf=True,
                max_features=15000,
                min_df=2
            ))
        ])
        
        base_clf = LogisticRegression(
            C=self.c_reg,
            class_weight="balanced",
            max_iter=1500,
            random_state=self.seed
        )
        self.clf = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=3)

    def _extract_features(self, texts: List[str], fit: bool = False):
        if fit:
            sparse_feats = self.vectorizer.fit_transform(texts)
        else:
            sparse_feats = self.vectorizer.transform(texts)
            
        if self.use_dense_embeddings:
            dense_embs = get_cached_embeddings(texts)
            dense_sparse = csr_matrix(dense_embs * 1.5)
            return hstack([sparse_feats, dense_sparse])
        return sparse_feats

    def fit(self, texts: List[str], labels: List[int]):
        X = self._extract_features(texts, fit=True)
        self.clf.fit(X, labels)
        return self

    def predict(self, texts: List[str]) -> np.ndarray:
        X = self._extract_features(texts, fit=False)
        return self.clf.predict(X)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        X = self._extract_features(texts, fit=False)
        return self.clf.predict_proba(X)

class DenseEmbeddingClassifier(nn.Module):
    """Dense MLP classification head over multilingual sentence embeddings."""
    def __init__(self, embedding_dim: int = 384, num_classes: int = 4, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

if __name__ == "__main__":
    texts = [
        "Hostel room geezer is not working properly",
        "How can I apply for GATE admission in MTech CSE?",
        "Campus wifi is disconnected on my laptop",
        "Need scholarship bonafide certificate for fee reimbursement"
    ]
    labels = [INTENT2ID["hostel_mess"], INTENT2ID["admissions"], INTENT2ID["it_support"], INTENT2ID["student_services"]]

    clf = CalibratedMultilingualClassifier()
    clf.fit(texts, labels)
    preds = clf.predict(["Wifi connectivity issue", "Admission application fee"])
    print("Predicted labels:", [ID2INTENT[p] for p in preds])
