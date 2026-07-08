import os
import panel as pn
from flask import Flask
from flask_cors import CORS
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler, RequestHandler
from flask_apscheduler import APScheduler

from configs.routes.v1.render_home  import render_home_page
from configs.routes.v1.render_admin import render_admin_page
from configs.routes.v1.data_ingest  import data_ingest_bp

from frontend.panel_app      import render_dashboard_page
from frontend.admin          import render_admin_page as panel_admin_page
from frontend.user_settings  import render_settings_page
from auth import login, _sessions, COOKIE_NAME, COOKIE_MAX_AGE


def my_job():
    print("Running at 10:45 Romanian time!")


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Sign In · AirQuality</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=DM+Mono&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'DM Sans', sans-serif;
      background: #F7F8FC;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 32px rgba(75,81,160,0.10);
      padding: 40px 36px;
      width: 100%;
      max-width: 400px;
    }
    .brand {
      text-align: center;
      font-size: 26px;
      font-weight: 700;
      color: #2D2F3E;
      margin-bottom: 4px;
    }
    .subtitle {
      text-align: center;
      color: #7B82B4;
      font-size: 14px;
      margin-bottom: 28px;
    }
    label {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: #5A5F94;
      margin-bottom: 4px;
      font-weight: 600;
    }
    input {
      display: block;
      width: 100%;
      font-family: 'DM Mono', monospace;
      font-size: 13px;
      border: 1.5px solid #E0E4F5;
      border-radius: 8px;
      padding: 9px 12px;
      background: #F7F8FC;
      color: #2D2F3E;
      margin-bottom: 16px;
      outline: none;
      transition: border-color .15s;
    }
    input:focus { border-color: #6366F1; background: #fff; }
    .error {
      color: #EF4444;
      font-size: 13px;
      margin-bottom: 12px;
      min-height: 18px;
    }
    button[type=submit] {
      width: 100%;
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      font-weight: 600;
      border-radius: 10px;
      background: linear-gradient(135deg, #6366F1 0%, #4B51A0 100%);
      color: #fff;
      border: none;
      padding: 11px 0;
      cursor: pointer;
      transition: opacity .15s;
    }
    button[type=submit]:hover { opacity: 0.88; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand">🌿 AirQuality</div>
    <div class="subtitle">Sign in to your account</div>
    {error_block}
    <form method="POST" action="/login">
      <label for="username">Username</label>
      <input id="username" name="username" type="text" placeholder="username" autocomplete="username" required/>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" placeholder="••••••••" autocomplete="current-password" required/>
      <button type="submit">Sign in</button>
    </form>
  </div>
</body>
</html>"""


class LoginHandler(RequestHandler):
    def get(self):
        token = self.get_cookie(COOKIE_NAME)
        if token and token in _sessions:
            self.redirect("/dashboard")
            return
        self.finish(LOGIN_HTML.replace("{error_block}", ""))

    def post(self):
        username = self.get_argument("username", "").strip()
        password = self.get_argument("password", "").strip()
        user, token = login(username, password)
        if user and token:
            self.set_cookie(
                COOKIE_NAME, token,
                max_age=COOKIE_MAX_AGE,
                path="/",
                httponly=True,
            )
            dest = "/admin-panel" if user.get("role") == "admin" else "/settings"
            self.redirect(dest)
        else:
            error = '<div class="error">⚠ Invalid username or password.</div>'
            self.finish(LOGIN_HTML.replace("{error_block}", error))

class LogoutHandler(RequestHandler):
    def get(self):
        token = self.get_cookie(COOKIE_NAME)
        if token:
            _sessions.pop(token, None)
        self.clear_cookie(COOKIE_NAME, path="/")
        self.redirect("/dashboard")

    post = get


def create_flask_app():
    app = Flask(__name__)

    app.config["SCHEDULER_API_ENABLED"]  = False
    app.config["SCHEDULER_JOB_DEFAULTS"] = {"coalesce": True, "max_instances": 1}

    scheduler = APScheduler()
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @scheduler.task("cron", id="daily_task", hour=10, minute=45, timezone="Europe/Bucharest")
    def scheduled_job():
        with scheduler.app.app_context():
            my_job()

    scheduler.init_app(app)
    scheduler.start()

    app.register_blueprint(render_home_page,  url_prefix="/")
    app.register_blueprint(render_admin_page, url_prefix="/admin")
    app.register_blueprint(data_ingest_bp,    url_prefix="/api/v1")

    return app


flask_app = create_flask_app()



def run_server():
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Server on port {port}...")

    server = pn.serve(
        {
            "/dashboard":   render_dashboard_page,
            "/admin-panel": panel_admin_page,
            "/settings":    render_settings_page,
        },
        port=port,
        address="0.0.0.0",
        websocket_origin=["*"],
        show=False,
        start=False,
    )

    tornado_app    = server._tornado
    wsgi_container = WSGIContainer(flask_app)

    PANEL_PREFIXES = ["/dashboard", "/admin-panel", "/settings", "/static", "/_root_"]
    exclusion = "|".join(PANEL_PREFIXES)

    tornado_app.add_handlers(r".*", [
        (r"^/login$",  LoginHandler),
        (r"^/logout$", LogoutHandler),
        (rf"^(?!{exclusion}).*", FallbackHandler, dict(fallback=wsgi_container)),
    ])

    server.start()
    server.io_loop.start()


if __name__ == "__main__":
    run_server()