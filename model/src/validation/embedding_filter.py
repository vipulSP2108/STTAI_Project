#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""embedding_filter.py - Gate 1: Semantic Embedding Cosine Similarity Filter.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Enforces:
CosineSim(v_orig, v_aug) >= threshold (default 0.82)
Rejects any candidate variant that semantically drifts from the original query.
"""

from typing import List, Tuple
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util

class EmbeddingSimilarityGate:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.82, device: str = None):
        self.threshold = threshold
        if device is None:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Initializing Semantic Embedding Gate (Model: {model_name}, Threshold: {threshold})...")
        self.model = SentenceTransformer(model_name, device=self.device)

    def evaluate_candidate(self, original_text: str, candidate_text: str) -> Tuple[bool, float]:
        """Returns (passes_gate, cosine_similarity_score)."""
        if not candidate_text or candidate_text.strip() == "":
            return False, 0.0

        emb1 = self.model.encode(original_text, convert_to_tensor=True, show_progress_bar=False)
        emb2 = self.model.encode(candidate_text, convert_to_tensor=True, show_progress_bar=False)
        similarity = util.cos_sim(emb1, emb2).item()
        
        passes = bool(similarity >= self.threshold)
        return passes, round(similarity, 4)

    def filter_candidates(self, original_text: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """Filters a list of candidate strings, returning only those passing threshold."""
        valid = []
        for cand in candidates:
            passes, sim = self.evaluate_candidate(original_text, cand)
            if passes:
                valid.append((cand, sim))
        return valid

if __name__ == "__main__":
    gate = EmbeddingSimilarityGate(threshold=0.82)
    orig = "I am facing an internet connectivity issue on campus wifi."
    candidates = [
        "I am having a wireless network connection problem on campus wifi.",
        "Where is the mess dining hall located?",
        "My laptop cannot connect to the institute wireless internet."
    ]
    for c in candidates:
        p, score = gate.evaluate_candidate(orig, c)
        print(f"[{'PASS' if p else 'FAIL'}] Sim: {score:.4f} | '{c}'")
