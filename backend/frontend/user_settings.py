import panel as pn
import datetime as dt
from auth import current_user, render_login_page
from db import get_user_api_keys, verify_password, update_user_password
from .navbar import render_navbar


FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700"
    "&family=DM+Mono:wght@400;500&display=swap');"
)
GLOBAL_CSS = """
body { font-family: 'DM Sans', sans-serif !important; background: #F7F8FC !important; }
"""
CARD = {
    "background": "#FFFFFF", "border-radius": "16px",
    "box-shadow": "0 2px 24px rgba(75,81,160,0.07)",
    "padding": "28px 32px", "margin-bottom": "20px",
}
SECTION_TITLE = {"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E", "margin-bottom": "4px"}
SUBLABEL = {
    "font-family": "'DM Sans', sans-serif", "font-size": "11px",
    "text-transform": "uppercase", "letter-spacing": "0.07em",
    "color": "#5A5F94", "margin-bottom": "4px",
}
INPUT_CSS = """
:host input {
    font-family: 'DM Mono', monospace !important; font-size: 13px !important;
    border: 1.5px solid #E0E4F5 !important; border-radius: 8px !important;
    padding: 7px 11px !important; background: #F7F8FC !important;
    color: #2D2F3E !important; width: 100% !important; box-sizing: border-box !important;
}
:host input:focus { border-color: #6366F1 !important; outline: none !important; background: #fff !important; }
"""

SETTINGS_JS = """
<script>
(function () {
    if (window.__ubdSettingsJs) return;
    window.__ubdSettingsJs = true;

    function _copy(text, btn, doneLabel) {
        var orig = btn.textContent;
        function ok() {
            btn.textContent = doneLabel;
            setTimeout(function () { btn.textContent = orig; }, 1500);
        }
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(ok).catch(function () { _fallback(text, ok); });
        } else {
            _fallback(text, ok);
        }
    }
    function _fallback(text, cb) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.cssText = 'position:fixed;top:-999px;left:-999px;opacity:0';
        document.body.appendChild(ta);
        ta.focus(); ta.select();
        try { document.execCommand('copy'); if (cb) cb(); } catch (e) {}
        document.body.removeChild(ta);
    }

    window.copyText = function (text, btn) { _copy(text, btn, '✓'); };
}());
</script>
"""


def _btn(label, bg="#6366F1", fg="#fff", width=None):
    css = (f":host button {{font-family:'DM Sans',sans-serif!important;"
           f"font-size:13px!important;font-weight:600!important;border-radius:8px!important;"
           f"background:{bg}!important;color:{fg}!important;border:1.5px solid {bg}!important;"
           f"padding:7px 18px!important;cursor:pointer!important;transition:opacity .15s!important;}}"
           f":host button:hover{{opacity:.82!important;}}")
    kw = {"name": label, "button_type": "light", "stylesheets": [css]}
    if width:
        kw["width"] = width
    return pn.widgets.Button(**kw)


def _lbl(text):
    return pn.pane.Markdown(f"**{text}**", styles=SUBLABEL)


def _notice():
    return pn.pane.Markdown("", styles={"color": "#22C55E", "font-size": "13px",
                                        "font-family": "'DM Sans',sans-serif", "min-height": "20px"})


def _ok(n, msg):
    n.styles = {**n.styles, "color": "#22C55E"}
    n.object = f"✓ {msg}"


def _err(n, msg):
    n.styles = {**n.styles, "color": "#EF4444"}
    n.object = f"⚠ {msg}"


