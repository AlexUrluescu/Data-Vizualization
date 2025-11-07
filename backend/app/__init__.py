from flask import Flask
from flask_cors import CORS
from app.routes.v1.car_routes import car_routes
from app.routes.v1.city_routes import city_routes

def create_app():
  app = Flask(__name__)
  CORS(app)

  # Allow all headers & methods for CORS
  CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

  # Register routes
  app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
  app.register_blueprint(city_routes, url_prefix='/api/v1/cities')

  return app