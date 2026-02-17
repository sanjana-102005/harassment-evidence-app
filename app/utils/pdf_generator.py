import os
import hashlib
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def _safe_text(x):
    if x is None:
        return ""
    return str(x)


def _sha256_file(path: str):
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def generate_evidence_pdf(case_json: dict, output_pdf_path: str):
    """
    Generates a real-world evidence pack PDF:
    - Case summary
    - Timeline
    - ML + rules analysis
    - Laws
    - Evidence readiness + missing evidence
    - Uploaded evidence listing + SHA256
    - Inline thumbnails for images
    """
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    styles = getSampleStyleSheet()
    story = []

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    # -----------------------------
    # Header
    # -----------------------------
    story.append(Paragraph("Harassment Evidence Pack (India)", styles["Title"]))
    story.append(Spacer(1, 8))

    meta = [
        ["Case ID", _safe_text(case_json.get("case_id"))],
        ["Case Title", _safe_text(case_json.get("case_title"))],
        ["Reporter Role", _safe_text(case_json.get("reporter_role"))],
        ["Incident Location", _safe_text(case_json.get("incident_location"))],
        ["Created At", _safe_text(case_json.get("created_at", datetime.now().isoformat()))],
    ]

    t = Table(meta, colWidths=[140, 360])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 14))

    # -----------------------------
    # Incident summary
    # -----------------------------
    story.append(Paragraph("Incident Summary", styles["Heading2"]))
    story.append(Paragraph(_safe_text(case_json.get("incident_summary")), styles["BodyText"]))
    story.append(Spacer(1, 12))

    # -----------------------------
    # Timeline
    # -----------------------------
    story.append(Paragraph("Timeline", styles["Heading2"]))
    timeline = case_json.get("timeline", []) or []
    if not timeline:
        story.append(Paragraph("No timeline entries provided.", styles["BodyText"]))
    else:
        rows = [["#", "Date", "Time", "Location", "Description"]]
        for i, e in enumerate(timeline, start=1):
            rows.append(
                [
                    str(i),
                    _safe_text(e.get("date")),
                    _safe_text(e.get("time")),
                    _safe_text(e.get("location")),
                    _safe_text(e.get("description")),
                ]
            )

        table = Table(rows, colWidths=[25, 70, 55, 120, 240])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)

    story.append(Spacer(1, 16))

    # -----------------------------
    # Analysis Section
    # -----------------------------
    story.append(PageBreak())
    story.append(Paragraph("Harassment Analysis", styles["Heading1"]))
    story.append(Spacer(1, 8))

    analysis = case_json.get("analysis_result", {}) or {}

    harassment_likely = analysis.get("harassment_likely", False)
    severity = analysis.get("combined_severity", 0)
    binary_prob = analysis.get("binary_prob", None)

    story.append(Paragraph(f"<b>Harassment Likely:</b> {'YES' if harassment_likely else 'NOT CLEAR'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Severity Score:</b> {severity}/100", styles["BodyText"]))

    if binary_prob is not None:
        story.append(Paragraph(f"<b>Binary Harassment Probability:</b> {binary_prob:.3f}", styles["BodyText"]))
    else:
        story.append(Paragraph("<b>Binary Harassment Probability:</b> Not available", styles["BodyText"]))

    story.append(Spacer(1, 10))

    # Types
    story.append(Paragraph("Detected Harassment Types", styles["Heading2"]))
    types = analysis.get("detected_types", []) or []
    if types:
        for ttype in types:
            story.append(Paragraph(f"• {ttype}", styles["BodyText"]))
    else:
        story.append(Paragraph("No harassment types detected.", styles["BodyText"]))

    story.append(Spacer(1, 10))

    # Laws
    story.append(Paragraph("Possible Indian Legal Sections (Informational)", styles["Heading2"]))
    laws = analysis.get("laws", []) or []
    if laws:
        for sec, desc in laws:
            story.append(Paragraph(f"<b>{_safe_text(sec)}</b> — {_safe_text(desc)}", styles["BodyText"]))
    else:
        story.append(Paragraph("No law suggestions available.", styles["BodyText"]))

    story.append(Spacer(1, 10))

    # Evidence readiness
    story.append(Paragraph("Evidence Readiness", styles["Heading2"]))
    readiness = analysis.get("evidence_readiness", 0)
    story.append(Paragraph(f"<b>Evidence Readiness Score:</b> {readiness}/100", styles["BodyText"]))

    missing = analysis.get("missing_evidence", []) or []
    if missing:
        story.append(Paragraph("<b>Missing evidence recommendations:</b>", styles["BodyText"]))
        for m in missing[:12]:
            story.append(Paragraph(f"• {m}", styles["BodyText"]))
    else:
        story.append(Paragraph("No missing evidence suggestions.", styles["BodyText"]))

    story.append(Spacer(1, 16))

    # -----------------------------
    # Evidence Uploads
    # -----------------------------
    story.append(PageBreak())
    story.append(Paragraph("Uploaded Evidence Files", styles["Heading1"]))
    story.append(Spacer(1, 8))

    uploads = case_json.get("uploads", []) or []
    if not uploads:
        story.append(Paragraph("No evidence files uploaded.", styles["BodyText"]))
    else:
        rows = [["#", "Original Name", "Size (KB)", "SHA256"]]
        for i, u in enumerate(uploads, start=1):
            rows.append(
                [
                    str(i),
                    _safe_text(u.get("original_name")),
                    _safe_text(u.get("size_kb")),
                    _safe_text(u.get("sha256")),
                ]
            )

        table = Table(rows, colWidths=[25, 180, 70, 240])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)

        story.append(Spacer(1, 14))

        # Inline thumbnails (images only)
        story.append(Paragraph("Inline Image Thumbnails", styles["Heading2"]))
        story.append(Spacer(1, 8))

        for u in uploads:
            path = u.get("path", "")
            if not path or not os.path.exists(path):
                continue

            lower = path.lower()
            if not (lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg")):
                continue

            story.append(Paragraph(f"File: {_safe_text(u.get('original_name'))}", styles["BodyText"]))
            story.append(Paragraph(f"SHA256: {_safe_text(u.get('sha256'))}", styles["BodyText"]))
            story.append(Spacer(1, 4))

            try:
                img = Image(path)
                img.drawHeight = 220
                img.drawWidth = 320
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception:
                story.append(Paragraph("⚠️ Could not render image thumbnail.", styles["BodyText"]))
                story.append(Spacer(1, 10))

    # -----------------------------
    # Footer Disclaimer
    # -----------------------------
    story.append(PageBreak())
    story.append(Paragraph("Disclaimer", styles["Heading1"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "This PDF is generated by an educational evidence-support tool. "
            "It does not provide legal advice. Machine learning predictions are not proof. "
            "Always consult appropriate authorities or legal professionals.",
            styles["BodyText"],
        )
    )

    doc.build(story)
