import os
import re
import joblib
import numpy as np
import pandas as pd

from gensim.models import Word2Vec
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report, f1_score


DATA_PATH = os.path.join("data", "train.csv")
MODEL_DIR = os.path.join("app", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

LABEL_COLS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " URL ", text)
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str):
    return clean_text(text).split()


def sentence_vector(tokens, w2v_model, vector_size=200):
    vecs = []
    for t in tokens:
        if t in w2v_model.wv:
            vecs.append(w2v_model.wv[t])
    if not vecs:
        return np.zeros(vector_size, dtype=np.float32)
    return np.mean(vecs, axis=0).astype(np.float32)


def main():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    # Keep only needed columns
    df = df[["comment_text"] + LABEL_COLS].dropna()
    df["comment_text"] = df["comment_text"].astype(str)

    print("Dataset shape:", df.shape)

    # Tokenize
    print("Tokenizing...")
    df["tokens"] = df["comment_text"].apply(tokenize)

    # Train/val split
    X = df["tokens"].tolist()
    Y = df[LABEL_COLS].values

    X_train, X_val, y_train, y_val = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )

    # -------------------------
    # Train Word2Vec
    # -------------------------
    print("\nTraining Word2Vec...")
    w2v = Word2Vec(
        sentences=X_train,
        vector_size=200,
        window=5,
        min_count=2,
        workers=4,
        sg=1,  # skip-gram
        epochs=10
    )

    # -------------------------
    # Convert texts to vectors
    # -------------------------
    print("Vectorizing train/val...")
    X_train_vec = np.vstack([sentence_vector(x, w2v, 200) for x in X_train])
    X_val_vec = np.vstack([sentence_vector(x, w2v, 200) for x in X_val])

    # -------------------------
    # Train multi-label classifier
    # -------------------------
    print("\nTraining Logistic Regression (OneVsRest)...")
    clf = OneVsRestClassifier(
        LogisticRegression(
            max_iter=2000,
            solver="liblinear",
            class_weight="balanced"
        )
    )
    clf.fit(X_train_vec, y_train)

    # -------------------------
    # Evaluate
    # -------------------------
    print("\nEvaluating...")
    y_pred = clf.predict(X_val_vec)

    print("\nMacro F1:", f1_score(y_val, y_pred, average="macro"))
    print("Micro F1:", f1_score(y_val, y_pred, average="micro"))

    print("\nClassification report:\n")
    print(classification_report(y_val, y_pred, target_names=LABEL_COLS))

    # -------------------------
    # Save models
    # -------------------------
    print("\nSaving models...")
    w2v_path = os.path.join(MODEL_DIR, "word2vec.model")
    clf_path = os.path.join(MODEL_DIR, "logreg_multilabel.pkl")

    w2v.save(w2v_path)
    joblib.dump(clf, clf_path)

    print("Saved Word2Vec:", w2v_path)
    print("Saved Classifier:", clf_path)

    print("\nDONE.")


if __name__ == "__main__":
    main()