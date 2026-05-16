"""
Purlin Design App — Main entry point
Streamlit multi-page application for Z-section purlin design
per IS 801-1975 and IS 875 (Part 3)-1987.
"""

import streamlit as st
import math

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
    import pandas as pd
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
    st.metric("Centroid X̄ (from top)", f"{s.Y:.3f} mm")
    st.metric("Cross-section Area", f"{s.area:.3f} cm²")
    st.metric("Self-weight", f"{s.weight_per_m:.3f} kg/m")
    eff = "✅ Full flange effective" if res.flange_effective else "⚠️ Reduced flange width"
    st.metric("Compression flange", eff)

# Row 3: Depth Checks + Stress Checks
st.markdown("##### 🔍 Section Classification & Stress Checks")
col_d, col_s = st.columns(2)

with col_d:
    st.markdown("###### Depth checks (IS 801 cl. 5.2.4)")
    for chk in [res.depth_check_150t, res.depth_check_dmin]:
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
