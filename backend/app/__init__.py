from flask import Flask
from flask_cors import CORS
from app.routes.v1.car_routes import car_routes
from app.routes.v1.city_routes import city_routes

def create_app():
  app = Flask(__name__)
  CORS(app)

  # Register routes
  app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
  app.register_blueprint(city_routes, url_prefix='/api/v1/cities')

  # Allow all headers & methods
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Origin', '*')
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
      return response

  return app