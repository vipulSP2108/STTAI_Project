#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""lexical_synsets.py - Domain Synset & Contextual Lexical Augmentation.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Performs:
1. Academic Domain Synset Substitution preserving campus intent.
2. Contextual Synonym Expansion across Hindi, Gujarati, and English terms.
3. Strict stopword and named entity preservation.
"""

import re
import random
from typing import List, Dict, Tuple

# Domain-specific academic synsets mapped bidirectionally
CAMPUS_SYNSETS: Dict[str, List[str]] = {
    # Hostel & Mess Synsets
    "mess": ["dining hall", "hostel canteen", "bhojanalaya", "mess facility"],
    "dining hall": ["mess", "hostel mess", "food hall"],
    "food": ["meals", "canteen food", "dietary options", "bhojan", "khana"],
    "khana": ["bhojan", "food", "mess food"],
    "bhojan": ["khana", "food", "mess meals"],
    "hostel": ["hall of residence", "student housing", "dormitory", "hostel block"],
    "room": ["kamra", "hostel room", "allotted room", "dorm room"],
    "kamra": ["room", "hostel room"],
    "caretaker": ["hostel warden", "hall supervisor", "maintenance office", "hall manager"],
    "warden": ["hostel authority", "caretaker office", "chief warden"],
    "rebate": ["mess refund", "leave rebate", "mess fee concession"],
    "laundry": ["washing service", "clothes washing counter", "dhobi facility"],
    "geyser": ["hot water facility", "water heater", "bathroom geezer"],

    # IT Support Synsets
    "wifi": ["campus network", "wireless internet", "Wi-Fi connection", "eduroam network"],
    "wi-fi": ["wifi", "campus internet", "wireless connection"],
    "internet": ["web connection", "network access", "bandwidth"],
    "login": ["portal sign-in", "user authentication", "system access"],
    "password": ["credentials", "passcode", "access key"],
    "portal": ["institute website", "ERP portal", "intranet page", "system"],
    "laptop": ["device", "computer", "system machine"],
    "ticket": ["complaint request", "support issue", "IT helpdesk grievance"],
    "complaint": ["issue report", "grievance", "service request"],
    "slow": ["intermittent", "sluggish", "experiencing high latency"],
    "disconnected": ["dropping connection", "failing to connect", "unstable"],

    # Admissions Synsets
    "admission": ["enrollment", "application process", "admissions", "pravesh"],
    "admissions": ["admission", "enrollment office", "candidate selection"],
    "eligibility": ["qualification criteria", "admission requirements", "qualifying score"],
    "application": ["admission form", "candidature submission", "registration form"],
    "interview": ["selection interview", "oral evaluation", "admissions interaction"],
    "call letter": ["shortlist notification", "interview invite", "selection letter"],
    "fees": ["tuition fees", "acceptance deposit", "programme fee"],
    "verification": ["document checking", "credential inspection", "physical verification"],
    "gate": ["GATE entrance exam", "qualifying GATE score"],

    # Student Services Synsets
    "scholarship": ["financial assistance", "fellowship grant", "tuition waiver", "merit scholarship"],
    "grade card": ["transcript", "official marksheet", "semester grade report"],
    "transcript": ["grade card", "official academic transcript", "marksheet"],
    "marksheet": ["grade card", "transcript", "semester result document"],
    "bonafide": ["student status certificate", "enrollment certificate", "bonafide letter"],
    "certificate": ["official document", "verification letter", "attested certificate"],
    "medical": ["health centre", "campus dispensary", "institute medical unit"],
    "dispensary": ["health centre", "student clinic", "medical care unit"],
    "library": ["central library", "resource centre", "study reading room"],
    "gym": ["gymnasium", "sports complex", "fitness centre"],
    "sports": ["athletic ground", "sports facility", "activity center"]
}

# Negation and critical guard words that MUST NEVER be altered or removed
PRESERVED_TOKENS = {
    "not", "no", "never", "none", "neither", "nor", "nahi", "nathi", "na",
    "mat", "nako", "urgent", "emergency", "immediately", "mandatory",
    "compulsory", "required", "fail", "failed", "offline", "online"
}

def augment_lexical_synsets(text: str, n_variants: int = 2, replacement_prob: float = 0.25, seed: int = 42) -> List[str]:
    """Generates lexical variants by replacing domain words with valid campus synsets."""
    rng = random.Random(seed)
    variants = []
    
    words = re.findall(r'\b[\w-]+\b|[^\w\s]', text)
    
    for v_idx in range(n_variants):
        modified_words = []
        replaced_count = 0
        
        for w in words:
            w_lower = w.lower()
            if w_lower in PRESERVED_TOKENS:
                modified_words.append(w)
                continue
            
            # Check single word matches in synsets
            if w_lower in CAMPUS_SYNSETS and rng.random() < replacement_prob:
                candidates = CAMPUS_SYNSETS[w_lower]
                chosen = rng.choice(candidates)
                # Match casing
                if w.isupper():
                    chosen = chosen.upper()
                elif w.istitle():
                    chosen = chosen.title()
                modified_words.append(chosen)
                replaced_count += 1
            else:
                modified_words.append(w)
        
        # Reconstruct text
        aug_text = ""
        for token in modified_words:
            if re.match(r'^[.,!?;:]$', token):
                aug_text = aug_text.rstrip() + token + " "
            else:
                aug_text += token + " "
        aug_text = aug_text.strip()
        
        if aug_text != text and aug_text not in variants:
            variants.append(aug_text)
            
    return variants

if __name__ == "__main__":
    sample = "Namaskar, IITGN Voice Help Desk. I am facing a slow wifi connection on my laptop. Is the IT portal down?"
    print("Original:", sample)
    variants = augment_lexical_synsets(sample, n_variants=3)
    for i, v in enumerate(variants, 1):
        print(f"Variant {i}: {v}")
