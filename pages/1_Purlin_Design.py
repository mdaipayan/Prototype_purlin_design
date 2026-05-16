"""
Purlin Design page
Streamlit page for Z-section purlin design
per IS 801-1975 and IS 875 (Part 3)-1987.
"""

import streamlit as st
import pandas as pd
import math
import html

st.set_page_config(
    page_title="Purlin Design — IS 801",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS overrides ───────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar width */
[data-testid="stSidebar"] { min-width: 320px; }

/* Section headers */
.section-header {
    font-size: 0.85rem;
    font-weight: 600;
    color: #1B3A6B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 6px 0 2px;
    border-bottom: 2px solid #2E6FBF;
    margin-bottom: 10px;
}

/* Check row colouring */
.ok-row   { background: #EAF6EE !important; }
.fail-row { background: #FCEAEA !important; }

/* Result metric box */
.metric-box {
    background: #EEF3FA;
    border-left: 4px solid #2E6FBF;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
}

/* Verdict banner */
.verdict-pass { background:#EAF6EE; border:1.5px solid #1F7A4A;
    border-radius:8px; padding:12px 18px; text-align:center; }
.verdict-fail { background:#FCEAEA; border:1.5px solid #C0392B;
    border-radius:8px; padding:12px 18px; text-align:center; }

/* Professional design step cards */
.step-card {
    border: 1px solid #D7E2F0;
    border-left: 5px solid #2E6FBF;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    background: #FFFFFF;
    box-shadow: 0 6px 18px rgba(27, 58, 107, 0.07);
}
.step-card-ok { border-left-color: #1F7A4A; }
.step-card-fail { border-left-color: #C0392B; }
.step-title { font-size: 1rem; font-weight: 700; color: #1B3A6B; margin-bottom: 4px; }
.step-clause { display: inline-block; background: #EEF3FA; color: #1B3A6B; border-radius: 999px; padding: 2px 9px; font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; }
.step-label { color: #5B6B7D; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 6px; }
.step-value { color: #12263A; font-size: 0.92rem; }
</style>
""", unsafe_allow_html=True)


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
            "Formula / check": "Centre-line area/centroid/inertia model; Z = I/y",
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
    st.image("https://img.icons8.com/ios/60/1B3A6B/structure.png", width=40)
    st.title("Purlin Design")
    st.caption("IS 801-1975 / IS 875 (Part 3)-1987")
    st.divider()

    # Project info
    st.markdown('<div class="section-header">Project</div>', unsafe_allow_html=True)
    project_name = st.text_input("Project name", value="AIR Concourse Building")
    bay_type = st.selectbox("Bay type", ["End Bay", "Mid Bay"])

    st.markdown('<div class="section-header">Geometry</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    bay_spacing    = c1.number_input("Bay spacing L (m)",   value=9.347, step=0.001, format="%.3f")
    purlin_spacing = c2.number_input("Purlin spacing Ps (m)", value=1.5, step=0.1)
    c1, c2 = st.columns(2)
    slope_x = c1.number_input("Slope X", value=10.0, step=0.5)
    slope_y = c2.number_input("Slope Y", value=1.0,  step=0.1)
    num_sag = st.number_input("Number of sag bars", value=4, min_value=1, max_value=10, step=1)

    st.markdown('<div class="section-header">Loads (kg/m²)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    dl = c1.number_input("Dead load DL",   value=15.0,  step=1.0)
    ll = c2.number_input("Live load LL",   value=75.0,  step=1.0)
    c1, c2 = st.columns(2)
    cl = c1.number_input("Collateral CL",  value=75.0,  step=1.0)
    wl = c2.number_input("Wind load WL",   value=130.0, step=1.0)
    cp1 = st.number_input("Wind coeff Cp1 (IS 875 Table 5)", value=1.4, step=0.05)

    st.markdown('<div class="section-header">Material</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    fy = c1.number_input("Fy (N/mm²)", value=345.0, step=5.0)
    E_mod = c2.number_input("E (N/mm²)", value=200000.0, step=1000.0, format="%.0f")

    st.markdown('<div class="section-header">Z-Section Dimensions (mm)</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    t_sec  = c1.number_input("t", value=2.0,   step=0.5, format="%.1f")
    d_sec  = c2.number_input("d", value=246.0, step=2.0, format="%.1f")
    D_sec  = c3.number_input("D (overall)", value=250.0, step=2.0, format="%.1f")
    c1, c2 = st.columns(2)
    b1_sec = c1.number_input("b1 (top flange)", value=64.0, step=1.0)
    b2_sec = c2.number_input("b2 (bot flange)", value=66.0, step=1.0)
    c1, c2 = st.columns(2)
    L1_sec = c1.number_input("L1 (top lip)", value=20.0, step=1.0)
    L2_sec = c2.number_input("L2 (bot lip)", value=20.0, step=1.0)

    st.markdown('<div class="section-header">Overlap</div>', unsafe_allow_html=True)
    lap_mm = st.number_input("Lap length (mm) — 0 = auto", value=0, step=25)

    run_btn = st.button("▶  Run Design", type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.header("🏗️ Purlin Design — IS 801-1975")
st.caption(f"Project: **{project_name}**  |  Bay type: **{bay_type}**")

if not run_btn:
    st.info("Configure inputs in the sidebar and click **▶ Run Design** to start.", icon="ℹ️")
    with st.expander("How to use this app", expanded=True):
        st.markdown("""
**Design algorithm implemented** (13 steps per IS 801-1975):

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

Download the **PDF report** after running the design.
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
