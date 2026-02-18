import os
import re
import pandas as pd
import numpy as np


RAW_DIR = os.path.join("app", "datasets_raw")
OUT_DIR = "data"

JIGSAW_FILE = os.path.join(RAW_DIR, "train.csv")
SEXIST_FILE = os.path.join(RAW_DIR, "sexist-tweets.csv")
CYBER_FILE = os.path.join(RAW_DIR, "CyberBullying Comments Dataset.csv")


def clean_text(x: str) -> str:
    x = str(x) if x is not None else ""
    x = x.replace("\n", " ").replace("\r", " ").strip()
    x = re.sub(r"\s+", " ", x)
    return x


def load_jigsaw():
    df = pd.read_csv(JIGSAW_FILE)
    # required columns: comment_text + toxicity labels
    df["text"] = df["comment_text"].astype(str)

    label_cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
    df[label_cols] = df[label_cols].fillna(0).astype(int)

    # harassment label = any toxicity label
    df["harassment_label"] = (df[label_cols].sum(axis=1) > 0).astype(int)

    df = df[["text", "harassment_label"] + label_cols].copy()
    df["source"] = "jigsaw"

    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() >= 3]
    return df


def load_sexist():
    df = pd.read_csv(SEXIST_FILE)

    # auto detect text column
    possible_text_cols = ["text", "tweet", "body", "comment", "sentence"]
    text_col = None
    for c in possible_text_cols:
        if c in df.columns:
            text_col = c
            break

    if text_col is None:
        # fallback: first object column
        obj_cols = [c for c in df.columns if df[c].dtype == "object"]
        if obj_cols:
            text_col = obj_cols[0]

    if text_col is None:
        raise ValueError("Could not detect text column in sexist-tweets.csv")

    df["text"] = df[text_col].astype(str)

    # auto detect label column
    possible_label_cols = ["label", "sexist", "class", "category"]
    label_col = None
    for c in possible_label_cols:
        if c in df.columns:
            label_col = c
            break

    if label_col is None:
        # if no label col, assume all are harassment
        df["harassment_label"] = 1
    else:
        # map labels to 0/1
        # common: 0=non-sexist, 1=sexist
        df[label_col] = df[label_col].astype(str).str.lower()

        def map_label(v):
            if v in ["1", "sexist", "yes", "true"]:
                return 1
            if v in ["0", "non-sexist", "no", "false"]:
                return 0
            # if unknown -> treat as harassment (safe)
            return 1

        df["harassment_label"] = df[label_col].apply(map_label)

    # add fake multilabel cols for compatibility
    df["toxic"] = df["harassment_label"]
    df["severe_toxic"] = 0
    df["obscene"] = df["harassment_label"]
    df["threat"] = 0
    df["insult"] = df["harassment_label"]
    df["identity_hate"] = 0

    df = df[
        [
            "text",
            "harassment_label",
            "toxic",
            "severe_toxic",
            "obscene",
            "threat",
            "insult",
            "identity_hate",
        ]
    ].copy()

    df["source"] = "sexist_tweets"
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() >= 3]
    return df


def load_cyberbullying():
    df = pd.read_csv(CYBER_FILE)

    # detect text col
    possible_text_cols = ["text", "comment", "tweet", "body", "message"]
    text_col = None
    for c in possible_text_cols:
        if c in df.columns:
            text_col = c
            break

    if text_col is None:
        obj_cols = [c for c in df.columns if df[c].dtype == "object"]
        if obj_cols:
            text_col = obj_cols[0]

    if text_col is None:
        raise ValueError("Could not detect text column in CyberBullying Comments Dataset.csv")

    df["text"] = df[text_col].astype(str)

    # detect label
    possible_label_cols = ["label", "class", "category", "type"]
    label_col = None
    for c in possible_label_cols:
        if c in df.columns:
            label_col = c
            break

    if label_col is None:
        # assume all are harassment (cyberbullying dataset)
        df["harassment_label"] = 1
    else:
        df[label_col] = df[label_col].astype(str).str.lower()

        def map_label(v):
            # common formats
            if v in ["bullying", "harassment", "1", "yes", "true", "cyberbullying"]:
                return 1
            if v in ["not bullying", "normal", "0", "no", "false", "none"]:
                return 0
            return 1

        df["harassment_label"] = df[label_col].apply(map_label)

    # add multilabel columns
    df["toxic"] = df["harassment_label"]
    df["severe_toxic"] = 0
    df["obscene"] = df["harassment_label"]
    df["threat"] = df["harassment_label"]
    df["insult"] = df["harassment_label"]
    df["identity_hate"] = 0

    df = df[
        [
            "text",
            "harassment_label",
            "toxic",
            "severe_toxic",
            "obscene",
            "threat",
            "insult",
            "identity_hate",
        ]
    ].copy()

    df["source"] = "cyberbullying"
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() >= 3]
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Loading datasets...")
    jigsaw = load_jigsaw()
    sexist = load_sexist()
    cyber = load_cyberbullying()

    print("Jigsaw:", jigsaw.shape)
    print("Sexist:", sexist.shape)
    print("Cyber:", cyber.shape)

    master = pd.concat([jigsaw, sexist, cyber], ignore_index=True)

    # remove duplicates
    master["text_norm"] = master["text"].str.lower().str.strip()
    master = master.drop_duplicates(subset=["text_norm"]).drop(columns=["text_norm"])

    # shuffle
    master = master.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Save master
    master_path = os.path.join(OUT_DIR, "train_master.csv")
    master.to_csv(master_path, index=False)
    print("Saved:", master_path, master.shape)

    # Build balanced binary dataset
    pos = master[master["harassment_label"] == 1]
    neg = master[master["harassment_label"] == 0]

    # If not enough negatives, take a subset from Jigsaw clean comments
    if len(neg) < len(pos) * 0.5:
        print("WARNING: Not enough negatives. Dataset may still false-positive.")

    n = min(len(pos), len(neg))
    pos_bal = pos.sample(n=n, random_state=42)
    neg_bal = neg.sample(n=n, random_state=42)

    binary = pd.concat([pos_bal, neg_bal], ignore_index=True)
    binary = binary.sample(frac=1.0, random_state=42).reset_index(drop=True)

    binary_path = os.path.join(OUT_DIR, "train_binary.csv")
    binary.to_csv(binary_path, index=False)
    print("Saved:", binary_path, binary.shape)

    print("\nDONE. Next: train binary model on data/train_binary.csv")


if __name__ == "__main__":
    main()
