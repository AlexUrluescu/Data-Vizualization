from flask import Flask, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

# Flask app setup
app = Flask(__name__)

# MongoDB connection
uri = "mongodb+srv://alexurluescu23_db_user:y8MDoUisyGf2Gayo@cluster0.c9gvi0h.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

# Choose the database and collection
db_name = "urbanbike"
collection_name = "cities"
db = client[db_name]
collection = db[collection_name]

# Helper: recursively convert ObjectIds to strings
def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

# Routes
@app.route("/getCities", methods=["GET"])
def get_cities():
    try:
        cities_cursor = collection.find()
        cities = [convert_objectid(doc) for doc in cities_cursor]
        return jsonify(cities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask
if __name__ == "__main__":
    app.run(debug=True)
