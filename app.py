"""Landing page for the steel member design application."""

import streamlit as st

st.set_page_config(
    page_title="Steel Member Design Suite",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.hero {
    background: linear-gradient(135deg, #102A43 0%, #1B3A6B 52%, #2E6FBF 100%);
    color: white;
    border-radius: 18px;
    padding: 34px 38px;
    margin-bottom: 24px;
    box-shadow: 0 12px 30px rgba(16, 42, 67, 0.18);
}
.hero h1 { margin: 0 0 8px 0; font-size: 2.35rem; }
.hero p { margin: 0; font-size: 1.05rem; opacity: 0.92; }
.module-card {
    border: 1px solid #D7E2F0;
    border-radius: 16px;
    padding: 22px;
    min-height: 230px;
    background: #FFFFFF;
    box-shadow: 0 8px 22px rgba(27, 58, 107, 0.08);
}
.module-card-active { border-top: 6px solid #1F7A4A; }
.module-card-future { border-top: 6px solid #D89B00; }
.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 10px;
}
.badge-active { background: #EAF6EE; color: #1F7A4A; }
.badge-future { background: #FFF4D6; color: #8A5A00; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <h1>🏗️ Steel Member Design Suite</h1>
  <p>Choose a design module from the sidebar. Purlin Design is available now with IS 801-1975 step-by-step calculations; Girt and Column modules are reserved for future development.</p>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
<div class="module-card module-card-active">
  <span class="badge badge-active">AVAILABLE</span>
  <h3>🏗️ Purlin Design</h3>
  <p>Complete cold-formed Z-purlin design workflow with IS 801 clause references, formulas, substitutions, checks, PDF report, and final adoption status.</p>
  <p><b>Open:</b> use the sidebar page navigation and select <b>Purlin Design</b>.</p>
</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
<div class="module-card module-card-future">
  <span class="badge badge-future">FUTURE</span>
  <h3>🏢 Girt Design</h3>
  <p>Placeholder for wall-girt design inputs, load combinations, member checks, serviceability checks, and report output.</p>
</div>
""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
<div class="module-card module-card-future">
  <span class="badge badge-future">FUTURE</span>
  <h3>🏛️ Column Design</h3>
  <p>Placeholder for column effective length, slenderness, axial and bending capacity, interaction checks, and summary reports.</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.info("Use the sidebar to open the Purlin Design calculation page.", icon="👉")
