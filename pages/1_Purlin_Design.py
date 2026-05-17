"""
Purlin Design page
Streamlit page for Z-section purlin design
per IS 801-1975 and IS 875 (Part 3)-1987.
"""

import streamlit as st
import pandas as pd
import math
import html

from utils.auth import render_brand_block, render_security_controls, require_authentication

st.set_page_config(
    page_title="Purlin Design — IS 801",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS overrides ───────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --ink: #102033;
    --muted: #64748B;
    --navy: #0B1F3A;
    --blue: #2563EB;
    --sky: #38BDF8;
    --green: #059669;
    --red: #DC2626;
    --amber: #D97706;
    --line: #D8E2EF;
    --panel: rgba(255,255,255,0.94);
}
.stApp { background: linear-gradient(180deg, #F7FAFC 0%, #EEF4F9 46%, #F8FAFC 100%); color: var(--ink); }
.block-container { padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1240px; }
[data-testid="stSidebar"] { min-width: 330px; background: linear-gradient(180deg, #F8FBFE 0%, #EEF5FB 100%); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #475569; }
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.86);
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 14px 16px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
}
[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 18px; overflow: hidden; box-shadow: 0 14px 36px rgba(15, 23, 42, 0.05); }
button[kind="primary"] { border-radius: 999px; }
button[kind="secondary"] { border-radius: 999px; }

/* Section headers */
.section-header {
    font-size: 0.74rem;
    font-weight: 850;
    color: #1D4ED8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 14px 0 6px;
    border-bottom: 1px solid #C7D8ED;
    margin: 8px 0 12px;
}

.page-hero {
    position: relative;
    overflow: hidden;
    border-radius: 28px;
    padding: 30px 34px;
    margin-bottom: 18px;
    color: white;
    background:
        radial-gradient(circle at 84% 16%, rgba(56,189,248,0.34), transparent 30%),
        linear-gradient(135deg, #07182D 0%, #0B1F3A 52%, #1E40AF 100%);
    box-shadow: 0 24px 62px rgba(15, 23, 42, 0.20);
}
.page-hero:after {
    content: "";
    position: absolute;
    right: -120px;
    bottom: -170px;
    width: 360px;
    height: 360px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.045);
}
.page-hero h1 { margin: 9px 0 8px; font-size: clamp(2rem, 4vw, 3.35rem); line-height: 1.04; letter-spacing: -0.045em; }
.page-hero p { margin: 0; max-width: 840px; color: #D8E8F7; line-height: 1.68; }
.eyebrow {
    display: inline-flex;
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 999px;
    padding: 6px 12px;
    background: rgba(255,255,255,0.11);
    color: #DFF6FF;
    font-size: 0.74rem;
    font-weight: 850;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.hero-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.hero-chip { border: 1px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.10); color: #EAF6FF; border-radius: 999px; padding: 7px 11px; font-size: 0.84rem; }

.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 16px 0 22px; }
.kpi-card {
    border: 1px solid #DCE6F1;
    border-radius: 20px;
    padding: 17px 18px;
    background: var(--panel);
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.07);
}
.kpi-label { color: var(--muted); font-size: 0.78rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
.kpi-value { margin-top: 8px; font-size: 1.48rem; line-height: 1.05; font-weight: 850; letter-spacing: -0.03em; color: var(--navy); }
.kpi-note { margin-top: 6px; color: #64748B; font-size: 0.84rem; }

.panel {
    border: 1px solid #DCE6F1;
    border-radius: 24px;
    padding: 20px;
    background: var(--panel);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.065);
    margin-bottom: 18px;
}
.panel-title { margin: 0 0 4px; color: var(--navy); font-size: 1.05rem; font-weight: 850; letter-spacing: -0.018em; }
.panel-subtitle { margin: 0 0 16px; color: var(--muted); font-size: 0.88rem; }

/* Verdict banner */
.verdict-pass, .verdict-fail {
    border-radius: 24px;
    padding: 18px 22px;
    text-align: left;
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
    font-size: 1.02rem;
}
.verdict-pass { background: linear-gradient(135deg, #ECFDF5, #FFFFFF); border: 1px solid #A7F3D0; color: #065F46; }
.verdict-fail { background: linear-gradient(135deg, #FEF2F2, #FFFFFF); border: 1px solid #FECACA; color: #991B1B; }

.step-card {
    border: 1px solid #D7E2F0;
    border-left: 6px solid #2563EB;
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    background: #FFFFFF;
    box-shadow: 0 12px 30px rgba(27, 58, 107, 0.07);
}
.step-card-ok { border-left-color: var(--green); }
.step-card-fail { border-left-color: var(--red); }
.step-title { font-size: 1rem; font-weight: 850; color: var(--navy); margin-bottom: 5px; }
.step-clause { display: inline-block; background: #EFF6FF; color: #1D4ED8; border-radius: 999px; padding: 3px 10px; font-size: 0.72rem; font-weight: 850; margin-bottom: 8px; }
.step-label { color: #64748B; font-size: 0.72rem; font-weight: 850; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 8px; }
.step-value { color: #12263A; font-size: 0.92rem; line-height: 1.55; }

.check-pill { border-radius: 16px; padding: 11px 13px; margin-bottom: 9px; border: 1px solid; }
.check-ok { background: #ECFDF5; border-color: #A7F3D0; color: #065F46; }
.check-fail { background: #FEF2F2; border-color: #FECACA; color: #991B1B; }
.check-pill b { display: block; }
.check-pill span { font-size: 0.86rem; opacity: 0.88; }

.viz-wrap { display: grid; grid-template-columns: 1.05fr 1fr; gap: 18px; align-items: stretch; }
.bar-row { display: grid; grid-template-columns: 150px 1fr 78px; gap: 10px; align-items: center; margin: 10px 0; }
.bar-label { color: #475569; font-size: 0.86rem; font-weight: 700; }
.bar-track { height: 13px; border-radius: 999px; background: #E2E8F0; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #2563EB, #38BDF8); }
.bar-fill.green { background: linear-gradient(90deg, #059669, #34D399); }
.bar-fill.amber { background: linear-gradient(90deg, #D97706, #FBBF24); }
.bar-value { color: #0F172A; font-size: 0.84rem; font-weight: 800; text-align: right; }
.svg-card { display: flex; align-items: center; justify-content: center; min-height: 320px; }

@media (max-width: 980px) { .kpi-grid, .viz-wrap { grid-template-columns: 1fr; } }
</style>
""", unsafe_allow_html=True)

require_authentication()


# ── Imports ──────────────────────────────────────────────────────
from utils.purlin_engine import (
    PurlinInputs, ZSectionProps, design_purlin, CheckResult
)
from utils.pdf_report import generate_pdf_report


# ── Helpers ──────────────────────────────────────────────────────

def check_badge(chk: CheckResult) -> str:
    if chk.status == "OK":
        return f"✅ **{chk.label}**: {chk.value} {chk.unit} ≤ {chk.limit} {chk.unit}"
    else:
        return f"❌ **{chk.label}**: {chk.value} {chk.unit} > {chk.limit} {chk.unit}"


def status_icon(s: str) -> str:
    return "✅" if s == "OK" else "❌"


def _fmt(value: float, digits: int = 3) -> str:
    """Format calculation values compactly for formula tables."""
    return f"{value:.{digits}f}"


def _pct(value: float, limit: float) -> float:
    """Return a bounded utilization percentage for compact visual bars."""
    if limit <= 0:
        return 0.0
    return max(0.0, min((value / limit) * 100, 140.0))


def kpi_card(label: str, value: str, note: str) -> str:
    """Build a compact executive summary metric card."""
    return f'''<div class="kpi-card">
        <div class="kpi-label">{html.escape(label)}</div>
        <div class="kpi-value">{html.escape(value)}</div>
        <div class="kpi-note">{html.escape(note)}</div>
    </div>'''


def check_pill(chk: CheckResult, value_label: str | None = None) -> str:
    """Render a pass/fail check as a polished pill."""
    ok = chk.status == "OK"
    icon = "✅" if ok else "❌"
    klass = "check-ok" if ok else "check-fail"
    detail = value_label or f"{chk.value} vs limit {chk.limit} {chk.unit}"
    return (
        f'<div class="check-pill {klass}">'
        f'{icon} <b>{html.escape(chk.label)}</b>'
        f'<span>{html.escape(detail)}</span></div>'
    )


def render_bar_rows(rows: list[tuple[str, float, float, str]], accent: str = "") -> str:
    """Render labelled utilization bars using pure HTML/CSS."""
    output = []
    for label, value, limit, display in rows:
        width = min(_pct(value, limit), 100.0)
        output.append(
            f'''<div class="bar-row">
                <div class="bar-label">{html.escape(label)}</div>
                <div class="bar-track"><div class="bar-fill {accent}" style="width:{width:.1f}%"></div></div>
                <div class="bar-value">{html.escape(display)}</div>
            </div>'''
        )
    return "".join(output)


def z_section_svg(sec: ZSectionProps, res) -> str:
    """Create an SVG schematic of the selected Z-section with centroid axes."""
    width, height = 460, 320
    scale_y = 230 / max(sec.D, 1)
    max_flange = max(sec.b1, sec.b2, 1)
    scale_x = 138 / max_flange
    cx = width / 2
    top_y = 42
    web_x = cx
    t_vis = max(sec.t * scale_x, 8)
    top_len = sec.b1 * scale_x
    bot_len = sec.b2 * scale_x
    lip1 = sec.L1 * scale_y
    lip2 = sec.L2 * scale_y
    depth = sec.D * scale_y
    centroid_x = web_x + res.section.X * scale_x
    centroid_y = top_y + res.section.Y * scale_y
    return f'''
    <svg viewBox="0 0 {width} {height}" width="100%" height="320" role="img" aria-label="Z-section schematic">
      <defs>
        <linearGradient id="steel" x1="0" x2="1">
          <stop offset="0" stop-color="#1D4ED8"/>
          <stop offset="1" stop-color="#38BDF8"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#0F172A" flood-opacity="0.16"/>
        </filter>
      </defs>
      <rect x="10" y="10" width="440" height="300" rx="24" fill="#F8FAFC" stroke="#D8E2EF"/>
      <g filter="url(#shadow)" stroke="url(#steel)" stroke-linecap="round" stroke-linejoin="round" stroke-width="{t_vis:.1f}" fill="none">
        <path d="M {web_x:.1f} {top_y:.1f} L {web_x+top_len:.1f} {top_y:.1f} L {web_x+top_len:.1f} {top_y+lip1:.1f}"/>
        <path d="M {web_x:.1f} {top_y:.1f} L {web_x:.1f} {top_y+depth:.1f}"/>
        <path d="M {web_x:.1f} {top_y+depth:.1f} L {web_x-bot_len:.1f} {top_y+depth:.1f} L {web_x-bot_len:.1f} {top_y+depth-lip2:.1f}"/>
      </g>
      <line x1="42" y1="{centroid_y:.1f}" x2="418" y2="{centroid_y:.1f}" stroke="#94A3B8" stroke-dasharray="5 6"/>
      <line x1="{centroid_x:.1f}" y1="26" x2="{centroid_x:.1f}" y2="294" stroke="#94A3B8" stroke-dasharray="5 6"/>
      <circle cx="{centroid_x:.1f}" cy="{centroid_y:.1f}" r="7" fill="#F97316" stroke="white" stroke-width="3"/>
      <text x="28" y="38" fill="#64748B" font-size="12" font-weight="700">Z-{sec.D:g} × {sec.t:g} mm</text>
      <text x="28" y="58" fill="#64748B" font-size="11">b1={sec.b1:g}, b2={sec.b2:g}, lips={sec.L1:g}/{sec.L2:g} mm</text>
      <text x="{centroid_x+12:.1f}" y="{centroid_y-10:.1f}" fill="#C2410C" font-size="12" font-weight="800">centroid</text>
      <text x="320" y="286" fill="#334155" font-size="12" font-weight="800">A = {res.section.area:.2f} cm²</text>
    </svg>'''


def purlin_formula_steps(inp: PurlinInputs, sec: ZSectionProps, res) -> list[dict[str, str]]:
    """Return step-by-step formulas, substitutions, and calculated values."""
    span_coeff = 0.0772 if inp.bay_type == "End Bay" else 0.0364
    support_coeff = 0.1071 if inp.bay_type == "End Bay" else 0.0714
    b1_t = sec.b1 / sec.t
    dmin_term = b1_t**2 - 281200 / inp.fy
    dmin_calc = 2.8 * sec.t * math.sqrt(dmin_term) if dmin_term > 0 else 0
    dmin = max(dmin_calc, 4.8 * sec.t)
    zxx_cm3 = res.section.Z1xx_top / 1000
    f_values = [
        (res.M_supp_c1 * 100) / (2 * zxx_cm3),
        (res.M_span_c1 * 100) / zxx_cm3,
        (res.M_supp_c2 * 100) / (2 * zxx_cm3),
        (res.M_span_c2 * 100) / zxx_cm3,
    ] if zxx_cm3 > 0 else [0]
    f_actual = max(max(f_values), 1)
    fb_wind = res.Fb * 1.33
    return [
        {
            "Step": "1. Input data",
            "IS reference": "Project inputs / IS 875 loading data",
            "Formula / check": "Use L, Ps, slope X:Y, loads, Fy, E, selected Z-section",
            "Substitution": (
                f"L={inp.bay_spacing:g} m, Ps={inp.purlin_spacing:g} m, "
                f"slope={inp.slope_x:g}:{inp.slope_y:g}, Fy={inp.fy:g} N/mm², "
                f"Z-{sec.D:g}×{sec.t:g}"
            ),
            "Value / result": "Inputs accepted",
        },
        {
            "Step": "2. Slope factors",
            "IS reference": "Roof geometry resolution",
            "Formula / check": "Kx = X/√(X²+Y²); Ky = Y/√(X²+Y²)",
            "Substitution": f"Kx={inp.slope_x:g}/√({inp.slope_x:g}²+{inp.slope_y:g}²), Ky={inp.slope_y:g}/√({inp.slope_x:g}²+{inp.slope_y:g}²)",
            "Value / result": f"Kx={_fmt(res.Kx, 6)}, Ky={_fmt(res.Ky, 6)}",
        },
        {
            "Step": "3A. Gravity UDL",
            "IS reference": "IS 875 gravity loads",
            "Formula / check": "w₁ = (DL+LL+CL)·Kx·Ps",
            "Substitution": f"({inp.dead_load:g}+{inp.live_load:g}+{inp.collateral_load:g})×{_fmt(res.Kx, 6)}×{inp.purlin_spacing:g}",
            "Value / result": f"w₁={_fmt(res.w_combo1)} kg/m",
        },
        {
            "Step": "3B. Wind uplift UDL",
            "IS reference": "IS 875 (Part 3) wind load",
            "Formula / check": "w₂ = (WL·Cp1 − DL·Kx)·Ps",
            "Substitution": f"({inp.wind_load:g}×{inp.wind_pressure_coeff:g} − {inp.dead_load:g}×{_fmt(res.Kx, 6)})×{inp.purlin_spacing:g}",
            "Value / result": f"w₂={_fmt(res.w_combo2)} kg/m",
        },
        {
            "Step": "4. Bending moments",
            "IS reference": "Continuous purlin analysis coefficients",
            "Formula / check": "Mspan = Cs·w·L²; Msupport = Cp·w·L²",
            "Substitution": f"Cs={span_coeff:g}, Cp={support_coeff:g}, L={inp.bay_spacing:g} m",
            "Value / result": (
                f"Mspan₁={_fmt(res.M_span_c1, 2)}, Msupp₁={_fmt(res.M_supp_c1, 2)}, "
                f"Mspan₂={_fmt(res.M_span_c2, 2)}, Msupp₂={_fmt(res.M_supp_c2, 2)} kg·m"
            ),
        },
        {
            "Step": "5. Section properties",
            "IS reference": "IS 801 section-property basis",
            "Formula / check": "Excel plate-line area/centroid/inertia model; Z = I/y",
            "Substitution": f"t={sec.t:g}, d={sec.d:g}, b1={sec.b1:g}, b2={sec.b2:g}, L1={sec.L1:g}, L2={sec.L2:g}, D={sec.D:g} mm",
            "Value / result": f"Ixx={_fmt(res.section.Ixx/1e4, 2)} cm⁴, Zxx-top={_fmt(res.section.Z1xx_top/1e3, 2)} cm³",
        },
        {
            "Step": "6A. Overall depth",
            "IS reference": "IS 801-1975 cl. 5.2.4",
            "Formula / check": "D < 150t",
            "Substitution": f"{sec.D:g} < 150×{sec.t:g} = {150*sec.t:g}",
            "Value / result": f"{res.depth_check_150t.status}",
        },
        {
            "Step": "6B. Minimum web depth",
            "IS reference": "IS 801-1975 cl. 5.2.1.2",
            "Formula / check": "dmin = max(2.8t√[(b1/t)² − 281200/Fy], 4.8t)",
            "Substitution": f"max(2.8×{sec.t:g}×√[{_fmt(b1_t, 2)}² − 281200/{inp.fy:g}], 4.8×{sec.t:g})",
            "Value / result": f"dmin={_fmt(dmin, 2)} mm; d={sec.d:g} mm → {res.depth_check_dmin.status}",
        },
        {
            "Step": "7. Effective compression flange",
            "IS reference": "IS 801-1975 cl. 5.2.1.1",
            "Formula / check": "b1/t ≤ 1435/√f",
            "Substitution": f"b1/t={_fmt(res.b1_t_actual, 2)}, f=max actual stress={_fmt(f_actual, 2)} kgf/cm²",
            "Value / result": f"limit={_fmt(res.b1_t_limit, 2)} → {res.flange_check.status}",
        },
        {
            "Step": "8. Unbraced length",
            "IS reference": "Sag-bar restraint layout",
            "Formula / check": "Lu = L/(number of sag bars + 1); Iyc = Iyy/2; Sxc = Zxx-top",
            "Substitution": f"Lu={inp.bay_spacing:g}/({inp.num_sag_bars}+1)",
            "Value / result": f"Lu={_fmt(res.L_unbraced)} m, Iyc={_fmt(res.Iyc, 2)} cm⁴, Sxc={_fmt(res.Sxc, 2)} cm³",
        },
        {
            "Step": "9. Permissible bending stress",
            "IS reference": "IS 801-1975 cl. 6.3(b) and cl. 6.1",
            "Formula / check": "λ=L²·Sxc/(d·Iyc); Fb per IS 801 cl. 6.3(b), capped by 0.6Fy",
            "Substitution": f"λ={_fmt(res.lambda_val, 2)}, Fbasic=0.6×{inp.fy:g}",
            "Value / result": f"Fb={_fmt(res.Fb, 2)} N/mm²; Fbasic={_fmt(res.F_basic, 2)} N/mm²",
        },
        {
            "Step": "10. Bending stress checks",
            "IS reference": "IS 801-1975 cl. 6.1 and cl. 6.1.2",
            "Formula / check": "fb = M/Z or M/(2Z); wind limit = 1.33Fb",
            "Substitution": f"Zxx={_fmt(res.section.Z1xx_top, 2)} mm³, Fb={_fmt(res.Fb, 2)}, 1.33Fb={_fmt(fb_wind, 2)} N/mm²",
            "Value / result": "; ".join(f"{chk.label}: {chk.value}/{chk.limit} {chk.status}" for chk in res.stress_checks),
        },
        {
            "Step": "11. Deflection",
            "IS reference": "Serviceability limit Le/150",
            "Formula / check": "δ = C·w·Le⁴/(EI) ≤ Le/150",
            "Substitution": f"C={'0.0065' if inp.bay_type == 'End Bay' else '0.00285'}, Le={inp.bay_spacing:g} m, E={inp.E:g} N/mm², Ixx={_fmt(res.section.Ixx, 2)} mm⁴",
            "Value / result": f"δ₁={_fmt(res.delta_c1, 2)} mm, δ₂={_fmt(res.delta_c2, 2)} mm ≤ { _fmt(res.delta_allow, 2)} mm",
        },
        {
            "Step": "12. Overlap / lap",
            "IS reference": "Lap-zone moment capacity check",
            "Formula / check": "Mcap = Zxx·Fb/100; Mx = wX²/2 + wL²/12 − wLX/2",
            "Substitution": f"X={_fmt(res.lap_used)} m, w={_fmt(res.w_governing)} kg/m, L={inp.bay_spacing:g} m",
            "Value / result": f"Mx={_fmt(res.M_at_lap, 2)} kg·m ≤ Mcap={_fmt(res.M_capacity, 2)} kg·m → {res.lap_check.status}",
        },
        {
            "Step": "13. Final adoption",
            "IS reference": "Design summary",
            "Formula / check": "All mandatory checks must be OK",
            "Substitution": "Depth + flange + stress + deflection + overlap checks",
            "Value / result": "SECTION ADOPTED" if res.passed else "SECTION NOT ADEQUATE",
        },
    ]


# ══════════════════════════════════════════════════════════════════
# SIDEBAR — ALL INPUTS
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    render_brand_block("Purlin Design", "IS 801-1975 / IS 875 (Part 3)-1987")
    render_security_controls()
    st.divider()

    presets = {
        "AIR concourse default": {
            "project_name": "AIR Concourse Building", "bay_type": "End Bay",
            "bay_spacing": 9.347, "purlin_spacing": 1.5, "slope_x": 10.0, "slope_y": 1.0,
            "num_sag": 4, "dl": 15.0, "ll": 75.0, "cl": 75.0, "wl": 130.0,
            "cp1": 1.4, "fy": 345.0, "E_mod": 200000.0,
            "t_sec": 2.0, "d_sec": 246.0, "D_sec": 250.0,
            "b1_sec": 64.0, "b2_sec": 66.0, "L1_sec": 20.0, "L2_sec": 20.0,
            "lap_mm": 0,
        },
        "Light roof review": {
            "project_name": "Light Roof Review", "bay_type": "Mid Bay",
            "bay_spacing": 7.5, "purlin_spacing": 1.4, "slope_x": 10.0, "slope_y": 1.0,
            "num_sag": 3, "dl": 12.0, "ll": 50.0, "cl": 25.0, "wl": 110.0,
            "cp1": 1.2, "fy": 345.0, "E_mod": 200000.0,
            "t_sec": 1.6, "d_sec": 246.0, "D_sec": 250.0,
            "b1_sec": 60.0, "b2_sec": 62.0, "L1_sec": 16.0, "L2_sec": 16.0,
            "lap_mm": 0,
        },
        "High wind trial": {
            "project_name": "High Wind Trial", "bay_type": "End Bay",
            "bay_spacing": 9.347, "purlin_spacing": 1.5, "slope_x": 10.0, "slope_y": 1.0,
            "num_sag": 5, "dl": 15.0, "ll": 75.0, "cl": 75.0, "wl": 165.0,
            "cp1": 1.4, "fy": 345.0, "E_mod": 200000.0,
            "t_sec": 2.5, "d_sec": 245.0, "D_sec": 250.0,
            "b1_sec": 64.0, "b2_sec": 66.0, "L1_sec": 20.0, "L2_sec": 20.0,
            "lap_mm": 0,
        },
    }
    preset_name = st.selectbox(
        "Design starting preset",
        list(presets),
        help="Choose a curated starting point, then fine-tune the inputs below.",
    )
    defaults = presets[preset_name]
    key_prefix = preset_name.lower().replace(" ", "_")

    # Project info
    st.markdown('<div class="section-header">Project</div>', unsafe_allow_html=True)
    project_name = st.text_input("Project name", value=defaults["project_name"], key=f"project_{key_prefix}")
    bay_type = st.selectbox(
        "Bay type",
        ["End Bay", "Mid Bay"],
        index=["End Bay", "Mid Bay"].index(defaults["bay_type"]),
        help="End bay uses higher continuous-purlin moment coefficients than mid bay.",
        key=f"bay_type_{key_prefix}",
    )

    st.markdown('<div class="section-header">Geometry</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    bay_spacing = c1.number_input("Bay spacing L (m)", value=defaults["bay_spacing"], min_value=0.1, step=0.001, format="%.3f", help="Effective purlin span between frames.", key=f"bay_spacing_{key_prefix}")
    purlin_spacing = c2.number_input("Purlin spacing Ps (m)", value=defaults["purlin_spacing"], min_value=0.1, step=0.1, help="Tributary roof width supported by each purlin.", key=f"purlin_spacing_{key_prefix}")
    c1, c2 = st.columns(2)
    slope_x = c1.number_input("Slope X", value=defaults["slope_x"], min_value=0.1, step=0.5, key=f"slope_x_{key_prefix}")
    slope_y = c2.number_input("Slope Y", value=defaults["slope_y"], min_value=0.0, step=0.1, key=f"slope_y_{key_prefix}")
    num_sag = st.number_input("Number of sag bars", value=defaults["num_sag"], min_value=1, max_value=10, step=1, help="Used to determine unbraced length Lu = L/(n+1).", key=f"num_sag_{key_prefix}")

    st.markdown('<div class="section-header">Loads (kg/m²)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    dl = c1.number_input("Dead load DL", value=defaults["dl"], min_value=0.0, step=1.0, key=f"dl_{key_prefix}")
    ll = c2.number_input("Live load LL", value=defaults["ll"], min_value=0.0, step=1.0, key=f"ll_{key_prefix}")
    c1, c2 = st.columns(2)
    cl = c1.number_input("Collateral CL", value=defaults["cl"], min_value=0.0, step=1.0, key=f"cl_{key_prefix}")
    wl = c2.number_input("Wind load WL", value=defaults["wl"], min_value=0.0, step=1.0, key=f"wl_{key_prefix}")
    cp1 = st.number_input("Wind coeff Cp1 (IS 875 Table 5)", value=defaults["cp1"], min_value=0.0, step=0.05, help="External/internal pressure coefficient used in wind uplift combination.", key=f"cp1_{key_prefix}")

    st.markdown('<div class="section-header">Material</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    fy = c1.number_input("Fy (N/mm²)", value=defaults["fy"], min_value=1.0, step=5.0, key=f"fy_{key_prefix}")
    E_mod = c2.number_input("E (N/mm²)", value=defaults["E_mod"], min_value=1.0, step=1000.0, format="%.0f", key=f"E_mod_{key_prefix}")

    st.markdown('<div class="section-header">Z-Section Dimensions (mm)</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    t_sec = c1.number_input("t", value=defaults["t_sec"], min_value=0.1, step=0.5, format="%.1f", key=f"t_sec_{key_prefix}")
    d_sec = c2.number_input("d", value=defaults["d_sec"], min_value=1.0, step=2.0, format="%.1f", key=f"d_sec_{key_prefix}")
    D_sec = c3.number_input("D (overall)", value=defaults["D_sec"], min_value=1.0, step=2.0, format="%.1f", key=f"D_sec_{key_prefix}")
    c1, c2 = st.columns(2)
    b1_sec = c1.number_input("b1 (top flange)", value=defaults["b1_sec"], min_value=1.0, step=1.0, key=f"b1_sec_{key_prefix}")
    b2_sec = c2.number_input("b2 (bot flange)", value=defaults["b2_sec"], min_value=1.0, step=1.0, key=f"b2_sec_{key_prefix}")
    c1, c2 = st.columns(2)
    L1_sec = c1.number_input("L1 (top lip)", value=defaults["L1_sec"], min_value=0.0, step=1.0, key=f"L1_sec_{key_prefix}")
    L2_sec = c2.number_input("L2 (bot lip)", value=defaults["L2_sec"], min_value=0.0, step=1.0, key=f"L2_sec_{key_prefix}")

    st.markdown('<div class="section-header">Overlap</div>', unsafe_allow_html=True)
    lap_mm = st.number_input("Lap length (mm) — 0 = auto", value=defaults["lap_mm"], min_value=0, step=25, help="Use 0 to let the app search for a satisfactory lap length.", key=f"lap_mm_{key_prefix}")

    if D_sec < d_sec:
        st.warning("Overall depth D should be greater than or equal to clear web depth d.", icon="⚠️")
    if L1_sec < t_sec or L2_sec < t_sec:
        st.warning("Lip depth is less than thickness; the section-property model will reduce effective lip depth to zero at the bend.", icon="⚠️")

    run_btn = st.button("▶  Run Design", type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.markdown(
    f"""
<div class="page-hero">
  <span class="eyebrow">Cold-formed steel design</span>
  <h1>Purlin Design — IS 801-1975</h1>
  <p>Professional Z-section calculation dashboard with live inputs, visual utilization summaries, section-property graphics, clause references, and an auditable PDF report.</p>
  <div class="hero-meta">
    <span class="hero-chip">Project: <b>{html.escape(project_name)}</b></span>
    <span class="hero-chip">Bay type: <b>{html.escape(bay_type)}</b></span>
    <span class="hero-chip">Section: <b>Z-{D_sec:g} × {t_sec:g} mm</b></span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if not run_btn:
    st.markdown(
        """
<div class="panel">
  <div class="panel-title">Ready for design review</div>
  <div class="panel-subtitle">Configure the engineering inputs in the sidebar, then run the calculation package.</div>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-label">Workflow</div><div class="kpi-value">13 steps</div><div class="kpi-note">Clause-led checks</div></div>
    <div class="kpi-card"><div class="kpi-label">Outputs</div><div class="kpi-value">PDF</div><div class="kpi-note">Formal report</div></div>
    <div class="kpi-card"><div class="kpi-label">Visualization</div><div class="kpi-value">Live</div><div class="kpi-note">Utilization + section graphics</div></div>
    <div class="kpi-card"><div class="kpi-label">Status</div><div class="kpi-value">Audit</div><div class="kpi-note">Pass/fail traceability</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.expander("Design algorithm implemented", expanded=True):
        st.markdown("""
| Step | Description |
|------|-------------|
| 1 | Collect input data — geometry, loads, material |
| 2 | Compute slope reduction factors Kx, Ky |
| 3 | Calculate design load per metre (2 combinations) |
| 4 | Compute design bending moments (end bay / mid bay coefficients) |
| 5 | Compute Z-section properties from dimensions |
| 6 | Section depth checks — cl. 5.2.4 & 5.2.1.2 |
| 7 | Effective width of compression flange — cl. 5.2.1.1 |
| 8 | Unbraced length, Iyc, Sxc for lateral buckling |
| 9 | Permissible bending stress Fb — cl. 6.3(b) |
| 10 | Actual vs permissible stress checks (4 cases) |
| 11 | Deflection serviceability check (Le/150) |
| 12 | Purlin overlap / lap length check |
| 13 | Final section adoption |
        """)
    st.stop()


# ── Build input objects ───────────────────────────────────────────
inp = PurlinInputs(
    bay_spacing=bay_spacing, purlin_spacing=purlin_spacing,
    slope_x=slope_x, slope_y=slope_y,
    bay_type=bay_type,
    dead_load=dl, live_load=ll, collateral_load=cl,
    wind_load=wl, wind_pressure_coeff=cp1,
    fy=fy, E=E_mod,
    num_sag_bars=int(num_sag),
    lap_length=float(lap_mm),
)
sec = ZSectionProps(
    t=t_sec, d=d_sec, b1=b1_sec, b2=b2_sec,
    L1=L1_sec, L2=L2_sec, D=D_sec,
)

# ── Run design ───────────────────────────────────────────────────
with st.spinner("Running design checks…"):
    res = design_purlin(inp, sec)

# ── Verdict banner ───────────────────────────────────────────────
if res.passed:
    st.markdown(
        f'<div class="verdict-pass">✅ &nbsp;<strong>SECTION ADOPTED</strong> — '
        f'Z-{int(sec.D)}×{sec.t} &nbsp;|&nbsp; {int(num_sag)} sag bars &nbsp;|&nbsp; '
        f'{int(res.lap_used*1000)} mm overlap &nbsp;|&nbsp; All checks satisfied.</div>',
        unsafe_allow_html=True,
    )
else:
    fails = ", ".join(res.fail_reasons[:3])
    st.markdown(
        f'<div class="verdict-fail">❌ &nbsp;<strong>NOT ADEQUATE</strong> — '
        f'Failed: {fails}. Revise section dimensions.</div>',
        unsafe_allow_html=True,
    )
st.markdown("")

# ── Executive KPI and visualization layer ────────────────────────
governing_stress_check = max(
    res.stress_checks,
    key=lambda chk: (chk.value / chk.limit) if chk.limit else 0,
    default=None,
)
governing_stress = governing_stress_check.value if governing_stress_check else 0
governing_stress_limit = governing_stress_check.limit if governing_stress_check else 1
deflection_ratio = max(
    _pct(res.defl_check_c1.value, res.defl_check_c1.limit),
    _pct(res.defl_check_c2.value, res.defl_check_c2.limit),
)
stress_ratio = _pct(governing_stress, governing_stress_limit)
lap_ratio = _pct(res.M_at_lap, res.M_capacity)
st.markdown(
    '<div class="kpi-grid">'
    + kpi_card("Adopted section", f"Z-{sec.D:g} × {sec.t:g}", f"{sec.d:g} mm web, {sec.b1:g}/{sec.b2:g} mm flanges")
    + kpi_card("Governing stress", f"{stress_ratio:.0f}%", f"{governing_stress:.1f} / {governing_stress_limit:.1f} N/mm²")
    + kpi_card("Deflection demand", f"{deflection_ratio:.0f}%", f"Limit = {res.delta_allow:.1f} mm")
    + kpi_card("Overlap demand", f"{lap_ratio:.0f}%", f"Lap = {res.lap_used*1000:.0f} mm")
    + '</div>',
    unsafe_allow_html=True,
)

left_viz, right_viz = st.columns([1.05, 1])
with left_viz:
    st.markdown(
        f'''<div class="panel svg-card">{z_section_svg(sec, res)}</div>''',
        unsafe_allow_html=True,
    )
with right_viz:
    st.markdown(
        '''<div class="panel"><div class="panel-title">Design utilization snapshot</div>
        <div class="panel-subtitle">Demand-to-capacity ratios for the governing checks.</div>'''
        + render_bar_rows(
            [
                ("Bending stress", governing_stress, governing_stress_limit, f"{stress_ratio:.0f}%"),
                ("Deflection", max(res.defl_check_c1.value, res.defl_check_c2.value), res.delta_allow, f"{deflection_ratio:.0f}%"),
                ("Lap moment", res.M_at_lap, res.M_capacity, f"{lap_ratio:.0f}%"),
                ("Flange slenderness", res.b1_t_actual, res.b1_t_limit, f"{_pct(res.b1_t_actual, res.b1_t_limit):.0f}%"),
            ]
        )
        + '</div>',
        unsafe_allow_html=True,
    )

# ── PDF Download ─────────────────────────────────────────────────
pdf_bytes = generate_pdf_report(project_name, inp, sec, res)
st.download_button(
    "⬇  Download PDF Report",
    data=pdf_bytes,
    file_name=f"Purlin_Design_{bay_type.replace(' ','_')}.pdf",
    mime="application/pdf",
    type="secondary",
)

st.divider()

# ── STEP-BY-STEP FORMULAS ───────────────────────────────────────
st.markdown("##### 🧮 Professional Design Steps with IS References")
st.caption("Review the clause/reference, governing expression, substituted values, and result for every purlin design step.")
formula_steps = purlin_formula_steps(inp, sec, res)

step_tab, table_tab, print_tab = st.tabs(["Design step cards", "Calculation table", "Printable checklist"])
with step_tab:
    for row in formula_steps:
        status_text = row["Value / result"]
        card_class = "step-card-ok" if "OK" in status_text or "ADOPTED" in status_text or "accepted" in status_text else ""
        if "NOT OK" in status_text or "NOT ADEQUATE" in status_text:
            card_class = "step-card-fail"
        step = html.escape(row["Step"])
        clause = html.escape(row["IS reference"])
        formula = html.escape(row["Formula / check"])
        substitution = html.escape(row["Substitution"])
        result = html.escape(row["Value / result"])
        st.markdown(
            f'''<div class="step-card {card_class}">
                <div class="step-title">{step}</div>
                <div class="step-clause">{clause}</div>
                <div class="step-label">Formula / Check</div>
                <div class="step-value"><code>{formula}</code></div>
                <div class="step-label">Substitution</div>
                <div class="step-value"><code>{substitution}</code></div>
                <div class="step-label">Calculated Value / Result</div>
                <div class="step-value"><b>{result}</b></div>
            </div>''',
            unsafe_allow_html=True,
        )

with table_tab:
    formula_df = pd.DataFrame(formula_steps)
    st.dataframe(formula_df, use_container_width=True, hide_index=True)

with print_tab:
    for row in formula_steps:
        st.markdown(f"""
**{row['Step']} — {row['IS reference']}**  
Formula/check: `{row['Formula / check']}`  
Expression: `{row['Substitution']}`  
Result: **{row['Value / result']}**
        """)

st.divider()

# ── RESULTS GRID ─────────────────────────────────────────────────
# Row 1: Loads + Moments
col_L, col_M = st.columns(2)

with col_L:
    st.markdown("##### 📐 Loads & Slope Factors")
    st.markdown(f"**Kx** = {res.Kx:.6f}  |  **Ky** = {res.Ky:.6f}")
    data = {
        "Combination": ["Combo I (↓)  DL+LL+CL", "Combo II (↑) WL−DL"],
        "w (kg/m)": [f"{res.w_combo1:.3f}", f"{res.w_combo2:.3f}"],
        "Direction": ["Downward", "Upward"],
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

with col_M:
    st.markdown("##### 📊 Bending Moments")
    coeff_s = "0.0772" if bay_type=="End Bay" else "0.0364"
    coeff_p = "0.1071" if bay_type=="End Bay" else "0.0714"
    mom_df = pd.DataFrame({
        "Case": ["DL+LL+CL span", "DL+LL+CL supp", "DL+WL span", "DL+WL supp"],
        "Coeff": [coeff_s, coeff_p, coeff_s, coeff_p],
        "Moment (kg·m)": [
            f"{res.M_span_c1:.2f}", f"{res.M_supp_c1:.2f}",
            f"{res.M_span_c2:.2f}", f"{res.M_supp_c2:.2f}",
        ],
    })
    st.dataframe(mom_df, use_container_width=True, hide_index=True)

# Row 2: Section Properties
st.markdown("##### 🔩 Z-Section Properties")
col_a, col_b = st.columns(2)
s = res.section

with col_a:
    props = {
        "Property": ["Ixx", "Iyy", "Z1xx-top", "Z1xx-bot", "Zyy-right"],
        "Value": [
            f"{s.Ixx/1e4:.2f} cm⁴",
            f"{s.Iyy/1e4:.2f} cm⁴",
            f"{s.Z1xx_top/1e3:.2f} cm³",
            f"{s.Z1xx_bot/1e3:.2f} cm³",
            f"{s.Zyy_right/1e3:.2f} cm³",
        ],
    }
    st.dataframe(pd.DataFrame(props), use_container_width=True, hide_index=True)

with col_b:
    st.metric("Centroid ȳ (from top)", f"{s.Y:.3f} mm")
    st.metric("Centroid x̄ (from web CL)", f"{s.X:.3f} mm")
    st.metric("Cross-section Area", f"{s.area:.3f} cm²")
    st.metric("Self-weight", f"{s.weight_per_m:.3f} kg/m")
    eff = "✅ Full flange effective" if res.flange_effective else "❌ Reduced-width section required"
    st.metric("Compression flange", eff)

# Row 3: Depth Checks + Stress Checks
st.markdown("##### 🔍 Section Classification & Stress Checks")
col_d, col_s = st.columns(2)

with col_d:
    st.markdown("###### Depth checks (IS 801 cl. 5.2.4)")
    for chk in [res.depth_check_150t, res.depth_check_dmin, res.flange_check]:
        icon = "✅" if chk.status == "OK" else "❌"
        color = "#EAF6EE" if chk.status == "OK" else "#FCEAEA"
        st.markdown(
            f'<div style="background:{color};border-radius:6px;padding:6px 10px;margin-bottom:6px">'
            f'{icon} <b>{chk.label}</b><br/>'
            f'<span style="font-size:0.85rem">{chk.value} vs limit {chk.limit} {chk.unit}</span>'
            f'</div>', unsafe_allow_html=True
        )

with col_s:
    st.markdown("###### Bending stress checks (IS 801 cl. 6.1)")
    for chk in res.stress_checks:
        icon = "✅" if chk.status == "OK" else "❌"
        color = "#EAF6EE" if chk.status == "OK" else "#FCEAEA"
        st.markdown(
            f'<div style="background:{color};border-radius:6px;padding:6px 10px;margin-bottom:4px">'
            f'{icon} <b>{chk.label}</b><br/>'
            f'<span style="font-size:0.85rem">fb = {chk.value} N/mm² vs Fb = {chk.limit} N/mm²</span>'
            f'</div>', unsafe_allow_html=True
        )

# Row 4: Permissible Stress + Deflection
col_fb, col_df = st.columns(2)

with col_fb:
    st.markdown("##### 📏 Permissible Bending Stress (cl. 6.3b)")
    st.metric("Unbraced length L_u", f"{res.L_unbraced:.3f} m")
    st.metric("λ = L²·Sxc / (d·Iyc)", f"{res.lambda_val:.2f}")
    st.metric("Fb adopted", f"{res.Fb:.2f} N/mm²")
    st.metric("F_basic = 0.6·Fy", f"{res.F_basic:.2f} N/mm²")

with col_df:
    st.markdown("##### 🔼 Deflection Checks (Le / 150)")
    st.metric("Permissible deflection", f"{res.delta_allow:.2f} mm")
    for chk in [res.defl_check_c1, res.defl_check_c2]:
        icon = "✅" if chk.status == "OK" else "❌"
        color = "#EAF6EE" if chk.status == "OK" else "#FCEAEA"
        st.markdown(
            f'<div style="background:{color};border-radius:6px;padding:6px 10px;margin-bottom:6px">'
            f'{icon} <b>{chk.label}</b><br/>'
            f'<span style="font-size:0.85rem">δ = {chk.value} mm vs {chk.limit} mm</span>'
            f'</div>', unsafe_allow_html=True
        )

# Row 5: Overlap Check
st.markdown("##### 🔗 Purlin Overlap Check")
col_o1, col_o2 = st.columns(2)
with col_o1:
    st.metric("Moment capacity M_cap", f"{res.M_capacity:.2f} kg·m")
    st.metric("Overlap X provided", f"{res.lap_used*1000:.0f} mm")
with col_o2:
    st.metric("Moment at X (M_at_X)", f"{res.M_at_lap:.2f} kg·m")
    icon = "✅" if res.lap_check.status == "OK" else "❌"
    color = "#EAF6EE" if res.lap_check.status == "OK" else "#FCEAEA"
    st.markdown(
        f'<div style="background:{color};border-radius:6px;padding:8px 12px">'
        f'{icon} <b>Overlap check: {res.lap_check.status}</b><br/>'
        f'<span style="font-size:0.85rem">{res.M_at_lap:.2f} kg·m ≤ {res.M_capacity:.2f} kg·m</span>'
        f'</div>', unsafe_allow_html=True
    )

# Footer
st.divider()
st.caption("IS 801-1975 · IS 875 (Part 3)-1987 · IS 2062 · "
           "Kavikulguru Institute of Technology and Science, Ramtek, Nagpur")
