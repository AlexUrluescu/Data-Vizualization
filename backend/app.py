
import os
import functools
import panel as pn
from flask import Flask, request, jsonify
from flask_cors import CORS
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler
from configs.routes.v1.render_home import render_home_page
from configs.routes.v1.render_admin import render_admin_page
from flask_apscheduler import APScheduler

from frontend.panel_app import render_dashboard_page

# ── Import nou: auth + admin panel ───────────────────────────
from auth import current_user, render_login_page
from frontend.admin import render_admin_page as panel_admin_page
from db import validate_api_secret


def require_api_secret(f):
    """Decorator — protects a Flask route with ?secret= query param validation.
    Apply only to REST API endpoints that need it. Never used on Panel or public routes."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        secret = request.args.get("secret", "")
        if not validate_api_secret(secret):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


def my_job():
    print("Running at 10:45 Romanian time!")


# ── Admin panel cu guard de autentificare ─────────────────────

# ── Flask app ─────────────────────────────────────────────────
def create_flask_app():
    app = Flask(__name__)

    app.config["SCHEDULER_API_ENABLED"] = False
    app.config["SCHEDULER_JOB_DEFAULTS"] = {"coalesce": True, "max_instances": 1}

    scheduler = APScheduler()
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @scheduler.task("cron", id="daily_task", hour=10, minute=45, timezone="Europe/Bucharest")
    def scheduled_job():
        with scheduler.app.app_context():
            my_job()

    scheduler.init_app(app)
    scheduler.start()

    app.register_blueprint(render_home_page,        url_prefix="/")
    app.register_blueprint(render_admin_page,       url_prefix="/admin")

    return app


flask_app = create_flask_app()

def run_server():

    port = int(os.environ.get("PORT", 7860))

    print(f"🚀 Starting Server on port {port}...")

    server = pn.serve(
        {
            "/dashboard":   render_dashboard_page,
            "/admin-panel": panel_admin_page,   
        },
        port=port,
        address="0.0.0.0",
        websocket_origin=["*"], 
        show=False,
        start=False,
    )

    tornado_app    = server._tornado
    wsgi_container = WSGIContainer(flask_app)

    tornado_app.add_handlers(r".*", [
        (r"^(?!/dashboard|/admin-panel|/static).*",
         FallbackHandler, dict(fallback=wsgi_container))
    ])

    server.start()
    server.io_loop.start()

if __name__ == '__main__':
    run_server()