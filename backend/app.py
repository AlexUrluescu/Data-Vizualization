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

# Import your Panel pages
from frontend.panel_app import render_dashboard_page, render_admin_page as panel_admin_page

def create_flask_app():
    app = Flask(__name__)
    
    # Update CORS to allow the Render domain if needed, or keep as is
    CORS(app, resources={r"/api/*": {"origins": "*"}}) 

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

# Initialize Flask
flask_app = create_flask_app()

def run_server():
    # 1. Get the PORT from Render (defaults to 5001 locally)
    port = int(os.environ.get("PORT", 5001))
    
    # 2. Get the public URL to allow WebSocket connections
    # On Render, this is set automatically. Locally, we default to localhost.
    public_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
    
    # 3. Define allowed origins
    allow_origins = [
        public_url, 
        f"{public_url}:{port}", 
        "127.0.0.1", 
        "127.0.0.1:5001",
        "localhost", 
        "localhost:5001"
    ]

    print(f"🚀 Starting Server on port {port}...")
    print(f"🌍 Allowed WebSocket Origins: {allow_origins}")

    # 4. Serve BOTH Flask and Panel on the same port
    pn.serve(
        {
            '/': flask_app,                # Flask handles the root
            '/dashboard': render_dashboard_page, # Panel handles /dashboard
            '/admin-panel': panel_admin_page     # Panel handles /admin-panel
        },
        port=port,
        address="0.0.0.0",
        allow_websocket_origin=allow_origins,
        show=False,
        threaded=True # Use threading to handle requests efficiently
    )

if __name__ == '__main__':
    run_server()