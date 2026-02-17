import os
import re
import joblib
import numpy as np
from gensim.models import Word2Vec

LABEL_COLS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")

W2V_PATH = os.path.join(MODELS_DIR, "word2vec.model")
MULTILABEL_PATH = os.path.join(MODELS_DIR, "logreg_multilabel.pkl")

HARASS_BINARY_PATH = os.path.join(MODELS_DIR, "harassment_binary.pkl")
HARASS_TFIDF_PATH = os.path.join(MODELS_DIR, "harassment_tfidf.pkl")


def simple_tokenize(text: str):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split()


def load_models():
    """
    Loads:
    1) Word2Vec + multi-label logistic regression (toxicity labels)
    2) TF-IDF + binary logistic regression (harassment yes/no)
    """
    w2v = None
    multilabel_clf = None
    harass_tfidf = None
    harass_clf = None

    # Multi-label
    if os.path.exists(W2V_PATH) and os.path.exists(MULTILABEL_PATH):
        w2v = Word2Vec.load(W2V_PATH)
        multilabel_clf = joblib.load(MULTILABEL_PATH)

    # Binary harassment
    if os.path.exists(HARASS_TFIDF_PATH) and os.path.exists(HARASS_BINARY_PATH):
        harass_tfidf = joblib.load(HARASS_TFIDF_PATH)
        harass_clf = joblib.load(HARASS_BINARY_PATH)

    return (w2v, multilabel_clf, harass_tfidf, harass_clf)


def vectorize_w2v(text: str, w2v_model: Word2Vec):
    tokens = simple_tokenize(text)
    vectors = []

    for t in tokens:
        if t in w2v_model.wv:
            vectors.append(w2v_model.wv[t])

    if not vectors:
        return np.zeros((w2v_model.vector_size,), dtype=np.float32)

    return np.mean(vectors, axis=0)


def predict_multilabel(text: str, w2v_model, multilabel_clf):
    vec = vectorize_w2v(text, w2v_model).reshape(1, -1)
    probs = multilabel_clf.predict_proba(vec)

    out = {}
    for i, label in enumerate(LABEL_COLS):
        out[label] = float(probs[i][0][1]) if hasattr(probs[i][0], "__len__") else float(probs[i][1])

    return out


def predict_harassment_binary(text: str, tfidf, clf):
    X = tfidf.transform([text])
    prob = float(clf.predict_proba(X)[0][1])
    pred = int(prob >= 0.50)
    return pred, prob
