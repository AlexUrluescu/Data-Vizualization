import panel as pn
import secrets
from db import verify_user

_sessions: dict = {}

COOKIE_NAME    = "aq_sid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def current_user() -> dict | None:
    token = pn.state.cookies.get(COOKIE_NAME)
    if token:
        return _sessions.get(token)
    return None


def login(username: str, password: str) -> tuple[dict, str] | tuple[None, None]:
    user = verify_user(username.strip(), password)
    if user:
        token = secrets.token_hex(32)
        _sessions[token] = user
        return user, token
    return None, None


def logout():
    token = pn.state.cookies.get(COOKIE_NAME)
    if token:
        _sessions.pop(token, None)


# ── Shared redirect helper for Panel pages ────────────────────
def redirect_to_login() -> pn.pane.HTML:
    """Drop this into any Panel page when current_user() is None."""
    return pn.pane.HTML(
        '<script>window.location.href = "/login";</script>',
        width=0, height=0, margin=0,
    )