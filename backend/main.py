from flask import Flask, jsonify, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

# ---------------------------
# Flask app setup
# ---------------------------
app = Flask(__name__)

# ---------------------------
# MongoDB connection
# ---------------------------
uri = "mongodb+srv://alexurluescu23_db_user:y8MDoUisyGf2Gayo@cluster0.c9gvi0h.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

db_name = "urbanbike"
db = client[db_name]

cars_collection = db["cars"]
cities_collection = db["cities"]


# ---------------------------
# Helper: convert ObjectId to str recursively
# ---------------------------
def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


# ---------------------------
# Endpoints
# ---------------------------

# 1. Get all cities
@app.route("/getCities", methods=["GET"])
def get_cities():
    try:
        cities_cursor = cities_collection.find()
        cities = [convert_objectid(doc) for doc in cities_cursor]
        return jsonify(cities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 2. Get all cars
@app.route("/getCars", methods=["GET"])
def get_cars():
    try:
        cars_cursor = cars_collection.find()
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. Get cars by city ID
@app.route("/getCarsByCityId", methods=["GET"])
def get_cars_by_city():
    try:
        city_id = request.args.get("cityId")
        if not city_id:
            return jsonify({"error": "cityId query parameter is required"}), 400
        cars_cursor = cars_collection.find({"cityId": city_id})
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 4. Get cars by year
@app.route("/getCarsByYear", methods=["GET"])
def get_cars_by_year():
    try:
        year = request.args.get("year")
        if not year:
            return jsonify({"error": "year query parameter is required"}), 400
        cars_cursor = cars_collection.find({"year": int(year)})
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 5. Get cars by city ID and year
@app.route("/getCarsByCityAndYear", methods=["GET"])
def get_cars_by_city_and_year():
    try:
        city_id = request.args.get("cityId")
        year = request.args.get("year")
        if not city_id or not year:
            return jsonify({"error": "cityId and year query parameters are required"}), 400

        cars_cursor = cars_collection.find({"cityId": city_id, "year": int(year)})
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 6. Get cars with city info (name + region) by cityId
@app.route("/getCarsWithCityInfo", methods=["GET"])
def get_cars_with_city_info():
    try:
        city_id = request.args.get("cityId")
        if not city_id:
            return jsonify({"error": "cityId query parameter is required"}), 400

        # Get city info
        city = cities_collection.find_one({"_id": ObjectId(city_id)})
        if not city:
            return jsonify({"error": "City not found"}), 404

        # Get cars for this city
        cars_cursor = cars_collection.find({"cityId": city_id})
        cars = [convert_objectid(doc) for doc in cars_cursor]

        response = {
            "city": convert_objectid(city),
            "cars": cars
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Run Flask
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
