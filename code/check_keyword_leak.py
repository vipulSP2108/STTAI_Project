# ============================================================
# Keyword Leak & Task Separability Audit
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Tests whether intent classification can be trivially solved by the
# first 3 words of transcripts (keyword leak test per Section 3.0.2 of Guide).
# ============================================================

import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from normalisation import normalise_text

def audit_keyword_leak():
    df_t = pd.read_csv("data/labels/transcripts.csv")
    df_i = pd.read_csv("data/labels/intents.csv")
    df = df_t.merge(df_i, on="clip_id")

    # Extract first 3 normalised words
    first_3_words = []
    for tx in df["transcript"]:
        norm = normalise_text(tx)
        words = norm.split()[:3]
        first_3_words.append(" ".join(words))

    df["first_3_words"] = first_3_words

    # Evaluate 5-fold CV
    vec = CountVectorizer()
    X = vec.fit_transform(df["first_3_words"])
    clf = LogisticRegression(max_iter=500)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, df["intent"], cv=skf, scoring="accuracy")

    print(f"=== Keyword Leak Audit (First 3 Words Only) ===")
    print(f"Sample Count: {len(df)}")
    print(f"Vocabulary Size (First 3 words): {len(vec.get_feature_names_out())}")
    print(f"5-Fold CV Accuracy: {scores.mean():.4f} +/- {scores.std():.4f}")
    if scores.mean() > 0.85:
        print("ALERT: Strong keyword leak detected in prompt openings (formulaic openings).")
    else:
        print("PASS: Openings alone do not trivially separate intents.")

if __name__ == "__main__":
    audit_keyword_leak()

