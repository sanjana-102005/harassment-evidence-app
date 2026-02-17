import os
import json
import uuid
import hashlib
from datetime import datetime

import streamlit as st

from utils.pdf_generator import generate_evidence_pdf
from utils.ml_predictor import load_models, predict_text, LABEL_COLS
from utils.harassment_rules import detect_harassment_types
from utils.india_laws import get_india_laws


# -----------------------------
# Basic config
# -----------------------------
st.set_page_config(
    page_title="Harassment Detection + Evidence Support",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, "..", "exports")
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -----------------------------
# Session defaults
# -----------------------------
if "case_id" not in st.session_state:
    st.session_state.case_id = str(uuid.uuid4())[:8]

if "timeline" not in st.session_state:
    st.session_state.timeline = []

if "uploads" not in st.session_state:
    st.session_state.uploads = []

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = {}

if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False

if "ml_ready" not in st.session_state:
    st.session_state.ml_ready = False


# -----------------------------
# Load ML models once
# -----------------------------
@st.cache_resource
def _load_ml_models():
    return load_models()


try:
    if not st.session_state.models_loaded:
        w2v, clf = _load_ml_models()
        st.session_state.models_loaded = True
        st.session_state.ml_ready = (w2v is not None and clf is not None)
except Exception:
    st.session_state.models_loaded = True
    st.session_state.ml_ready = False


# -----------------------------
# Helpers
# -----------------------------
def compute_sha256(file_path: str):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def safe_delete_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
            return True
    except Exception:
        return False
    return False


def save_upload(file_obj):
    if file_obj is None:
        return None

    safe_name = f"{uuid.uuid4().hex}_{file_obj.name}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(save_path, "wb") as f:
        f.write(file_obj.getbuffer())

    size_kb = round(os.path.getsize(save_path) / 1024, 2)
    sha256_hash = compute_sha256(save_path)

    return {
        "original_name": file_obj.name,
        "saved_name": safe_name,
        "path": save_path,
        "size_kb": size_kb,
        "sha256": sha256_hash,
        "uploaded_at": datetime.now().isoformat(),
    }


def run_full_analysis(text: str):
    """
    Hybrid analysis:
    - Rule-based harassment type detection
    - ML toxicity probabilities
    - India laws mapping
    - Final combined severity score
    """

    text = (text or "").strip()

    # RULE BASED
    detected_types, rule_hits = detect_harassment_types(text)

    # INDIA LAWS (based on detected types)
    laws = get_india_laws(detected_types)

    # ML BASED
    ml_probs = {}
    if st.session_state.ml_ready:
        try:
            ml_probs = predict_text(text)
        except Exception:
            ml_probs = {}

    # Combine into severity score (0-100)
    severity = 0

    type_weights = {
        "Sexual Harassment / Physical Touching": 40,
        "Workplace Harassment": 25,
        "Stalking / Repeated Contact": 30,
        "Online Sexual Harassment / Obscene Content": 30,
        "Threat / Intimidation": 35,
        "Blackmail / Sextortion": 35,
        "Hate-based Harassment": 25,
        "General Verbal Abuse": 15,
    }

    for t in detected_types:
        severity += type_weights.get(t, 15)

    if ml_probs:
        severity += int(ml_probs.get("toxic", 0) * 25)
        severity += int(ml_probs.get("threat", 0) * 35)
        severity += int(ml_probs.get("identity_hate", 0) * 20)
        severity += int(ml_probs.get("obscene", 0) * 20)
        severity += int(ml_probs.get("insult", 0) * 15)

    severity = min(100, severity)

    harassment_likely = False
    if detected_types:
        harassment_likely = True
    elif ml_probs and ml_probs.get("toxic", 0) > 0.55:
        harassment_likely = True

    return {
        "harassment_likely": harassment_likely,
        "combined_severity": severity,
        "detected_types": detected_types,
        "rule_hits": rule_hits,
        "ml_probs": ml_probs,
        "laws": laws,
    }


# -----------------------------
# UI Layout
# -----------------------------
st.title("🛡️ Harassment Detection + Evidence Support (India)")

left, mid, right = st.columns([1, 1.6, 1.2])


# -----------------------------
# LEFT: Case Setup
# -----------------------------
with left:
    st.subheader("📌 Case Setup")

    st.markdown(f"**Case ID:** `{st.session_state.case_id}`")

    case_title = st.text_input(
        "Case Title",
        value="Harassment Incident Report",
        key="case_title",
    )

    reporter_role = st.selectbox(
        "Your role",
        ["Victim/Target", "Witness", "Friend/Helper", "HR/Employer", "Other"],
        key="reporter_role",
    )

    st.divider()
    st.subheader("🔐 Privacy Mode")

    delete_after_export = st.checkbox(
        "Delete uploaded evidence files after generating PDF",
        value=True,
        help="Recommended for real-world privacy. PDF will still contain file hashes + thumbnails.",
    )

    st.divider()
    st.subheader("⚠️ Disclaimer")
    st.write(
        "This app provides organizational support and general information. "
        "It is **not legal advice**. ML outputs are **not proof**."
    )


