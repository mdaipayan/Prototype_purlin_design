"""
Page 2 — Z-Section Database
Browse and select standard cold-formed Z-sections.
"""

import streamlit as st
import pandas as pd
from utils.purlin_engine import ZSectionProps, compute_section

st.set_page_config(page_title="Z-Section Database", page_icon="📋", layout="wide")

st.header("📋 Z-Section Database")
st.caption("Standard cold-formed Z-sections commonly used for purlins (IS 811)")

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

st.caption(f"Showing {len(filt)} sections. Values computed using centre-line model.")
st.info("💡 Select a section in the main **Design** page sidebar to run full IS 801 checks.", icon="ℹ️")
