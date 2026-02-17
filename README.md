# Harassment Detection + Evidence Support App (India)

A Streamlit-based real-world oriented application that helps users:
- Document harassment incidents in a structured timeline
- Analyse incident summaries using Machine Learning (real dataset)
- Detect harassment categories (hybrid ML + rule-based)
- Suggest India-specific legal guidance (informational)
- Upload evidence files
- Generate a PDF Evidence Pack for reporting

---

## Features

### 1) Case Setup
- Generates a Case ID
- Allows case title and role selection (Victim/Target, Witness, Reporter)

### 2) Incident Timeline Builder
- Add multiple incident entries (date, time, location, description)
- Encourages structured evidence collection

### 3) Harassment Detection (Hybrid)
The app detects harassment signals using:
- **ML Model (Real Dataset)**
  - Word2Vec embeddings
  - Multi-label Logistic Regression (OneVsRest)
  - Outputs toxicity probabilities:
    - toxic
    - obscene
    - insult
    - threat
    - identity_hate
    - severe_toxic
- **Rule-Based Harassment Type Detection**
  - Workplace harassment
  - Cyber harassment
  - Sexual harassment indicators
  - Stalking indicators
  - Threat / intimidation indicators

### 4) India Legal Guidance (Informational)
Based on detected harassment types, the app suggests relevant Indian legal references such as:
- IPC sections
- IT Act references
- POSH Act guidance (workplace harassment)

> Disclaimer: The app provides informational guidance only and is not legal advice.

### 5) Evidence Upload Support
- Upload files such as screenshots, chat logs, images, etc.
- Stored locally in the project directory (not uploaded publicly)

### 6) Evidence Readiness Score
A basic scoring system to indicate whether the case documentation is strong enough for reporting.

### 7) PDF Evidence Pack Export
Generates a structured PDF report containing:
- Case details
- Timeline events
- Harassment detection results
- ML risk signals
- Suggested India legal guidance
- Evidence file listing

---

## Tech Stack

- **Frontend:** Streamlit
- **ML/NLP:** Gensim Word2Vec, Scikit-learn
- **Data:** Multi-label toxicity dataset (`train.csv`)
- **PDF Generation:** ReportLab
- **Version Control:** Git + GitHub

---

## Project Structure
# Harassment Detection + Evidence Support App (India)

A Streamlit-based real-world oriented application that helps users:
- Document harassment incidents in a structured timeline
- Analyse incident summaries using Machine Learning (real dataset)
- Detect harassment categories (hybrid ML + rule-based)
- Suggest India-specific legal guidance (informational)
- Upload evidence files
- Generate a PDF Evidence Pack for reporting

---

## Features

### 1) Case Setup
- Generates a Case ID
- Allows case title and role selection (Victim/Target, Witness, Reporter)

### 2) Incident Timeline Builder
- Add multiple incident entries (date, time, location, description)
- Encourages structured evidence collection

### 3) Harassment Detection (Hybrid)
The app detects harassment signals using:
- **ML Model (Real Dataset)**
  - Word2Vec embeddings
  - Multi-label Logistic Regression (OneVsRest)
  - Outputs toxicity probabilities:
    - toxic
    - obscene
    - insult
    - threat
    - identity_hate
    - severe_toxic
- **Rule-Based Harassment Type Detection**
  - Workplace harassment
  - Cyber harassment
  - Sexual harassment indicators
  - Stalking indicators
  - Threat / intimidation indicators

### 4) India Legal Guidance (Informational)
Based on detected harassment types, the app suggests relevant Indian legal references such as:
- IPC sections
- IT Act references
- POSH Act guidance (workplace harassment)

> Disclaimer: The app provides informational guidance only and is not legal advice.

### 5) Evidence Upload Support
- Upload files such as screenshots, chat logs, images, etc.
- Stored locally in the project directory (not uploaded publicly)

### 6) Evidence Readiness Score
A basic scoring system to indicate whether the case documentation is strong enough for reporting.

### 7) PDF Evidence Pack Export
Generates a structured PDF report containing:
- Case details
- Timeline events
- Harassment detection results
- ML risk signals
- Suggested India legal guidance
- Evidence file listing

---

## Tech Stack

- **Frontend:** Streamlit
- **ML/NLP:** Gensim Word2Vec, Scikit-learn
- **Data:** Multi-label toxicity dataset (`train.csv`)
- **PDF Generation:** ReportLab
- **Version Control:** Git + GitHub

---

## Project Structure

harassment_evidence_app/
│
├── app/
│ ├── streamlit_app.py
│ ├── models/
│ └── utils/
│ ├── ml_predictor.py
│ ├── harassment_rules.py
│ ├── india_laws.py
│ └── pdf_generator.py
│
├── data/
│ └── train.csv
│
├── model_training/
│ └── train_model.py
│
└── requirements.txt

---

## Setup Instructions

### 1) Create Environment
```bash
conda create -n harassmentapp python=3.10 -y
conda activate harassmentapp
pip install -r requirements.txt
python model_training/train_model.py
python -m streamlit run app/streamlit_app.py
Notes

ML outputs are supportive indicators, not proof.

Future improvements:

Inline image thumbnails in PDF evidence pack

Better harassment taxonomy and dataset coverage

Better model performance and threshold tuning

Deployment to Streamlit Cloud
Author

Sanjana Kulkarni

