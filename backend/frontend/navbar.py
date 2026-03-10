"""
navbar.py — Shared top navigation bar.
Usage:
    from navbar import render_navbar
    layout = pn.Column(render_navbar(active="dashboard"), ...)
"""

import panel as pn
from auth import current_user, logout

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700"
    "&family=DM+Mono&display=swap');"
)

NAV_CSS = """
.nav-link-active button {
    background: #EEF0FF !important;
    color: #4B51A0 !important;
    border-color: #C7D2FE !important;
}
"""

def _nav_btn(label: str, href: str, active: bool = False):
    btn = pn.widgets.Button(
        name=label,
        button_type="light",
        stylesheets=[f"""
        :host button {{
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1.5px solid {"#C7D2FE" if active else "transparent"} !important;
            background: {"#EEF0FF" if active else "transparent"} !important;
            color: {"#4B51A0" if active else "#7B82B4"} !important;
            padding: 7px 16px !important;
            cursor: pointer !important;
            transition: all 0.15s !important;
        }}
        :host button:hover {{
            background: #EEF0FF !important;
            color: #4B51A0 !important;
            border-color: #C7D2FE !important;
        }}
        """],
    )
    btn.js_on_click(code=f"window.location.href = '{href}'")
    return btn


def render_navbar(active: str = "dashboard", title: str = "") -> pn.Row:
    """
    Parameters
    ----------
    active : "dashboard" | "admin"
        Which nav item to highlight.
    """
    pn.config.raw_css.append(FONT_IMPORT)

    user = current_user()

    # ── Logo / brand ─────────────────────────────────────────
    brand = pn.pane.Markdown(
        title,
        styles={
            "font-family": "'DM Sans', sans-serif",
            "font-size": "16px",
            "color": "#4B51A0",
            "margin": "0",
            "white-space": "nowrap",
        },
    )

    # ── Nav links ─────────────────────────────────────────────
    nav_links = pn.Row(
        _nav_btn("📊 Dashboard", "/",       active=(active == "dashboard")),
        _nav_btn("🛠 Admin",     "/admin-panel",  active=(active == "admin")),
        styles={"gap": "4px", "align-items": "center"},
    )

    # ── Right side: user info + logout ────────────────────────
    if user:
        role_badge_color = "#6366F1" if user.get("role") == "admin" else "#7B82B4"
        user_info = pn.pane.Markdown(
            f"👤 **{user['username']}** "
            f"<span style='background:{role_badge_color};color:#fff;"
            f"border-radius:4px;padding:1px 7px;font-size:11px;"
            f"font-family:DM Mono,monospace'>{user['role']}</span>",
            styles={
                "font-family": "'DM Sans', sans-serif",
                "font-size": "13px",
                "color": "#5A5F94",
                "white-space": "nowrap",
                "align-self": "center",
            },
        )

        logout_btn = pn.widgets.Button(
            name="Sign out",
            button_type="light",
            stylesheets=["""
            :host button {
                font-family: 'DM Sans', sans-serif !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                border-radius: 8px !important;
                border: 1.5px solid #FCA5A5 !important;
                background: #FFF1F2 !important;
                color: #EF4444 !important;
                padding: 6px 14px !important;
                cursor: pointer !important;
            }
            :host button:hover { background: #FEE2E2 !important; }
            """],
        )

        def on_logout(e):
            logout()
            import panel as pn
            pn.state.location.reload = True  # forces full page reload to login
        logout_btn.on_click(on_logout)

        right_side = pn.Row(
            user_info,
            logout_btn,
            styles={"gap": "12px", "align-items": "center"},
        )
    else:
        # Not logged in — show a login link
        right_side = _nav_btn("🔑 Login", "/admin-panel")

    # ── Assemble bar ──────────────────────────────────────────
    navbar = pn.Row(
        brand,
        pn.Spacer(sizing_mode="stretch_width"),
        nav_links,
        pn.Spacer(sizing_mode="stretch_width"),
        right_side,
        sizing_mode="stretch_width",
        styles={
            "background": "#FFFFFF",
            "border-bottom": "1.5px solid #EEF0FA",
            "padding": "12px 28px",
            "align-items": "center",
            "box-shadow": "0 2px 12px rgba(75,81,160,0.06)",
            "position": "sticky",
            "top": "0",
            "z-index": "100",
            "border-radius": "15px"
        },
    )

    return navbar