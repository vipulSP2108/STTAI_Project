#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""discourse_marker_augmenter.py - Colloquial Indic Helpdesk Conversational Frames & Discourse Marker Augmentation.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Key Insight:
Spontaneous voice queries in Gujarati, Hindi, and English campus helpdesks contain authentic conversational openers,
discourse markers, and institutional framing phrases (e.g., "સર, એક પૂછપરછ છે કે...", "नमस्ते, कृपया मुझे बताइए कि...",
"Hello helpdesk, I need urgent assistance regarding...").

Training models solely on terse or template-derived strings causes them to overfit to unigram keywords.
This module synthesizes authentic conversational speech variants by:
1. Injecting realistic colloquial helpdesk discourse frames matched to the detected language.
2. Injecting common student hesitation markers and polite institutional inquiry prefixes.
3. Preserving core semantic entities and intent invariants.
"""

import re
import random
from typing import List

# Gujarati conversational helpdesk frames
GUJARATI_FRAMES = [
    "સર, એક પૂછપરછ છે કે {query}",
    "નમસ્તે, મારે જાણવું છે કે {query}",
    "કૃપા કરીને મદદ કરો, {query}",
    "હેલ્પડેસ્ક પર જણાવશો કે {query}",
    "મારો પ્રશ્ન એવો છે કે {query}",
    "સાહેબ, થોડી માહિતી જોઈતી હતી કે {query}"
]

# Hindi conversational helpdesk frames
HINDI_FRAMES = [
    "सर, मुझे एक जानकारी चाहिए कि {query}",
    "नमस्ते, कृपया बताइए कि {query}",
    "हेल्पडेस्क से सहायता चाहिए, {query}",
    "मेरा सवाल यह है कि {query}",
    "कृपया मार्गदर्शन करें, {query}",
    "नमस्ते सर, इस बारे में बताएं कि {query}"
]

# English / Code-Mixed helpdesk frames
ENGLISH_FRAMES = [
    "Hello helpdesk, could you please clarify {query}",
    "Sir, I have a quick inquiry regarding {query}",
    "Excuse me, could you guide me on {query}",
    "Hi, I need official assistance with {query}",
    "Greetings, I wanted to confirm whether {query}",
    "Please help, I am inquiring about {query}"
]

# Common institutional terminology synsets for spoken Indian campus context
CAMPUS_SYNONYMS = {
    # Gujarati
    "હોસ્ટેલ": ["છાત્રાલય", "રૂમ", "હોસ્ટેલ પરિસર"],
    "ફી": ["ચુકવણી", "ફીસ", "પેમેન્ટ"],
    "પ્રવેશ": ["દાખલો", "એડમિશન", "રજિસ્ટ્રેશન"],
    "ઇન્ટરનેટ": ["વાઇફાઇ", "નેટ કનેક્શન", "કેમ્પસ નેટવર્ક"],
    
    # Hindi
    "हॉस्टल": ["छात्रावास", "कमरा", "हॉस्टल रूम"],
    "फीस": ["शुल्क", "पेमेंट", "भुगतान"],
    "प्रवेश": ["दाखिला", "एडमिशन", "पंजीकरण"],
    "इंटरनेट": ["वाईफाई", "नेटवर्क", "इंटरनेट कनेक्शन"],
    
    # English / Transliterated
    "hostel": ["hostel accommodation", "residence hall", "hostel room"],
    "fees": ["fee payment", "dues", "charges"],
    "admission": ["enrolment", "registration", "admission process"],
    "wifi": ["internet connection", "campus network", "wifi access"],
    "portal": ["student portal", "online system", "ERP portal"]
}

def detect_script(text: str) -> str:
    """Classifies script as gujarati, devanagari, or latin."""
    guj_chars = len(re.findall(r'[\u0A80-\u0AFF]', text))
    hin_chars = len(re.findall(r'[\u0900-\u097F]', text))
    if guj_chars > 2:
        return "gu"
    elif hin_chars > 2:
        return "hi"
    return "en"

def augment_discourse_framing(text: str, n_variants: int = 3, seed: int = 42) -> List[str]:
    """Generates conversational helpdesk variants with authentic discourse framing."""
    if not text or len(text.strip().split()) < 2:
        return []

    rng = random.Random(seed + hash(text) % 10000)
    script = detect_script(text)
    
    # Select appropriate frame pool
    if script == "gu":
        frame_pool = GUJARATI_FRAMES
    elif script == "hi":
        frame_pool = HINDI_FRAMES
    else:
        frame_pool = ENGLISH_FRAMES

    # Clean text to blend naturally into a frame
    clean_text = text.strip()
    if clean_text.endswith("."):
        clean_text = clean_text[:-1].strip()

    variants = []
    
    # Strategy A: Frame injection
    sampled_frames = rng.sample(frame_pool, min(n_variants, len(frame_pool)))
    for frame in sampled_frames:
        # Lowercase first letter of clean_text if English
        formatted_query = clean_text
        if script == "en" and formatted_query and formatted_query[0].isupper():
            formatted_query = formatted_query[0].lower() + formatted_query[1:]
        candidate = frame.format(query=formatted_query)
        if candidate != text and candidate not in variants:
            variants.append(candidate)

    # Strategy B: Institutional terminology variation if space permits
    words = clean_text.split()
    for word in words:
        clean_w = word.strip(".,?!\"'").lower()
        if clean_w in CAMPUS_SYNONYMS and len(variants) < n_variants:
            syns = CAMPUS_SYNONYMS[clean_w]
            chosen_syn = rng.choice(syns)
            sub_candidate = re.sub(r'\b' + re.escape(word) + r'\b', chosen_syn, clean_text, count=1)
            if sub_candidate != text and sub_candidate not in variants:
                variants.append(sub_candidate)

    return variants[:n_variants]

if __name__ == "__main__":
    test_queries = [
        "હોસ્ટેલ ફી ભરવા માટે પોર્ટલ ક્યાં છે?",
        "मुझे लाइब्रेरी कार्ड बनवाना है, क्या प्रक्रिया है?",
        "The wifi is not working in the academic block."
    ]
    for q in test_queries:
        print(f"Original: {q}")
        for i, var in enumerate(augment_discourse_framing(q, n_variants=2), 1):
            print(f"  [{i}] {var}")
        print()

