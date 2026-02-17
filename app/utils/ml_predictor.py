import os
import re
import numpy as np
import joblib
from gensim.models import Word2Vec


LABEL_COLS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

MODEL_DIR = os.path.join("app", "models")
W2V_PATH = os.path.join(MODEL_DIR, "word2vec.model")
CLF_PATH = os.path.join(MODEL_DIR, "logreg_multilabel.pkl")


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


def load_models():
    if not os.path.exists(W2V_PATH):
        raise FileNotFoundError(f"Missing Word2Vec model at: {W2V_PATH}")

    if not os.path.exists(CLF_PATH):
        raise FileNotFoundError(f"Missing classifier model at: {CLF_PATH}")

    w2v = Word2Vec.load(W2V_PATH)
    clf = joblib.load(CLF_PATH)
    return w2v, clf


def predict_text(text: str, w2v, clf):
    tokens = tokenize(text)
    vec = sentence_vector(tokens, w2v, 200).reshape(1, -1)

    # predict_proba returns list of arrays in OneVsRest
    probas = clf.predict_proba(vec)[0]

    results = {LABEL_COLS[i]: float(probas[i]) for i in range(len(LABEL_COLS))}
    return results