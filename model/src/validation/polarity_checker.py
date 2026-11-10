#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""polarity_checker.py - Gate 2: Negation & Entity Invariance Auditor.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Strict Negation Preservation (polarity flip detection across English, Hindi, and Gujarati).
2. Domain Entity Consistency (verifies query topic keywords match target domain).
3. Guidelines Rule 5.1 Enforcement: Prioritizes initial query topic.
"""

import re
from typing import Tuple, Dict, Set

# Multilingual negation markers
NEGATION_MARKERS = {
    "not", "no", "never", "none", "neither", "nor", "cannot", "can't", "won't",
    "nahi", "nahin", "nhi", "na", "mat",
    "nathi", "nathiye", "nahotu"
}

# Key topic indicators per intent domain
DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
    "hostel_mess": {
        "hostel", "mess", "dining", "room", "food", "khana", "bhojan",
        "geyser", "caretaker", "warden", "laundry", "canteen", "rebate",
        "cleaning", "bed", "washroom", "plumbing", "maintenance"
    },
    "it_support": {
        "wifi", "wi-fi", "internet", "portal", "login", "password", "network",
        "laptop", "system", "speed", "disconnected", "erp", "it", "technical",
        "ip", "mac", "server", "email", "credentials"
    },
    "admissions": {
        "admission", "admissions", "eligibility", "gate", "cutoff", "cut-off",
        "interview", "call letter", "application", "shortlist", "btech",
        "mtech", "phd", "msc", "selection", "seat", "pravesh"
    },
    "student_services": {
        "scholarship", "bonafide", "transcript", "grade card", "marksheet",
        "medical", "dispensary", "health", "library", "gym", "sports",
        "railway concession", "id card", "certificate", "fellowship"
    }
}

class PolarityEntityAuditor:
    def __init__(self):
        pass

    def extract_negations(self, text: str) -> Set[str]:
        words = re.findall(r'\b[\w\']+\b', text.lower())
        return {w for w in words if w in NEGATION_MARKERS}

    def verify_negation_invariance(self, orig_text: str, aug_text: str) -> Tuple[bool, str]:
        """Ensures negation status is invariant (positive stays positive, negative stays negative)."""
        orig_neg = self.extract_negations(orig_text)
        aug_neg = self.extract_negations(aug_text)

        orig_has_neg = len(orig_neg) > 0
        aug_has_neg = len(aug_neg) > 0

        if orig_has_neg and not aug_has_neg:
            return False, f"REJECT: Original had negation {orig_neg}, but augmented dropped it."
        if not orig_has_neg and aug_has_neg:
            return False, f"REJECT: Original had NO negation, but augmented introduced {aug_neg}."

        return True, "PASS: Negation polarity preserved."

    def verify_domain_consistency(self, aug_text: str, target_intent: str) -> Tuple[bool, str]:
        """Ensures augmented text maintains target domain topicality without spurious cross-domain drift."""
        if target_intent not in DOMAIN_KEYWORDS:
            return True, "PASS: Unknown domain."

        expected_keywords = DOMAIN_KEYWORDS[target_intent]
        aug_lower = aug_text.lower()
        aug_words = set(re.findall(r'\b[\w-]+\b', aug_lower))

        # Check for cross-domain collision (e.g. text for admissions having solely hostel mess words)
        matches = aug_words.intersection(expected_keywords)
        
        # If text is long and has explicit keywords from an opposing domain but 0 from target domain
        if not matches and len(aug_words) > 8:
            opposing_counts = {}
            for dom, kws in DOMAIN_KEYWORDS.items():
                if dom != target_intent:
                    cnt = len(aug_words.intersection(kws))
                    if cnt >= 2:
                        opposing_counts[dom] = cnt
            if opposing_counts:
                dominant_other = max(opposing_counts, key=opposing_counts.get)
                return False, f"REJECT: Cross-domain drift detected. Text belongs to {dominant_other}, not {target_intent}."

        return True, "PASS: Domain entity consistency verified."

    def evaluate(self, orig_text: str, aug_text: str, target_intent: str) -> Tuple[bool, str]:
        neg_ok, neg_msg = self.verify_negation_invariance(orig_text, aug_text)
        if not neg_ok:
            return False, neg_msg

        dom_ok, dom_msg = self.verify_domain_consistency(aug_text, target_intent)
        if not dom_ok:
            return False, dom_msg

        return True, "PASS: All polarity and entity constraints satisfied."

if __name__ == "__main__":
    auditor = PolarityEntityAuditor()
    print(auditor.evaluate(
        "Hostel room me wifi connect nahi ho raha hai.",
        "Hostel room me wifi connect ho raha hai.",
        "it_support"
    ))
    print(auditor.evaluate(
        "What is the MTech admission cut-off?",
        "What is the MTech enrollment qualification score?",
        "admissions"
    ))
