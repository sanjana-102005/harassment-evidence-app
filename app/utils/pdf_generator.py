import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image as RLImage,
    KeepTogether,
)
from reportlab.lib import colors


def _safe(v, default=""):
    if v is None:
        return default
    return str(v)


def _is_image(path: str):
    if not path:
        return False
    ext = os.path.splitext(path.lower())[1]
    return ext in [".png", ".jpg", ".jpeg"]


def generate_evidence_pdf(case_data: dict, output_path: str):
    """
    Creates a full evidence pack PDF (with inline thumbnails for images).
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Harassment Evidence Pack",
        author="Harassment Detection + Evidence Support App",
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    h_style = styles["Heading2"]
    h3_style = styles["Heading3"]

    normal = styles["BodyText"]
    normal.fontSize = 10
    normal.leading = 14

    small = ParagraphStyle(
        name="Small",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.grey,
    )

    story = []

    # ---------------------------
    # Header
    # ---------------------------
    story.append(Paragraph("Harassment Evidence Pack (India)", title_style))
    story.append(Spacer(1, 12))

    case_id = _safe(case_data.get("case_id"))
    story.append(Paragraph(f"<b>Case ID:</b> {case_id}", normal))
    story.append(Paragraph(f"<b>Generated at:</b> {datetime.now().isoformat()}", normal))
    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "<i>Disclaimer: This document is generated for organizational support and does not constitute legal advice.</i>",
            small,
        )
    )
    story.append(Spacer(1, 14))

    # ---------------------------
    # Case info
    # ---------------------------
    story.append(Paragraph("1) Case Information", h_style))
    story.append(Spacer(1, 8))

    case_title = _safe(case_data.get("case_title"))
    reporter_role = _safe(case_data.get("reporter_role"))
    incident_location = _safe(case_data.get("incident_location"))
    incident_summary = _safe(case_data.get("incident_summary"))

    info_table = Table(
        [
            ["Case Title", case_title],
            ["Reporter Role", reporter_role],
            ["Incident Location", incident_location],
        ],
        colWidths=[5 * cm, 10 * cm],
    )

    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(info_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Incident Summary:</b>", normal))
    story.append(Spacer(1, 4))
    story.append(Paragraph(incident_summary.replace("\n", "<br/>"), normal))
    story.append(Spacer(1, 14))

    # ---------------------------
    # Analysis section
    # ---------------------------
    story.append(Paragraph("2) Harassment Detection Analysis (Hybrid)", h_style))
    story.append(Spacer(1, 10))

    analysis_done = bool(case_data.get("analysis_done"))
    analysis = case_data.get("analysis_result") or {}

    if not analysis_done or not analysis:
        story.append(
            Paragraph(
                "No analysis was performed before export. (User did not click Analyse.)",
                normal,
            )
        )
        story.append(PageBreak())
    else:
        harassment_likely = analysis.get("harassment_likely", False)
        severity = analysis.get("combined_severity", 0)

        story.append(
            Paragraph(
                f"<b>Harassment Likely:</b> {'YES' if harassment_likely else 'NOT CLEAR / LOW SIGNAL'}",
                normal,
            )
        )
        story.append(Paragraph(f"<b>Severity Score:</b> {severity}/100", normal))
        story.append(Spacer(1, 12))

        # Detected types
        story.append(Paragraph("2.1 Detected Harassment Types", h3_style))
        story.append(Spacer(1, 6))

        types = analysis.get("detected_types") or []
        if types:
            for t in types:
                story.append(Paragraph(f"• {t}", normal))
        else:
            story.append(Paragraph("No harassment types detected.", normal))

        story.append(Spacer(1, 12))

        # India laws
        story.append(Paragraph("2.2 Possible Indian Laws (Informational)", h3_style))
        story.append(Spacer(1, 6))

        laws = analysis.get("laws") or []
        if laws:
            for sec, desc in laws:
                story.append(Paragraph(f"<b>{_safe(sec)}</b> — {_safe(desc)}", normal))
        else:
            story.append(Paragraph("No law suggestions available.", normal))

        story.append(Spacer(1, 12))

        # ML probabilities
        story.append(Paragraph("2.3 ML Toxicity Probabilities", h3_style))
        story.append(Spacer(1, 6))

        ml_probs = analysis.get("ml_probs") or {}
        if ml_probs:
            prob_table_data = [["Label", "Probability"]]
            for k, v in ml_probs.items():
                prob_table_data.append([k, f"{float(v):.3f}"])

            prob_table = Table(prob_table_data, colWidths=[7 * cm, 4 * cm])
            prob_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(prob_table)
        else:
            story.append(
                Paragraph(
                    "ML model probabilities not available (model missing or error).",
                    normal,
                )
            )

        story.append(Spacer(1, 12))

        # Rule hits
        story.append(Paragraph("2.4 Rule Matches (Explainability)", h3_style))
        story.append(Spacer(1, 6))

        rule_hits = analysis.get("rule_hits") or {}
        if rule_hits:
            for cat, phrases in rule_hits.items():
                story.append(Paragraph(f"<b>{cat}</b>", normal))
                for p in phrases:
                    story.append(Paragraph(f"• matched: {p}", normal))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No rule matches recorded.", normal))

        story.append(PageBreak())

    # ---------------------------
    # Timeline section
    # ---------------------------
    story.append(Paragraph("3) Timeline of Events", h_style))
    story.append(Spacer(1, 10))

    timeline = case_data.get("timeline") or []
    if timeline:
        for i, e in enumerate(timeline, start=1):
            story.append(Paragraph(f"<b>Event {i}</b>", h3_style))
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"<b>Date:</b> {_safe(e.get('date'))} &nbsp;&nbsp; "
                    f"<b>Time:</b> {_safe(e.get('time'))} &nbsp;&nbsp; "
                    f"<b>Location:</b> {_safe(e.get('location'))}",
                    normal,
                )
            )
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(_safe(e.get("description")).replace("\n", "<br/>"), normal)
            )
            story.append(Spacer(1, 12))
    else:
        story.append(Paragraph("No timeline entries provided.", normal))

    story.append(PageBreak())

    # ---------------------------
    # Uploads section (with thumbnails)
    # ---------------------------
    story.append(Paragraph("4) Uploaded Evidence Files", h_style))
    story.append(Spacer(1, 10))

    uploads = case_data.get("uploads") or []
    if not uploads:
        story.append(Paragraph("No uploads were added.", normal))
        story.append(Spacer(1, 12))
    else:
        # 4.1 List files
        story.append(Paragraph("4.1 Evidence File List", h3_style))
        story.append(Spacer(1, 6))

        upload_table_data = [["Original Name", "Type", "Size (KB)", "Uploaded At"]]
        for u in uploads:
            path = u.get("path", "")
            ext = os.path.splitext(path.lower())[1] if path else ""
            upload_table_data.append(
                [
                    _safe(u.get("original_name")),
                    ext.replace(".", "").upper(),
                    _safe(u.get("size_kb")),
                    _safe(u.get("uploaded_at")),
                ]
            )

        upload_table = Table(
            upload_table_data,
            colWidths=[7 * cm, 2 * cm, 2 * cm, 4 * cm],
        )
        upload_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(upload_table)
        story.append(Spacer(1, 16))

        # 4.2 Inline thumbnails
        story.append(PageBreak())
        story.append(Paragraph("4.2 Inline Image Thumbnails", h3_style))
        story.append(Spacer(1, 10))

        image_uploads = [u for u in uploads if _is_image(u.get("path"))]

        if not image_uploads:
            story.append(Paragraph("No image evidence files were uploaded.", normal))
        else:
            for idx, u in enumerate(image_uploads, start=1):
                path = u.get("path", "")
                original_name = _safe(u.get("original_name"))
                uploaded_at = _safe(u.get("uploaded_at"))
                size_kb = _safe(u.get("size_kb"))

                story.append(
                    Paragraph(
                        f"<b>Image {idx}:</b> {original_name} "
                        f"(Uploaded: {uploaded_at}, Size: {size_kb} KB)",
                        normal,
                    )
                )
                story.append(Spacer(1, 6))

                try:
                    img = RLImage(path)

                    # Fit into page nicely
                    img.drawWidth = 14 * cm
                    img.drawHeight = 9 * cm

                    story.append(KeepTogether([img, Spacer(1, 12)]))

                except Exception:
                    story.append(
                        Paragraph(
                            f"⚠️ Could not render image thumbnail for: {original_name}",
                            normal,
                        )
                    )
                    story.append(Spacer(1, 12))

    story.append(Spacer(1, 16))

    # ---------------------------
    # Footer notes
    # ---------------------------
    story.append(Paragraph("5) Notes", h_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "• Keep original screenshots and device metadata intact.<br/>"
            "• Do not edit evidence files before submitting to police/HR/court.<br/>"
            "• If in immediate danger, contact emergency services.",
            normal,
        )
    )

    doc.build(story)