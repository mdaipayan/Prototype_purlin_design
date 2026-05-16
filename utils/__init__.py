"""Compatibility package for application modules.

The Streamlit app and tests import modules from ``utils`` while the source files
live at the project root. These wrappers keep those imports working without
changing the public module layout.
"""
