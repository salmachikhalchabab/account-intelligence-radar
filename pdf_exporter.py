import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register DejaVu Fonts (Unicode support) ──
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(_FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")))

# ── Brand Colors ──
TEAL       = HexColor("#1B4F72")
TEAL_LIGHT = HexColor("#1B9AAA")
GOLD       = HexColor("#B7950B")
DARK       = HexColor("#0A0D12")
GRAY_DARK  = HexColor("#1E2535")
GRAY_MID   = HexColor("#505868")
GRAY_LIGHT = HexColor("#E8EAF0")
WHITE      = white
BLACK      = black


def build_styles():
    styles = getSampleStyleSheet()

    custom = {
        "ReportTitle": ParagraphStyle(
            "ReportTitle",
            fontName="DejaVu-Bold",
            fontSize=26,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "ReportSub": ParagraphStyle(
            "ReportSub",
            fontName="DejaVu",
            fontSize=11,
            textColor=HexColor("#AED6F1"),
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            fontName="DejaVu-Bold",
            fontSize=13,
            textColor=TEAL,
            spaceBefore=16,
            spaceAfter=6,
            borderPadding=(0, 0, 4, 0),
        ),
        "FieldLabel": ParagraphStyle(
            "FieldLabel",
            fontName="DejaVu-Bold",
            fontSize=9,
            textColor=GRAY_MID,
            spaceAfter=2,
            spaceBefore=8,
            leftIndent=0,
        ),
        "FieldValue": ParagraphStyle(
            "FieldValue",
            fontName="DejaVu",
            fontSize=11,
            textColor=HexColor("#222222"),
            spaceAfter=2,
        ),
        "SourceURL": ParagraphStyle(
            "SourceURL",
            fontName="DejaVu",
            fontSize=8,
            textColor=TEAL_LIGHT,
            spaceAfter=6,
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            fontName="DejaVu",
            fontSize=10,
            textColor=HexColor("#333333"),
            leftIndent=12,
            spaceAfter=4,
            bulletIndent=0,
        ),
        "Footer": ParagraphStyle(
            "Footer",
            fontName="DejaVu",
            fontSize=8,
            textColor=GRAY_MID,
            alignment=TA_CENTER,
        ),
        "MetaTag": ParagraphStyle(
            "MetaTag",
            fontName="DejaVu",
            fontSize=9,
            textColor=GRAY_MID,
            alignment=TA_RIGHT,
        ),
    }

    return {**{k: styles[k] for k in styles.byName}, **custom}


def header_block(styles, company_name: str, generated_at: str) -> list:
    """Dark header banner with company name."""
    elements = []

    # Header table (dark background)
    header_data = [[
        Paragraph(f"<b>{company_name}</b>", styles["ReportTitle"]),
        Paragraph(f"Generated: {generated_at}", styles["MetaTag"])
    ]]
    header_table = Table(header_data, colWidths=[120 * mm, 55 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (-1, -1), 18),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 18),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(header_table)

    # Sub-header strip (gold bar)
    sub_data = [[
        Paragraph("Account Intelligence Report", styles["ReportSub"]),
        Paragraph("Averroa — Built by Experts", styles["ReportSub"])
    ]]
    sub_table = Table(sub_data, colWidths=[110 * mm, 65 * mm])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 18),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 18),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 12))

    return elements


def render_value(value, styles, indent=0) -> list:
    """Recursively render a JSON value into reportlab elements."""
    elements = []

    if value is None or value == "" or value == [] or value == {}:
        return elements

    # Simple string
    if isinstance(value, str):
        elements.append(Paragraph(value, styles["FieldValue"]))

    # Fact with source
    elif isinstance(value, dict) and "value" in value and "source" in value:
        elements.append(Paragraph(str(value["value"]), styles["FieldValue"]))
        elements.append(Paragraph(f"Source: {value['source']}", styles["SourceURL"]))

    # List
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                elements.append(Paragraph(f"• {item}", styles["BulletItem"]))
            elif isinstance(item, dict):
                # Build a mini table for dict items
                rows = []
                for k, v in item.items():
                    label = k.replace("_", " ").title()
                    if isinstance(v, str):
                        rows.append([
                            Paragraph(label, styles["FieldLabel"]),
                            Paragraph(v, styles["FieldValue"])
                        ])
                    elif isinstance(v, dict) and "value" in v:
                        rows.append([
                            Paragraph(label, styles["FieldLabel"]),
                            Paragraph(str(v["value"]), styles["FieldValue"])
                        ])
                        if "source" in v:
                            rows.append([
                                Paragraph("", styles["FieldLabel"]),
                                Paragraph(f"Source: {v['source']}", styles["SourceURL"])
                            ])

                if rows:
                    t = Table(rows, colWidths=[45 * mm, 120 * mm])
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F4F6F8")),
                        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#D5D8DC")),
                        ("TOPPADDING",    (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (0, -1), "DejaVu-Bold"),
                        ("FONTSIZE", (0, 0), (0, -1), 8),
                        ("TEXTCOLOR", (0, 0), (0, -1), GRAY_MID),
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 6))

    # Nested dict
    elif isinstance(value, dict):
        for k, v in value.items():
            label = k.replace("_", " ").title()
            elements.append(Paragraph(label, styles["FieldLabel"]))
            elements.extend(render_value(v, styles))

    return elements


def generate_pdf(company_name: str, data: dict, output_path: str) -> str:
    """Generate a professional PDF report from intelligence data."""

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=20 * mm,
        title=f"Intelligence Report — {company_name}",
        author="Account Intelligence Radar",
        subject="Business Intelligence Report",
        creator="Averroa",
    )

    styles = build_styles()
    story = []
    generated_at = datetime.now().strftime("%B %d, %Y  %H:%M")

    # ── Header ──
    story.extend(header_block(styles, company_name, generated_at))

    # ── Sections ──
    for key, value in data.items():
        if not value or value == [] or value == {}:
            continue

        # Section title
        section_title = key.replace("_", " ").replace("-", " ").title()
        section_elements = [
            HRFlowable(width="100%", thickness=1, color=TEAL, spaceAfter=4),
            Paragraph(section_title, styles["SectionHeading"]),
        ]
        section_elements.extend(render_value(value, styles))

        story.append(KeepTogether(section_elements))
        story.append(Spacer(1, 6))

    # ── Footer note ──
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_LIGHT))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by Account Intelligence Radar. "
        "All facts include source URLs for verification. "
        "Content is based on publicly available information only.",
        styles["Footer"]
    ))

    doc.build(story)
    return output_path