def _credential_card(key: dict) -> pn.pane.HTML:
    uid   = key.get("user_id",   "—")
    uhash = key.get("user_hash", "—")
    url   = "https://data-vizualization-5rxh.onrender.com/api/v1/data"
    label = key.get("label", "API Key")

    active_badge = (
        '<span style="background:#D1FAE5;color:#065F46;border-radius:20px;'
        'padding:2px 10px;font-size:11px;font-weight:600;">● Active</span>'
        if key.get("is_active") else
        '<span style="background:#FEE2E2;color:#991B1B;border-radius:20px;'
        'padding:2px 10px;font-size:11px;font-weight:600;">○ Inactive</span>'
    )

    def _sq(v):
        return v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

    def _copy_btn(value, icon="⎘"):
        return (f'<button onclick="window.copyText(\'{_sq(value)}\',this)" '
                f'style="background:#EEF0FF;border:none;border-radius:6px;padding:4px 10px;'
                f'cursor:pointer;font-size:14px;color:#4B51A0;flex-shrink:0;">{icon}</button>')

    html = f"""
<div style="background:#fff;border-radius:14px;border:1.5px solid #EEF0FA;
            padding:24px 28px;margin-bottom:16px;
            box-shadow:0 2px 16px rgba(75,81,160,0.06);font-family:'DM Sans',sans-serif;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
    <span style="font-size:18px;font-weight:700;color:#2D2F3E;">🔑 {label}</span>
    {active_badge}
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px;">
    <div style="background:#F7F8FC;border-radius:10px;padding:14px 16px;border:1px solid #E8EBFA;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;
                   color:#7B82B4;margin-bottom:6px;font-weight:600;">X-User-id</div>
      <div style="display:flex;align-items:center;gap:8px;">
        <code style="font-family:'DM Mono',monospace;font-size:14px;color:#2D2F3E;
                     font-weight:500;flex:1;word-break:break-all;">{uid}</code>
        {_copy_btn(uid)}
      </div>
    </div>
    <div style="background:#F7F8FC;border-radius:10px;padding:14px 16px;border:1px solid #E8EBFA;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;
                   color:#7B82B4;margin-bottom:6px;font-weight:600;">X-User-hash</div>
      <div style="display:flex;align-items:center;gap:8px;">
        <code style="font-family:'DM Mono',monospace;font-size:14px;color:#2D2F3E;
                     font-weight:500;flex:1;word-break:break-all;
                     filter:blur(4px);transition:filter .2s;"
             onmouseenter="this.style.filter='none'"
             onmouseleave="this.style.filter='blur(4px)'">{uhash}</code>
        {_copy_btn(uhash)}
      </div>
      <div style="font-size:10px;color:#A5B4FC;margin-top:5px;">Hover to reveal</div>
    </div>
    <div style="grid-column:span 2;background:#F7F8FC;border-radius:10px;
                padding:14px 16px;border:1px solid #E8EBFA;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;
                   color:#7B82B4;margin-bottom:6px;font-weight:600;">API URL (POST)</div>
      <div style="display:flex;align-items:center;gap:8px;">
        <code style="font-family:'DM Mono',monospace;font-size:13px;color:#4B51A0;
                     flex:1;word-break:break-all;">{url}</code>
        {_copy_btn(url)}
      </div>
    </div>
  </div>
</div>
"""
    return pn.pane.HTML(html, sizing_mode="stretch_width")


def _profile_card(user: dict) -> pn.pane.HTML:
    role       = user.get("role", "viewer")
    username   = user.get("username", "—")
    created_at = user.get("created_at", "")

    if created_at:
        try:
            if isinstance(created_at, str):
                created_at = dt.datetime.fromisoformat(created_at)
            created_str = created_at.strftime("%d %B %Y")
        except Exception:
            created_str = str(created_at)
    else:
        created_str = "—"

    initials = "".join(w[0].upper() for w in username.split()[:2]) or username[:2].upper()

    html = f"""
<div style="background:linear-gradient(135deg,#4B51A0 0%,#6366F1 100%);
            border-radius:16px;padding:28px 32px;display:flex;align-items:center;gap:24px;
            box-shadow:0 4px 30px rgba(99,102,241,0.25);
            font-family:'DM Sans',sans-serif;color:#fff;margin-bottom:20px;">
  <div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,0.18);
              display:flex;align-items:center;justify-content:center;font-size:26px;
              font-weight:700;flex-shrink:0;border:2px solid rgba(255,255,255,0.35);">{initials}</div>
  <div style="flex:1;">
    <div style="font-size:22px;font-weight:700;letter-spacing:-.01em;">{username}</div>
    <div style="display:flex;align-items:center;gap:10px;margin-top:6px;">
      <span style="background:rgba(255,255,255,0.2);border-radius:20px;padding:2px 12px;
                   font-size:12px;font-weight:600;font-family:'DM Mono',monospace;">{role}</span>
      <span style="font-size:13px;opacity:.75;">Member since {created_str}</span>
    </div>
  </div>
  <div style="font-size:40px;opacity:.25;flex-shrink:0;">⚙</div>
</div>
"""
    return pn.pane.HTML(html, sizing_mode="stretch_width")


