"""Regression tests for PDF report formatting helpers."""

from pdf_report import _pdf_text, _value_with_unit


def test_pdf_text_renders_superscript_units():
    assert _pdf_text("741.63 cm^4 <= 800 N/mm^2") == (
        "741.63 cm<super>4</super> &le; 800 N/mm<super>2</super>"
    )


def test_value_with_unit_keeps_unit_beside_value():
    assert _value_with_unit("741.63", "cm^4") == "741.63 cm^4"
    assert _value_with_unit("OK", "-") == "OK"
