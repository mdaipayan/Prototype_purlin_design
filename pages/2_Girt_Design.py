"""Future page for cold-formed girt design."""

import streamlit as st

st.set_page_config(page_title="Girt Design — Future", page_icon="🏢", layout="wide")

st.header("🏢 Girt Design")
st.caption("Future development module")

st.info(
    "Girt design calculations will be added in a future release. "
    "This page is reserved for wall-girt inputs, load combinations, "
    "member checks, serviceability checks, and report output.",
    icon="ℹ️",
)

st.markdown(
    """
### Planned workflow
1. Collect wall bay geometry, girt spacing, support conditions, and section dimensions.
2. Calculate wind and gravity load combinations applicable to girts.
3. Check bending, shear, deflection, local buckling, and connection requirements.
4. Generate a step-by-step design report with formulas, substitutions, and results.
    """
)
