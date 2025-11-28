from flask import Flask
from flask_cors import CORS
from app.routes.v1.car_routes import car_routes
from app.routes.v1.render_home import render_home_page
from app.routes.v1.render_admin import render_admin_page
from app.routes.v1.city_routes import city_routes
from app.routes.v1.population_routes import population_routes
from app.routes.v1.pollution_routes import pollution_routes
from app.routes.v1.ai_response import traffic_routes
from app.routes.v1.parking_spots_routes import parking_spots_routes
from app.routes.v1.home_ai_response import traffic_routes_home

def create_app():
  app = Flask(__name__)
  
  CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "https://data-vizualization-hkr3.vercel.app", "https://data-vizualization-hkr3-git-development-alexurluescus-projects.vercel.app"]}})

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


app = create_app()

if __name__ == '__main__':
    app.run(port=5001, debug=True, use_reloader=False)