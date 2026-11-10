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

DOMAIN_KEYWORDS = {
    "it_support": [
        "wifi", "wi-fi", "internet", "lan", "connection", "login", "password", "ldap", "portal",
        "email", "outlook", "id card swipe", "server", "printers", "printer", "software", "vpn",
        "it support", "વાયફાઈ", "ઇન્ટરનેટ", "પાસવર્ડ", "વાઇફાઇ", "वाइफ़ाई", "वाईफाई", "इंटरनेट", "पासवर्ड"
    ],
    "admissions": [
        "admission", "admissions", "jee", "gate", "jam", "eligibility", "cut-off", "cutoff",
        "application", "counseling", "counselling", "btech", "mtech", "msc", "phd", "entrance",
        "seat", "quota", "merit", "એડમિશન", "પ્રવેશ", "દાખલા", "एडमिशन", "प्रवेश", "कटऑफ", "पात्रता"
    ],
    "hostel_mess": [
        "hostel", "mess", "food", "dining", "meal", "rebate", "warden", "room", "bed", "allotment",
        "geyser", "cleaning", "washroom", "water filter", "curfew", "security", "drainage",
        "હોસ્ટેલ", "મેસ", "જમવાનું", "ખોરાક", "રૂમ", "હોસ્ટેલની", "हॉस्टल", "मेस", "खाना", "भोजन", "कमरा"
    ],
    "student_services": [
        "scholarship", "bonafide", "transcript", "grade", "grade card", "marksheet", "concession",
        "railway", "bus", "shuttle", "medical", "hospital", "dispensary", "doctor", "counselor",
        "certificate", "sports", "gym", "library", "fine", "convocation", "degree",
        "સ્કોલરશિપ", "બોનાફાઈડ", "પ્રમાણપત્ર", "પુસ્તકાલય", "લાઇબ્રેરી", "મેડિકલ", "દવાખાના", "छात्रवृत्ति", "प्रमाणपत्र"
    ]
}

def extract_domain_priors(texts: List[str]) -> np.ndarray:
    """Extracts multilingual campus domain keyword indicator priors."""
    feats = np.zeros((len(texts), 4), dtype=np.float32)
    classes = ["admissions", "hostel_mess", "it_support", "student_services"]
    for i, t in enumerate(texts):
        tl = t.lower()
        for c_idx, cls_name in enumerate(classes):
            score = 0.0
            for kw in DOMAIN_KEYWORDS[cls_name]:
                if kw in tl:
                    score += 1.0
            feats[i, c_idx] = score
    return feats

def get_shared_embedder():
    global _SHARED_EMBEDDER
    if _SHARED_EMBEDDER is None:
        _SHARED_EMBEDDER = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
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
    """Robust Dual-Tower Calibrated Classifier combining Subword N-grams with Multilingual Sentence Transformers and Domain Priors."""
    def __init__(self, c_reg: float = 2.5, seed: int = 42, use_dense_embeddings: bool = True, dense_weight: float = 0.75):
        self.c_reg = c_reg
        self.seed = seed
        self.use_dense_embeddings = use_dense_embeddings
        self.dense_weight = dense_weight
        
        # Sparse Subword & Word N-gram Pipeline
        self.vectorizer = FeatureUnion([
            ("word_ngram", TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                max_features=5000,
                token_pattern=r'(?u)\b\w+\b',
                min_df=1
            )),
            ("subword_char_wb", TfidfVectorizer(
                ngram_range=(3, 5),
                analyzer="char_wb",
                sublinear_tf=True,
                max_features=10000,
                min_df=2
            ))
        ])
        
        base_sparse_clf = LogisticRegression(
            C=self.c_reg,
            class_weight="balanced",
            max_iter=1500,
            random_state=self.seed
        )
        self.clf_sparse = CalibratedClassifierCV(estimator=base_sparse_clf, method="sigmoid", cv=3)
        
        if self.use_dense_embeddings:
            base_dense_clf = LogisticRegression(
                C=self.c_reg,
                class_weight="balanced",
                max_iter=1500,
                random_state=self.seed
            )
            self.clf_dense = CalibratedClassifierCV(estimator=base_dense_clf, method="sigmoid", cv=3)

    def fit(self, texts: List[str], labels: List[int]):
        X_sparse = self.vectorizer.fit_transform(texts)
        self.clf_sparse.fit(X_sparse, labels)
        
        if self.use_dense_embeddings:
            X_dense = get_cached_embeddings(texts)
            X_dom = extract_domain_priors(texts)
            X_dense_features = np.hstack([X_dense, X_dom])
            self.clf_dense.fit(X_dense_features, labels)
        return self

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        X_sparse = self.vectorizer.transform(texts)
        prob_sparse = self.clf_sparse.predict_proba(X_sparse)
        
        if not self.use_dense_embeddings:
            return prob_sparse
            
        X_dense = get_cached_embeddings(texts)
        X_dom = extract_domain_priors(texts)
        X_dense_features = np.hstack([X_dense, X_dom])
        prob_dense = self.clf_dense.predict_proba(X_dense_features)
        
        # Calibrated soft-voting mixture (75% Dense Multilingual + Domain Priors, 25% Subword Char N-grams)
        prob_mix = (1.0 - self.dense_weight) * prob_sparse + self.dense_weight * prob_dense
        return prob_mix

    def predict(self, texts: List[str]) -> np.ndarray:
        probs = self.predict_proba(texts)
        return np.argmax(probs, axis=1)

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
