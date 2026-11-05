# ============================================================
# Text Normalisation Engine
# CS203 Project 5: Cross-Lingual Institute Voice Helpdesk ASR
#
# Implements the standard normalisation specification documented in
# docs/normalisation.md.
# Used symmetrically across reference transcripts and model predictions.
# ============================================================

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

    # 4b. Collapse character and syllable-level repetition hallucinations
    text = re.sub(r"(.)\1{3,}", r"\1", text)
    text = re.sub(r"(\b\w{1,4}\b\s+)\1{3,}", r"\1", text)

    # 5. Filter excessive n-gram repetition loops (Whisper decoding artifacts)
    words = text.split()
    if len(words) >= 6:
        filtered_words = []
        i = 0
        while i < len(words):
            repeated = False
            for ngram_len in range(2, 9):
                if i + 3 * ngram_len <= len(words):
                    g1 = words[i : i + ngram_len]
                    g2 = words[i + ngram_len : i + 2 * ngram_len]
                    g3 = words[i + 2 * ngram_len : i + 3 * ngram_len]
                    if g1 == g2 == g3:
                        # Append one instance and skip the loop
                        filtered_words.extend(g1)
                        i += 3 * ngram_len
                        # Also skip any further repetitions of the same pattern
                        while i + ngram_len <= len(words) and words[i : i + ngram_len] == g1:
                            i += ngram_len
                        repeated = True
                        break
            if not repeated:
                filtered_words.append(words[i])
                i += 1
        text = " ".join(filtered_words)

    return text


def detect_repetition(text: str, max_repeat: int = 3) -> bool:
    """Detects if text contains an n-gram repeated >= max_repeat times."""
    words = text.split()
    for n in range(2, 9):
        for i in range(len(words) - n * max_repeat + 1):
            pattern = words[i : i + n]
            matches = 1
            for k in range(1, max_repeat):
                if words[i + k * n : i + (k + 1) * n] == pattern:
                    matches += 1
                else:
                    break
            if matches >= max_repeat:
                return True
    return False


if __name__ == "__main__":
    test_raw = "IIT Gandhinagar student voice helpdesk query, IIT Gandhinagar student voice helpdesk query, IIT Gandhinagar student voice helpdesk query, IIT Gandhinagar student voice helpdesk query, please help with WiFi password!"
    print("Raw:       ", test_raw)
    print("Normalised:", normalise_text(test_raw))
    print("Loop detected:", detect_repetition(test_raw))
