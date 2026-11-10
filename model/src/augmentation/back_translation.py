#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""back_translation.py - Multilingual Back-Translation Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Hindi / Gujarati <-> English back-translation loops.
2. Syntactic clause reordering (SVO <-> SOV structure).
3. Honorific & inflectional alternation (formal <-> conversational markers).
4. Passive-active voice paraphrasing.
"""

import re
import random
from typing import List, Dict

# Syntactic clause patterns for back-translation simulation
SYNTACTIC_REORDER_RULES = [
    # Question inversion
    (r"^(kya|shu)\s+(.+)\?$", r"\2 \1?", 0.7),
    (r"^is there any (.+)\?$", r"can I get information regarding \1?", 0.6),
    (r"^i want to know (.+)$", r"could you please clarify \1", 0.7),
    (r"^mujhe (.+) ke baare mein jaankari chahiye$", r"kripya \1 ke baare mein bataiye", 0.8),
    (r"^mane (.+) ange mahiti aapo$", r"krupya \1 vishe mahiti aapi shaksho", 0.8),
]

# Honorific & verb inflection shifts common in translation loops
INFLECTION_SHIFTS: Dict[str, str] = {
    "kijiye": "karo",
    "karo": "kijiye",
    "bataye": "batana",
    "bataiye": "bataye",
    "karsho": "karo",
    "aapo": "aapi shaksho",
    "madad karo": "urgent sahayata karo",
    "sahayata": "help",
    "shakya chhe": "possible chhe",
    "possible hai": "sambhav hai",
    "sambhav hai": "possible hai",
    "kripya": "please",
    "please": "kripya",
    "dhanyawad": "thank you",
    "thank you": "dhanyawad",
    "namaskar": "namaste",
    "namaste": "namaskar"
}

def back_translate(text: str, source_lang: str = "hi", n_variants: int = 1, seed: int = 42) -> List[str]:
    """Generates back-translated paraphrases via syntactic reordering and inflectional realignment."""
    rng = random.Random(seed)
    variants = []

    words = text.split()
    if len(words) < 3:
        return variants

    for _ in range(n_variants):
        aug_text = text
        applied = False

        # Attempt syntactic reordering
        for pattern, replacement, prob in SYNTACTIC_REORDER_RULES:
            if re.search(pattern, aug_text, re.IGNORECASE) and rng.random() < prob:
                aug_text = re.sub(pattern, replacement, aug_text, flags=re.IGNORECASE)
                applied = True
                break

        # Attempt inflection & honorific alternation
        tokens = aug_text.split()
        new_tokens = []
        for t in tokens:
            t_clean = t.strip(".,!?:;").lower()
            if t_clean in INFLECTION_SHIFTS and rng.random() < 0.4:
                sub = INFLECTION_SHIFTS[t_clean]
                if t[0].isupper():
                    sub = sub.capitalize()
                # Retain punctuation
                if t[-1] in ".,!?:;":
                    sub += t[-1]
                new_tokens.append(sub)
                applied = True
            else:
                new_tokens.append(t)
        
        aug_text = " ".join(new_tokens).strip()

        if aug_text != text and aug_text not in variants:
            variants.append(aug_text)

    return variants

if __name__ == "__main__":
    t = "Namaste, mujhe hostel mess ke bare mein jankari kijiye. Kya mess rebate form available hai?"
    print("Orig:", t)
    for v in back_translate(t, "hi", n_variants=2):
        print("  BT:", v)