# -----------------------------
# MID: Incident + Timeline
# -----------------------------
with mid:
    st.subheader("📝 Incident Details")

    incident_location = st.text_input(
        "Where did it happen? (optional)",
        placeholder="WhatsApp, Instagram, Office, College, Street...",
        key="incident_location",
    )

    incident_summary = st.text_area(
        "What happened? (Write the incident summary here)",
        height=140,
        placeholder="Example: My boss touched me inappropriately in the office and threatened my job...",
        key="incident_summary",
    )

    st.subheader("📅 Timeline Entry")

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input("Date", key="entry_date")

    with col2:
        entry_time = st.time_input("Time", key="entry_time")

    entry_location = st.text_input(
        "Location",
        placeholder="Office floor 2 / WhatsApp chat / College gate...",
        key="entry_location",
    )

    entry_desc = st.text_area(
        "Event description",
        height=80,
        placeholder="Describe what happened in this timeline entry...",
        key="entry_desc",
    )

    if st.button("➕ Add to Timeline"):
        if entry_desc.strip():
            st.session_state.timeline.append(
                {
                    "date": str(entry_date),
                    "time": str(entry_time),
                    "location": entry_location.strip(),
                    "description": entry_desc.strip(),
                }
            )
            st.success("Timeline entry added.")
        else:
            st.error("Timeline description cannot be empty.")

    if st.session_state.timeline:
        st.info("Timeline entries:")
        for i, e in enumerate(st.session_state.timeline, start=1):
            st.write(f"**{i}.** {e['date']} {e['time']} — {e['location']}")
            st.caption(e["description"])
    else:
        st.info("No timeline entries yet. Add at least 2–3 for a strong report.")


# -----------------------------
# RIGHT: Analyse + Upload + Export
# -----------------------------
with right:
    st.subheader("🔍 Harassment Detection (Hybrid)")
    st.write("This will NOT run automatically. Click the button below.")

    analyse_clicked = st.button("🔍 Analyse Incident", use_container_width=True)

    if analyse_clicked:
        if not incident_summary.strip():
            st.error("Write an incident summary first.")
        else:
            result = run_full_analysis(incident_summary)
            st.session_state.analysis_done = True
            st.session_state.analysis_result = result

    if st.session_state.analysis_done:
        res = st.session_state.analysis_result

        st.subheader("📌 Analysis Result")

        if res.get("harassment_likely"):
            st.success("Harassment Likely: YES")
        else:
            st.warning("Harassment Likely: NOT CLEAR / LOW SIGNAL")

        st.write(f"**Severity Score:** `{res.get('combined_severity', 0)}/100`")

        st.divider()
        st.subheader("📍 Detected Harassment Types")

        types = res.get("detected_types", [])
        if types:
            for t in types:
                st.write(f"✅ {t}")
        else:
            st.write("No harassment types detected.")

        st.divider()
        st.subheader("⚖️ Possible Indian Laws (Informational)")

        laws = res.get("laws", [])
        if laws:
            for sec, desc in laws:
                st.write(f"**{sec}** — {desc}")
        else:
            st.write("No law suggestions available for this summary.")

        st.divider()
        st.subheader("🤖 ML Toxicity Probabilities")

        if st.session_state.ml_ready:
            ml_probs = res.get("ml_probs", {})
            if ml_probs:
                for k in LABEL_COLS:
                    st.progress(float(ml_probs.get(k, 0.0)))
                    st.caption(f"{k}: {ml_probs.get(k, 0.0):.3f}")
            else:
                st.write("ML model returned no probabilities.")
        else:
            st.warning("ML model not available. Only rule-based detection is active.")

        with st.expander("🔎 Why it detected these types (rule matches)"):
            hits = res.get("rule_hits", {})
            if hits:
                for cat, phrases in hits.items():
                    st.write(f"**{cat}**")
                    for p in phrases:
                        st.write(f"• matched: `{p}`")
            else:
                st.write("No rule hits recorded.")

    st.divider()
    st.subheader("📎 Upload Evidence (SHA256 secured)")

    up = st.file_uploader(
        "Upload screenshots / audio / docs",
        type=["png", "jpg", "jpeg", "pdf", "txt", "mp3", "wav"],
        accept_multiple_files=True,
    )

    if up:
        for f in up:
            saved = save_upload(f)
            if saved:
                st.session_state.uploads.append(saved)
        st.success("Uploaded successfully.")

    if st.session_state.uploads:
        st.write("Uploaded files (with SHA256 hash):")
        for u in st.session_state.uploads:
            st.caption(f"• {u['original_name']} ({u['size_kb']} KB)")
            st.code(u.get("sha256", "N/A"), language="text")
    else:
        st.caption("No files uploaded yet.")

    st.divider()
    st.subheader("📄 Export Evidence Pack")

    case_json = {
        "case_id": st.session_state.case_id,
        "case_title": case_title.strip(),
        "reporter_role": reporter_role,
        "incident_location": incident_location.strip(),
        "incident_summary": incident_summary.strip(),
        "timeline": st.session_state.timeline,
        "uploads": st.session_state.uploads,
        "analysis_done": st.session_state.analysis_done,
        "analysis_result": st.session_state.analysis_result,
        "created_at": datetime.now().isoformat(),
    }

    if st.button("📄 Generate PDF Evidence Pack", use_container_width=True):
        pdf_name = f"evidence_pack_{st.session_state.case_id}.pdf"
        pdf_path = os.path.join(EXPORT_DIR, pdf_name)

        generate_evidence_pdf(case_json, pdf_path)

        # Offer download
        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                data=f.read(),
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
            )

        # PRIVACY MODE: delete evidence after export
        if delete_after_export:
            deleted_count = 0
            for u in list(st.session_state.uploads):
                if safe_delete_file(u.get("path")):
                    deleted_count += 1

            st.session_state.uploads = []
            st.success(
                f"PDF generated successfully. Privacy Mode ON → deleted {deleted_count} evidence files."
            )
        else:
            st.success("PDF generated successfully. Privacy Mode OFF → evidence files kept locally.")

    st.download_button(
        "💾 Save Case as JSON",
        data=json.dumps(case_json, indent=2).encode("utf-8"),
        file_name=f"case_{st.session_state.case_id}.json",
        mime="application/json",
        use_container_width=True,
    )
