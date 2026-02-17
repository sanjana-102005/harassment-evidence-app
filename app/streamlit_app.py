import os
import json
import uuid
import shutil
import hashlib
from datetime import datetime

import streamlit as st

from utils.pdf_generator import generate_evidence_pdf
from utils.ml_predictor import load_models, predict_text, LABEL_COLS
from utils.harassment_rules import detect_harassment_types
from utils.india_laws import get_india_laws
from utils.complaint_drafts import (
    build_police_complaint,
    build_posh_complaint,
    build_cybercrime_draft,
)

# -----------------------------
# Basic config
# -----------------------------
st.set_page_config(
    page_title="Harassment Detection + Evidence Support",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_ROOT = os.path.join(BASE_DIR, "..", "exports")
UPLOAD_ROOT = os.path.join(BASE_DIR, "..", "uploads")

os.makedirs(EXPORT_ROOT, exist_ok=True)
os.makedirs(UPLOAD_ROOT, exist_ok=True)


# -----------------------------
# Case/session helpers
# -----------------------------
def get_case_upload_dir(case_id: str) -> str:
    p = os.path.join(UPLOAD_ROOT, case_id)
    os.makedirs(p, exist_ok=True)
    return p


def get_case_export_dir(case_id: str) -> str:
    p = os.path.join(EXPORT_ROOT, case_id)
    os.makedirs(p, exist_ok=True)
    return p


def safe_rmtree(path: str):
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            return True
    except Exception:
        return False
    return False


def new_case():
    st.session_state.case_id = str(uuid.uuid4())[:8]
    st.session_state.timeline = []
    st.session_state.uploads = []
    st.session_state.analysis_done = False
    st.session_state.analysis_result = {}
    st.session_state.police_draft = None
    st.session_state.posh_draft = None
    st.session_state.cyber_draft = None
    st.session_state.case_title = "Harassment Incident Report"
    st.session_state.reporter_role = "Victim/Target"
    st.session_state.incident_location = ""
    st.session_state.incident_summary = ""


if "case_id" not in st.session_state:
    new_case()

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
# Hashing
# -----------------------------
def compute_sha256(file_path: str):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


# -----------------------------
# Upload handling
# -----------------------------
def save_upload(file_obj):
    if file_obj is None:
        return None

    case_id = st.session_state.case_id
    upload_dir = get_case_upload_dir(case_id)

    safe_name = f"{uuid.uuid4().hex}_{file_obj.name}"
    save_path = os.path.join(upload_dir, safe_name)

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


def cleanup_case_files():
    """
    Deletes the entire uploads/<case_id>/ folder
    and clears session uploads list.
    """
    case_id = st.session_state.case_id
    upload_dir = os.path.join(UPLOAD_ROOT, case_id)
    safe_rmtree(upload_dir)
    st.session_state.uploads = []


def cleanup_case_exports():
    """
    Deletes exports/<case_id>/ folder.
    """
    case_id = st.session_state.case_id
    export_dir = os.path.join(EXPORT_ROOT, case_id)
    safe_rmtree(export_dir)


# -----------------------------
# Analysis
# -----------------------------
def run_full_analysis(text: str):
    text = (text or "").strip()

    detected_types, rule_hits = detect_harassment_types(text)
    laws = get_india_laws(detected_types)

    ml_probs = {}
    if st.session_state.ml_ready:
        try:
            ml_probs = predict_text(text)
        except Exception:
            ml_probs = {}

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
# UI Header
# -----------------------------
st.title("🛡️ Harassment Detection + Evidence Support (India)")
st.caption("Hybrid harassment analysis + evidence integrity + complaint draft generation.")

st.warning(
    "⚠️ Real-world safety note: Do NOT upload highly sensitive evidence on a public deployment. "
    "Use local deployment for real cases. This tool is for educational + organizational support."
)

topA, topB, topC = st.columns([1, 1, 1])

with topA:
    st.markdown(f"**Case ID:** `{st.session_state.case_id}`")

with topB:
    st.caption("Uploads and exports are isolated per Case ID (real-world safe).")

with topC:
    if st.button("🧹 Reset Case (Delete uploads + clear data)", use_container_width=True):
        cleanup_case_files()
        cleanup_case_exports()
        new_case()
        st.success("Case reset done. Uploads and exports cleared.")
        st.rerun()

tabs = st.tabs(["🔍 Analyse Incident", "📄 Evidence Pack (PDF)", "📝 Complaint Drafts"])


# =========================================================
# TAB 1
# =========================================================
with tabs[0]:
    left, mid, right = st.columns([1, 1.6, 1.2])

    with left:
        st.subheader("📌 Case Setup")

        st.session_state.case_title = st.text_input(
            "Case Title",
            value=st.session_state.case_title,
        )

        roles = ["Victim/Target", "Witness", "Friend/Helper", "HR/Employer", "Other"]
        st.session_state.reporter_role = st.selectbox(
            "Your role",
            roles,
            index=roles.index(st.session_state.reporter_role)
            if st.session_state.reporter_role in roles
            else 0,
        )

        st.divider()
        st.subheader("⚠️ Disclaimer")
        st.write(
            "This app provides organizational support and general information. "
            "It is **not legal advice**. ML outputs are **not proof**."
        )

    with mid:
        st.subheader("📝 Incident Details")

        st.session_state.incident_location = st.text_input(
            "Where did it happen? (optional)",
            placeholder="WhatsApp, Instagram, Office, College, Street...",
            value=st.session_state.incident_location,
        )

        st.session_state.incident_summary = st.text_area(
            "What happened? (Write the incident summary here)",
            height=140,
            placeholder="Example: My boss touched me inappropriately in the office and threatened my job...",
            value=st.session_state.incident_summary,
        )

        st.subheader("📅 Timeline Entry")

        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Date")
        with col2:
            entry_time = st.time_input("Time")

        entry_location = st.text_input(
            "Location",
            placeholder="Office floor 2 / WhatsApp chat / College gate...",
        )

        entry_desc = st.text_area(
            "Event description",
            height=80,
            placeholder="Describe what happened in this timeline entry...",
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

    with right:
        st.subheader("🔍 Harassment Detection (Hybrid)")
        st.write("This will NOT run automatically. Click the button below.")

        analyse_clicked = st.button("🔍 Analyse Incident", use_container_width=True)

        if analyse_clicked:
            if not st.session_state.incident_summary.strip():
                st.error("Write an incident summary first.")
            else:
                result = run_full_analysis(st.session_state.incident_summary)
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


# =========================================================
# TAB 2
# =========================================================
with tabs[1]:
    st.subheader("📎 Upload Evidence + Export PDF")

    st.info(
        "Evidence uploads are stored temporarily in `/uploads/<case_id>/`. "
        "Recommended: keep Privacy Mode ON."
    )

    delete_after_export = st.checkbox(
        "Privacy Mode: Delete uploaded evidence files after generating PDF",
        value=True,
    )

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

    case_json = {
        "case_id": st.session_state.case_id,
        "case_title": st.session_state.case_title.strip(),
        "reporter_role": st.session_state.reporter_role,
        "incident_location": st.session_state.incident_location.strip(),
        "incident_summary": st.session_state.incident_summary.strip(),
        "timeline": st.session_state.timeline,
        "uploads": st.session_state.uploads,
        "analysis_done": st.session_state.analysis_done,
        "analysis_result": st.session_state.analysis_result,
        "created_at": datetime.now().isoformat(),
    }

    st.divider()

    if st.button("📄 Generate PDF Evidence Pack", use_container_width=True):
        case_id = st.session_state.case_id
        export_dir = get_case_export_dir(case_id)

        pdf_name = f"evidence_pack_{case_id}.pdf"
        pdf_path = os.path.join(export_dir, pdf_name)

        generate_evidence_pdf(case_json, pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                data=f.read(),
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
            )

        if delete_after_export:
            cleanup_case_files()
            cleanup_case_exports()
            st.success("PDF generated. Privacy Mode ON → uploads and exports deleted.")
        else:
            st.success("PDF generated. Privacy Mode OFF → uploads and exports kept.")

    st.download_button(
        "💾 Save Case as JSON",
        data=json.dumps(case_json, indent=2).encode("utf-8"),
        file_name=f"case_{st.session_state.case_id}.json",
        mime="application/json",
        use_container_width=True,
    )


# =========================================================
# TAB 3
# =========================================================
with tabs[2]:
    st.subheader("📝 Complaint Draft Generator (India)")
    st.write(
        "Generates structured complaint drafts based on your case summary, timeline, "
        "detected harassment types, and suggested laws."
    )

    case_json = {
        "case_id": st.session_state.case_id,
        "case_title": st.session_state.case_title.strip(),
        "reporter_role": st.session_state.reporter_role,
        "incident_location": st.session_state.incident_location.strip(),
        "incident_summary": st.session_state.incident_summary.strip(),
        "timeline": st.session_state.timeline,
        "uploads": st.session_state.uploads,
        "analysis_done": st.session_state.analysis_done,
        "analysis_result": st.session_state.analysis_result,
        "created_at": datetime.now().isoformat(),
    }

    if not case_json["incident_summary"]:
        st.warning("Please fill the incident summary in the Analyse tab first.")
    else:
        colA, colB, colC = st.columns(3)

        with colA:
            if st.button("🚓 Generate Police Complaint", use_container_width=True):
                st.session_state.police_draft = build_police_complaint(case_json)

        with colB:
            if st.button("🏢 Generate POSH Complaint", use_container_width=True):
                st.session_state.posh_draft = build_posh_complaint(case_json)

        with colC:
            if st.button("💻 Generate Cybercrime Draft", use_container_width=True):
                st.session_state.cyber_draft = build_cybercrime_draft(case_json)

        st.divider()

        if st.session_state.get("police_draft"):
            st.subheader("🚓 Police Complaint Draft")
            st.text_area("Draft", st.session_state.police_draft, height=320)
            st.download_button(
                "⬇️ Download Police Draft (TXT)",
                data=st.session_state.police_draft.encode("utf-8"),
                file_name=f"police_complaint_{st.session_state.case_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if st.session_state.get("posh_draft"):
            st.subheader("🏢 POSH Complaint Draft")
            st.text_area("Draft", st.session_state.posh_draft, height=320)
            st.download_button(
                "⬇️ Download POSH Draft (TXT)",
                data=st.session_state.posh_draft.encode("utf-8"),
                file_name=f"posh_complaint_{st.session_state.case_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if st.session_state.get("cyber_draft"):
            st.subheader("💻 Cybercrime Complaint Draft")
            st.text_area("Draft", st.session_state.cyber_draft, height=320)
            st.download_button(
                "⬇️ Download Cybercrime Draft (TXT)",
                data=st.session_state.cyber_draft.encode("utf-8"),
                file_name=f"cybercrime_complaint_{st.session_state.case_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )
