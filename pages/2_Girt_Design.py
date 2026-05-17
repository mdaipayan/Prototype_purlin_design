"""Future page for cold-formed girt design."""

import streamlit as st

from utils.auth import render_brand_block, render_security_controls, require_authentication

st.set_page_config(page_title="Girt Design — Future", page_icon="🏢", layout="wide")
require_authentication()

with st.sidebar:
    render_brand_block("Girt Design", "Roadmap module")
    render_security_controls()

st.markdown(
    """
<style>
.roadmap-hero { border:1px solid #D8E2EF; border-radius:26px; padding:30px; background:linear-gradient(135deg,#FFFFFF,#EFF6FF); box-shadow:0 18px 44px rgba(15,23,42,.08); }
.roadmap-hero h1 { margin:0 0 8px; color:#0B1F3A; letter-spacing:-.04em; }
.roadmap-hero p { color:#64748B; line-height:1.65; max-width:780px; }
.roadmap-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:18px; }
.roadmap-step { border:1px solid #E2E8F0; border-radius:18px; padding:15px; background:white; color:#334155; }
.roadmap-step b { display:block; color:#1D4ED8; margin-bottom:6px; }
@media(max-width:900px){.roadmap-grid{grid-template-columns:1fr;}}
</style>
<div class="roadmap-hero">
  <h1>🏢 Girt Design</h1>
  <p>This module is password-protected and reserved for the upcoming wall-girt workflow. The layout is prepared for inputs, load combinations, member checks, serviceability checks, and report output.</p>
  <div class="roadmap-grid">
    <div class="roadmap-step"><b>01 Inputs</b>Wall bay geometry, girt spacing, support conditions, and section dimensions.</div>
    <div class="roadmap-step"><b>02 Loads</b>Wind and gravity combinations applicable to girts.</div>
    <div class="roadmap-step"><b>03 Checks</b>Bending, shear, deflection, local buckling, and connections.</div>
    <div class="roadmap-step"><b>04 Report</b>Step-by-step design report with formulas and results.</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
