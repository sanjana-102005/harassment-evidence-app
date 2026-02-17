import re

# -----------------------------
# Harassment Type Rules
# -----------------------------
HARASSMENT_PATTERNS = {
    "Sexual Harassment / Physical Touching": [
        r"\btouched\b",
        r"\bgrabbed\b",
        r"\bgroped\b",
        r"\bmolested\b",
        r"\bkiss(ed)?\b",
        r"\bforced\b.*\bkiss\b",
        r"\bprivate\b.*\bpart\b",
        r"\binappropriate\b.*\btouch\b",
        r"\bbody\b.*\btouch\b",
    ],
    "Workplace Harassment": [
        r"\bboss\b",
        r"\bmanager\b",
        r"\bhr\b",
        r"\bworkplace\b",
        r"\boffice\b",
        r"\bteam lead\b",
        r"\bcolleague\b",
        r"\bsupervisor\b",
    ],
    "Stalking / Repeated Contact": [
        r"\bstalking\b",
        r"\bfollowing\b",
        r"\bfollowed\b",
        r"\bkeeps calling\b",
        r"\bkeeps texting\b",
        r"\bkeeps messaging\b",
        r"\bwon't stop\b",
        r"\boutside my house\b",
        r"\bwaited\b.*\boutside\b",
    ],
    "Online Sexual Harassment / Obscene Content": [
        r"\bdick pic\b",
        r"\bnude\b",
        r"\bnudes\b",
        r"\bexplicit\b",
        r"\bobscene\b",
        r"\bporn\b",
        r"\bsex chat\b",
        r"\bsext\b",
        r"\bdirty\b.*\bmessages\b",
    ],
    "Threat / Intimidation": [
        r"\bthreat\b",
        r"\bkill\b",
        r"\bhurt\b",
        r"\bruined\b.*\blife\b",
        r"\bblackmail\b",
        r"\bthreatened\b",
        r"\bif you tell\b",
        r"\blose your job\b",
        r"\bfire you\b",
    ],
    "Blackmail / Sextortion": [
        r"\bsextortion\b",
        r"\bblackmail\b.*\bvideo\b",
        r"\bblackmail\b.*\bphoto\b",
        r"\bshare\b.*\bvideo\b",
        r"\bshare\b.*\bphotos\b",
        r"\bleak\b.*\bphotos\b",
        r"\bleak\b.*\bvideo\b",
    ],
    "Hate-based Harassment": [
        r"\bcaste\b",
        r"\breligion\b",
        r"\bmuslim\b",
        r"\bhindu\b",
        r"\bchristian\b",
        r"\bdalit\b",
        r"\bslur\b",
        r"\bracist\b",
    ],
    "General Verbal Abuse": [
        r"\bidiot\b",
        r"\bstupid\b",
        r"\bwhore\b",
        r"\bslut\b",
        r"\bbitch\b",
        r"\bcheap\b",
        r"\bshame\b",
        r"\bembarrass\b",
    ],
}


def detect_harassment_types(text: str):
    text = (text or "").lower()

    detected = []
    hits = {}

    for category, patterns in HARASSMENT_PATTERNS.items():
        matched_phrases = []
        for p in patterns:
            if re.search(p, text):
                matched_phrases.append(p)
        if matched_phrases:
            detected.append(category)
            hits[category] = matched_phrases

    return detected, hits


# -----------------------------
# Evidence Checklist (REAL WORLD)
# -----------------------------
EVIDENCE_LIBRARY = {
    "Sexual Harassment / Physical Touching": [
        "CCTV footage (office/college/public place)",
        "Witness statement (colleagues, friends, security)",
        "Medical report (if injury occurred)",
        "Written record of incident (date/time/location)",
        "HR complaint / POSH Internal Committee complaint",
    ],
    "Workplace Harassment": [
        "Email/Teams/Slack messages",
        "HR complaint / POSH complaint",
        "Witness statement from coworkers",
        "Office entry logs / attendance proof",
        "CCTV footage (if available)",
    ],
    "Stalking / Repeated Contact": [
        "Call logs and screenshots of messages",
        "Location proof (CCTV / gate logs)",
        "Witness statement (neighbors/friends)",
        "Police diary entry / complaint number",
    ],
    "Online Sexual Harassment / Obscene Content": [
        "Screenshots of obscene messages",
        "Chat export (WhatsApp/Instagram)",
        "Profile link/username of offender",
        "Device metadata (timestamps)",
    ],
    "Threat / Intimidation": [
        "Screenshots/audio proof of threats",
        "Witness statement (if threats spoken)",
        "Police complaint acknowledgement",
    ],
    "Blackmail / Sextortion": [
        "Screenshots of blackmail messages",
        "Links or files used for threats",
        "Payment proof (if money demanded)",
        "Cybercrime complaint acknowledgement",
    ],
    "Hate-based Harassment": [
        "Screenshots of hate speech / slurs",
        "Witness statement",
        "Any recordings (audio/video)",
    ],
    "General Verbal Abuse": [
        "Screenshots of abusive messages",
        "Witness statement",
    ],
}


def build_evidence_checklist(detected_types: list, uploads: list):
    """
    Returns:
    - checklist: list[str]
    - missing: list[str]
    - readiness_score: int (0-100)
    """
    detected_types = detected_types or []
    uploads = uploads or []

    # Gather evidence recommendations
    recommended = []
    for t in detected_types:
        recommended.extend(EVIDENCE_LIBRARY.get(t, []))

    # Deduplicate
    recommended = list(dict.fromkeys(recommended))

    # Basic evidence signals from uploads
    upload_names = " ".join([u.get("original_name", "").lower() for u in uploads])

    present = set()
    for item in recommended:
        k = item.lower()

        # crude matching
        if "screenshot" in k and ("png" in upload_names or "jpg" in upload_names or "jpeg" in upload_names):
            present.add(item)
        elif "cctv" in k and ("video" in upload_names or "mp4" in upload_names or "mov" in upload_names):
            present.add(item)
        elif "chat export" in k and ("txt" in upload_names or "pdf" in upload_names):
            present.add(item)
        elif "audio" in k and ("mp3" in upload_names or "wav" in upload_names):
            present.add(item)
        elif "medical" in k and ("pdf" in upload_names):
            present.add(item)
        elif "email" in k and ("pdf" in upload_names or "txt" in upload_names):
            present.add(item)

    missing = [x for x in recommended if x not in present]

    # Score
    if not recommended:
        readiness_score = 30 if uploads else 10
    else:
        readiness_score = int((len(present) / len(recommended)) * 100)

    # Bonus if timeline exists
    readiness_score = min(100, readiness_score)

    return recommended, missing, readiness_score
