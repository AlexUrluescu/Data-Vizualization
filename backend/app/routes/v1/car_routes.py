from flask import Blueprint, jsonify, request
from bson import ObjectId
from app.config import Config
from app.models.helpers import convert_objectid

car_routes = Blueprint("car_routes", __name__)
db = Config.get_db()
cars_collection = db["cars"]
cities_collection = db["cities"]

@car_routes.route("/getCars", methods=["GET"])
def get_cars():
    try:
        cars_cursor = cars_collection.find()
        cars = [convert_objectid(doc) for doc in cars_cursor]
        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@car_routes.route("/getCarsByCityId", methods=["GET"])
def get_cars_by_city():
    try:
        city_id = request.args.get("cityId")
        print(f"city_id received: {city_id}")
        
        if not city_id:
            return jsonify({"error": "cityId query parameter is required"}), 400
        
        # Try querying with ObjectId first
        try:
            cars_cursor = cars_collection.find({"cityId": ObjectId(city_id)})
            cars = [convert_objectid(doc) for doc in cars_cursor]
            
            # If no results, try as string
            if not cars:
                print("No results with ObjectId, trying string...")
                cars_cursor = cars_collection.find({"cityId": city_id})
                cars = [convert_objectid(doc) for doc in cars_cursor]
            
            print(f"Found {len(cars)} cars")
            return jsonify(cars), 200
            
        except Exception as id_error:
            print(f"ObjectId conversion error: {id_error}")
            # Fallback to string query
            cars_cursor = cars_collection.find({"cityId": city_id})
            cars = [convert_objectid(doc) for doc in cars_cursor]
            return jsonify(cars), 200
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@car_routes.route("/getCarsByYear", methods=["GET"])
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

@car_routes.route("/getCarsByCityAndYear", methods=["GET"])
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

@car_routes.route("/getCarsWithCityInfo", methods=["GET"])
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
