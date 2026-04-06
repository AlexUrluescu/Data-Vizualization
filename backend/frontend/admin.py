import panel as pn
import pandas as pd
from auth import current_user, logout
from db import (
    list_sensors, upsert_sensor, delete_sensor,
    list_api_keys, add_api_key, toggle_api_key, delete_api_key,
    list_configs, set_config,
    list_users, create_user, delete_user, update_user_role,
)

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700"
    "&family=DM+Mono&display=swap');"
)
GLOBAL_CSS = "body { font-family:'DM Sans',sans-serif!important; background:#F7F8FC!important; }"

CARD = {
    "background": "#FFFFFF", "border-radius": "14px",
    "box-shadow": "0 2px 20px rgba(75,81,160,0.07)",
    "padding": "28px 28px 24px 28px", "margin-bottom": "20px",
}
SECTION_TITLE = {"font-family": "'DM Sans',sans-serif", "color": "#2D2F3E", "margin-bottom": "6px"}
SUBLABEL = {
    "font-family": "'DM Sans',sans-serif", "font-size": "11px",
    "text-transform": "uppercase", "letter-spacing": "0.07em",
    "color": "#5A5F94", "margin-bottom": "4px",
}
INPUT_CSS = """
:host input, :host select {
    font-family:'DM Mono',monospace!important; font-size:13px!important;
    border:1.5px solid #E0E4F5!important; border-radius:8px!important;
    padding:7px 11px!important; background:#F7F8FC!important;
    color:#2D2F3E!important; width:100%!important; box-sizing:border-box!important;
}
:host input:focus { border-color:#6366F1!important; outline:none!important; background:#fff!important; }
"""

def _btn(bg="#6366F1", fg="#fff"):
    return f"""
:host button {{
    font-family:'DM Sans',sans-serif!important; font-size:13px!important;
    font-weight:600!important; border-radius:8px!important;
    background:{bg}!important; color:{fg}!important;
    border:1.5px solid {bg}!important; padding:7px 18px!important; cursor:pointer!important;
}}
:host button:hover {{ opacity:.82!important; }}
"""

def _lbl(text):
    return pn.pane.Markdown(f"**{text}**", styles=SUBLABEL)

def _notice():
    return pn.pane.Markdown("", styles={
        "color": "#22C55E", "font-size": "13px",
        "font-family": "'DM Sans',sans-serif", "min-height": "20px",
    })

def _ok(n, msg):
    n.styles = {**n.styles, "color": "#22C55E"}
    n.object = f"✓ {msg}"

def _err(n, msg):
    n.styles = {**n.styles, "color": "#EF4444"}
    n.object = f"⚠ {msg}"

def _warn(n, msg):
    n.styles = {**n.styles, "color": "#F59E0B"}
    n.object = f"⚠ {msg}"

def _table(data, cols=None):
    if not data:
        return pn.pane.Markdown("_No records yet._",
            styles={"color":"#7B82B4","font-style":"italic","font-size":"13px"})
    df = pd.DataFrame(data)
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    return pn.widgets.Tabulator(
        df, pagination="remote", page_size=8, sizing_mode="stretch_width",
        stylesheets=["""
            .tabulator { font-family:'DM Mono',monospace!important; font-size:12px!important;
                border:none!important; border-radius:10px!important; overflow:hidden; }
            .tabulator-header { background:#F0F2FF!important; border-bottom:2px solid #E0E4F5!important; }
            .tabulator-header .tabulator-col { background:transparent!important; color:#5A5F94!important;
                font-weight:600!important; font-size:11px!important;
                text-transform:uppercase!important; letter-spacing:.05em!important; }
            .tabulator-row { border-bottom:1px solid #EEF0FA!important; background:#fff!important; }
            .tabulator-row:hover { background:#F7F8FF!important; }
        """],
    )


