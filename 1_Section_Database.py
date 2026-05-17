"""
Page 2 — Z-Section Database
Browse and select standard cold-formed Z-sections.
"""

import streamlit as st

from utils.auth import render_brand_block, render_security_controls, require_authentication
import pandas as pd
from utils.purlin_engine import ZSectionProps, compute_section

st.set_page_config(page_title="Z-Section Database", page_icon="📋", layout="wide")
require_authentication()

with st.sidebar:
    render_brand_block("Section Database", "Protected section library")
    render_security_controls()

st.markdown(
    """
<style>
.database-hero { border:1px solid #D8E2EF; border-radius:24px; padding:24px 28px; background:linear-gradient(135deg,#FFFFFF,#EFF6FF); box-shadow:0 16px 40px rgba(15,23,42,.07); margin-bottom:18px; }
.database-hero h1 { margin:0 0 6px; color:#0B1F3A; letter-spacing:-.035em; }
.database-hero p { color:#64748B; margin:0; line-height:1.6; }
</style>
<div class="database-hero">
  <h1>📋 Z-Section Database</h1>
  <p>Protected reference table for standard cold-formed Z-sections. Values are computed using the Excel-aligned plate-line section-property model.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Standard sections ─────────────────────────────────────────
SECTIONS = [
    # t,   d,    b1,  b2,  L1,  L2,  D
    (1.6,  196,  60,  62,  16,  16,  200),
    (1.6,  246,  60,  62,  16,  16,  250),
    (2.0,  196,  62,  64,  18,  18,  200),
    (2.0,  246,  64,  66,  20,  20,  250),
    (2.0,  296,  64,  66,  20,  20,  300),
    (2.5,  196,  62,  64,  18,  18,  200),
    (2.5,  245,  64,  66,  20,  20,  250),
    (2.5,  295,  64,  66,  20,  20,  300),
    (3.0,  245,  65,  67,  22,  22,  250),
    (3.0,  295,  65,  67,  22,  22,  300),
    (3.0,  345,  65,  67,  22,  22,  350),
]

rows = []
for s in SECTIONS:
    sec = ZSectionProps(*s)
    compute_section(sec)
    rows.append({
        "Designation": f"Z-{int(sec.D)}×{sec.t}",
        "t (mm)": sec.t,
        "d (mm)": sec.d,
        "b1 (mm)": sec.b1,
        "b2 (mm)": sec.b2,
        "D (mm)": sec.D,
        "Area (cm²)": round(sec.area, 3),
        "Wt (kg/m)": round(sec.weight_per_m, 3),
        "Ixx (cm⁴)": round(sec.Ixx / 1e4, 2),
        "Zxx-top (cm³)": round(sec.Z1xx_top / 1e3, 2),
        "Iyy (cm⁴)": round(sec.Iyy / 1e4, 2),
    })

df = pd.DataFrame(rows)

# Filters
c1, c2 = st.columns(2)
t_options = sorted(df["t (mm)"].unique())
D_options = sorted(df["D (mm)"].unique())
sel_t = c1.multiselect("Filter by thickness t (mm)", t_options, default=t_options)
sel_D = c2.multiselect("Filter by overall depth D (mm)", D_options, default=D_options)

filt = df[df["t (mm)"].isin(sel_t) & df["D (mm)"].isin(sel_D)]

st.dataframe(
    filt.style.background_gradient(subset=["Ixx (cm⁴)", "Zxx-top (cm³)"], cmap="Blues"),
    use_container_width=True,
    hide_index=True,
)

st.caption(f"Showing {len(filt)} sections. Values computed using the Excel-aligned plate-line model.")
st.info("💡 Select a section in the main **Design** page sidebar to run full IS 801 checks.", icon="ℹ️")
