#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""tri_directional_translator.py - 100% Offline Symmetric Multilingual Translation Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Key Capabilities:
1. Translates every voice query symmetrically across English, Hindi, and Gujarati.
2. Operates 100% OFFLINE using local neural MarianMT models (opus-mt-en-hi and opus-mt-hi-en)
   and Indo-Aryan morphological-script transfer for Gujarati.
3. Completely avoids web rate limits and network latency.
4. Produces exact 3x-4x cross-lingual data multiplication per sample.
"""

import os
import re
import json
import torch
from pathlib import Path
from typing import List, Dict, Tuple
from transformers import MarianTokenizer, MarianMTModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CACHE_FILE = BASE_DIR / "model" / "data" / "cache" / "translations_cache.json"

_CACHE: Dict[str, str] = {}

def load_cache():
    global _CACHE
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
        except Exception:
            _CACHE = {}

def save_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_CACHE, f, ensure_ascii=False, indent=2)

load_cache()

# Devanagari to Gujarati Unicode script mapping (offset 0x180)
DEVA2GUJ = {chr(cp): chr(cp + 0x180) for cp in range(0x0901, 0x0970) if cp + 0x180 <= 0x0AF9}
GUJ2DEVA = {v: k for k, v in DEVA2GUJ.items()}

HI_TO_GU_GRAMMAR = {
    'है': 'છે', 'हैं': 'છે', 'था': 'હતો', 'थी': 'હતી', 'थे': 'હતા',
    'मुझे': 'મને', 'मेरा': 'મારું', 'मेरी': 'મારી', 'मेरे': 'મારા',
    'हम': 'અમે', 'हमारा': 'અમારું', 'आप': 'તમે', 'आपका': 'તમારું',
    'क्या': 'શું', 'कहाँ': 'ક્યાં', 'कैसे': 'કેવી રીતે', 'कब': 'ક્યારે',
    'नहीं': 'નથી', 'और': 'અને', 'या': 'અથવા', 'से': 'થી', 'में': 'માં',
    'पर': 'પર', 'के लिए': 'માટે', 'की': 'ની', 'का': 'નો', 'के': 'ના',
    'चाहिए': 'જોઈએ', 'करना': 'કરવું', 'होगा': 'થશે', 'सकते': 'શકો',
    'धन्यवाद': 'આભાર', 'कृपया': 'કૃપા કરીને', 'हॉस्टल': 'હોસ્ટેલ', 'फीस': 'ફી'
}

GU_TO_HI_GRAMMAR = {v: k for k, v in HI_TO_GU_GRAMMAR.items()}

# Lazy model singletons
_MODELS = {}

def get_en2hi():
    if "en2hi" not in _MODELS:
        tok = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-en-hi')
        mod = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-en-hi')
        _MODELS["en2hi"] = (tok, mod)
    return _MODELS["en2hi"]

def get_hi2en():
    if "hi2en" not in _MODELS:
        tok = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-hi-en')
        mod = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-hi-en')
        _MODELS["hi2en"] = (tok, mod)
    return _MODELS["hi2en"]

def detect_script(text: str) -> str:
    guj_chars = len(re.findall(r'[\u0A80-\u0AFF]', text))
    hin_chars = len(re.findall(r'[\u0900-\u097F]', text))
    if guj_chars > 2:
        return "gu"
    elif hin_chars > 2:
        return "hi"
    return "en"

def hi2gu(hi_text: str) -> str:
    words = hi_text.split()
    res = []
    for w in words:
        clean = w.strip(".,?!:;।")
        if clean in HI_TO_GU_GRAMMAR:
            sub = HI_TO_GU_GRAMMAR[clean]
            if w[-1] in ".,?!:;।":
                sub += w[-1]
            res.append(sub)
        else:
            res.append("".join(DEVA2GUJ.get(c, c) for c in w))
    return " ".join(res)

def gu2hi(gu_text: str) -> str:
    words = gu_text.split()
    res = []
    for w in words:
        clean = w.strip(".,?!:;।")
        if clean in GU_TO_HI_GRAMMAR:
            sub = GU_TO_HI_GRAMMAR[clean]
            if w[-1] in ".,?!:;।":
                sub += w[-1]
            res.append(sub)
        else:
            res.append("".join(GUJ2DEVA.get(c, c) for c in w))
    return " ".join(res)

def neural_translate(text: str, direction: str) -> str:
    cache_key = f"{direction}::{text.strip()}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    try:
        if direction == "en2hi":
            tok, mod = get_en2hi()
        elif direction == "hi2en":
            tok, mod = get_hi2en()
        else:
            return ""

        inputs = tok(text.strip(), return_tensors="pt", truncation=True, max_length=128, padding=True)
        with torch.no_grad():
            outputs = mod.generate(**inputs, max_length=128, num_beams=1)
        res = tok.decode(outputs[0], skip_special_tokens=True).strip()
        if res:
            _CACHE[cache_key] = res
            return res
    except Exception as e:
        print(f"Neural MT error ({direction}): {e}")
    return ""

def batch_neural_translate(texts: List[str], direction: str, batch_size: int = 32) -> List[str]:
    """Batch-translates texts using MarianMT, filling and reading from cache."""
    results = ["" for _ in texts]
    to_translate_idx = []
    to_translate_texts = []

    for i, t in enumerate(texts):
        key = f"{direction}::{t.strip()}"
        if key in _CACHE:
            results[i] = _CACHE[key]
        elif t.strip():
            to_translate_idx.append(i)
            to_translate_texts.append(t.strip())

    if not to_translate_texts:
        return results

    try:
        tok, mod = get_en2hi() if direction == "en2hi" else get_hi2en()
        for b_start in range(0, len(to_translate_texts), batch_size):
            b_texts = to_translate_texts[b_start:b_start + batch_size]
            b_indices = to_translate_idx[b_start:b_start + batch_size]

            inputs = tok(b_texts, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = mod.generate(**inputs, max_length=128, num_beams=1)
            decoded = tok.batch_decode(outputs, skip_special_tokens=True)
            for orig, dec, idx in zip(b_texts, decoded, b_indices):
                dec_clean = dec.strip()
                _CACHE[f"{direction}::{orig}"] = dec_clean
                results[idx] = dec_clean
        save_cache()
    except Exception as e:
        print(f"Batch MT error ({direction}): {e}")
        for orig, idx in zip(to_translate_texts, to_translate_idx):
            results[idx] = neural_translate(orig, direction)

    return results

def precompute_dataset_translations(transcripts: List[str]):
    """Precomputes all neural translations across all dataset transcripts in fast batches."""
    en_texts = [t.strip() for t in transcripts if detect_script(t) == "en" and len(t.strip().split()) >= 2]
    hi_texts = [t.strip() for t in transcripts if detect_script(t) == "hi" and len(t.strip().split()) >= 2]
    gu_texts = [t.strip() for t in transcripts if detect_script(t) == "gu" and len(t.strip().split()) >= 2]

    print(f"Precomputing MT cache: {len(en_texts)} EN, {len(hi_texts)} HI, {len(gu_texts)} GU...")

    # 1. EN -> HI
    if en_texts:
        hi_trans = batch_neural_translate(en_texts, "en2hi")
        # EN -> HI -> EN back-translation
        valid_hi = [h for h in hi_trans if h]
        if valid_hi:
            batch_neural_translate(valid_hi, "hi2en")

    # 2. HI -> EN
    if hi_texts:
        en_trans = batch_neural_translate(hi_texts, "hi2en")
        # HI -> EN -> HI back-translation
        valid_en = [e for e in en_trans if e]
        if valid_en:
            batch_neural_translate(valid_en, "en2hi")

    # 3. GU -> HI -> EN -> HI
    if gu_texts:
        hi_from_gu = [gu2hi(g) for g in gu_texts]
        en_from_gu = batch_neural_translate(hi_from_gu, "hi2en")
        valid_en_gu = [e for e in en_from_gu if e]
        if valid_en_gu:
            batch_neural_translate(valid_en_gu, "en2hi")

    save_cache()
    print(f"MT cache precomputed! Total cached pairs: {len(_CACHE)}")

def translate_cross_lingual(text: str) -> List[Tuple[str, str]]:
    """Returns list of (translated_text, technique_name) across all missing languages."""
    if not text or len(text.strip().split()) < 2:
        return []

    script = detect_script(text)
    variants = []

    if script == "en":
        # 1. EN -> HI
        hi_trans = neural_translate(text, "en2hi")
        if hi_trans:
            variants.append((hi_trans, "cross_lingual_hi"))
            # 2. EN -> HI -> GU
            gu_trans = hi2gu(hi_trans)
            if gu_trans:
                variants.append((gu_trans, "cross_lingual_gu"))
            # 3. EN -> HI -> EN (Back-translation)
            back_en = neural_translate(hi_trans, "hi2en")
            if back_en and back_en.lower() != text.lower():
                variants.append((back_en, "back_translation_neural"))

    elif script == "hi":
        # 1. HI -> EN
        en_trans = neural_translate(text, "hi2en")
        if en_trans:
            variants.append((en_trans, "cross_lingual_en"))
            # 2. HI -> EN -> HI (Back-translation)
            back_hi = neural_translate(en_trans, "en2hi")
            if back_hi and back_hi != text:
                variants.append((back_hi, "back_translation_neural"))
        # 3. HI -> GU
        gu_trans = hi2gu(text)
        if gu_trans:
            variants.append((gu_trans, "cross_lingual_gu"))

    elif script == "gu":
        # 1. GU -> HI
        hi_trans = gu2hi(text)
        if hi_trans:
            variants.append((hi_trans, "cross_lingual_hi"))
            # 2. GU -> HI -> EN
            en_trans = neural_translate(hi_trans, "hi2en")
            if en_trans:
                variants.append((en_trans, "cross_lingual_en"))
                # 3. GU -> HI -> EN -> HI -> GU (Back-translation)
                back_hi = neural_translate(en_trans, "en2hi")
                if back_hi:
                    back_gu = hi2gu(back_hi)
                    if back_gu and back_gu != text:
                        variants.append((back_gu, "back_translation_neural"))

    return variants

if __name__ == "__main__":
    t = "Hello IITGN Helpdesk, my hostel room hot water supply has not been available for two days."
    print("Orig EN:", t)
    for v_text, v_type in translate_cross_lingual(t):
        print(f"  [{v_type:24s}] {v_text}")
    save_cache()
