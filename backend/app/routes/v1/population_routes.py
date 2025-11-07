from pyexpat import errors
from flask import Blueprint, jsonify, request
from bson import ObjectId
from app.config import Config
from app.models.helpers import convert_objectid

population_routes = Blueprint("population_routes", __name__)
db = Config.get_db()
population_collection = db["population"]
cities_collection = db["cities"]

@population_routes.route("/", methods=["GET"])
def get_population():
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
            except (errors.InvalidId, TypeError):
                return jsonify({"error": "Invalid cityId"}), 400
        if year:
            try:
                query["year"] = int(year)
            except ValueError:
                return jsonify({"error": "Year must be an integer"}), 400

        # Fetch population data
        population_cursor = population_collection.find(query)
        population = [convert_objectid(doc) for doc in population_cursor]

        # If requested, include city info
        if include_city and city_id:
            city = cities_collection.find_one({"_id": ObjectId(city_id)})
            if not city:
                return jsonify({"error": "City not found"}), 404
            response = {
                "city": convert_objectid(city),
                "cars": population
            }
            return jsonify(response), 200

        return jsonify(population), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500