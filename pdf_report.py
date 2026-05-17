"""
PDF Report Generator for Purlin Design.
Produces a polished, industry-style IS-code calculation report.
"""

from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.graphics.shapes import Circle, Drawing, Line, Path, Rect, String
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from utils.purlin_engine import PurlinInputs, ZSectionProps, DesignResult, CheckResult


# ── Industry-grade colour palette ────────────────────────────────
NAVY = colors.HexColor("#0F2742")
PRIMARY = colors.HexColor("#173B63")
ACCENT = colors.HexColor("#2E6FBF")
GOLD = colors.HexColor("#C9941A")
LIGHT_BG = colors.HexColor("#F3F6FA")
PANEL_BG = colors.HexColor("#EAF1F8")
OK_GREEN = colors.HexColor("#177245")
OK_BG = colors.HexColor("#E8F5EE")
FAIL_RED = colors.HexColor("#B8322A")
FAIL_BG = colors.HexColor("#FBEAEA")
TABLE_ALT = colors.HexColor("#F8FAFD")
GREY_LINE = colors.HexColor("#CCD6E2")
TEXT = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#627386")
WHITE = colors.white


def _pdf_text(value):
    """Return escaped ReportLab paragraph markup with professional powers."""
    replacements = {
        "²": "^2", "³": "^3", "⁴": "^4",
        "₁": "1", "₂": "2",
        "−": "-", "—": "-", "✓": "OK", "✗": "NOT OK",
        "kg*m": "kg·m", "N*mm": "N·mm",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = escape(text)
    text = text.replace("&lt;=", "&le;").replace("&gt;=", "&ge;")
    text = text.replace("*", "×")
    return re.sub(r"\^([0-9]+)", r"<super>\1</super>", text)


def _value_with_unit(value, unit):
    """Format a table value with its unit immediately beside it."""
    if unit in (None, "", "-", "—"):
        return str(value)
    return f"{value} {unit}"


def _limit_with_unit(limit, unit):
    """Format a limit with professional inequality and adjacent unit."""
    if unit in (None, "", "-", "—"):
        return f"≤ {limit}"
    return f"≤ {limit} {unit}"


def _pdf_cell(value):
    return value if isinstance(value, Paragraph) else _pdf_text(value)


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=21, leading=25, textColor=WHITE, spaceAfter=4,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"], fontSize=9.5, leading=13,
            textColor=colors.HexColor("#D9E7F7"),
        ),
        "title": ParagraphStyle(
            "title", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=18, textColor=NAVY,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=13, textColor=WHITE,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=8.3, leading=11,
            textColor=TEXT,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=7.2, leading=9.2,
            textColor=MUTED,
        ),
        "table_header": ParagraphStyle(
            "table_header", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.8, leading=9.2, textColor=WHITE, alignment=TA_LEFT,
        ),
        "table_cell": ParagraphStyle(
            "table_cell", parent=base["Normal"], fontSize=7.6, leading=9.5,
            textColor=TEXT,
        ),
        "table_cell_center": ParagraphStyle(
            "table_cell_center", parent=base["Normal"], fontSize=7.6, leading=9.5,
            textColor=TEXT, alignment=TA_CENTER,
        ),
        "ok": ParagraphStyle(
            "ok", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.8, leading=9.5, textColor=OK_GREEN, alignment=TA_CENTER,
        ),
        "fail": ParagraphStyle(
            "fail", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.8, leading=9.5, textColor=FAIL_RED, alignment=TA_CENTER,
        ),
        "right": ParagraphStyle(
            "right", parent=base["Normal"], fontSize=8, leading=10,
            textColor=TEXT, alignment=TA_RIGHT,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", parent=base["Normal"], fontSize=6.8, leading=8,
            textColor=MUTED, alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=12.5, leading=15, textColor=NAVY, alignment=TA_CENTER,
        ),
    }


def _para(value, style):
    return value if isinstance(value, Paragraph) else Paragraph(_pdf_text(value), style)


