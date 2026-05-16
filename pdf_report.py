"""
PDF Report Generator for Purlin Design
Uses ReportLab to produce a professional IS-code design report.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from utils.purlin_engine import PurlinInputs, ZSectionProps, DesignResult, CheckResult


# ── Colour palette ─────────────────────────
PRIMARY   = colors.HexColor("#1B3A6B")
ACCENT    = colors.HexColor("#2E6FBF")
LIGHT_BG  = colors.HexColor("#EEF3FA")
OK_GREEN  = colors.HexColor("#1F7A4A")
FAIL_RED  = colors.HexColor("#C0392B")
TABLE_ALT = colors.HexColor("#F5F7FB")
GREY_LINE = colors.HexColor("#C8CDD6")


def _pdf_text(value):
    """Return ReportLab/Helvetica-safe text without Unicode superscripts."""
    replacements = {
        "²": "^2", "³": "^3", "⁴": "^4", "₁": "1", "₂": "2",
        "√": "sqrt", "≤": "<=", "≥": ">=", "−": "-", "×": "x", "·": "*",
        "λ": "lambda", "π": "pi", "ȳ": "y-bar", "x-bar": "x-bar", "X̄": "X-bar",
        "-": "-", "↓": "down", "↑": "up", "✓": "OK", "✗": "NOT OK",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _pdf_cell(value):
    return value if isinstance(value, Paragraph) else _pdf_text(value)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Heading1"],
            fontSize=16, textColor=PRIMARY, spaceAfter=4, leading=20),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"],
            fontSize=10, textColor=ACCENT, spaceAfter=10),
        "section": ParagraphStyle("section", parent=base["Heading2"],
            fontSize=11, textColor=PRIMARY, spaceBefore=14, spaceAfter=4,
            borderPad=3, leading=14, fontName="Helvetica-Bold"),
        "body": ParagraphStyle("body", parent=base["Normal"],
            fontSize=9, textColor=colors.HexColor("#2C2C2A"), leading=13),
        "mono": ParagraphStyle("mono", parent=base["Normal"],
            fontSize=8.5, fontName="Courier", textColor=colors.HexColor("#333"),
            leading=12),
        "ok": ParagraphStyle("ok", parent=base["Normal"],
            fontSize=9, textColor=OK_GREEN, fontName="Helvetica-Bold"),
        "fail": ParagraphStyle("fail", parent=base["Normal"],
            fontSize=9, textColor=FAIL_RED, fontName="Helvetica-Bold"),
        "center": ParagraphStyle("center", parent=base["Normal"],
            fontSize=9, alignment=TA_CENTER),
        "right": ParagraphStyle("right", parent=base["Normal"],
            fontSize=9, alignment=TA_RIGHT),
    }


def _section_head(text, styles):
    return [
        Spacer(1, 6),
        Paragraph(_pdf_text(text), styles["section"]),
        HRFlowable(width="100%", thickness=0.6, color=ACCENT, spaceAfter=4),
    ]


def _check_row(chk: CheckResult, styles):
    status_style = styles["ok"] if chk.status == "OK" else styles["fail"]
    return [
        Paragraph(_pdf_text(chk.label), styles["body"]),
        Paragraph(_pdf_text(f"{chk.value} {chk.unit}"), styles["body"]),
        Paragraph(_pdf_text(f"<= {chk.limit} {chk.unit}"), styles["body"]),
        Paragraph(_pdf_text(chk.status), status_style),
    ]


def _table(data, col_widths, alt=True):
    data = [[_pdf_cell(cell) for cell in row] for row in data]
    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ("FONTNAME",  (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 8.5),
        ("BACKGROUND",(0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0),  colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ALT] if alt else [colors.white]),
        ("GRID",      (0, 0), (-1, -1), 0.35, GREY_LINE),
        ("TOPPADDING",(0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",(0, 0), (-1, -1),6),
        ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t




def _design_step_rows(inp: PurlinInputs, sec: ZSectionProps, res: DesignResult):
    """Compact clause-referenced calculation steps for the PDF report."""
    span_coeff = 0.0772 if inp.bay_type == "End Bay" else 0.0364
    support_coeff = 0.1071 if inp.bay_type == "End Bay" else 0.0714
    return [
        ["1", "Inputs", "Project inputs / IS 875", f"L={inp.bay_spacing:g} m; Ps={inp.purlin_spacing:g} m; Fy={inp.fy:g} N/mm^2"],
        ["2", "Slope factors", "Roof geometry", f"Kx=X/sqrt(X^2+Y^2)={res.Kx:.6f}; Ky={res.Ky:.6f}"],
        ["3", "Design UDL", "IS 875 loads", f"w1=(DL+LL+CL)*Kx*Ps={res.w_combo1:.3f} kg/m; w2=(WL*Cp1-DL*Kx)*Ps={res.w_combo2:.3f} kg/m"],
        ["4", "Bending moments", "Analysis coefficients", f"Cs={span_coeff:g}; Cp={support_coeff:g}; Mspan={res.M_span_gvn:.2f} kg*m; Msupp={res.M_supp_gvn:.2f} kg*m"],
        ["5", "Section properties", "IS 801 section basis", f"Ixx={res.section.Ixx/1e4:.2f} cm^4; Zxx={res.section.Z1xx_top/1e3:.2f} cm^3"],
        ["6", "Depth limits", "IS 801 cl. 5.2.4, 5.2.1.2", f"D<150t: {res.depth_check_150t.status}; d>=dmin: {res.depth_check_dmin.status}"],
        ["7", "Compression flange", "IS 801 cl. 5.2.1.1", f"b1/t={res.b1_t_actual:.2f} <= {res.b1_t_limit:.2f}: {res.flange_check.status}"],
        ["8", "Lateral buckling", "IS 801 cl. 6.3(b)", f"lambda={res.lambda_val:.2f}; Fb={res.Fb:.2f} N/mm^2"],
        ["9", "Stress checks", "IS 801 cl. 6.1, 6.1.2", "; ".join(f"{c.label}: {c.status}" for c in res.stress_checks)],
        ["10", "Deflection", "Le/150 serviceability", f"delta1={res.delta_c1:.2f} mm; delta2={res.delta_c2:.2f} mm; limit={res.delta_allow:.2f} mm"],
        ["11", "Lap/overlap", "Lap moment capacity", f"Mx={res.M_at_lap:.2f} kg*m <= Mcap={res.M_capacity:.2f} kg*m: {res.lap_check.status}"],
        ["12", "Final adoption", "Design summary", "SECTION ADOPTED" if res.passed else "SECTION NOT ADEQUATE"],
    ]

def generate_pdf_report(
    project_name: str,
    inp: PurlinInputs,
    sec: ZSectionProps,
    res: DesignResult,
) -> bytes:
    buf = BytesIO()
    PAGE_W, PAGE_H = A4
    M = 20 * mm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=M, rightMargin=M,
        topMargin=M, bottomMargin=M,
        title="Purlin Design Report",
        author="Purlin Design App - IS 801-1975",
    )

    styles = _styles()
    W = PAGE_W - 2*M   # usable width

    story = []

    # ── HEADER ─────────────────────────────────
    header_data = [[
        Paragraph(f"<b>DESIGN OF PURLINS</b><br/>"
                  f"<font size='8'>{project_name}</font>", styles["title"]),
        Paragraph(
            f"<font size='8' color='grey'>Code: IS 801-1975 / IS 875-1987<br/>"
            f"Date: {datetime.now().strftime('%d %b %Y')}<br/>"
            f"Bay type: {inp.bay_type}</font>",
            styles["right"]
        ),
    ]]
    ht = Table(header_data, colWidths=[W*0.65, W*0.35])
    ht.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(ht)
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY))
    story.append(Spacer(1, 8))

    # ── STEP 1: Input Data ─────────────────────
    story += _section_head("1. Input Data", styles)
    inp_data = [
        ["Parameter", "Symbol", "Value", "Unit"],
        ["Bay spacing (effective length)", "L = Le", inp.bay_spacing, "m"],
        ["Purlin spacing", "Ps", inp.purlin_spacing, "m"],
        ["Roof slope", "X:Y", f"{inp.slope_x}:{inp.slope_y}", "-"],
        ["Dead load intensity", "DL", inp.dead_load, "kg/m²"],
        ["Live load intensity", "LL", inp.live_load, "kg/m²"],
        ["Collateral load", "CL", inp.collateral_load, "kg/m²"],
        ["Wind load intensity", "WL", inp.wind_load, "kg/m²"],
        ["Wind pressure coefficient", "Cp1", inp.wind_pressure_coeff, "-"],
        ["Yield strength of steel", "Fy", inp.fy, "N/mm^2"],
        ["Modulus of elasticity", "E", inp.E, "N/mm^2"],
        ["Number of sag bars", "n", inp.num_sag_bars, "nos"],
    ]
    story.append(_table(inp_data, [W*0.40, W*0.18, W*0.22, W*0.20]))

    # ── STEP 2: Slope & Loads ─────────────────
    story += _section_head("2. Load Calculations", styles)
    load_data = [
        ["Item", "Formula", "Value", "Unit"],
        ["Kx (along-slope factor)", "X / sqrt(X^2+Y^2)", round(res.Kx, 6), "-"],
        ["Ky (cross-slope factor)", "Y / sqrt(X^2+Y^2)", round(res.Ky, 6), "-"],
        ["Combo I - DL+LL+CL (down)", "(DL+LL+CL)*Kx*Ps", round(res.w_combo1, 3), "kg/m"],
        ["Combo II - WL-DL (↑)", "(WL*Cp1-DL*Kx)*Ps", round(res.w_combo2, 3), "kg/m"],
    ]
    story.append(_table(load_data, [W*0.38, W*0.30, W*0.18, W*0.14]))

    # ── STEP 4: Moments ────────────────────────
    story += _section_head("3. Design Bending Moments", styles)
    mom_data = [
        ["Load case", "Location", "Coefficient", "Moment (kg*m)"],
        ["DL+LL+CL", "Midspan",  f"0.{'0772' if inp.bay_type=='End Bay' else '0364'}",
         round(res.M_span_c1, 2)],
        ["DL+LL+CL", "Near support", f"0.{'1071' if inp.bay_type=='End Bay' else '0714'}",
         round(res.M_supp_c1, 2)],
        ["DL+WL",    "Midspan",  f"0.{'0772' if inp.bay_type=='End Bay' else '0364'}",
         round(res.M_span_c2, 2)],
        ["DL+WL",    "Near support", f"0.{'1071' if inp.bay_type=='End Bay' else '0714'}",
         round(res.M_supp_c2, 2)],
    ]
    story.append(_table(mom_data, [W*0.25, W*0.25, W*0.22, W*0.28]))

    # ── PROFESSIONAL STEP SUMMARY ──────────────
    story += _section_head("4. Clause-Referenced Design Step Summary", styles)
    step_data = [["Step", "Design check", "IS reference", "Expression / value"]]
    step_data.extend(_design_step_rows(inp, sec, res))
    story.append(_table(step_data, [W*0.08, W*0.22, W*0.24, W*0.46]))

    # ── STEP 5: Section Properties ─────────────
    story += _section_head("5. Z-Section Properties", styles)
    dims_data = [
        ["t (mm)", "d (mm)", "b1 (mm)", "b2 (mm)", "L1 (mm)", "L2 (mm)", "D (mm)"],
        [sec.t, sec.d, sec.b1, sec.b2, sec.L1, sec.L2, sec.D],
    ]
    story.append(_table(dims_data, [W/7]*7))
    story.append(Spacer(1, 6))

    props_data = [
        ["Property", "Symbol", "Value", "Unit"],
        ["Centroid x-bar from web centre-line", "x-bar", round(res.section.X, 3), "mm"],
        ["Centroid ȳ from top",             "ȳ", round(res.section.Y, 3), "mm"],
        ["Moment of inertia (XX)", "Ixx", f"{res.section.Ixx:.2f}", "mm^4"],
        ["Moment of inertia (YY)", "Iyy", f"{res.section.Iyy:.2f}", "mm^4"],
        ["Section modulus top",    "Z1xx-top", f"{res.section.Z1xx_top:.2f}", "mm^3"],
        ["Section modulus bottom", "Z1xx-bot", f"{res.section.Z1xx_bot:.2f}", "mm^3"],
        ["Section modulus right",  "Zyy-right", f"{res.section.Zyy_right:.2f}", "mm^3"],
        ["Cross-sectional area",   "A", round(res.section.area, 3), "cm^2"],
        ["Self-weight",            "w/m", round(res.section.weight_per_m, 3), "kg/m"],
    ]
    story.append(_table(props_data, [W*0.38, W*0.18, W*0.26, W*0.18]))

    # ── STEP 6: Depth Checks ───────────────────
    story += _section_head("6. Section Classification Checks (IS 801 cl. 5.2.4 & 5.2.1.1)", styles)
    chk_data = [["Check", "Value", "Limit", "Status"]]
    chk_data.append(_check_row(res.depth_check_150t, styles))
    chk_data.append(_check_row(res.depth_check_dmin, styles))
    chk_data.append(_check_row(res.flange_check, styles))
    t_chk = Table(chk_data, colWidths=[W*0.46, W*0.18, W*0.22, W*0.14])
    t_chk.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 8.5),
        ("BACKGROUND",(0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0),  colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, TABLE_ALT]),
        ("GRID", (0,0), (-1,-1), 0.35, GREY_LINE),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(t_chk)

    # ── STEP 7–9: Lateral Buckling ─────────────
    story += _section_head("7. Lateral Buckling - Permissible Bending Stress (IS 801 cl. 6.3b)", styles)
    lb_data = [
        ["Parameter", "Value", "Unit"],
        ["Unbraced length (L_u)", round(res.L_unbraced, 3), "m"],
        ["Iyc = Iyy/2", round(res.Iyc, 3), "cm^4"],
        ["Sxc = Zxx-top", round(res.Sxc, 3), "cm^3"],
        ["lambda = L^2*Sxc / (d·Iyc)", round(res.lambda_val, 2), "-"],
        ["Fb (computed)", round(res.Fb, 2), "N/mm^2"],
        ["F_basic = 0.6*Fy", round(res.F_basic, 2), "N/mm^2"],
        ["Fb (adopted, min of above)", round(res.Fb, 2), "N/mm^2"],
    ]
    story.append(_table(lb_data, [W*0.52, W*0.28, W*0.20]))

    # ── STEP 10: Stress Checks ─────────────────
    story += _section_head("8. Bending Stress Checks", styles)
    sc_data = [["Load case / location", "fb_actual (N/mm^2)", "Limit (N/mm^2)", "Status"]]
    for chk in res.stress_checks:
        sc_data.append(_check_row(chk, styles))
    t_sc = Table(sc_data, colWidths=[W*0.46, W*0.20, W*0.20, W*0.14])
    t_sc.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1),8.5),
        ("BACKGROUND",(0,0),(-1,0),PRIMARY),
        ("TEXTCOLOR", (0,0),(-1,0),colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,TABLE_ALT]),
        ("GRID",(0,0),(-1,-1),0.35,GREY_LINE),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(t_sc)

    # ── STEP 11: Deflection ────────────────────
    story += _section_head("9. Deflection Check", styles)
    defl_data = [["Check", "Deflection (mm)", "Limit (mm)", "Status"]]
    defl_data.append(_check_row(res.defl_check_c1, styles))
    defl_data.append(_check_row(res.defl_check_c2, styles))
    t_defl = Table(defl_data, colWidths=[W*0.46, W*0.20, W*0.20, W*0.14])
    t_defl.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1),8.5),
        ("BACKGROUND",(0,0),(-1,0),PRIMARY),
        ("TEXTCOLOR", (0,0),(-1,0),colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,TABLE_ALT]),
        ("GRID",(0,0),(-1,-1),0.35,GREY_LINE),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(t_defl)

    # ── STEP 12: Overlap ───────────────────────
    story += _section_head("10. Purlin Overlap Check", styles)
    lap_data = [
        ["Parameter", "Value", "Unit"],
        ["Wind load (governing UDL)", round(res.w_governing, 3), "kg/m"],
        ["Moment capacity = Zxx*Fb", round(res.M_capacity, 2), "kg*m"],
        ["Bay spacing L", inp.bay_spacing, "m"],
        ["Overlap length X provided", round(res.lap_used * 1000, 0), "mm"],
        ["Moment at X (M_at_X)", round(res.M_at_lap, 2), "kg*m"],
        ["Status", res.lap_check.status, "-"],
    ]
    story.append(_table(lap_data, [W*0.52, W*0.28, W*0.20]))

    # ── SUMMARY ────────────────────────────────
    story += _section_head("11. Design Summary", styles)
    verdict_color = OK_GREEN if res.passed else FAIL_RED
    verdict_text  = "SECTION ADOPTED - ALL CHECKS SATISFIED" if res.passed \
                    else "SECTION NOT ADEQUATE - REVISE"

    summary_data = [[
        Paragraph(
            f"<font color='{'#1F7A4A' if res.passed else '#C0392B'}'><b>{verdict_text}</b></font>",
            styles["body"]
        )
    ]]
    t_sum = Table(summary_data, colWidths=[W])
    t_sum.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BG),
        ("BOX", (0,0), (-1,-1), 1.5, verdict_color),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 6))

    provide_text = (
        f"<b>PROVIDE PURLIN Z-{int(sec.D)} x {sec.t} mm</b> with "
        f"<b>{inp.num_sag_bars} sag bars</b> and "
        f"<b>{int(res.lap_used*1000)} mm overlap</b>"
    )
    story.append(Paragraph(provide_text, styles["body"]))

    # Footer note
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.4, color=GREY_LINE))
    story.append(Paragraph(
        "References: IS 801-1975, IS 875 (Part 3)-1987, IS 2062. "
        "Generated by Purlin Design App.",
        ParagraphStyle("footer", parent=styles["body"],
            fontSize=7.5, textColor=colors.grey)
    ))

    doc.build(story)
    return buf.getvalue()
