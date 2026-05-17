"""Shared authentication and branding helpers for the Streamlit app."""

from __future__ import annotations

import hmac
import os
from html import escape

import streamlit as st

DEFAULT_APP_TOKEN = "purlin-dev-token"


def _split_tokens(value) -> list[str]:
    """Normalize a token secret/env value into a list of non-empty tokens."""
    if value is None:
        return []
    if isinstance(value, str):
        candidates = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        candidates = value
    else:
        candidates = [value]
    return [str(token).strip() for token in candidates if str(token).strip()]


def _secret_value(name: str):
    """Read a Streamlit secret without failing in local/test contexts."""
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def _configured_tokens() -> tuple[list[str], bool]:
    """Return configured access tokens and whether they came from a secure source.

    Preferred configuration is token based: set `APP_ACCESS_TOKEN` or
    `APP_ACCESS_TOKENS` in Streamlit secrets or environment variables.
    `APP_PASSWORD` is still accepted for backwards compatibility only.
    """
    token_sources = [
        _secret_value("APP_ACCESS_TOKENS"),
        _secret_value("APP_ACCESS_TOKEN"),
        os.environ.get("APP_ACCESS_TOKENS"),
        os.environ.get("APP_ACCESS_TOKEN"),
    ]
    legacy_sources = [
        _secret_value("APP_PASSWORD"),
        os.environ.get("APP_PASSWORD"),
    ]

    tokens: list[str] = []
    for source in token_sources:
        tokens.extend(_split_tokens(source))
    if tokens:
        return tokens, True

    legacy_tokens: list[str] = []
    for source in legacy_sources:
        legacy_tokens.extend(_split_tokens(source))
    if legacy_tokens:
        return legacy_tokens, True

    return [DEFAULT_APP_TOKEN], False


def _token_is_valid(candidate: str, valid_tokens: list[str]) -> bool:
    """Compare a submitted token against configured tokens in constant time."""
    return any(hmac.compare_digest(candidate, token) for token in valid_tokens)


def brand_mark(size: int = 54) -> str:
    """Return a compact inline SVG mark for the steel design suite."""
    return f'''
<svg width="{size}" height="{size}" viewBox="0 0 64 64" role="img" aria-label="Steel Member Design Suite logo" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="steelGradient" x1="8" y1="8" x2="58" y2="58" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#38BDF8"/>
      <stop offset="0.45" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#0B1F3A"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#steelGradient)"/>
  <path d="M18 46V18h28v7H26v6h17v7H26v8h20" fill="none" stroke="white" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M20 50h27" stroke="#BAE6FD" stroke-width="3" stroke-linecap="round"/>
</svg>'''


def render_brand_block(title: str = "Steel Member Design Suite", subtitle: str = "IS 801 engineering dashboard") -> None:
    """Render a professional brand block for sidebars and auth screens."""
    st.markdown(
        f'''
<div class="brand-block">
  <div class="brand-logo">{brand_mark(50)}</div>
  <div>
    <div class="brand-title">{escape(title)}</div>
    <div class="brand-subtitle">{escape(subtitle)}</div>
  </div>
</div>
''',
        unsafe_allow_html=True,
    )


def _auth_styles() -> None:
    st.markdown(
        """
<style>
.brand-block {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 18px;
}
.brand-logo {
    flex: 0 0 auto;
    display: inline-flex;
    filter: drop-shadow(0 10px 18px rgba(15, 23, 42, 0.18));
}
.brand-title {
    color: #0B1F3A;
    font-size: 1.03rem;
    font-weight: 850;
    letter-spacing: -0.025em;
    line-height: 1.12;
}
.brand-subtitle {
    color: #64748B;
    font-size: 0.78rem;
    font-weight: 650;
    margin-top: 3px;
}
.auth-shell {
    max-width: 520px;
    margin: 7vh auto 0;
    padding: 30px;
    border: 1px solid #D8E2EF;
    border-radius: 28px;
    background: rgba(255,255,255,0.96);
    box-shadow: 0 24px 70px rgba(15, 23, 42, 0.14);
}
.auth-eyebrow {
    color: #2563EB;
    font-size: 0.76rem;
    font-weight: 850;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 16px 0 6px;
}
.auth-shell h1 {
    color: #0B1F3A;
    margin: 0 0 8px;
    font-size: 2rem;
    letter-spacing: -0.04em;
}
.auth-copy {
    color: #64748B;
    line-height: 1.65;
    margin-bottom: 18px;
}
.security-note {
    border: 1px solid #BFDBFE;
    border-radius: 16px;
    padding: 11px 13px;
    color: #1E3A8A;
    background: #EFF6FF;
    font-size: 0.88rem;
    margin-top: 14px;
}
.auth-status {
    border: 1px solid #BBF7D0;
    background: #F0FDF4;
    color: #166534;
    border-radius: 14px;
    padding: 9px 11px;
    font-size: 0.84rem;
    font-weight: 700;
    margin: 8px 0 14px;
}
</style>
""",
        unsafe_allow_html=True,
    )


def require_authentication() -> None:
    """Stop page execution until the user has entered a configured access token."""
    _auth_styles()
    valid_tokens, configured_securely = _configured_tokens()

    if st.session_state.get("authenticated"):
        return

    query_token = st.query_params.get("token") or st.query_params.get("access_token")
    if query_token and _token_is_valid(str(query_token), valid_tokens):
        st.session_state["authenticated"] = True
        st.query_params.clear()
        st.rerun()

    st.markdown(
        f'''
<div class="auth-shell">
  <div class="brand-block">
    <div class="brand-logo">{brand_mark(58)}</div>
    <div>
      <div class="brand-title">Steel Member Design Suite</div>
      <div class="brand-subtitle">Protected engineering workspace</div>
    </div>
  </div>
  <div class="auth-eyebrow">Access token required</div>
  <h1>Secure token access</h1>
  <div class="auth-copy">Enter your Streamlit access token to unlock calculation modules, section databases, and PDF reports.</div>
</div>
''',
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        entered_token = st.text_input("Access token", type="password", placeholder="Paste Streamlit access token")
        submitted = st.form_submit_button("Unlock dashboard", type="primary", use_container_width=True)

    if submitted:
        if _token_is_valid(entered_token, valid_tokens):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid access token. Please try again.", icon="🔒")

    if not configured_securely:
        st.info(
            "For production, set `APP_ACCESS_TOKEN` or `APP_ACCESS_TOKENS` in Streamlit secrets "
            "or as an environment variable. The local fallback token is `purlin-dev-token`.",
            icon="ℹ️",
        )
    st.stop()


def render_security_controls() -> None:
    """Render a compact authenticated-session control in the sidebar."""
    st.markdown('<div class="auth-status">🔐 Token session active</div>', unsafe_allow_html=True)
    if st.button("Log out", use_container_width=True):
        st.session_state.pop("authenticated", None)
        st.rerun()
