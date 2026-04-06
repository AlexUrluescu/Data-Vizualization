import os
import panel as pn
from flask import Flask, redirect, make_response
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
from auth import current_user, render_login_page, _sessions, COOKIE_NAME


def my_job():
    print("Running at 10:45 Romanian time!")

class LogoutHandler(RequestHandler):
    def get(self):
        token = self.get_cookie(COOKIE_NAME)
        if token:
            _sessions.pop(token, None)         
        self.clear_cookie(COOKIE_NAME, path="/") 
        self.redirect("/")

   
    post = get


# ── Flask app ─────────────────────────────────────────────────
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


# ── Panel + Tornado server ────────────────────────────────────
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
        # /logout is intercepted by Tornado BEFORE Flask fallback
        (r"^/logout$", LogoutHandler),
        (rf"^(?!{exclusion}).*", FallbackHandler, dict(fallback=wsgi_container)),
    ])

    server.start()
    server.io_loop.start()


if __name__ == "__main__":
    run_server()