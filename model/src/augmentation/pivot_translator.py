#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""pivot_translator.py - Pivot-Language (English -> Latin/Romance -> English) Augmentation.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Transforms linguistic phrasing through intermediate morphological abstraction,
testing model resilience against Latinate academic root variation.
"""

import re
import random
from typing import List, Dict

# Latinate & Romance pivot lexical mappings preserving academic intent
LATINATE_PIVOT_MAPPINGS: Dict[str, List[str]] = {
    "student": ["scholar", "candidate", "academic disciple"],
    "students": ["scholars", "candidates", "enrolled students"],
    "help desk": ["assistance bureau", "inquiry office", "help registry"],
    "support": ["assistance", "facilitation", "administrative aid"],
    "admission": ["enrollment", "candidature admission", "institutional matriculation"],
    "hostel": ["residential hall", "domiciliary residence", "student housing"],
    "food": ["sustenance", "nutritional meals", "canteen provisions"],
    "room": ["chamber", "assigned quarters", "hostel room"],
    "internet": ["digital communication network", "campus network portal"],
    "connection": ["connectivity link", "network access point"],
    "issue": ["impediment", "operational complication", "technical grievance"],
    "complaint": ["formal petition", "grievance notice", "technical report"],
    "verify": ["authenticate", "substantiate", "formally validate"],
    "certificate": ["attestation document", "official charter", "credential record"],
    "scholarship": ["endowment stipend", "fellowship grant", "financial bursary"],
    "fee": ["institutional tuition dues", "remittance fee", "administrative charge"],
    "urgent": ["pressing", "high priority", "critical requirement"],
    "request": ["petition", "formal solicit", "official inquiry"]
}

def augment_latin_pivot(text: str, n_variants: int = 1, seed: int = 42) -> List[str]:
    """Generates Latinate/Romance pivot paraphrases by applying morphological root abstractions."""
    rng = random.Random(seed)
    variants = []

    for _ in range(n_variants):
        aug_text = text
        applied = 0
        for term, replacements in LATINATE_PIVOT_MAPPINGS.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            if pattern.search(aug_text) and rng.random() < 0.35:
                replacement = rng.choice(replacements)
                # Preserve capitalization
                match = pattern.search(aug_text)
                if match and match.group().istitle():
                    replacement = replacement.title()
                aug_text = pattern.sub(replacement, aug_text, count=1)
                applied += 1

        aug_text = aug_text.strip()
        if aug_text != text and applied > 0 and aug_text not in variants:
            variants.append(aug_text)

    return variants

if __name__ == "__main__":
    t = "Urgent request: My hostel room has a water leakage issue and I need immediate support from the caretaker."
    print("Original:", t)
    for v in augment_latin_pivot(t, n_variants=2):
        print("Pivot:", v)
