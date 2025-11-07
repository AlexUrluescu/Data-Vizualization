from flask import Blueprint, jsonify
from app.config import Config
from app.models.helpers import convert_objectid

city_routes = Blueprint("city_routes", __name__)
db = Config.get_db()
cities_collection = db["cities"]

@city_routes.route("/", methods=["GET"])
def get_cities():
    try:
        cities_cursor = cities_collection.find()
        cities = [convert_objectid(doc) for doc in cities_cursor]
        return jsonify(cities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@city_routes.route("/test", methods=["GET"])
def test_cities():
    return jsonify(list(cities_collection.find())), 200