def _change_password_card(user: dict) -> pn.Column:
    n       = _notice()
    old_pw  = pn.widgets.PasswordInput(placeholder="Current password",            sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    new_pw  = pn.widgets.PasswordInput(placeholder="New password (min. 8 chars)", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    conf_pw = pn.widgets.PasswordInput(placeholder="Confirm new password",         sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    save_btn = _btn("💾 Update Password")

    def on_save(e):
        n.object = ""
        if not old_pw.value or not new_pw.value or not conf_pw.value:
            return _err(n, "All fields are required.")
        if len(new_pw.value) < 8:
            return _err(n, "New password must be at least 8 characters.")
        if new_pw.value != conf_pw.value:
            return _err(n, "Passwords do not match.")
        if not verify_password(user["username"], old_pw.value):
            return _err(n, "Current password is incorrect.")
        update_user_password(user["id"], new_pw.value)
        _ok(n, "Password updated successfully.")
        old_pw.value = new_pw.value = conf_pw.value = ""

    save_btn.on_click(on_save)

    return pn.Column(
        pn.pane.Markdown("## 🔒 Change Password", styles=SECTION_TITLE),
        pn.layout.Divider(),
        pn.Row(
            pn.Column(_lbl("Current Password"), old_pw,  sizing_mode="stretch_width"),
            pn.Column(_lbl("New Password"),     new_pw,  sizing_mode="stretch_width"),
            pn.Column(_lbl("Confirm"),          conf_pw, sizing_mode="stretch_width"),
            sizing_mode="stretch_width", styles={"gap": "14px"},
        ),
        pn.Row(save_btn, n, styles={"align-items": "center", "gap": "16px", "margin-top": "4px"}),
        sizing_mode="stretch_width",
        styles=CARD,
    )


def render_settings_page() -> pn.viewable.Viewable:
    pn.config.raw_css.append(FONT_IMPORT + GLOBAL_CSS)

    container = pn.Column(
        sizing_mode="stretch_width",
        styles={"background": "#F7F8FC", "min-height": "100vh"},
    )

    user = current_user()

    if user is None:
        def on_login(u):
            if u.get("role") == "admin":
                with pn.io.unlocked():
                    container.objects = [
                        pn.pane.HTML(
                            '<script>window.location.href = "/admin-panel";</script>',
                            width=0, height=0, margin=0,
                        )
                    ]
                return
            with pn.io.unlocked():
                container.objects = [
                    pn.pane.HTML(
                        '<script>window.location.href = "/settings";</script>',
                        width=0, height=0, margin=0,
                    )
                ]

        container.objects = [render_login_page(on_success=on_login)]
        return container

    container.objects = [_build_settings(user)]
    return container


def _build_settings(user: dict) -> pn.Column:
    user_keys = get_user_api_keys(user["username"])

    if user_keys:
        cred_items = [
            pn.pane.Markdown(
                "Use the credentials below to POST sensor data to the Urban Bike Data API.",
                styles={"color": "#7B82B4", "font-size": "13px", "margin-bottom": "8px"},
            )
        ] + [_credential_card(k) for k in user_keys]
    else:
        cred_items = [pn.pane.HTML(
            '<div style="text-align:center;padding:48px 0;color:#7B82B4;font-family:\'DM Sans\',sans-serif;">'
            '<div style="font-size:36px;margin-bottom:12px;">🔑</div>'
            '<div style="font-size:15px;font-weight:600;color:#4B51A0;">No API credentials assigned yet</div>'
            '<div style="font-size:13px;margin-top:6px;">Contact an admin to get your credentials added.</div>'
            '</div>', sizing_mode="stretch_width"
        )]

    credentials_card = pn.Column(
        pn.pane.Markdown("## 🌐 API Credentials", styles=SECTION_TITLE),
        pn.layout.Divider(),
        *cred_items,
        sizing_mode="stretch_width",
        styles=CARD,
    )

    return pn.Column(
        render_navbar(active="settings", title="🌿 **Urban Bike Data**"),
        pn.Column(
            _profile_card(user),
            credentials_card,
            _change_password_card(user),
            sizing_mode="stretch_width",
            styles={"max-width": "960px", "margin": "0 auto", "padding": "28px 20px"},
        ),
        sizing_mode="stretch_width",
    )