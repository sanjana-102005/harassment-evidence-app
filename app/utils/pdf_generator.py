import os
import io
import hashlib
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_str(x):
    if x is None:
        return ""
    return str(x)


def _build_case_fingerprint(case_data: dict) -> str:
    """
    Creates a stable fingerprint of the entire case
    excluding local file paths.
    """
    clean = dict(case_data)

    uploads = []
    for u in case_data.get("uploads", []):
        uploads.append(
            {
                "original_name": u.get("original_name"),
                "saved_name": u.get("saved_name"),
                "size_kb": u.get("size_kb"),
                "sha256": u.get("sha256"),
                "uploaded_at": u.get("uploaded_at"),
            }
        )
    clean["uploads"] = uploads

    return _sha256_text(str(clean))


def _image_thumbnail(path: str, max_w=3.5 * inch, max_h=3.5 * inch):
    """
    Returns a ReportLab Image object resized safely.
    """
    try:
        pil = PILImage.open(path)
        pil.thumbnail((int(max_w), int(max_h)))
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        buf.seek(0)
        return Image(buf, width=pil.size[0], height=pil.size[1])
    except Exception:
        return None


def generate_evidence_pdf(case_data: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("Harassment Evidence Pack (India)", styles["Title"]))
    story.append(Spacer(1, 10))

    # Case meta
    case_id = case_data.get("case_id", "N/A")
    story.append(Paragraph(f"<b>Case ID:</b> {case_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Created:</b> {datetime.now().isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 10))

    # Case summary
    story.append(Paragraph("<b>Case Title</b>", styles["Heading2"]))
    story.append(Paragraph(_safe_str(case_data.get("case_title", "")), styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Reporter Role</b>", styles["Heading2"]))
    story.append(Paragraph(_safe_str(case_data.get("reporter_role", "")), styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Incident Location</b>", styles["Heading2"]))
    story.append(Paragraph(_safe_str(case_data.get("incident_location", "")), styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Incident Summary</b>", styles["Heading2"]))
    story.append(Paragraph(_safe_str(case_data.get("incident_summary", "")), styles["Normal"]))
    story.append(Spacer(1, 12))

    # Timeline
    story.append(Paragraph("Timeline", styles["Heading1"]))
    timeline = case_data.get("timeline", [])
    if timeline:
        rows = [["#", "Date", "Time", "Location", "Description"]]
        for i, e in enumerate(timeline, start=1):
            rows.append(
                [
                    str(i),
                    _safe_str(e.get("date")),
                    _safe_str(e.get("time")),
                    _safe_str(e.get("location")),
                    _safe_str(e.get("description")),
                ]
            )
        table = Table(rows, colWidths=[0.4 * inch, 1.0 * inch, 0.8 * inch, 1.6 * inch, 2.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No timeline entries provided.", styles["Normal"]))

    story.append(PageBreak())

    # Analysis
    story.append(Paragraph("Analysis Output", styles["Heading1"]))
    analysis = case_data.get("analysis_result", {}) if case_data.get("analysis_done") else {}

    story.append(Paragraph(f"<b>Harassment Likely:</b> {_safe_str(analysis.get('harassment_likely'))}", styles["Normal"]))
    story.append(Paragraph(f"<b>Severity:</b> {_safe_str(analysis.get('combined_severity'))}/100", styles["Normal"]))
    story.append(Spacer(1, 10))

    # Types
    story.append(Paragraph("<b>Detected Types</b>", styles["Heading2"]))
    types = analysis.get("detected_types", [])
    if types:
        for t in types:
            story.append(Paragraph(f"• {t}", styles["Normal"]))
    else:
        story.append(Paragraph("None detected.", styles["Normal"]))

    story.append(Spacer(1, 10))

    # Laws
    story.append(Paragraph("<b>Suggested Indian Legal References (Informational)</b>", styles["Heading2"]))
    laws = analysis.get("laws", [])
    if laws:
        for sec, desc in laws:
            story.append(Paragraph(f"• <b>{sec}</b>: {desc}", styles["Normal"]))
    else:
        story.append(Paragraph("No law suggestions available.", styles["Normal"]))

    story.append(PageBreak())

    # Evidence list + hashes
    story.append(Paragraph("Evidence Listing + Integrity (SHA256)", styles["Heading1"]))
    uploads = case_data.get("uploads", [])
    if uploads:
        rows = [["#", "File", "Size (KB)", "SHA256"]]
        for i, u in enumerate(uploads, start=1):
            rows.append(
                [
                    str(i),
                    _safe_str(u.get("original_name")),
                    _safe_str(u.get("size_kb")),
                    _safe_str(u.get("sha256")),
                ]
            )
        table = Table(rows, colWidths=[0.4 * inch, 2.0 * inch, 0.9 * inch, 3.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No evidence files uploaded.", styles["Normal"]))

    story.append(Spacer(1, 12))

    # Case fingerprint
    fingerprint = _build_case_fingerprint(case_data)
    story.append(Paragraph("<b>Case Fingerprint (SHA256)</b>", styles["Heading2"]))
    story.append(Paragraph(fingerprint, styles["Code"]))
    story.append(Spacer(1, 10))

    # Thumbnails
    story.append(Paragraph("Image Thumbnails (if applicable)", styles["Heading1"]))
    any_thumb = False
    for u in uploads:
        p = u.get("path", "")
        if p.lower().endswith((".png", ".jpg", ".jpeg")) and os.path.exists(p):
            thumb = _image_thumbnail(p)
            if thumb:
                any_thumb = True
                story.append(Paragraph(f"<b>{u.get('original_name')}</b>", styles["Normal"]))
                story.append(thumb)
                story.append(Spacer(1, 12))

    if not any_thumb:
        story.append(Paragraph("No image thumbnails available.", styles["Normal"]))

    # Footer note
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "<i>Note: This PDF is generated for documentation support. "
            "Hashes are included for integrity verification.</i>",
            styles["Normal"],
        )
    )

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    doc.build(story)