# ── Tabs ──────────────────────────────────────────────────────
def _sensors_tab():
    n = _notice()
    th = pn.Column(sizing_mode="stretch_width")

    def refresh():
        th.objects = [_table(list_sensors(), ["id","name","lat","lon","location","is_active","created_at"])]
    refresh()

    f_id  = pn.widgets.TextInput(placeholder="1600013B", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_nm  = pn.widgets.TextInput(placeholder="Sibiu 1",  sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_lat = pn.widgets.TextInput(placeholder="45.7983",  sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_lon = pn.widgets.TextInput(placeholder="24.1256",  sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_loc = pn.widgets.TextInput(placeholder="Zone",     sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    add_btn = pn.widgets.Button(name="➕ Add Sensor", button_type="primary", stylesheets=[_btn()])

    def on_add(e):
        n.object = ""
        sid = f_id.value.strip().upper()
        nm  = f_nm.value.strip()
        if not sid or not nm: return _err(n, "ID and Name are required.")
        try:
            lat, lon = float(f_lat.value), float(f_lon.value)
        except ValueError:
            return _err(n, "Lat / Lon must be numbers.")
        upsert_sensor(sid, nm, lat, lon, f_loc.value.strip())
        _ok(n, f"Sensor **{nm}** saved.")
        for w in (f_id, f_nm, f_lat, f_lon, f_loc): w.value = ""
        refresh()
    add_btn.on_click(on_add)

    d_id = pn.widgets.TextInput(placeholder="Sensor ID", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    del_btn = pn.widgets.Button(name="🗑 Deactivate", stylesheets=[_btn("#EF4444")])

    def on_del(e):
        sid = d_id.value.strip().upper()
        if not sid: return
        delete_sensor(sid)
        _warn(n, f"Sensor {sid} deactivated.")
        d_id.value = ""
        refresh()
    del_btn.on_click(on_del)

    return pn.Column(
        pn.pane.Markdown("## 📡 Sensors", styles=SECTION_TITLE),
        pn.layout.Divider(),
        pn.Column(
            pn.Row(
                pn.Column(_lbl("Sensor ID"), f_id),
                pn.Column(_lbl("Name"), f_nm),
                pn.Column(_lbl("Location"), f_loc),
                sizing_mode="stretch_width", styles={"gap": "12px"},
            ),
            pn.Row(
                pn.Column(_lbl("Latitude"), f_lat),
                pn.Column(_lbl("Longitude"), f_lon),
                sizing_mode="stretch_width", styles={"gap": "12px"},
            ),
            pn.Row(add_btn),  
            n,         
            sizing_mode="stretch_width",
            styles=CARD, 
        ),
        pn.Column(
            pn.pane.Markdown("### Deactivate", styles={"color":"#4B51A0"}),
            pn.Row(_lbl("Sensor ID"), d_id, del_btn, styles={"gap":"14px","align-items":"flex-end"}),
            styles=CARD,
        ),
        pn.Column(pn.pane.Markdown("### All Sensors", styles={"color":"#4B51A0"}), th, styles=CARD),
        sizing_mode="stretch_width",
    )


def _api_keys_tab():
    n = _notice()
    th = pn.Column(sizing_mode="stretch_width")

    def refresh():
        data = list_api_keys()
        for r in data: r["user_hash"] = r["user_hash"][:6] + "••••••"
        th.objects = [_table(data, ["id","label","user_id","user_hash","api_url","is_active","created_at"])]
    refresh()

    f_lbl  = pn.widgets.TextInput(placeholder="Label",       sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_uid  = pn.widgets.TextInput(placeholder="X-User-id",   sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_hash = pn.widgets.PasswordInput(placeholder="X-User-hash", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_url  = pn.widgets.TextInput(placeholder="https://...", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    add_btn = pn.widgets.Button(name="➕ Add", button_type="primary", stylesheets=[_btn()])

    def on_add(e):
        n.object = ""
        if not all([f_lbl.value, f_uid.value, f_hash.value, f_url.value]):
            return _err(n, "All fields required.")
        add_api_key(f_lbl.value.strip(), f_uid.value.strip(), f_hash.value.strip(), f_url.value.strip())
        _ok(n, f"Key **{f_lbl.value}** added.")
        for w in (f_lbl, f_uid, f_hash, f_url): w.value = ""
        refresh()
    add_btn.on_click(on_add)

    t_id = pn.widgets.IntInput(placeholder="1", width=120, stylesheets=[INPUT_CSS])
    tog  = pn.widgets.Button(name="⏸ Toggle", stylesheets=[_btn("#F59E0B")])
    dl   = pn.widgets.Button(name="🗑 Delete", stylesheets=[_btn("#EF4444")])

    def on_tog(e):
        kid = t_id.value
        if not kid: return
        keys = {k["id"]: k for k in list_api_keys()}
        if kid in keys:
            toggle_api_key(kid, not bool(keys[kid]["is_active"]))
            _warn(n, f"Key {kid} toggled.")
            refresh()

    def on_del(e):
        kid = t_id.value
        if not kid: return
        delete_api_key(kid)
        _err(n, f"Key {kid} deleted.")
        refresh()

    tog.on_click(on_tog)
    dl.on_click(on_del)

    return pn.Column(
        pn.pane.Markdown("## 🔑 API Keys", styles=SECTION_TITLE),
        pn.layout.Divider(),
        pn.Column(
            pn.Row(
                pn.Column(_lbl("Label"),   f_lbl),
                pn.Column(_lbl("API URL"), f_url),
                sizing_mode="stretch_width", styles={"gap": "12px"},
            ),
            pn.Row(
                pn.Column(_lbl("User ID"),   f_uid),
                pn.Column(_lbl("User Hash"), f_hash),
                sizing_mode="stretch_width", styles={"gap": "12px"},
            ),
            sizing_mode="stretch_width",
        ),
        pn.Column(
            pn.pane.Markdown("### Manage by ID", styles={"color":"#4B51A0"}),
            pn.Row(_lbl("Key ID"), t_id, tog, dl, styles={"gap":"12px","align-items":"flex-end"}),
            styles=CARD,
        ),
        pn.Column(pn.pane.Markdown("### All Keys", styles={"color":"#4B51A0"}), th, styles=CARD),
        sizing_mode="stretch_width",
    )


def _configs_tab():
    n = _notice()
    th = pn.Column(sizing_mode="stretch_width")

    def refresh():
        th.objects = [_table(list_configs(), ["key","value","description","updated_at"])]
    refresh()

    PRESETS = {
        "map_refresh_ms":   ("300000", "Live map refresh interval (ms)"),
        "chart_max_points": ("500",    "Max chart data-points"),
        "alert_temp_max":   ("35",     "Temperature alert threshold °C"),
        "alert_pm25_max":   ("150",    "PM2.5 alert threshold µg/m³"),
        "default_location": ("Centru", "Default location on load"),
    }

    p_sel = pn.widgets.Select(
        options=["— preset —"] + list(PRESETS.keys()),
        sizing_mode="stretch_width", stylesheets=[INPUT_CSS],
    )
    f_key  = pn.widgets.TextInput(placeholder="key",         sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_val  = pn.widgets.TextInput(placeholder="value",       sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_desc = pn.widgets.TextInput(placeholder="description", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    save   = pn.widgets.Button(name="💾 Save", button_type="primary", stylesheets=[_btn()])

    def on_preset(e):
        key = e.new
        if key in PRESETS:
            f_key.value, f_val.value, f_desc.value = key, PRESETS[key][0], PRESETS[key][1]
    p_sel.param.watch(on_preset, "value")

    def on_save(e):
        if not f_key.value or not f_val.value:
            return _err(n, "Key and Value required.")
        set_config(f_key.value.strip(), f_val.value.strip(), f_desc.value.strip())
        _ok(n, f"Config **{f_key.value}** saved.")
        for w in (f_key, f_val, f_desc): w.value = ""
        refresh()
    save.on_click(on_save)

    return pn.Column(
        pn.pane.Markdown("## ⚙ App Configuration", styles=SECTION_TITLE),
        pn.layout.Divider(),
        pn.Column(
            pn.pane.Markdown("### Set / Update Config", styles={"color":"#4B51A0"}),
            pn.Row(_lbl("Quick preset"), p_sel, sizing_mode="stretch_width"),
            pn.Row(
            pn.Column(_lbl("Key"),         f_key),
            pn.Column(_lbl("Value"),       f_val),
            pn.Column(_lbl("Description"), f_desc),
            sizing_mode="stretch_width", styles={"gap": "12px"},
        ),
            pn.Row(save), n, styles=CARD,
        ),
        pn.Column(pn.pane.Markdown("### Current Configs", styles={"color":"#4B51A0"}), th, styles=CARD),
        sizing_mode="stretch_width",
    )


def _users_tab():
    n = _notice()
    th = pn.Column(sizing_mode="stretch_width")

    def refresh():
        th.objects = [_table(list_users(), ["id","username","role","created_at","is_active"])]
    refresh()

    f_usr  = pn.widgets.TextInput(placeholder="username",    sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_pwd  = pn.widgets.PasswordInput(placeholder="password", sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    f_role = pn.widgets.Select(options=["viewer","admin"], value="viewer",
                               sizing_mode="stretch_width", stylesheets=[INPUT_CSS])
    add_btn = pn.widgets.Button(name="➕ Create User", button_type="primary", stylesheets=[_btn()])

    def on_add(e):
        u, p, r = f_usr.value.strip(), f_pwd.value.strip(), f_role.value
        if not u or not p: return _err(n, "Username and password required.")
        if len(p) < 8:    return _err(n, "Password must be at least 8 characters.")
        res = create_user(u, p, r)
        if res["ok"]:
            _ok(n, f"User **{u}** created as `{r}`.")
            f_usr.value = f_pwd.value = ""
            refresh()
        else:
            _err(n, res["error"])
    add_btn.on_click(on_add)

    u_id = pn.widgets.IntInput(placeholder="1", width=100, stylesheets=[INPUT_CSS])
    r_sel = pn.widgets.Select(options=["viewer","admin"], value="viewer", width=120, stylesheets=[INPUT_CSS])
    r_btn = pn.widgets.Button(name="✏ Change Role", stylesheets=[_btn()])
    d_btn = pn.widgets.Button(name="🗑 Deactivate",  stylesheets=[_btn("#EF4444")])

    def on_role(e):
        uid = u_id.value
        if not uid: return
        update_user_role(uid, r_sel.value)
        _ok(n, f"User {uid} → `{r_sel.value}`")
        refresh()

    def on_deact(e):
        uid = u_id.value
        if not uid: return
        delete_user(uid)
        _warn(n, f"User {uid} deactivated.")
        refresh()

    r_btn.on_click(on_role)
    d_btn.on_click(on_deact)

    return pn.Column(
        pn.pane.Markdown("## 👤 User Management", styles=SECTION_TITLE),
        pn.layout.Divider(),
        pn.Column(
            pn.pane.Markdown("### Create User", styles={"color":"#4B51A0"}),
            pn.Row(
                pn.Column(_lbl("Username"), f_usr),
                pn.Column(_lbl("Password"), f_pwd),
                pn.Column(_lbl("Role"),     f_role),
                sizing_mode="stretch_width", styles={"gap": "12px"},
            ),
            pn.Row(add_btn), n, styles=CARD,
        ),
        pn.Column(
            pn.pane.Markdown("### Manage by ID", styles={"color":"#4B51A0"}),
            pn.Row(_lbl("User ID"), u_id, _lbl("Role"), r_sel, r_btn, d_btn,
                   styles={"gap":"12px","align-items":"flex-end"}),
            styles=CARD,
        ),
        pn.Column(pn.pane.Markdown("### All Users", styles={"color":"#4B51A0"}), th, styles=CARD),
        sizing_mode="stretch_width",
    )


def _build_admin_panel(container: pn.Column, user: dict):
    back_btn = pn.widgets.Button(name="← Dashboard", button_type="light",
                                 stylesheets=[_btn("#FFFFFF", "#4B51A0")])
    back_btn.js_on_click(code="window.location.href='/'")

    logout_btn = pn.widgets.Button(name="Sign out", button_type="light",
                                   stylesheets=[_btn("#FEE2E2", "#EF4444")])

    def on_logout(e):
        logout()
        with pn.io.unlocked():
            container.objects = [render_login_page(
                on_success=lambda u: _swap_to_admin(container, u)
            )]
    logout_btn.on_click(on_logout)

    top_bar = pn.pane.HTML(
        f"""
        <div style="display:flex; align-items:center; gap:12px;
                    border-bottom:2px solid #EEF0FA; padding:16px 25px;
                    margin-bottom:20px; background:#fff; font-family:'DM Sans',sans-serif;border-radius: 10px">
            <span style="font-size:20px; font-weight:700; color:#2D2F3E;">🛠 Admin Panel</span>
            <span style="flex:1;"></span>
            <span style="color:#7B82B4; font-size:13px; white-space:nowrap;">
                👤 <b>{user['username']}</b> · <code style="font-family:'DM Mono',monospace">{user['role']}</code>
            </span>
            <a href="/" style="font-family:'DM Sans',sans-serif; font-size:13px; font-weight:600;
                border-radius:8px; border:1.5px solid #4B51A0; background:#fff; color:#4B51A0;
                padding:7px 18px; cursor:pointer; text-decoration:none;">← Dashboard</a>
                <button onclick="window.location.href='/logout'"
                    style="font-family:'DM Sans',sans-serif; font-size:13px; font-weight:600;
                    border-radius:8px; border:1.5px solid #FCA5A5; background:#FEE2E2; color:#EF4444;
                    padding:7px 18px; cursor:pointer;">Sign out</button>
        </div>
        """,
        sizing_mode="stretch_width",
    )
    tabs = pn.Tabs(
        ("📡 Sensors",  _sensors_tab()),
        ("🔑 API Keys", _api_keys_tab()),
        ("⚙ Configs",  _configs_tab()),
        ("👤 Users",    _users_tab()),
        sizing_mode="stretch_width",
        stylesheets=["""
            .bk-tab { font-family:'DM Sans',sans-serif!important; font-size:13px!important;
                      font-weight:600!important; color:#7B82B4!important;
                      border-radius:8px 8px 0 0!important; padding:8px 20px!important; }
            .bk-tab.bk-active { color:#4B51A0!important; border-bottom:2px solid #6366F1!important; }
        """],
    )

    with pn.io.unlocked():                     
        container.objects = [pn.Column(
            top_bar,
            tabs,
            sizing_mode="stretch_width",
            styles={"max-width":"1200px","margin":"0 auto",
                    "padding":"28px 24px","background":"#F7F8FC"},
        )]


def _swap_to_admin(container: pn.Column, user: dict):
    if user.get("role") != "admin":
        with pn.io.unlocked():                 
            container.objects = [pn.pane.Markdown(
                "## 🚫 Access Denied\nAi nevoie de privilegii **admin**.",
                styles={"color":"#EF4444","padding":"80px 40px",
                        "font-family":"'DM Sans',sans-serif","text-align":"center"},
            )]
        return
    _build_admin_panel(container, user)



def render_admin_page() -> pn.viewable.Viewable:
    pn.extension('tabulator')
    pn.config.raw_css.append(FONT_IMPORT + GLOBAL_CSS)

    user = current_user()

    if user is None:
        return pn.pane.HTML(
            '<script>window.location.href = "/login";</script>',
            width=0, height=0, margin=0,
        )

    if user.get("role") != "admin":
        return pn.pane.HTML(
            '<script>window.location.href = "/";</script>',
            width=0, height=0, margin=0,
        )

    container = pn.Column(
        sizing_mode="stretch_width",
        styles={"background": "#F7F8FC", "min-height": "100vh"},
    )
    _build_admin_panel(container, user)
    return container