def _table(data, col_widths, styles, alt=True, header_color=PRIMARY, font_size=None):
    """Create a wrapped, repeat-header table with refined styling."""
    prepared = []
    for r, row in enumerate(data):
        row_style = styles["table_header"] if r == 0 else styles["table_cell"]
        prepared.append([_para(cell, row_style) for cell in row])

    t = Table(prepared, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_ALT] if alt else [WHITE]),
        ("BOX", (0, 0), (-1, -1), 0.55, GREY_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, GREY_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if font_size:
        commands.append(("FONTSIZE", (0, 0), (-1, -1), font_size))
    t.setStyle(TableStyle(commands))
    return t


def _section_head(text, styles, number=None):
    label = f"{number}. {text}" if number else text
    data = [[Paragraph(_pdf_text(label.upper()), styles["section"])]]
    t = Table(data, colWidths=[170 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [Spacer(1, 8), t, Spacer(1, 5)]


def _check_row(chk: CheckResult, styles):
    status_style = styles["ok"] if chk.status == "OK" else styles["fail"]
    return [
        Paragraph(_pdf_text(chk.label), styles["table_cell"]),
        Paragraph(_pdf_text(_value_with_unit(chk.value, chk.unit)), styles["table_cell"]),
        Paragraph(_pdf_text(_limit_with_unit(chk.limit, chk.unit)), styles["table_cell"]),
        Paragraph(_pdf_text(chk.status), status_style),
    ]


def _plain_check_row(chk: CheckResult):
    return [
        chk.label,
        _value_with_unit(chk.value, chk.unit),
        _limit_with_unit(chk.limit, chk.unit),
        chk.status,
    ]



def _line_arrow(drawing, x1, y1, x2, y2, color=ACCENT, width=1.0, head=4):
    """Draw a compact drafting arrow for the structural arrangement sketch."""
    drawing.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    if y2 < y1:
        drawing.add(Line(x2, y2, x2 - head / 2, y2 + head, strokeColor=color, strokeWidth=width))
        drawing.add(Line(x2, y2, x2 + head / 2, y2 + head, strokeColor=color, strokeWidth=width))
    elif y2 > y1:
        drawing.add(Line(x2, y2, x2 - head / 2, y2 - head, strokeColor=color, strokeWidth=width))
        drawing.add(Line(x2, y2, x2 + head / 2, y2 - head, strokeColor=color, strokeWidth=width))
    elif x2 > x1:
        drawing.add(Line(x2, y2, x2 - head, y2 - head / 2, strokeColor=color, strokeWidth=width))
        drawing.add(Line(x2, y2, x2 - head, y2 + head / 2, strokeColor=color, strokeWidth=width))
    else:
        drawing.add(Line(x2, y2, x2 + head, y2 - head / 2, strokeColor=color, strokeWidth=width))
        drawing.add(Line(x2, y2, x2 + head, y2 + head / 2, strokeColor=color, strokeWidth=width))


def _structural_drawing(inp: PurlinInputs, sec: ZSectionProps, res: DesignResult, W):
    """Create a professional purlin arrangement and Z-section drawing for the PDF."""
    H = 104 * mm
    d = Drawing(W, H)

    # Sheet border and title strip.
    d.add(Rect(0, 0, W, H, strokeColor=GREY_LINE, strokeWidth=0.8, fillColor=WHITE))
    d.add(Rect(0, H - 13 * mm, W, 13 * mm, strokeColor=NAVY, strokeWidth=0, fillColor=NAVY))
    d.add(String(8 * mm, H - 8.5 * mm, "STRUCTURAL ARRANGEMENT - PURLIN MEMBER", fontName="Helvetica-Bold", fontSize=8.5, fillColor=WHITE))
    d.add(String(W - 58 * mm, H - 8.5 * mm, f"Z-{int(sec.D)} x {sec.t:g} mm", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#D9E7F7")))

    # Elevation / roof line panel.
    panel_y = 10 * mm
    panel_h = 74 * mm
    left_w = W * 0.62
    d.add(Rect(6 * mm, panel_y, left_w, panel_h, strokeColor=GREY_LINE, strokeWidth=0.55, fillColor=colors.HexColor("#FBFCFE")))
    d.add(String(10 * mm, panel_y + panel_h - 7 * mm, "PURLIN ELEVATION / BAY ARRANGEMENT", fontName="Helvetica-Bold", fontSize=7.2, fillColor=NAVY))

    x0 = 18 * mm
    x1 = 6 * mm + left_w - 14 * mm
    y0 = panel_y + 24 * mm
    rise = min(max((inp.slope_y / max(inp.slope_x, 0.1)) * (x1 - x0), 4 * mm), 19 * mm)
    y1 = y0 + rise

    # Supporting frames.
    for x, y_top in ((x0, y0), (x1, y1)):
        d.add(Line(x, panel_y + 9 * mm, x, y_top, strokeColor=PRIMARY, strokeWidth=2.0))
        d.add(Line(x - 5 * mm, panel_y + 9 * mm, x + 5 * mm, panel_y + 9 * mm, strokeColor=PRIMARY, strokeWidth=1.2))
        d.add(Line(x - 3 * mm, panel_y + 5 * mm, x + 3 * mm, panel_y + 9 * mm, strokeColor=GREY_LINE, strokeWidth=0.7))
        d.add(Line(x + 1 * mm, panel_y + 5 * mm, x + 7 * mm, panel_y + 9 * mm, strokeColor=GREY_LINE, strokeWidth=0.7))

    # Main purlin line and lap zone.
    d.add(Line(x0, y0, x1, y1, strokeColor=ACCENT, strokeWidth=2.4))
    lap_len = min(max(res.lap_used / max(inp.bay_spacing, 0.1), 0.08), 0.32) * (x1 - x0)
    d.add(Line(x1 - lap_len, y1 - rise * lap_len / (x1 - x0), x1, y1, strokeColor=GOLD, strokeWidth=4.0))
    d.add(String(x1 - lap_len - 8 * mm, y1 + 5 * mm, f"lap {int(res.lap_used * 1000)} mm", fontName="Helvetica-Bold", fontSize=6.6, fillColor=GOLD))

    # Sag bars/intermediate restraint points.
    n_spaces = inp.num_sag_bars + 1
    for i in range(1, n_spaces):
        x = x0 + (x1 - x0) * i / n_spaces
        y = y0 + (y1 - y0) * i / n_spaces
        d.add(Circle(x, y, 2.0, strokeColor=OK_GREEN, strokeWidth=0.8, fillColor=OK_BG))
        d.add(Line(x, y - 8 * mm, x, y + 8 * mm, strokeColor=OK_GREEN, strokeWidth=0.65, strokeDashArray=[2, 2]))
    d.add(String(x0 + 4 * mm, panel_y + 14 * mm, f"{inp.num_sag_bars} sag bars / restraints", fontSize=6.4, fillColor=MUTED))

    # Distributed load arrows.
    for i in range(6):
        x = x0 + (x1 - x0) * (i + 0.5) / 6
        y = y0 + (y1 - y0) * (i + 0.5) / 6
        _line_arrow(d, x, y + 15 * mm, x, y + 4 * mm, ACCENT, 0.75, 3)
    d.add(String(x0 + 22 * mm, y1 + 22 * mm, f"governing UDL = {res.w_governing:.2f} kg/m", fontName="Helvetica-Bold", fontSize=6.7, fillColor=ACCENT))

    # Dimension line for span.
    dim_y = panel_y + 4 * mm
    d.add(Line(x0, dim_y, x1, dim_y, strokeColor=TEXT, strokeWidth=0.65))
    _line_arrow(d, x0 + 12 * mm, dim_y, x0, dim_y, TEXT, 0.65, 3)
    _line_arrow(d, x1 - 12 * mm, dim_y, x1, dim_y, TEXT, 0.65, 3)
    d.add(String((x0 + x1) / 2 - 15 * mm, dim_y + 3 * mm, f"Bay spacing L = {inp.bay_spacing:g} m", fontName="Helvetica-Bold", fontSize=6.6, fillColor=TEXT))

    # Z-section cross-section panel.
    right_x = 6 * mm + left_w + 6 * mm
    right_w = W - right_x - 6 * mm
    d.add(Rect(right_x, panel_y, right_w, panel_h, strokeColor=GREY_LINE, strokeWidth=0.55, fillColor=colors.HexColor("#FBFCFE")))
    d.add(String(right_x + 4 * mm, panel_y + panel_h - 7 * mm, "Z-SECTION ORIENTATION", fontName="Helvetica-Bold", fontSize=7.2, fillColor=NAVY))

    cx = right_x + right_w * 0.50
    top_y = panel_y + panel_h - 22 * mm
    depth = 42 * mm
    top_len = min(max(sec.b1 / max(sec.D, 1) * depth, 13 * mm), 25 * mm)
    bot_len = min(max(sec.b2 / max(sec.D, 1) * depth, 13 * mm), 25 * mm)
    lip1 = min(max(sec.L1 / max(sec.D, 1) * depth, 4 * mm), 9 * mm)
    lip2 = min(max(sec.L2 / max(sec.D, 1) * depth, 4 * mm), 9 * mm)

    z = Path(strokeColor=PRIMARY, strokeWidth=4.0, fillColor=None)
    z.moveTo(cx, top_y)
    z.lineTo(cx + top_len, top_y)
    z.lineTo(cx + top_len, top_y - lip1)
    z.moveTo(cx, top_y)
    z.lineTo(cx, top_y - depth)
    z.lineTo(cx - bot_len, top_y - depth)
    z.lineTo(cx - bot_len, top_y - depth + lip2)
    d.add(z)

    # Centroid axes and labels.
    centroid_x = cx + res.section.X / max(sec.D, 1) * depth
    centroid_y = top_y - res.section.Y / max(sec.D, 1) * depth
    d.add(Line(right_x + 8 * mm, centroid_y, right_x + right_w - 8 * mm, centroid_y, strokeColor=GREY_LINE, strokeWidth=0.6, strokeDashArray=[2, 2]))
    d.add(Line(centroid_x, panel_y + 15 * mm, centroid_x, panel_y + panel_h - 17 * mm, strokeColor=GREY_LINE, strokeWidth=0.6, strokeDashArray=[2, 2]))
    d.add(Circle(centroid_x, centroid_y, 2.4, strokeColor=GOLD, strokeWidth=0.7, fillColor=GOLD))
    d.add(String(right_x + 5 * mm, panel_y + 18 * mm, f"x-bar={res.section.X:.2f} mm", fontSize=6.2, fillColor=MUTED))
    d.add(String(right_x + 5 * mm, panel_y + 11 * mm, f"y-bar={res.section.Y:.2f} mm", fontSize=6.2, fillColor=MUTED))
    d.add(String(right_x + right_w - 34 * mm, panel_y + 18 * mm, f"Zyy R={res.section.Zyy_right:.2f} mm^3", fontSize=6.0, fillColor=MUTED))
    d.add(String(right_x + right_w - 34 * mm, panel_y + 11 * mm, f"Zyy L={res.section.Zyy_left:.2f} mm^3", fontSize=6.0, fillColor=MUTED))

    # Depth dimension.
    dim_x = right_x + right_w - 8 * mm
    d.add(Line(dim_x, top_y, dim_x, top_y - depth, strokeColor=TEXT, strokeWidth=0.6))
    _line_arrow(d, dim_x, top_y - 9 * mm, dim_x, top_y, TEXT, 0.6, 3)
    _line_arrow(d, dim_x, top_y - depth + 9 * mm, dim_x, top_y - depth, TEXT, 0.6, 3)
    d.add(String(dim_x - 12 * mm, top_y - depth / 2, f"D={sec.D:g} mm", fontSize=6.3, fillColor=TEXT))

    return d

def _design_step_rows(inp: PurlinInputs, sec: ZSectionProps, res: DesignResult):
    """Compact clause-referenced calculation steps for the PDF report."""
    span_coeff = 0.0772 if inp.bay_type == "End Bay" else 0.0364
    support_coeff = 0.1071 if inp.bay_type == "End Bay" else 0.0714
    return [
        ["1", "Input data", "Project inputs / IS 875", f"L={inp.bay_spacing:g} m; Ps={inp.purlin_spacing:g} m; Fy={inp.fy:g} N/mm^2"],
        ["2", "Slope factors", "Roof geometry", f"Kx=X/sqrt(X^2+Y^2)={res.Kx:.6f}; Ky={res.Ky:.6f}"],
        ["3", "Design UDL", "IS 875 loads", f"w1=(DL+LL+CL)*Kx*Ps={res.w_combo1:.3f} kg/m; w2=(WL*Cp1-DL*Kx)*Ps={res.w_combo2:.3f} kg/m"],
        ["4", "Bending moments", "Analysis coefficients", f"Cs={span_coeff:g}; Cp={support_coeff:g}; Mspan={res.M_span_gvn:.2f} kg*m; Msupp={res.M_supp_gvn:.2f} kg*m"],
        ["5", "Section properties", "IS 801 section basis", f"Ixx={res.section.Ixx/1e4:.2f} cm^4; Zxx={res.section.Z1xx_top/1e3:.2f} cm^3"],
        ["6", "Depth limits", "IS 801 cl. 5.2.4, 5.2.1.2", f"D<150t: {res.depth_check_150t.status}; d>=dmin: {res.depth_check_dmin.status}"],
        ["7", "Compression flange", "IS 801 cl. 5.2.1.1", f"b1/t={res.b1_t_actual:.2f} <= {res.b1_t_limit:.2f}: {res.flange_check.status}"],
        ["8", "Lateral buckling", "IS 801 cl. 6.3(b)", f"lambda={res.lambda_val:.2f}; Fb={res.Fb:.2f} N/mm^2"],
        ["9", "Stress checks", "IS 801 cl. 6.1, 6.1.2", "; ".join(f"{c.label}: {c.status}" for c in res.stress_checks)],
        ["10", "Deflection", "Le/150 serviceability", f"delta1={res.delta_c1:.2f} mm; delta2={res.delta_c2:.2f} mm; limit={res.delta_allow:.2f} mm"],
        ["11", "Lap / overlap", "Lap moment capacity", f"Mx={res.M_at_lap:.2f} kg*m <= Mcap={res.M_capacity:.2f} kg*m: {res.lap_check.status}"],
        ["12", "Final adoption", "Design summary", "SECTION ADOPTED" if res.passed else "SECTION NOT ADEQUATE"],
    ]


def _kpi_card(label, value, styles, accent=ACCENT, bg=WHITE):
    data = [[Paragraph(_pdf_text(label.upper()), styles["kpi_label"])],
            [Paragraph(_pdf_text(value), styles["kpi_value"] )]]
    t = Table(data, colWidths=[38 * mm], rowHeights=[9 * mm, 13 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, GREY_LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2.0, accent),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _header_footer(canvas, doc):
    """Draw industry-style repeated header and footer."""
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(doc.leftMargin, height - 7.7 * mm, "PURLIN DESIGN CALCULATION REPORT")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(width - doc.rightMargin, height - 7.7 * mm, "IS 801-1975 | IS 875 | IS 2062")

    canvas.setStrokeColor(GREY_LINE)
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, 12 * mm, width - doc.rightMargin, 12 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(doc.leftMargin, 7.5 * mm, "Generated by Purlin Design App")
    canvas.drawRightString(width - doc.rightMargin, 7.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _hero_block(project_name, inp, sec, res, styles, W):
    verdict = "SECTION ADOPTED" if res.passed else "SECTION NOT ADEQUATE"
    verdict_color = OK_GREEN if res.passed else FAIL_RED
    header = Table([[Paragraph(
        f"<b>DESIGN OF COLD-FORMED Z-PURLIN</b><br/><font size='9'>{_pdf_text(project_name)}</font>",
        styles["cover_title"],
    )]], colWidths=[W])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))

    meta = Table([[Paragraph(_pdf_text(
        f"Code basis: IS 801-1975 / IS 875 (Part 3)-1987 / IS 2062  |  "
        f"Bay type: {inp.bay_type}  |  Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}"
    ), styles["small"])]], colWidths=[W])
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY_LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    cards = Table([[ 
        _kpi_card("Design Status", verdict, styles, verdict_color, OK_BG if res.passed else FAIL_BG),
        _kpi_card("Adopted Section", f"Z-{int(sec.D)} x {sec.t} mm", styles),
        _kpi_card("Sag Bars", f"{inp.num_sag_bars} Nos", styles),
        _kpi_card("Lap / Overlap", f"{int(res.lap_used * 1000)} mm", styles),
    ]], colWidths=[W / 4] * 4)
    cards.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return [header, meta, Spacer(1, 8), cards, Spacer(1, 8)]


def generate_pdf_report(
    project_name: str,
    inp: PurlinInputs,
    sec: ZSectionProps,
    res: DesignResult,
) -> bytes:
    buf = BytesIO()
    PAGE_W, _ = A4
    M = 18 * mm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=M, rightMargin=M,
        topMargin=18 * mm, bottomMargin=16 * mm,
        title="Purlin Design Report",
        author="Purlin Design App - IS 801-1975",
    )

    styles = _styles()
    W = PAGE_W - 2 * M
    story = []

    # ── Cover / Executive summary ─────────────────────────────────
    story += _hero_block(project_name, inp, sec, res, styles, W)

    executive_data = [
        ["Item", "Value", "Design note"],
        ["Governing UDL", f"{res.w_governing:.3f} kg/m", "Maximum of gravity and wind-uplift combinations"],
        ["Governing moments", f"Mspan={res.M_span_gvn:.2f} kg*m; Msupport={res.M_supp_gvn:.2f} kg*m", "Based on selected bay-type coefficients"],
        ["Permissible bending stress", f"Fb={res.Fb:.2f} N/mm^2", "IS 801 cl. 6.3(b), limited by 0.6Fy"],
        ["Serviceability", f"delta max={max(res.delta_c1, res.delta_c2):.2f} mm <= {res.delta_allow:.2f} mm", "Le/150 deflection limit"],
        ["Overall verdict", "PASS" if res.passed else "REVISE", "All mandatory checks must be satisfactory"],
    ]
    story += _section_head("Executive Design Summary", styles, 1)
    story.append(_table(executive_data, [W * 0.28, W * 0.30, W * 0.42], styles, header_color=NAVY))

    # ── Input Data ────────────────────────────────────────────────
    story += _section_head("Input Data", styles, 2)
    inp_data = [
        ["Parameter", "Symbol", "Value"],
        ["Bay spacing (effective length)", "L = Le", _value_with_unit(inp.bay_spacing, "m")],
        ["Purlin spacing", "Ps", _value_with_unit(inp.purlin_spacing, "m")],
        ["Roof slope", "X:Y", f"{inp.slope_x}:{inp.slope_y}"],
        ["Dead load intensity", "DL", _value_with_unit(inp.dead_load, "kg/m^2")],
        ["Live load intensity", "LL", _value_with_unit(inp.live_load, "kg/m^2")],
        ["Collateral load", "CL", _value_with_unit(inp.collateral_load, "kg/m^2")],
        ["Wind load intensity", "WL", _value_with_unit(inp.wind_load, "kg/m^2")],
        ["Wind pressure coefficient", "Cp1", inp.wind_pressure_coeff],
        ["Yield strength of steel", "Fy", _value_with_unit(inp.fy, "N/mm^2")],
        ["Modulus of elasticity", "E", _value_with_unit(inp.E, "N/mm^2")],
        ["Number of sag bars", "n", _value_with_unit(inp.num_sag_bars, "nos")],
    ]
    story.append(_table(inp_data, [W * 0.44, W * 0.20, W * 0.36], styles))

    # ── Structural arrangement drawing ────────────────────────────
    story += _section_head("Structural Arrangement Drawing", styles, 3)
    story.append(_structural_drawing(inp, sec, res, W))
    story.append(Spacer(1, 6))

    # ── Loads and moments ─────────────────────────────────────────
    story += _section_head("Load Calculations", styles, 4)
    load_data = [
        ["Item", "Formula", "Value"],
        ["Kx (along-slope factor)", "X / sqrt(X^2+Y^2)", round(res.Kx, 6)],
        ["Ky (cross-slope factor)", "Y / sqrt(X^2+Y^2)", round(res.Ky, 6)],
        ["Combo I - DL+LL+CL (down)", "(DL+LL+CL)*Kx*Ps", _value_with_unit(round(res.w_combo1, 3), "kg/m")],
        ["Combo II - WL-DL (up)", "(WL*Cp1-DL*Kx)*Ps", _value_with_unit(round(res.w_combo2, 3), "kg/m")],
    ]
    story.append(_table(load_data, [W * 0.38, W * 0.38, W * 0.24], styles))

    story += _section_head("Design Bending Moments", styles, 5)
    mom_data = [
        ["Load case", "Location", "Coefficient", "Moment"],
        ["DL+LL+CL", "Midspan", f"0.{'0772' if inp.bay_type == 'End Bay' else '0364'}", _value_with_unit(round(res.M_span_c1, 2), "kg·m")],
        ["DL+LL+CL", "Near support", f"0.{'1071' if inp.bay_type == 'End Bay' else '0714'}", _value_with_unit(round(res.M_supp_c1, 2), "kg·m")],
        ["DL+WL", "Midspan", f"0.{'0772' if inp.bay_type == 'End Bay' else '0364'}", _value_with_unit(round(res.M_span_c2, 2), "kg·m")],
        ["DL+WL", "Near support", f"0.{'1071' if inp.bay_type == 'End Bay' else '0714'}", _value_with_unit(round(res.M_supp_c2, 2), "kg·m")],
    ]
    story.append(_table(mom_data, [W * 0.25, W * 0.25, W * 0.22, W * 0.28], styles))

    # ── Clause-referenced summary ─────────────────────────────────
    story += _section_head("Clause-Referenced Design Step Summary", styles, 6)
    step_data = [["Step", "Design check", "IS reference", "Expression / value"]]
    step_data.extend(_design_step_rows(inp, sec, res))
    story.append(_table(step_data, [W * 0.08, W * 0.22, W * 0.24, W * 0.46], styles, header_color=NAVY))

    # ── Section properties and checks ─────────────────────────────
    story += _section_head("Z-Section Properties", styles, 7)
    dims_data = [
        ["t", "d", "b1", "b2", "L1", "L2", "D"],
        [
            _value_with_unit(sec.t, "mm"),
            _value_with_unit(sec.d, "mm"),
            _value_with_unit(sec.b1, "mm"),
            _value_with_unit(sec.b2, "mm"),
            _value_with_unit(sec.L1, "mm"),
            _value_with_unit(sec.L2, "mm"),
            _value_with_unit(sec.D, "mm"),
        ],
    ]
    story.append(_table(dims_data, [W / 7] * 7, styles, header_color=PRIMARY))
    story.append(Spacer(1, 5))

    props_data = [
        ["Property", "Symbol", "Value"],
        ["Centroid x-bar from web centre-line", "x-bar", _value_with_unit(round(res.section.X, 3), "mm")],
        ["Centroid y-bar from top", "y-bar", _value_with_unit(round(res.section.Y, 3), "mm")],
        ["Moment of inertia (XX)", "Ixx", _value_with_unit(f"{res.section.Ixx:.2f}", "mm^4")],
        ["Moment of inertia (YY)", "Iyy", _value_with_unit(f"{res.section.Iyy:.2f}", "mm^4")],
        ["Section modulus top", "Z1xx-top", _value_with_unit(f"{res.section.Z1xx_top:.2f}", "mm^3")],
        ["Section modulus bottom", "Z1xx-bot", _value_with_unit(f"{res.section.Z1xx_bot:.2f}", "mm^3")],
        ["Section modulus right", "Zyy-right", _value_with_unit(f"{res.section.Zyy_right:.2f}", "mm^3")],
        ["Section modulus left", "Zyy-left", _value_with_unit(f"{res.section.Zyy_left:.2f}", "mm^3")],
        ["Cross-sectional area", "A", _value_with_unit(round(res.section.area, 3), "cm^2")],
        ["Self-weight", "w/m", _value_with_unit(round(res.section.weight_per_m, 3), "kg/m")],
    ]
    story.append(_table(props_data, [W * 0.44, W * 0.20, W * 0.36], styles))

    story += _section_head("Section Classification Checks", styles, 8)
    chk_data = [["Check", "Value", "Limit", "Status"]]
    chk_data.extend([
        _plain_check_row(res.depth_check_150t),
        _plain_check_row(res.depth_check_dmin),
        _plain_check_row(res.flange_check),
    ])
    story.append(_table(chk_data, [W * 0.46, W * 0.18, W * 0.22, W * 0.14], styles))

    # ── Strength and serviceability ───────────────────────────────
    story += _section_head("Lateral Buckling - Permissible Bending Stress", styles, 9)
    lb_data = [
        ["Parameter", "Value"],
        ["Unbraced length (L_u)", _value_with_unit(round(res.L_unbraced, 3), "m")],
        ["Iyc = Iyy/2", _value_with_unit(round(res.Iyc, 3), "cm^4")],
        ["Sxc = Zxx-top", _value_with_unit(round(res.Sxc, 3), "cm^3")],
        ["lambda = L^2*Sxc / (d*Iyc)", round(res.lambda_val, 2)],
        ["Fb (computed)", _value_with_unit(round(res.Fb, 2), "N/mm^2")],
        ["F_basic = 0.6*Fy", _value_with_unit(round(res.F_basic, 2), "N/mm^2")],
        ["Fb (adopted, min of above)", _value_with_unit(round(res.Fb, 2), "N/mm^2")],
    ]
    story.append(_table(lb_data, [W * 0.62, W * 0.38], styles))

    story += _section_head("Bending Stress Checks", styles, 10)
    sc_data = [["Load case / location", "fb actual", "Limit", "Status"]]
    for chk in res.stress_checks:
        sc_data.append(_plain_check_row(chk))
    story.append(_table(sc_data, [W * 0.46, W * 0.20, W * 0.20, W * 0.14], styles))

    story += _section_head("Deflection Check", styles, 11)
    defl_data = [["Check", "Deflection", "Limit", "Status"]]
    defl_data.extend([_plain_check_row(res.defl_check_c1), _plain_check_row(res.defl_check_c2)])
    story.append(_table(defl_data, [W * 0.46, W * 0.20, W * 0.20, W * 0.14], styles))

    story += _section_head("Purlin Overlap Check", styles, 12)
    lap_data = [
        ["Parameter", "Value"],
        ["Governing UDL", _value_with_unit(round(res.w_governing, 3), "kg/m")],
        ["Moment capacity = Zxx*Fb", _value_with_unit(round(res.M_capacity, 2), "kg·m")],
        ["Bay spacing L", _value_with_unit(inp.bay_spacing, "m")],
        ["Overlap length X provided", _value_with_unit(round(res.lap_used * 1000, 0), "mm")],
        ["Moment at X (M_at_X)", _value_with_unit(round(res.M_at_lap, 2), "kg·m")],
        ["Status", res.lap_check.status],
    ]
    story.append(_table(lap_data, [W * 0.62, W * 0.38], styles))

    # ── Final recommendation ─────────────────────────────────────
    story += _section_head("Final Recommendation", styles, 13)
    verdict_color = OK_GREEN if res.passed else FAIL_RED
    verdict_bg = OK_BG if res.passed else FAIL_BG
    verdict_text = "SECTION ADOPTED - ALL CHECKS SATISFIED" if res.passed else "SECTION NOT ADEQUATE - REVISE"
    recommendation = (
        f"Provide purlin Z-{int(sec.D)} x {sec.t} mm with {inp.num_sag_bars} sag bars "
        f"and {int(res.lap_used * 1000)} mm overlap."
    )
    summary = Table([
        [Paragraph(_pdf_text(verdict_text), styles["kpi_value"])],
        [Paragraph(_pdf_text(recommendation), styles["body"])],
    ], colWidths=[W])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), verdict_bg),
        ("BOX", (0, 0), (-1, -1), 1.2, verdict_color),
        ("LINEABOVE", (0, 0), (-1, 0), 3.0, verdict_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(KeepTogether([summary, Spacer(1, 8), Paragraph(
        _pdf_text("References: IS 801-1975, IS 875 (Part 3)-1987, IS 2062. Calculations are based on the submitted geometry, loads, material properties, and selected section dimensions."),
        styles["small"],
    )]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
