from pyexpat import errors
from flask import Blueprint, jsonify, request
from bson import ObjectId
from app.config import Config
from app.models.helpers import convert_objectid

city_routes = Blueprint("city_routes", __name__)
db = Config.get_db()
cities_collection = db["cities"]

@city_routes.route("/", methods=["GET"])
def get_cities():
    try:
        # Optional query parameter
        city_id = request.args.get("cityId")

        # Build query dynamically
        query = {}
        if city_id:
            try:
                query["_id"] = ObjectId(city_id)
            except (errors.InvalidId, TypeError):
                return jsonify({"error": "Invalid cityId"}), 400

        # Fetch cities from MongoDB
        cities_cursor = cities_collection.find(query)
        cities = [convert_objectid(doc) for doc in cities_cursor]

        # If cityId is provided and no city found
        if city_id and not cities:
            return jsonify({"error": "City not found"}), 404

        return jsonify(cities), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500