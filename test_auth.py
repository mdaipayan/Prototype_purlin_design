"""Regression tests for shared authentication/branding helpers."""

from utils.auth import DEFAULT_APP_TOKEN, _configured_tokens, _split_tokens, _token_is_valid, brand_mark


def test_brand_mark_is_inline_svg_logo():
    logo = brand_mark(42)
    assert '<svg width="42" height="42"' in logo
    assert "Steel Member Design Suite logo" in logo


def test_default_token_is_available_for_local_development():
    assert DEFAULT_APP_TOKEN == "purlin-dev-token"


def test_split_tokens_supports_streamlit_secret_lists_and_csv():
    assert _split_tokens("alpha, beta\ngamma") == ["alpha", "beta", "gamma"]
    assert _split_tokens(["alpha", " beta ", ""]) == ["alpha", "beta"]


def test_token_validation_accepts_any_configured_token():
    assert _token_is_valid("beta", ["alpha", "beta"])
    assert not _token_is_valid("gamma", ["alpha", "beta"])


def test_configured_tokens_prefer_access_token_env(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKENS", "alpha,beta")
    tokens, configured_securely = _configured_tokens()
    assert tokens == ["alpha", "beta"]
    assert configured_securely
