# from flask import Flask
# from flask_cors import CORS
# from configs.routes.v1.car_routes import car_routes
# from configs.routes.v1.render_home import render_home_page
# from configs.routes.v1.render_admin import render_admin_page
# from configs.routes.v1.city_routes import city_routes
# from configs.routes.v1.population_routes import population_routes
# from configs.routes.v1.pollution_routes import pollution_routes
# from configs.routes.v1.ai_response import traffic_routes
# from configs.routes.v1.parking_spots_routes import parking_spots_routes
# from configs.routes.v1.home_ai_response import traffic_routes_home

# def create_app():
#   app = Flask(__name__)
  
#   CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "https://data-vizualization-hkr3.vercel.app", "https://data-vizualization-hkr3-git-development-alexurluescus-projects.vercel.app"]}})

#   app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
#   app.register_blueprint(city_routes, url_prefix='/api/v1/cities')
#   app.register_blueprint(population_routes, url_prefix='/api/v1/population')
#   app.register_blueprint(pollution_routes, url_prefix='/api/v1/pollution')
#   app.register_blueprint(traffic_routes, url_prefix="/api/v1/traffic-chat-bot")
#   app.register_blueprint(parking_spots_routes, url_prefix='/api/v1/parking_spots')
#   app.register_blueprint(traffic_routes_home, url_prefix="/api/v1/traffic-chat-bot-home")
#   app.register_blueprint(render_home_page, url_prefix="/")
#   app.register_blueprint(render_admin_page, url_prefix="/admin")

#   return app


# app = create_app()

# if __name__ == '__main__':
#     app.run(port=5001, debug=True, use_reloader=False)
import os
import panel as pn
from flask import Flask
from flask_cors import CORS

# Import Tornado helpers (Panel runs on Tornado)
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler

# Import your routes
from configs.routes.v1.car_routes import car_routes
from configs.routes.v1.render_home import render_home_page
from configs.routes.v1.render_admin import render_admin_page
from configs.routes.v1.city_routes import city_routes
from configs.routes.v1.population_routes import population_routes
from configs.routes.v1.pollution_routes import pollution_routes
from configs.routes.v1.ai_response import traffic_routes
from configs.routes.v1.parking_spots_routes import parking_spots_routes
from configs.routes.v1.home_ai_response import traffic_routes_home
from flask_apscheduler import APScheduler

# Import your Panel pages
from frontend.panel_app import render_dashboard_page, render_admin_page as panel_admin_page

def my_job():
    print("Running at 10:45 Romanian time!")

# 1. Create Flask App
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

    app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
    app.register_blueprint(city_routes, url_prefix='/api/v1/cities')
    app.register_blueprint(population_routes, url_prefix='/api/v1/population')
    app.register_blueprint(pollution_routes, url_prefix='/api/v1/pollution')
    app.register_blueprint(traffic_routes, url_prefix="/api/v1/traffic-chat-bot")
    app.register_blueprint(parking_spots_routes, url_prefix='/api/v1/parking_spots')
    app.register_blueprint(traffic_routes_home, url_prefix="/api/v1/traffic-chat-bot-home")
    app.register_blueprint(render_home_page, url_prefix="/")
    app.register_blueprint(render_admin_page, url_prefix="/admin")

    return app

flask_app = create_flask_app()

def run_server():
    port = int(os.environ.get("PORT", 5001))
    public_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
    
    allow_origins = [
        public_url, 
        f"{public_url}:{port}", 
        "127.0.0.1", 
        "127.0.0.1:5001",
        "localhost", 
        "localhost:5001",
        "0.0.0.0:5001"
    ]

    print(f"🚀 Starting Server on port {port}...")

    # 2. Setup Panel Server (BUT DO NOT START IT YET)
    # We only pass the Panel apps here. We do NOT pass Flask here.
    server = pn.serve(
        {
            '/dashboard': render_dashboard_page, 
            '/admin-panel': panel_admin_page    
        },
        port=port,
        address="0.0.0.0",
        allow_websocket_origin=allow_origins,
        show=False,
        start=False  # <--- Important: We pause execution here to inject Flask
    )

    # 3. Inject Flask as a Fallback
    # This logic says: "If the URL matches /dashboard, Panel handles it."
    # "If it matches ANYTHING else (.*), give it to Flask."
    tornado_app = server._tornado
    wsgi_container = WSGIContainer(flask_app)
    
    # regex: Match any URL that does NOT start with /dashboard or /admin-panel
    # This forces Tornado to skip Flask for your dashboard routes
    tornado_app.add_handlers(r".*", [
        (r"^(?!/dashboard|/admin-panel|/static).*", FallbackHandler, dict(fallback=wsgi_container))
    ])

    # 4. Start the Server Loop manually
    server.start()
    server.io_loop.start()

if __name__ == '__main__':
    run_server()