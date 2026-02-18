import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


DATA_PATH = os.path.join("data", "train_binary.csv")

OUT_DIR = os.path.join("app", "models")
os.makedirs(OUT_DIR, exist_ok=True)

TFIDF_PATH = os.path.join(OUT_DIR, "harassment_tfidf.pkl")
MODEL_PATH = os.path.join(OUT_DIR, "harassment_binary.pkl")


def main():
    print("Loading balanced dataset...")
    df = pd.read_csv(DATA_PATH)

    df["text"] = df["text"].astype(str).fillna("")
    df["harassment_label"] = df["harassment_label"].astype(int)

    X = df["text"].values
    y = df["harassment_label"].values

    print("Split train/val...")
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print("Training TF-IDF...")
    tfidf = TfidfVectorizer(
        max_features=60000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.98,
        stop_words="english",
    )

    X_train_vec = tfidf.fit_transform(X_train)
    X_val_vec = tfidf.transform(X_val)

    print("Training Logistic Regression...")
    clf = LogisticRegression(
        max_iter=300,
        class_weight="balanced",
        n_jobs=1,
    )
    clf.fit(X_train_vec, y_train)

    preds = clf.predict(X_val_vec)
    f1 = f1_score(y_val, preds)

    print("\nF1:", f1)
    print("\nReport:\n", classification_report(y_val, preds))

    print("\nSaving models...")
    joblib.dump(tfidf, TFIDF_PATH)
    joblib.dump(clf, MODEL_PATH)

    print("Saved:", TFIDF_PATH)
    print("Saved:", MODEL_PATH)
    print("\nDONE.")


if __name__ == "__main__":
    main()main()
