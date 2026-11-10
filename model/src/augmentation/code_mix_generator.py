#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""code_mix_generator.py - Campus Multilingual Code-Mixing Synthesis.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Synthesizes realistic intra-sentential and inter-sentential code-switching patterns
observed among IIT Gandhinagar students (Gujarati-English and Hindi-English).
"""

import re
import random
from typing import List, Dict

# Institutional English noun phrases commonly switched into Hindi/Gujarati matrix frames
CAMPUS_SWITCHABLE_ENTITIES = {
    # Admissions
    "admission": ["pravesh", "admission"],
    "eligibility": ["yogyata", "eligibility criteria"],
    "interview": ["sakshatkar", "interview"],
    "cutoff": ["cut-off marks", "minimum rank"],
    "application form": ["aavedan patra", "online application form"],
    "call letter": ["bulava patra", "interview call letter"],

    # Hostel & Mess
    "mess": ["bhojanalaya", "hostel mess"],
    "food": ["khana", "mess meal"],
    "room change": ["kamra badalna", "room change request"],
    "geyser": ["pani garam karne ka geyser", "water heater geyser"],
    "rebate": ["mess chhutti", "mess rebate form"],

    # IT Support
    "wifi": ["internet network", "campus Wi-Fi"],
    "portal": ["website login", "ERP portal"],
    "complaint": ["shikayat", "IT complaint ticket"],
    "slow": ["dheema", "slow speed problem"],
    "password": ["passcode", "account password"],

    # Student Services
    "scholarship": ["chhatravritti", "scholarship assistance"],
    "marksheet": ["ankpatra", "grade sheet transcript"],
    "certificate": ["praman patra", "bonafide certificate"],
    "dispensary": ["swasthya kendra", "campus medical clinic"],
    "library": ["pustakalaya", "central library reading room"]
}

# Conversational campus markers
HINDI_MARKERS = [
    ("actually ", ""),
    ("regarding that, ", ""),
    ("please check karke bataye ", ""),
    ("urgent basis pe ", "urgently "),
    ("mujhe issue aa raha hai ", "I am facing an issue ")
]

GUJARATI_MARKERS = [
    ("actually mane query chhe ke ", ""),
    ("krupya confirm karsho ke ", ""),
    ("aama problem avi rahi chhe ", "there is a problem here ")
]

def synthesize_code_mixed_variants(text: str, detected_lang: str = "hi", n_variants: int = 2, seed: int = 42) -> List[str]:
    """Generates natural campus code-mixed sentences by alternating institutional terms and discourse markers."""
    rng = random.Random(seed)
    variants = []

    words = text.split()
    if len(words) < 4:
        return variants

    for _ in range(n_variants):
        aug_text = text
        # Step 1: Institutional entity injection / substitution
        for eng_term, replacements in CAMPUS_SWITCHABLE_ENTITIES.items():
            if eng_term in aug_text.lower() and rng.random() < 0.4:
                alt = rng.choice(replacements)
                # Case-insensitive replacement
                pattern = re.compile(re.escape(eng_term), re.IGNORECASE)
                aug_text = pattern.sub(alt, aug_text, count=1)

        # Step 2: Natural discourse marker addition
        if rng.random() < 0.5:
            if detected_lang in ["hi", "ur"]:
                prefix, _ = rng.choice(HINDI_MARKERS)
                if not aug_text.lower().startswith(prefix.strip().lower()):
                    aug_text = prefix.capitalize() + aug_text[0].lower() + aug_text[1:] if len(aug_text) > 1 else prefix + aug_text
            elif detected_lang in ["gu"]:
                prefix, _ = rng.choice(GUJARATI_MARKERS)
                if not aug_text.lower().startswith(prefix.strip().lower()):
                    aug_text = prefix.capitalize() + aug_text[0].lower() + aug_text[1:] if len(aug_text) > 1 else prefix + aug_text

        aug_text = aug_text.strip()
        if aug_text != text and aug_text not in variants:
            variants.append(aug_text)

    return variants

if __name__ == "__main__":
    t1 = "Hello, I want to know about the admission process and eligibility criteria for MTech."
    print("Orig 1:", t1)
    for v in synthesize_code_mixed_variants(t1, detected_lang="hi"):
        print("  CM:", v)

    t2 = "Namaskar, IITGN Voice Help Desk. Campus Wi-Fi disconnect thai chhe."
    print("Orig 2:", t2)
    for v in synthesize_code_mixed_variants(t2, detected_lang="gu"):
        print("  CM:", v)
