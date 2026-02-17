from datetime import datetime


def build_police_complaint(case_data: dict) -> str:
    case_id = case_data.get("case_id", "N/A")
    title = case_data.get("case_title", "Harassment Complaint")
    role = case_data.get("reporter_role", "Victim/Target")
    location = case_data.get("incident_location", "")
    summary = case_data.get("incident_summary", "")
    timeline = case_data.get("timeline", [])
    analysis = case_data.get("analysis_result", {})
    laws = analysis.get("laws", [])

    lines = []
    lines.append("To,")
    lines.append("The Station House Officer (SHO),")
    lines.append("[Police Station Name],")
    lines.append("[City], [State]")
    lines.append("")
    lines.append(f"Subject: Complaint regarding harassment and request for action (Case ID: {case_id})")
    lines.append("")
    lines.append("Respected Sir/Madam,")
    lines.append("")
    lines.append(
        f"I am writing to file a formal complaint regarding harassment that I have experienced. "
        f"My role is: {role}. The case title is: {title}."
    )
    lines.append("")

    if location:
        lines.append(f"The incident(s) occurred at/through: {location}.")
        lines.append("")

    lines.append("Incident Summary:")
    lines.append(summary if summary else "[Incident summary not provided]")
    lines.append("")

    if timeline:
        lines.append("Timeline of Events:")
        for i, e in enumerate(timeline, start=1):
            lines.append(
                f"{i}. Date: {e.get('date','')} Time: {e.get('time','')} "
                f"Location: {e.get('location','')} - {e.get('description','')}"
            )
        lines.append("")

    if laws:
        lines.append("Possible applicable legal references (informational):")
        for sec, desc in laws:
            lines.append(f"- {sec}: {desc}")
        lines.append("")

    lines.append(
        "I request you to kindly register my complaint, take necessary legal action, "
        "and ensure my safety. I am also prepared to submit supporting evidence (screenshots/files)."
    )
    lines.append("")
    lines.append("Thank you.")
    lines.append("")
    lines.append("Yours faithfully,")
    lines.append("[Your Name]")
    lines.append("[Phone Number]")
    lines.append("[Address]")
    lines.append(f"Date: {datetime.now().date().isoformat()}")

    return "\n".join(lines)


def build_posh_complaint(case_data: dict) -> str:
    case_id = case_data.get("case_id", "N/A")
    title = case_data.get("case_title", "POSH Complaint")
    location = case_data.get("incident_location", "")
    summary = case_data.get("incident_summary", "")
    timeline = case_data.get("timeline", [])
    analysis = case_data.get("analysis_result", {})
    types = analysis.get("detected_types", [])

    lines = []
    lines.append("To,")
    lines.append("The Presiding Officer / Internal Committee (IC),")
    lines.append("[Company / Organization Name]")
    lines.append("")
    lines.append(f"Subject: Formal complaint under POSH Act (Case ID: {case_id})")
    lines.append("")
    lines.append("Respected Sir/Madam,")
    lines.append("")
    lines.append(
        "I am submitting this complaint under the Sexual Harassment of Women at Workplace "
        "(Prevention, Prohibition and Redressal) Act, 2013."
    )
    lines.append("")
    lines.append(f"Case Title: {title}")
    if location:
        lines.append(f"Incident Channel/Location: {location}")
    lines.append("")

    if types:
        lines.append("Detected indicators (supportive):")
        for t in types:
            lines.append(f"- {t}")
        lines.append("")

    lines.append("Incident Summary:")
    lines.append(summary if summary else "[Incident summary not provided]")
    lines.append("")

    if timeline:
        lines.append("Timeline of Events:")
        for i, e in enumerate(timeline, start=1):
            lines.append(
                f"{i}. Date: {e.get('date','')} Time: {e.get('time','')} "
                f"Location: {e.get('location','')} - {e.get('description','')}"
            )
        lines.append("")

    lines.append(
        "I request the Internal Committee to initiate an inquiry, ensure confidentiality, "
        "and take appropriate action as per the POSH Act and company policy."
    )
    lines.append("")
    lines.append("Yours faithfully,")
    lines.append("[Your Name]")
    lines.append("[Employee ID / Department]")
    lines.append("[Phone Number]")
    lines.append(f"Date: {datetime.now().date().isoformat()}")

    return "\n".join(lines)


def build_cybercrime_draft(case_data: dict) -> str:
    case_id = case_data.get("case_id", "N/A")
    location = case_data.get("incident_location", "")
    summary = case_data.get("incident_summary", "")
    timeline = case_data.get("timeline", [])
    uploads = case_data.get("uploads", [])
    analysis = case_data.get("analysis_result", {})
    types = analysis.get("detected_types", [])

    lines = []
    lines.append("Cybercrime Complaint Draft (India)")
    lines.append(f"Case ID: {case_id}")
    lines.append("")
    lines.append("Complaint Type:")
    lines.append(", ".join(types) if types else "Online Harassment / Abuse")
    lines.append("")
    lines.append("Platform / Channel:")
    lines.append(location if location else "[Instagram/WhatsApp/Email/Other]")
    lines.append("")
    lines.append("Incident Summary:")
    lines.append(summary if summary else "[Incident summary not provided]")
    lines.append("")

    if timeline:
        lines.append("Timeline of Events:")
        for i, e in enumerate(timeline, start=1):
            lines.append(
                f"{i}. {e.get('date','')} {e.get('time','')} - {e.get('description','')}"
            )
        lines.append("")

    if uploads:
        lines.append("Evidence Available:")
        for u in uploads:
            lines.append(
                f"- {u.get('original_name')} | SHA256: {u.get('sha256','N/A')}"
            )
        lines.append("")

    lines.append("Requested Action:")
    lines.append(
        "- Register complaint and investigate\n"
        "- Take action against offender\n"
        "- Preserve platform logs and message records\n"
        "- Ensure victim safety and confidentiality"
    )

    return "\n".join(lines)
