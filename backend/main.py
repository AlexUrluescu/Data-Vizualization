from flask import Flask, jsonify, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from dotenv import load_dotenv
import os

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
MONGO_DB = os.getenv("MONGO_DB")

# ---------------------------
# Flask app setup
# ---------------------------
app = Flask(__name__)

# ---------------------------
# MongoDB connection
# ---------------------------
uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?appName={MONGO_DB}"
client = MongoClient(uri, server_api=ServerApi('1'))

db = client[MONGO_DB]
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

@app.route("/getCities", methods=["GET"])
def get_cities():
    try:
        cities_cursor = cities_collection.find()
        cities = [convert_objectid(doc) for doc in cities_cursor]
        return jsonify(cities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getCars", methods=["GET"])
def get_cars():
    try:
        cars_cursor = cars_collection.find()
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route("/getCarsWithCityInfo", methods=["GET"])
def get_cars_with_city_info():
    try:
        city_id = request.args.get("cityId")
        if not city_id:
            return jsonify({"error": "cityId query parameter is required"}), 400

        city = cities_collection.find_one({"_id": ObjectId(city_id)})
        if not city:
            return jsonify({"error": "City not found"}), 404

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
