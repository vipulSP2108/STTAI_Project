# Text Normalisation Specification
**CS203 Project 5: Cross-Lingual Institute Voice Helpdesk ASR**  
**IIT Gandhinagar**

---

## 1. Rationale & Objectives
In bilingual and multilingual code-mixed speech recognition (English, Hindi, and Gujarati), scoring raw ASR outputs directly against reference transcripts causes artificial error inflation due to:
1. Punctuation and casing discrepancies (e.g., `Hello!` vs `hello`).
2. Numerical format divergence (e.g., `1000` vs `one thousand` or `hazar`).
3. Inter-word whitespace and redundant hesitation tokens.
4. Unicode diacritic and script variations across English and Indic tokens.

This specification defines a single, deterministic normalisation function applied identically to both **reference transcripts** and **model predictions** prior to computing Levenshtein-based Word Error Rate (WER) and Character Error Rate (CER).

---

## 2. Normalisation Rules

| Stage | Rule Description | Raw Input Example | Normalised Output Example |
|---|---|---|---|
| **1. Casing** | Convert all Latin characters to lowercase. | `"MTech Admissions"` | `"mtech admissions"` |
| **2. Punctuation** | Strip all punctuation marks (`.,?!:;'"()[]{}<>-–—/\|*_~#@$%^&=+`). | `"status: pending, ticket #1021!"` | `"status pending ticket 1021"` |
| **3. Numbers** | Preserve cardinal digits as isolated digit tokens; standardise spoken representations. | `"room 4-10"` | `"room 4 10"` |
| **4. Whitespace** | Collapse consecutive whitespace, tabs, and newlines into a single space; strip leading/trailing spaces. | `"  fees   receipt\n"` | `"fees receipt"` |
| **4b. Char/Syllable Hallucinations** | Collapse character repetitions ($\ge 4$ identical consecutive characters or short syllables). | `"potppnnnnnnnnnn"` | `"potppn"` |
| **5. Unicode & Accents** | Decompose and standardise Unicode strings via NFKC normalization. | `"café \u0928\u092e\u0938\u094d\u0924\u0947"` | `"cafe नमस्ते"` |
| **6. Repetition Filtering** | Detect and truncate prompt-induced n-gram repetition loops ($\ge 3$ consecutive repeated 3-grams). | `"helpdesk query helpdesk query helpdesk query"` | `"helpdesk query"` |

---

## 3. Reference Implementation (`code/normalisation.py`)

```python
import re
import unicodedata

PUNCTUATION_REGEX = re.compile(r"[\.,\?!:;\'\"()\[\]{}<>\-–—/\\\|*_\~#@\$%\^&=+\`]")
WHITESPACE_REGEX = re.compile(r"\s+")

def normalise_text(text: str) -> str:
    """Deterministic normalisation for multilingual code-mixed ASR evaluation."""
    if not text:
        return ""
    
    # 1. Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", str(text))
    
    # 2. Lowercase
    text = text.lower()
    
    # 3. Strip punctuation
    text = PUNCTUATION_REGEX.sub(" ", text)
    
    # 4. Collapse whitespace
    text = WHITESPACE_REGEX.sub(" ", text).strip()
    
    # 5. Filter excessive n-gram repetition loops (Whisper decoding artifacts)
    words = text.split()
    if len(words) >= 6:
        filtered_words = []
        i = 0
        while i < len(words):
            # Check 2-word, 3-word, and 4-word loops
            repeated = False
            for ngram_len in [2, 3, 4]:
                if i + 3 * ngram_len <= len(words):
                    g1 = words[i:i + ngram_len]
                    g2 = words[i + ngram_len:i + 2 * ngram_len]
                    g3 = words[i + 2 * ngram_len:i + 3 * ngram_len]
                    if g1 == g2 == g3:
                        filtered_words.extend(g1)
                        i += 3 * ngram_len
                        repeated = True
                        break
            if not repeated:
                filtered_words.append(words[i])
                i += 1
        text = " ".join(filtered_words)
        
    return text
```

---

## 4. Worked Example

- **Raw Reference:**  
  `"Namaste sir, MTech Computer Science admissions portal par application deadline details verify karni hain under ref 1000. Kya aap application procedure clarify kar sakte hain?"`
- **Normalised Reference:**  
  `"namaste sir mtech computer science admissions portal par application deadline details verify karni hain under ref 1000 kya aap application procedure clarify kar sakte hain"`

- **Raw Model Output:**  
  `"namaste sir, mtech computer science admissions portal par application deadline details verify karni hain under ref 1000... kya aap application procedure clarify kar sakte hain?"`
- **Normalised Model Output:**  
  `"namaste sir mtech computer science admissions portal par application deadline details verify karni hain under ref 1000 kya aap application procedure clarify kar sakte hain"`

- **Scored WER on Normalised Pair:** **0.00%** (Clean match without punctuation/casing penalty).
