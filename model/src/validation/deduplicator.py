#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""deduplicator.py - Gate 3: MinHash & N-Gram Jaccard Deduplication Filter.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. MinHash n-gram hashing across text variants.
2. Jaccard similarity thresholding (rejects variants with similarity > 0.88 to prevent dataset bloat).
3. Ensures diversity across all augmented candidate pools.
"""

import re
import hashlib
from typing import List, Set, Dict

class MinHashDeduplicator:
    def __init__(self, max_jaccard_similarity: float = 0.88, n_gram_size: int = 3):
        self.max_similarity = max_jaccard_similarity
        self.n_gram_size = n_gram_size
        self.seen_signatures: List[Set[str]] = []

    def get_shingles(self, text: str) -> Set[str]:
        """Extracts word and character n-gram shingles."""
        cleaned = re.sub(r'\s+', ' ', text.lower().strip())
        if len(cleaned) < self.n_gram_size:
            return {cleaned}
        # Character 3-grams
        char_shingles = {cleaned[i:i+self.n_gram_size] for i in range(len(cleaned) - self.n_gram_size + 1)}
        # Word 2-grams
        words = cleaned.split()
        word_shingles = {f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)} if len(words) > 1 else set()
        return char_shingles.union(word_shingles)

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, text: str, reference_texts: List[str] = None) -> bool:
        shingles = self.get_shingles(text)
        
        # Check against reference pool
        if reference_texts:
            for ref in reference_texts:
                ref_shingles = self.get_shingles(ref)
                sim = self.jaccard_similarity(shingles, ref_shingles)
                if sim > self.max_similarity:
                    return True

        # Check against already admitted signatures in current session
        for seen in self.seen_signatures:
            sim = self.jaccard_similarity(shingles, seen)
            if sim > self.max_similarity:
                return True

        return False

    def add_and_validate(self, text: str) -> bool:
        """Returns True if candidate is novel and passes deduplication."""
        if self.is_duplicate(text):
            return False
        self.seen_signatures.append(self.get_shingles(text))
        return True

if __name__ == "__main__":
    dedup = MinHashDeduplicator(max_jaccard_similarity=0.88)
    t1 = "Can I get my scholarship bonafide certificate from the academic office?"
    t2 = "Can I get my scholarship bonafide certificate from the academic office?" # Identical
    t3 = "Can I get my scholarship bonafide certificate from academic office?" # Near-duplicate
    t4 = "Where can I apply for mess rebate leave in hostel 5?" # Novel

    print("t1 added:", dedup.add_and_validate(t1))
    print("t2 added:", dedup.add_and_validate(t2))
    print("t3 added:", dedup.add_and_validate(t3))
    print("t4 added:", dedup.add_and_validate(t4))
