from flask import Flask
from flask_cors import CORS
from app.routes.v1.car_routes import car_routes
from app.routes.v1.city_routes import city_routes
from app.routes.v1.population_routes import population_routes
from app.routes.v1.pollution_routes import pollution_routes
from app.routes.v1.ai_response import traffic_routes
from app.routes.v1.parking_spots_routes import parking_spots_routes

def create_app():
  app = Flask(__name__)
  
  # Allow all headers & methods for CORS
  CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

  # Register routes
  app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
  app.register_blueprint(city_routes, url_prefix='/api/v1/cities')
  app.register_blueprint(population_routes, url_prefix='/api/v1/population')
  app.register_blueprint(pollution_routes, url_prefix='/api/v1/pollution')
  app.register_blueprint(traffic_routes, url_prefix="/api/v1/traffic-chat-bot")
  app.register_blueprint(parking_spots_routes, url_prefix='/api/v1/parking_spots')

  return app