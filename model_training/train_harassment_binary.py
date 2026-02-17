import os
import re
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score


DATA_PATH = os.path.join("data", "train.csv")
OUT_DIR = os.path.join("app", "models")
os.makedirs(OUT_DIR, exist_ok=True)


def clean_text(t: str) -> str:
    t = str(t).lower()
    t = re.sub(r"http\S+", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# Rule-based harassment signals (used ONLY to create binary labels)
HARASSMENT_PATTERNS = [
    r"touched me",
    r"touching",
    r"grabbed",
    r"groped",
    r"molested",
    r"forced",
    r"kissed",
    r"sex",
    r"nude",
    r"nudes",
    r"obscene",
    r"stalking",
    r"followed me",
    r"keeps calling",
    r"threat",
    r"kill you",
    r"rape",
    r"blackmail",
    r"leaked",
    r"leak my",
    r"porn",
    r"sexual",
    r"boss",
    r"teacher",
    r"manager",
]


def make_harassment_label(text: str) -> int:
    t = clean_text(text)
    for pat in HARASSMENT_PATTERNS:
        if re.search(pat, t):
            return 1
    return 0


def main():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    if "comment_text" not in df.columns:
        raise ValueError("Dataset must contain comment_text column")

    df["text"] = df["comment_text"].astype(str)
    df["harassment"] = df["text"].apply(make_harassment_label)

    # balance dataset: keep all harassment, sample non-harassment
    pos = df[df["harassment"] == 1]
    neg = df[df["harassment"] == 0].sample(n=min(len(pos) * 2, len(df)), random_state=42)

    data = pd.concat([pos, neg]).sample(frac=1, random_state=42)

    X = data["text"].astype(str)
    y = data["harassment"].astype(int)

    print("Split train/val...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training TF-IDF + Logistic Regression...")
    tfidf = TfidfVectorizer(
        max_features=40000,
        ngram_range=(1, 2),
        stop_words="english",
    )

    X_train_vec = tfidf.fit_transform(X_train)
    X_val_vec = tfidf.transform(X_val)

    clf = LogisticRegression(max_iter=300, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_val_vec)

    print("\nF1:", f1_score(y_val, y_pred))
    print("\nReport:\n", classification_report(y_val, y_pred))

    print("Saving models...")
    joblib.dump(tfidf, os.path.join(OUT_DIR, "harassment_tfidf.pkl"))
    joblib.dump(clf, os.path.join(OUT_DIR, "harassment_binary.pkl"))

    print("DONE.")


if __name__ == "__main__":
    main()
