from flask import Flask
from flask_cors import CORS
from app.routes.v1.car_routes import car_routes
from app.routes.v1.city_routes import city_routes
from app.routes.v1.population_routes import population_routes

def create_app():
  app = Flask(__name__)
  
  # app.url_map.strict_slashes = False

  # Allow all headers & methods for CORS
  CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

  # Register routes
  app.register_blueprint(car_routes, url_prefix='/api/v1/cars')
  app.register_blueprint(city_routes, url_prefix='/api/v1/cities')
  app.register_blueprint(population_routes, url_prefix='/api/v1/population')
  
  # for bp, prefix in [
  #   (car_routes, '/api/v1/cars'),
  #   (city_routes, '/api/v1/cities'),
  #   (population_routes, '/api/v1/population')
  # ]:
  #   bp.strict_slashes = False
  #   app.register_blueprint(bp, url_prefix=prefix)


  return app