from flask import Blueprint, jsonify, request
from bson import ObjectId
from bson.errors import InvalidId
from app.config import Config
from app.models.helpers import convert_objectid

parking_spots_routes = Blueprint("parking_spots_routes", __name__)
db = Config.get_db()
parking_spots_collection = db["parking_spots"]
cities_collection = db["cities"]

@parking_spots_routes.route("/", methods=["GET"])
def get_parking_spots():
    try:
        # Collect optional query params
        city_id = request.args.get("cityId")
        year = request.args.get("year")
        include_city = request.args.get("includeCity", "false").lower() == "true"

        # Build MongoDB query dynamically
        query = {}
        if city_id:
            try:
                query["cityId"] = ObjectId(city_id)
            except (InvalidId, TypeError):
                return jsonify({"error": "Invalid cityId"}), 400
        if year:
            try:
                query["year"] = int(year)
            except ValueError:
                return jsonify({"error": "Year must be an integer"}), 400

        # Fetch cars
        parking_spots_cursor = parking_spots_collection.find(query)
        parking_spots = [convert_objectid(doc) for doc in parking_spots_cursor]

        # If requested, include city info
        if include_city and city_id:
            city = cities_collection.find_one({"_id": ObjectId(city_id)})
            if not city:
                return jsonify({"error": "City not found"}), 404
            response = {
                "city": convert_objectid(city),
                "parking_spots": parking_spots
            }
            return jsonify(response), 200

        return jsonify(parking_spots), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500