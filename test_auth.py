"""Regression tests for shared authentication/branding helpers."""

from utils.auth import DEFAULT_APP_PASSWORD, brand_mark


def test_brand_mark_is_inline_svg_logo():
    logo = brand_mark(42)
    assert '<svg width="42" height="42"' in logo
    assert "Steel Member Design Suite logo" in logo


def test_default_password_is_available_for_local_development():
    assert DEFAULT_APP_PASSWORD == "purlin@2026"
