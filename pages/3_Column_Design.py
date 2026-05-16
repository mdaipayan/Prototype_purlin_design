"""Future page for column design."""

import streamlit as st

st.set_page_config(page_title="Column Design — Future", page_icon="🏛️", layout="wide")

st.header("🏛️ Column Design")
st.caption("Future development module")

st.warning(
    "Column design is reserved for future development. "
    "The current production-ready module is Purlin Design.",
    icon="🚧",
)

st.markdown(
    """
### Planned workflow
1. Collect column height, restraint conditions, loading, and section data.
2. Compute effective lengths, slenderness ratios, axial capacity, and bending capacity.
3. Check combined axial force and bending interaction.
4. Prepare a detailed design summary and downloadable calculation report.
    """
)
