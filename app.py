"""Landing page for the steel member design application."""

import streamlit as st

from utils.auth import brand_mark, render_brand_block, render_security_controls, require_authentication

st.set_page_config(
    page_title="Steel Member Design Suite",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
    --ink: #102033;
    --muted: #64748B;
    --navy: #0B1F3A;
    --blue: #2563EB;
    --cyan: #38BDF8;
    --green: #059669;
    --amber: #D97706;
    --card: rgba(255, 255, 255, 0.94);
    --line: #D8E2EF;
}
.stApp { background: linear-gradient(180deg, #F7FAFC 0%, #EEF4F9 100%); color: var(--ink); }
.block-container { padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1220px; }
.hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 86% 12%, rgba(56, 189, 248, 0.34), transparent 28%),
        linear-gradient(135deg, #061629 0%, #0B1F3A 48%, #1E3A8A 100%);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 28px;
    padding: 44px 46px;
    margin-bottom: 24px;
    box-shadow: 0 26px 70px rgba(15, 23, 42, 0.22);
}
.hero:after {
    content: "";
    position: absolute;
    inset: auto -8% -44% auto;
    width: 420px;
    height: 420px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.04);
}
.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 999px;
    padding: 7px 13px;
    background: rgba(255,255,255,0.10);
    color: #DFF6FF;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.hero h1 { margin: 16px 0 10px 0; font-size: clamp(2.1rem, 4.2vw, 4rem); line-height: 1.02; letter-spacing: -0.045em; }
.hero p { margin: 0; max-width: 850px; font-size: 1.08rem; line-height: 1.75; color: #D9E8F7; }
.hero-grid { display: grid; grid-template-columns: 1.5fr 0.9fr; gap: 26px; align-items: center; }
.hero-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.hero-stat {
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 18px;
    padding: 16px;
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(10px);
}
.hero-stat b { display: block; font-size: 1.35rem; color: white; }
.hero-stat span { color: #CFE0F4; font-size: 0.83rem; }
.section-kicker { color: #2563EB; font-size: 0.78rem; font-weight: 850; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 10px; }
.module-card {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 26px;
    min-height: 282px;
    background: var(--card);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}
.module-card:before { content: ""; position: absolute; inset: 0 0 auto 0; height: 6px; background: linear-gradient(90deg, #2563EB, #38BDF8); }
.module-card-future:before { background: linear-gradient(90deg, #D97706, #FBBF24); }
.module-card h3 { margin: 10px 0 10px; font-size: 1.35rem; letter-spacing: -0.02em; color: var(--navy); }
.module-card p { color: var(--muted); line-height: 1.62; }
.badge {
    display: inline-flex;
    border-radius: 999px;
    padding: 5px 11px;
    font-size: 0.73rem;
    font-weight: 850;
    letter-spacing: 0.06em;
}
.badge-active { background: #DCFCE7; color: #047857; }
.badge-future { background: #FEF3C7; color: #A16207; }
.module-list { margin: 16px 0 0; padding: 0; list-style: none; color: #475569; font-size: 0.92rem; }
.module-list li { padding: 7px 0; border-top: 1px solid #E8EEF6; }
.callout {
    border: 1px solid #BFDBFE;
    background: linear-gradient(135deg, #EFF6FF, #FFFFFF);
    border-radius: 20px;
    padding: 18px 20px;
    color: #1E3A8A;
    margin-top: 20px;
}
@media (max-width: 900px) { .hero-grid { grid-template-columns: 1fr; } .hero { padding: 32px 28px; } }
</style>
""",
    unsafe_allow_html=True,
)

require_authentication()

st.markdown(
    f"""
<div class="hero">
  <div class="hero-grid">
    <div>
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">{brand_mark(62)}<span class="eyebrow">Structural engineering dashboard</span></div>
      <h1>Steel Member Design Suite</h1>
      <p>A polished calculation environment for cold-formed steel member design. Start with the available purlin workflow for IS 801-1975 checks, transparent formula substitutions, acceptance summaries, and PDF reporting.</p>
    </div>
    <div class="hero-stat-grid">
      <div class="hero-stat"><b>13</b><span>auditable design steps</span></div>
      <div class="hero-stat"><b>IS 801</b><span>clause-led checking</span></div>
      <div class="hero-stat"><b>PDF</b><span>report generation</span></div>
      <div class="hero-stat"><b>Z</b><span>section visualization</span></div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    render_brand_block()
    render_security_controls()
    st.markdown("### Navigation")
    st.caption("Use the Streamlit page menu above to open the active design module.")
    st.markdown("---")
    st.markdown("**Active module:** Purlin Design")
    st.markdown("**Security:** token protected")

st.markdown('<div class="section-kicker">Design modules</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
<div class="module-card module-card-active">
  <span class="badge badge-active">AVAILABLE</span>
  <h3>🏗️ Purlin Design</h3>
  <p>Cold-formed Z-purlin design workflow with governing loads, moment envelopes, section properties, stress checks, deflection checks, lap verification, and final adoption status.</p>
  <ul class="module-list">
    <li>Use the sidebar page navigation.</li>
    <li>Select <b>Purlin Design</b>.</li>
    <li>Run checks and export the report.</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
<div class="module-card module-card-future">
  <span class="badge badge-future">ROADMAP</span>
  <h3>🏢 Girt Design</h3>
  <p>Reserved for wall-girt inputs, load combinations, member checks, serviceability checks, wind suction review, and report output.</p>
  <ul class="module-list">
    <li>Clean placeholder module.</li>
    <li>Consistent future UX language.</li>
    <li>Prepared for engineering extensions.</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
<div class="module-card module-card-future">
  <span class="badge badge-future">ROADMAP</span>
  <h3>🏛️ Column Design</h3>
  <p>Reserved for effective length setup, slenderness, axial and bending capacity, interaction equations, and summary reporting.</p>
  <ul class="module-list">
    <li>Professional navigation shell.</li>
    <li>Clear future-state messaging.</li>
    <li>Aligned visual system.</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="callout"><b>Next step:</b> open <b>Purlin Design</b> from the sidebar to view the upgraded engineering dashboard and visualization panels.</div>
""",
    unsafe_allow_html=True,
)
