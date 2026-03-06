import panel as pn
import secrets
from db import verify_user

_sessions: dict = {}

COOKIE_NAME = "aq_sid"
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


BTN_CSS = """
:host button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important; font-weight: 600 !important;
    border-radius: 10px !important;
    background: linear-gradient(135deg, #6366F1 0%, #4B51A0 100%) !important;
    color: #FFFFFF !important; border: none !important;
    padding: 10px 0 !important; width: 100% !important; cursor: pointer !important;
}
:host button:hover { opacity: 0.88 !important; }
:host button:disabled { opacity: 0.5 !important; cursor: not-allowed !important; }
"""

INPUT_CSS = """
:host input {
    font-family: 'DM Mono', monospace !important; font-size: 13px !important;
    border: 1.5px solid #E0E4F5 !important; border-radius: 8px !important;
    padding: 8px 12px !important; background: #F7F8FC !important;
    color: #2D2F3E !important; width: 100% !important; box-sizing: border-box !important;
}
:host input:focus { border-color: #6366F1 !important; outline: none !important; }
"""

LABEL_STYLE = {
    "font-family": "'DM Sans', sans-serif", "font-size": "11px",
    "text-transform": "uppercase", "letter-spacing": "0.07em",
    "color": "#5A5F94", "margin-bottom": "4px",
}


def render_login_page(on_success=None) -> pn.viewable.Viewable:
    username_input = pn.widgets.TextInput(
        placeholder="username", sizing_mode="stretch_width", stylesheets=[INPUT_CSS]
    )
    password_input = pn.widgets.PasswordInput(
        placeholder="••••••••", sizing_mode="stretch_width", stylesheets=[INPUT_CSS]
    )
    login_btn = pn.widgets.Button(
        name="Sign in", button_type="primary",
        sizing_mode="stretch_width", stylesheets=[BTN_CSS]
    )
    error_msg = pn.pane.Markdown(
        "", styles={"color": "#EF4444", "font-size": "13px",
                    "font-family": "'DM Sans', sans-serif", "min-height": "18px"}
    )
    cookie_setter = pn.pane.HTML("", width=0, height=0, margin=0)

    def on_click(event):
        error_msg.object = ""
        login_btn.disabled = True
        login_btn.name = "Signing in…"
        try:
            user, token = login(username_input.value, password_input.value)
            if user and token:
                cookie_setter.object = (
                    f'<script>document.cookie='
                    f'"{COOKIE_NAME}={token};path=/;max-age={COOKIE_MAX_AGE}"'
                    f';</script>'
                )
                if on_success:
                    on_success(user)
            else:
                error_msg.object = "⚠ Invalid username or password."
                password_input.value = ""
                login_btn.disabled = False
                login_btn.name = "Sign in"
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg.object = f"⚠ Error: {str(e)}"
            login_btn.disabled = False
            login_btn.name = "Sign in"

    login_btn.on_click(on_click)

    return pn.Column(
        cookie_setter,
        pn.pane.Markdown(
            "# 🌿 AirQuality",
            styles={"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E",
                    "text-align": "center", "margin-bottom": "4px"},
        ),
        pn.pane.Markdown(
            "Sign in to your account",
            styles={"color": "#7B82B4", "font-size": "14px", "text-align": "center",
                    "font-family": "'DM Sans', sans-serif", "margin-bottom": "24px"},
        ),
        pn.pane.Markdown("**USERNAME**", styles=LABEL_STYLE),
        username_input,
        pn.pane.Markdown("**PASSWORD**", styles={**LABEL_STYLE, "margin-top": "12px"}),
        password_input,
        pn.Spacer(height=6),
        error_msg,
        login_btn,
        styles={
            "background": "#FFFFFF", "border-radius": "16px",
            "box-shadow": "0 4px 32px rgba(75,81,160,0.10)",
            "padding": "40px 36px", "max-width": "400px",
            "margin": "80px auto 0 auto",
        },
        sizing_mode="stretch_width",
    )