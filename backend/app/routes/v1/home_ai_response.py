# # # # app/routes/traffic_routes.py
# # # from app.config import Config
# # # from flask import Blueprint, request, jsonify
# # # import os
# # # import json
# # # import requests
# # # from typing import List, Dict, Any
# # # from pymongo import MongoClient
# # # from bson import ObjectId


# # # traffic_routes_home = Blueprint("traffic_routes_home", __name__)

# # # # ========================= CONFIG =========================


# # # db = Config.get_db()
# # # # ========================= SCHEMA INFO =========================
# # # SCHEMA_INFO = """
# # # Database: urbanbike

# # # Collection 1: cities
# # # Schema:
# # # {
# # #   _id: ObjectId,
# # #   name: string,
# # #   region: string
# # # }

# # # Collection 2: cars
# # # Schema:
# # # {
# # #   _id: ObjectId,
# # #   cityId: ObjectId,  # References cities._id
# # #   year: number,
# # #   amount: number
# # # }

# # # Relationship: cars.cityId references cities._id

# # # IMPORTANT NOTES FOR QUERY GENERATION:
# # # 1. When a question references a SPECIFIC city name (e.g., "Sibiu", "in Bucharest"), use $lookup FIRST, then $match on city.name
# # # 2. When a question asks "which city" or "what city" or "top cities" (ranking queries), do NOT match a specific city name. Instead: $match year first, $group by cityId, then $lookup to get city names, $sort, and $limit
# # # 3. NEVER use {'$oid': '...'} syntax - this is invalid in PyMongo
# # # 4. For questions about specific cities, always use $lookup to match city names
# # # 5. Use aggregate pipelines for any query involving joins between collections
# # # 6. For questions comparing TWO YEARS, use $group with $cond to separate the years, then use $subtract to calculate the difference
# # # """

# # # # ========================= OLLAMA =========================
# # # def ollama_chat(
# # #     base_url: str,
# # #     model: str,
# # #     messages: List[Dict[str, str]],
# # #     temperature: float = 0.3,
# # #     timeout: int = 360000,
# # # ) -> str:
# # #     """
# # #     Calls Ollama's native /api/chat endpoint using requests.
# # #     Returns the assistant message content string.
# # #     """
# # #     print(messages)
# # #     url = f"{base_url.rstrip('/')}/api/chat"
# # #     payload = {
# # #         "model": model,
# # #         "messages": messages,
# # #         "stream": False,
# # #         "options": {
# # #             "num_ctx": 12000,
# # #             "temperature": temperature,
# # #             "top_k": 30,
# # #             "top_p": 0.9,
# # #             "num_predict": -1
# # #         }
# # #     }
# # #     resp = requests.post(url, json=payload, timeout=timeout)
# # #     resp.raise_for_status()
# # #     data = resp.json()
# # #     try:
# # #         return data["message"]["content"]
# # #     except Exception:
# # #         return f"[Unexpected response]\n{json.dumps(data, indent=2)}"

# # # def check_ollama_connection():
# # #     """Check if Ollama is running and model is available."""
# # #     try:
# # #         response = requests.get(f"{Config.OLLAMA_URL}/api/tags", timeout=5)
# # #         response.raise_for_status()
# # #         models = response.json()
        
# # #         available_models = [model['name'] for model in models.get('models', [])]
        
# # #         print(f"✅ Ollama is running")
# # #         print(f"📦 Available models: {', '.join(available_models)}\n")
        
# # #         if Config.OLLAMA_MODEL not in available_models:
# # #             print(f"⚠️  Warning: Model '{Config.OLLAMA_MODEL}' not found!")
# # #             print(f"💡 Please either:")
# # #             print(f"   1. Pull the model: ollama pull {Config.OLLAMA_MODEL}")
# # #             print(f"   2. Change OLLAMA_MODEL to one of: {', '.join(available_models)}\n")
# # #             return False
        
# # #         return True
# # #     except requests.exceptions.RequestException as e:
# # #         print(f"❌ Cannot connect to Ollama at {Config.OLLAMA_URL}")
# # #         print(f"   Make sure Ollama is running: ollama serve")
# # #         print(f"   Error: {e}\n")
# # #         return False


# # # def generate_human_response(question, results):
# # #     """Use Ollama to generate a human-friendly response."""
# # #     try:
# # #         prompt = f"""You are a helpful assistant. Based on the user's question and the data retrieved from the database, provide a clear, natural, and informative response in Romanian.

# # # User Question: {question}

# # # Database Results: {json.dumps(results, indent=2)}

# # # Generate a human-friendly response that answers the user's question based on the data. Be conversational and clear.
# # # If the results contain totals or differences, use those numbers in your response.
# # # If comparing two years, mention both years and their values, then state the difference.
# # # """
        
# # #         messages = [
# # #             {"role": "system", "content": "You are a helpful assistant that provides clear and natural responses in Romanian."},
# # #             {"role": "user", "content": prompt}
# # #         ]
        
# # #         answer = ollama_chat(
# # #             base_url=Config.OLLAMA_URL,
# # #             model=Config.OLLAMA_MODEL,
# # #             messages=messages,
# # #             temperature=0.3
# # #         )
        
# # #         if not answer:
# # #             return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."
        
# # #         return answer
# # #     except Exception as e:
# # #         print(f"Error generating response: {e}")
# # #         return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."


# # # def execute_mongodb_query(query_info):
# # #     """Execute the MongoDB query and return results."""
# # #     try:
# # #         collection_name = query_info["collection"]
# # #         operation = query_info["operation"]
# # #         query = query_info["query"]
        
# # #         collection = db[collection_name]
        
# # #         if operation == "find":
# # #             results = list(collection.find(query))
# # #         elif operation == "aggregate":
# # #             results = list(collection.aggregate(query))
# # #         elif operation == "count":
# # #             results = collection.count_documents(query)
# # #         else:
# # #             results = []
        
# # #         # Convert ObjectId to string for JSON serialization
# # #         if isinstance(results, list):
# # #             for doc in results:
# # #                 if "_id" in doc:
# # #                     doc["_id"] = str(doc["_id"])
# # #                 if "cityId" in doc:
# # #                     doc["cityId"] = str(doc["cityId"])
        
# # #         return results
# # #     except Exception as e:
# # #         print(f"Error executing query: {e}")
# # #         import traceback
# # #         traceback.print_exc()
# # #         return None

# # # def generate_mongodb_query(question):
# # #     """Use Ollama to generate a MongoDB query from natural language."""
# # #     try:
# # #         prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

# # # {SCHEMA_INFO}

# # # Question: {question}

# # # Generate a MongoDB query to answer this question. Respond with a JSON object containing:
# # # 1. "collection": the collection to query (either "cities" or "cars")
# # # 2. "operation": the operation type ("find", "aggregate", "count", etc.)
# # # 3. "query": the actual MongoDB query/pipeline as a Python list or dictionary
# # # 4. "explanation": brief explanation of what the query does

# # # CRITICAL RULES:
# # # - If the question asks about a SPECIFIC city NAME (like "in Sibiu", "cars in București"), you MUST use "aggregate" with $lookup FIRST, then $match with city.name
# # # - If the question asks "WHICH city" or "WHAT city" or "TOP cities" (ranking/comparison), do NOT filter by city name. Instead: $match year → $group by cityId → $lookup cities → $sort → $limit
# # # - NEVER use {{"$oid": "..."}} syntax - use direct ObjectId values or $lookup for joins
# # # - For single year queries, use this pattern:
# # #   {{
# # #     "collection": "cars",
# # #     "operation": "aggregate",
# # #     "query": [
# # #       {{
# # #         "$lookup": {{
# # #           "from": "cities",
# # #           "localField": "cityId",
# # #           "foreignField": "_id",
# # #           "as": "city"
# # #         }}
# # #       }},
# # #       {{"$unwind": "$city"}},
# # #       {{
# # #         "$match": {{
# # #           "city.name": "CityName",
# # #           "year": YearNumber
# # #         }}
# # #       }},
# # #       {{
# # #         "$group": {{
# # #           "_id": null,
# # #           "total": {{"$sum": "$amount"}}
# # #         }}
# # #       }}
# # #     ]
# # #   }}

# # # - For COMPARING TWO YEARS (e.g., "difference between 2022 and 2014"), use this pattern:
# # #   {{
# # #     "collection": "cars",
# # #     "operation": "aggregate",
# # #     "query": [
# # #       {{
# # #         "$lookup": {{
# # #           "from": "cities",
# # #           "localField": "cityId",
# # #           "foreignField": "_id",
# # #           "as": "city"
# # #         }}
# # #       }},
# # #       {{"$unwind": "$city"}},
# # #       {{
# # #         "$match": {{
# # #           "city.name": "CityName",
# # #           "year": {{"$in": [Year1, Year2]}}
# # #         }}
# # #       }},
# # #       {{
# # #         "$group": {{
# # #           "_id": null,
# # #           "year1_total": {{
# # #             "$sum": {{
# # #               "$cond": [{{"$eq": ["$year", Year1]}}, "$amount", 0]
# # #             }}
# # #           }},
# # #           "year2_total": {{
# # #             "$sum": {{
# # #               "$cond": [{{"$eq": ["$year", Year2]}}, "$amount", 0]
# # #             }}
# # #           }}
# # #         }}
# # #       }},
# # #       {{
# # #         "$project": {{
# # #           "_id": 0,
# # #           "year1": Year1,
# # #           "year1_total": "$year1_total",
# # #           "year2": Year2,
# # #           "year2_total": "$year2_total",
# # #           "difference": {{"$subtract": ["$year1_total", "$year2_total"]}}
# # #         }}
# # #       }}
# # #     ]
# # #   }}

# # # - For RANKING/TOP queries (e.g., "which city has the most cars in 2022?", "top 5 cities"), use this pattern:
# # #   {{
# # #     "collection": "cars",
# # #     "operation": "aggregate",
# # #     "query": [
# # #       {{
# # #         "$match": {{
# # #           "year": YearNumber
# # #         }}
# # #       }},
# # #       {{
# # #         "$group": {{
# # #           "_id": "$cityId",
# # #           "total": {{"$sum": "$amount"}}
# # #         }}
# # #       }},
# # #       {{
# # #         "$lookup": {{
# # #           "from": "cities",
# # #           "localField": "_id",
# # #           "foreignField": "_id",
# # #           "as": "city"
# # #         }}
# # #       }},
# # #       {{"$unwind": "$city"}},
# # #       {{
# # #         "$project": {{
# # #           "_id": 0,
# # #           "city": "$city.name",
# # #           "region": "$city.region",
# # #           "total": "$total"
# # #         }}
# # #       }},
# # #       {{
# # #         "$sort": {{"total": -1}}
# # #       }},
# # #       {{
# # #         "$limit": 1
# # #       }}
# # #     ]
# # #   }}

# # # IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks, no additional text.

# # # Example response for "Which city has the most cars in 2022?" or "care este orasul cu cele mai multe masini in anul 2022?":
# # # {{
# # #   "collection": "cars",
# # #   "operation": "aggregate",
# # #   "query": [
# # #     {{
# # #       "$match": {{
# # #         "year": 2022
# # #       }}
# # #     }},
# # #     {{
# # #       "$group": {{
# # #         "_id": "$cityId",
# # #         "total": {{"$sum": "$amount"}}
# # #       }}
# # #     }},
# # #     {{
# # #       "$lookup": {{
# # #         "from": "cities",
# # #         "localField": "_id",
# # #         "foreignField": "_id",
# # #         "as": "city"
# # #       }}
# # #     }},
# # #     {{"$unwind": "$city"}},
# # #     {{
# # #       "$project": {{
# # #         "_id": 0,
# # #         "city": "$city.name",
# # #         "region": "$city.region",
# # #         "total": "$total"
# # #       }}
# # #     }},
# # #     {{
# # #       "$sort": {{"total": -1}}
# # #     }},
# # #     {{
# # #       "$limit": 1
# # #     }}
# # #   ],
# # #   "explanation": "This query filters for year 2022, groups by cityId to sum totals, joins with cities to get names, sorts by total descending, and returns the top city"
# # # }}

# # # Example response for "What is the difference between 2022 and 2014 in Sibiu?":
# # # {{
# # #   "collection": "cars",
# # #   "operation": "aggregate",
# # #   "query": [
# # #     {{
# # #       "$lookup": {{
# # #         "from": "cities",
# # #         "localField": "cityId",
# # #         "foreignField": "_id",
# # #         "as": "city"
# # #       }}
# # #     }},
# # #     {{"$unwind": "$city"}},
# # #     {{
# # #       "$match": {{
# # #         "city.name": "Sibiu",
# # #         "year": {{"$in": [2022, 2014]}}
# # #       }}
# # #     }},
# # #     {{
# # #       "$group": {{
# # #         "_id": null,
# # #         "total_2022": {{
# # #           "$sum": {{
# # #             "$cond": [{{"$eq": ["$year", 2022]}}, "$amount", 0]
# # #           }}
# # #         }},
# # #         "total_2014": {{
# # #           "$sum": {{
# # #             "$cond": [{{"$eq": ["$year", 2014]}}, "$amount", 0]
# # #           }}
# # #         }}
# # #       }}
# # #     }},
# # #     {{
# # #       "$project": {{
# # #         "_id": 0,
# # #         "year_2022": 2022,
# # #         "total_2022": "$total_2022",
# # #         "year_2014": 2014,
# # #         "total_2014": "$total_2014",
# # #         "difference": {{"$subtract": ["$total_2022", "$total_2014"]}}
# # #       }}
# # #     }}
# # #   ],
# # #   "explanation": "This query joins cars with cities, filters for Sibiu in years 2022 and 2014, groups data to sum amounts for each year separately using $cond, then calculates the difference (2022 - 2014)"
# # # }}
# # # """
        
# # #         messages = [
# # #             {"role": "system", "content": "You are a MongoDB query generator that responds only with valid JSON. IMPORTANT: Distinguish between 'which city has most cars' (ranking query - group by cityId first) vs 'how many cars in Sibiu' (specific city - lookup and match city.name). For comparing two years, use $group with $cond to separate the data, then $project with $subtract."},
# # #             {"role": "user", "content": prompt}
# # #         ]
        
# # #         content = ollama_chat(
# # #             base_url=Config.OLLAMA_URL,
# # #             model=Config.OLLAMA_MODEL,
# # #             messages=messages,
# # #             temperature=0
# # #         )
        
# # #         if not content:
# # #             return None
        
# # #         # Clean the response
# # #         content = content.strip()
# # #         if content.startswith("```json"):
# # #             content = content[7:]
# # #         if content.startswith("```"):
# # #             content = content[3:]
# # #         if content.endswith("```"):
# # #             content = content[:-3]
# # #         content = content.strip()
        
# # #         query_info = json.loads(content)
# # #         return query_info
# # #     except json.JSONDecodeError as e:
# # #         print(f"Error parsing JSON: {e}")
# # #         print(f"Raw response: {content}")
# # #         return None
# # #     except Exception as e:
# # #         print(f"Error generating query: {e}")
# # #         return None

# # # @traffic_routes_home.route("/ask", methods=["POST"])
# # # def ask_traffic_question():
# # #     """
# # #     POST /api/traffic/ask
# # #     {
# # #         "question": "care este diferența de mașini între azi și ieri?"
# # #     }
# # #     """
# # #     try:
# # #         data = request.get_json()
# # #         if not data or "question" not in data:
# # #             return jsonify({"error": "Lipsește câmpul 'question'"}), 400

# # #         question = data["question"].strip()
# # #         if not question:
# # #             return jsonify({"error": "Întrebarea nu poate fi goală"}), 400

# # #         print(f"\nNew question: {question}")

# # #         # 1. Generează query-ul cu AI-ul tău
# # #         query_info = generate_mongodb_query(question)
# # #         if not query_info:
# # #             return jsonify({
# # #                 "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
# # #                 "question": question
# # #             }), 400

# # #         # 2. Execută query-ul
# # #         results = execute_mongodb_query(query_info)
# # #         if results is None or (isinstance(results, list) and len(results) == 0):
# # #             return jsonify({
# # #                 "error": "Nu am găsit date pentru această întrebare.",
# # #                 "question": question
# # #             }), 404

# # #         # 3. Generează răspunsul uman
# # #         answer = generate_human_response(question, results)

# # #         # Răspuns final
# # #         return jsonify({
# # #             "question": question,
# # #             "answer": answer,
# # #             "ai_method": query_info.get("recommended_processing", "mongo"),
# # #             "raw_results": results  # opțional, pentru debug
# # #         }), 200

# # #     except Exception as e:
# # #         print(f"Eroare endpoint /ask: {e}")
# # #         import traceback
# # #         traceback.print_exc()
# # #         return jsonify({
# # #             "error": "Eroare internă la procesarea întrebării.",
# # #             "details": str(e)
# # #         }), 500




# # from app.config import Config
# # from flask import Blueprint, request, jsonify
# # import os
# # import json
# # import requests
# # from typing import List, Dict, Any
# # from pymongo import MongoClient
# # from bson import ObjectId


# # traffic_routes_home = Blueprint("traffic_routes_home", __name__)

# # # ========================= CONFIG =========================


# # db = Config.get_db()
# # # ========================= SCHEMA INFO =========================
# # SCHEMA_INFO = """
# # Database: urbanbike

# # Collection: cities
# # Schema:
# # {
# #   _id: ObjectId,
# #   name: string,
# #   region: string,
# #   carsPerYear: [
# #     {
# #       year: number,
# #       amount: number
# #     }
# #   ],
# #   populationPerYear: [
# #     {
# #       year: number,
# #       amount: number
# #     }
# #   ],
# #   parkingSpotsPerYear: [
# #     {
# #       year: number,
# #       amount: number
# #     }
# #   ]
# # }

# # IMPORTANT NOTES FOR QUERY GENERATION:
# # 1. There is ONLY ONE collection called "cities"
# # 2. All data (cars, population, parking spots) is embedded in the city document
# # 3. To get data for a specific city, use a simple find query: {"name": "CityName"}
# # 4. To get specific year data, use $filter in aggregation or filter in Python after retrieval
# # 5. To compare two years, retrieve the city document and calculate in the aggregation pipeline
# # 6. NEVER use {'$oid': '...'} syntax
# # 7. For simple queries (e.g., "how many cars in Sibiu in 2022?"), use "find" operation
# # 8. For complex queries (calculations, comparisons), use "aggregate" operation
# # """

# # # ========================= OLLAMA =========================
# # def ollama_chat(
# #     base_url: str,
# #     model: str,
# #     messages: List[Dict[str, str]],
# #     temperature: float = 0.3,
# #     timeout: int = 360000,
# # ) -> str:
# #     """
# #     Calls Ollama's native /api/chat endpoint using requests.
# #     Returns the assistant message content string.
# #     """
# #     print(messages)
# #     url = f"{base_url.rstrip('/')}/api/chat"
# #     payload = {
# #         "model": model,
# #         "messages": messages,
# #         "stream": False,
# #         "options": {
# #             "num_ctx": 12000,
# #             "temperature": temperature,
# #             "top_k": 30,
# #             "top_p": 0.9,
# #             "num_predict": -1
# #         }
# #     }
# #     resp = requests.post(url, json=payload, timeout=timeout)
# #     resp.raise_for_status()
# #     data = resp.json()
# #     try:
# #         return data["message"]["content"]
# #     except Exception:
# #         return f"[Unexpected response]\n{json.dumps(data, indent=2)}"

# # def check_ollama_connection():
# #     """Check if Ollama is running and model is available."""
# #     try:
# #         response = requests.get(f"{Config.OLLAMA_URL}/api/tags", timeout=5)
# #         response.raise_for_status()
# #         models = response.json()
        
# #         available_models = [model['name'] for model in models.get('models', [])]
        
# #         print(f"✅ Ollama is running")
# #         print(f"📦 Available models: {', '.join(available_models)}\n")
        
# #         if Config.OLLAMA_MODEL not in available_models:
# #             print(f"⚠️  Warning: Model '{Config.OLLAMA_MODEL}' not found!")
# #             print(f"💡 Please either:")
# #             print(f"   1. Pull the model: ollama pull {Config.OLLAMA_MODEL}")
# #             print(f"   2. Change OLLAMA_MODEL to one of: {', '.join(available_models)}\n")
# #             return False
        
# #         return True
# #     except requests.exceptions.RequestException as e:
# #         print(f"❌ Cannot connect to Ollama at {Config.OLLAMA_URL}")
# #         print(f"   Make sure Ollama is running: ollama serve")
# #         print(f"   Error: {e}\n")
# #         return False


# # def generate_human_response(question, city_data):
# #     """Use Ollama to generate a human-friendly response based on city data."""
# #     try:
# #         prompt = f"""You are a helpful assistant. Based on the user's question and the city data provided, provide a clear, natural, and informative response in Romanian.

# # User Question: {question}

# # CITY DATA (This is your PRIMARY SOURCE OF TRUTH):
# # {json.dumps(city_data, indent=2, ensure_ascii=False)}

# # INSTRUCTIONS:
# # 1. Use ONLY the data from CITY DATA above to answer the question
# # 2. The data structure contains:
# #    - name: city name (e.g., "Sibiu")
# #    - region: city region
# #    - carsPerYear: array of {{year, amount}} for number of cars
# #    - populationPerYear: array of {{year, amount}} for population
# #    - parkingSpotsPerYear: array of {{year, amount}} for parking spots
# # 3. When asked about a specific year, find that year in the appropriate array
# # 4. When comparing years, calculate the difference between the amounts
# # 5. Always format numbers with thousands separator (e.g., 67.200 instead of 67200)
# # 6. Be conversational, clear, and natural in Romanian
# # 7. If data for a requested year is not available, mention this politely

# # EXAMPLES:
# # - Question: "Câte mașini au fost în 2023?"
# #   → Look in carsPerYear array for year 2023, report the amount
  
# # - Question: "Care a fost evoluția populației din 2014 până în 2023?"
# #   → Look at populationPerYear array, compare 2014 vs 2023, mention the trend
  
# # - Question: "Diferența de mașini între 2022 și 2014?"
# #   → Find 2022 and 2014 in carsPerYear, calculate difference

# # Generate a natural, friendly response in Romanian based on the data.
# # """
        
# #         messages = [
# #             {"role": "system", "content": "You are a helpful assistant that provides clear and natural responses in Romanian. Always use the provided city data as your only source of truth."},
# #             {"role": "user", "content": prompt}
# #         ]
        
# #         answer = ollama_chat(
# #             base_url=Config.OLLAMA_URL,
# #             model=Config.OLLAMA_MODEL,
# #             messages=messages,
# #             temperature=0.3
# #         )
        
# #         if not answer:
# #             return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."
        
# #         return answer
# #     except Exception as e:
# #         print(f"Error generating response: {e}")
# #         return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."


# # def execute_mongodb_query(query_info):
# #     """Execute the MongoDB query and return results."""
# #     try:
# #         collection_name = query_info["collection"]
# #         operation = query_info["operation"]
# #         query = query_info["query"]
        
# #         collection = db[collection_name]
        
# #         if operation == "find":
# #             results = list(collection.find(query))
# #         elif operation == "aggregate":
# #             results = list(collection.aggregate(query))
# #         elif operation == "count":
# #             results = collection.count_documents(query)
# #         else:
# #             results = []
        
# #         # Convert ObjectId to string for JSON serialization
# #         if isinstance(results, list):
# #             for doc in results:
# #                 if "_id" in doc:
# #                     doc["_id"] = str(doc["_id"])
        
# #         return results
# #     except Exception as e:
# #         print(f"Error executing query: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return None

# # def generate_mongodb_query(question):
# #     """Use Ollama to generate a MongoDB query from natural language."""
# #     try:
# #         prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

# # {SCHEMA_INFO}

# # Question: {question}

# # Generate a MongoDB query to answer this question. Respond with a JSON object containing:
# # 1. "collection": always "cities"
# # 2. "operation": the operation type ("find" or "aggregate")
# # 3. "query": the actual MongoDB query/pipeline
# # 4. "explanation": brief explanation of what the query does

# # QUERY PATTERNS:

# # 1. SIMPLE QUERIES (single year, single metric):
# # Use "find" operation with projection:
# # {{
# #   "collection": "cities",
# #   "operation": "find",
# #   "query": {{
# #     "name": "Sibiu"
# #   }},
# #   "projection": {{
# #     "name": 1,
# #     "carsPerYear": {{
# #       "$filter": {{
# #         "input": "$carsPerYear",
# #         "as": "item",
# #         "cond": {{"$eq": ["$$item.year", 2022]}}
# #       }}
# #     }}
# #   }},
# #   "explanation": "Find Sibiu and filter carsPerYear for year 2022"
# # }}

# # 2. COMPARING TWO YEARS:
# # Use "aggregate" with $project and array filtering:
# # {{
# #   "collection": "cities",
# #   "operation": "aggregate",
# #   "query": [
# #     {{
# #       "$match": {{"name": "Sibiu"}}
# #     }},
# #     {{
# #       "$project": {{
# #         "name": 1,
# #         "year1_data": {{
# #           "$filter": {{
# #             "input": "$carsPerYear",
# #             "as": "item",
# #             "cond": {{"$eq": ["$$item.year", 2022]}}
# #           }}
# #         }},
# #         "year2_data": {{
# #           "$filter": {{
# #             "input": "$carsPerYear",
# #             "as": "item",
# #             "cond": {{"$eq": ["$$item.year", 2014]}}
# #           }}
# #         }}
# #       }}
# #     }},
# #     {{
# #       "$project": {{
# #         "name": 1,
# #         "year1": 2022,
# #         "year1_amount": {{"$arrayElemAt": ["$year1_data.amount", 0]}},
# #         "year2": 2014,
# #         "year2_amount": {{"$arrayElemAt": ["$year2_data.amount", 0]}},
# #         "difference": {{
# #           "$subtract": [
# #             {{"$arrayElemAt": ["$year1_data.amount", 0]}},
# #             {{"$arrayElemAt": ["$year2_data.amount", 0]}}
# #           ]
# #         }}
# #       }}
# #     }}
# #   ],
# #   "explanation": "Compare cars in Sibiu between 2022 and 2014"
# # }}

# # 3. MULTIPLE METRICS (cars, population, parking):
# # Use "aggregate" with multiple $filter operations:
# # {{
# #   "collection": "cities",
# #   "operation": "aggregate",
# #   "query": [
# #     {{
# #       "$match": {{"name": "Sibiu"}}
# #     }},
# #     {{
# #       "$project": {{
# #         "name": 1,
# #         "cars": {{
# #           "$filter": {{
# #             "input": "$carsPerYear",
# #             "as": "item",
# #             "cond": {{"$eq": ["$$item.year", 2023]}}
# #           }}
# #         }},
# #         "population": {{
# #           "$filter": {{
# #             "input": "$populationPerYear",
# #             "as": "item",
# #             "cond": {{"$eq": ["$$item.year", 2023]}}
# #           }}
# #         }},
# #         "parking": {{
# #           "$filter": {{
# #             "input": "$parkingSpotsPerYear",
# #             "as": "item",
# #             "cond": {{"$eq": ["$$item.year", 2023]}}
# #           }}
# #         }}
# #       }}
# #     }},
# #     {{
# #       "$project": {{
# #         "name": 1,
# #         "year": 2023,
# #         "cars": {{"$arrayElemAt": ["$cars.amount", 0]}},
# #         "population": {{"$arrayElemAt": ["$population.amount", 0]}},
# #         "parking_spots": {{"$arrayElemAt": ["$parking.amount", 0]}}
# #       }}
# #     }}
# #   ],
# #   "explanation": "Get all metrics for Sibiu in 2023"
# # }}

# # 4. RANKING/COMPARISON ACROSS CITIES:
# # Use "aggregate" with $unwind and $sort:
# # {{
# #   "collection": "cities",
# #   "operation": "aggregate",
# #   "query": [
# #     {{
# #       "$unwind": "$carsPerYear"
# #     }},
# #     {{
# #       "$match": {{"carsPerYear.year": 2023}}
# #     }},
# #     {{
# #       "$sort": {{"carsPerYear.amount": -1}}
# #     }},
# #     {{
# #       "$limit": 1
# #     }},
# #     {{
# #       "$project": {{
# #         "name": 1,
# #         "region": 1,
# #         "year": "$carsPerYear.year",
# #         "cars": "$carsPerYear.amount"
# #       }}
# #     }}
# #   ],
# #   "explanation": "Find city with most cars in 2023"
# # }}

# # IMPORTANT RULES:
# # - Always use "cities" as collection name
# # - For questions about Sibiu specifically, always match {{"name": "Sibiu"}}
# # - For simple single-year queries, prefer "find" with projection
# # - For calculations and comparisons, use "aggregate"
# # - Always filter arrays to get specific year data
# # - Use $arrayElemAt to extract the amount from filtered arrays
# # - Year values should be numbers, not strings

# # Return ONLY valid JSON, no markdown, no code blocks, no additional text.
# # """
        
# #         messages = [
# #             {"role": "system", "content": "You are a MongoDB query generator that responds only with valid JSON. Always query the 'cities' collection and filter embedded arrays for specific years."},
# #             {"role": "user", "content": prompt}
# #         ]
        
# #         content = ollama_chat(
# #             base_url=Config.OLLAMA_URL,
# #             model=Config.OLLAMA_MODEL,
# #             messages=messages,
# #             temperature=0
# #         )
        
# #         if not content:
# #             return None
        
# #         # Clean the response
# #         content = content.strip()
# #         if content.startswith("```json"):
# #             content = content[7:]
# #         if content.startswith("```"):
# #             content = content[3:]
# #         if content.endswith("```"):
# #             content = content[:-3]
# #         content = content.strip()
        
# #         query_info = json.loads(content)
# #         return query_info
# #     except json.JSONDecodeError as e:
# #         print(f"Error parsing JSON: {e}")
# #         print(f"Raw response: {content}")
# #         return None
# #     except Exception as e:
# #         print(f"Error generating query: {e}")
# #         return None

# # @traffic_routes_home.route("/ask", methods=["POST"])
# # def ask_traffic_question():
# #     """
# #     POST /api/traffic/ask
# #     {
# #         "question": "care este diferența de mașini între 2022 și 2014 în Sibiu?"
# #     }
# #     """
# #     try:
# #         data = request.get_json()
# #         if not data or "question" not in data:
# #             return jsonify({"error": "Lipsește câmpul 'question'"}), 400

# #         question = data["question"].strip()
# #         if not question:
# #             return jsonify({"error": "Întrebarea nu poate fi goală"}), 400

# #         print(f"\nNew question: {question}")

# #         # 1. Generează query-ul cu AI-ul tău
# #         query_info = generate_mongodb_query(question)
# #         if not query_info:
# #             return jsonify({
# #                 "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
# #                 "question": question
# #             }), 400

# #         # 2. Execută query-ul
# #         results = execute_mongodb_query(query_info)
# #         if results is None or (isinstance(results, list) and len(results) == 0):
# #             return jsonify({
# #                 "error": "Nu am găsit date pentru această întrebare.",
# #                 "question": question
# #             }), 404

# #         # 3. Generează răspunsul uman
# #         answer = generate_human_response(question, results)

# #         # Răspuns final
# #         return jsonify({
# #             "question": question,
# #             "answer": answer,
# #             "query_explanation": query_info.get("explanation", ""),
# #             "raw_results": results  # opțional, pentru debug
# #         }), 200

# #     except Exception as e:
# #         print(f"Eroare endpoint /ask: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return jsonify({
# #             "error": "Eroare internă la procesarea întrebării.",
# #             "details": str(e)
# #         }), 500


# from app.config import Config
# from flask import Blueprint, request, jsonify
# import os
# import json
# import google.generativeai as genai
# from typing import List, Dict, Any
# from pymongo import MongoClient
# from bson import ObjectId


# traffic_routes_home = Blueprint("traffic_routes_home", __name__)

# # ========================= CONFIG =========================
# db = Config.get_db()

# # Configure Gemini API
# GEMINI_API_KEY = "AIzaSyBs9DnQ-LEt-M0101Qs9kr3yH3TiR1KjcE"  # Set this in your environment variables
# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY environment variable is not set")

# genai.configure(api_key=GEMINI_API_KEY)

# # ========================= SCHEMA INFO =========================
# SCHEMA_INFO = """
# Database: urbanbike

# Collection: cities
# Schema:
# {
#   _id: ObjectId,
#   name: string,
#   region: string,
#   carsPerYear: [
#     {
#       year: number,
#       amount: number
#     }
#   ],
#   populationPerYear: [
#     {
#       year: number,
#       amount: number
#     }
#   ],
#   parkingSpotsPerYear: [
#     {
#       year: number,
#       amount: number
#     }
#   ]
# }

# IMPORTANT NOTES FOR QUERY GENERATION:
# 1. There is ONLY ONE collection called "cities"
# 2. All data (cars, population, parking spots) is embedded in the city document
# 3. To get data for a specific city, use a simple find query: {"name": "CityName"}
# 4. To get specific year data, use $filter in aggregation or filter in Python after retrieval
# 5. To compare two years, retrieve the city document and calculate in the aggregation pipeline
# 6. NEVER use {'$oid': '...'} syntax
# 7. For simple queries (e.g., "how many cars in Sibiu in 2022?"), use "find" operation
# 8. For complex queries (calculations, comparisons), use "aggregate" operation
# """

# # ========================= GEMINI =========================
# def gemini_chat(prompt: str, system_instruction: str = None, temperature: float = 0.3) -> str:
#     """
#     Calls Google Gemini API.
#     Returns the response text.
#     """
#     try:
#         # Use gemini-1.5-flash for faster responses or gemini-1.5-pro for better quality
#         model = genai.GenerativeModel(
#             'gemini-2.5-flash',
#             system_instruction=system_instruction
#         )
        
#         generation_config = genai.types.GenerationConfig(
#             temperature=temperature,
#             max_output_tokens=8192,
#         )
        
#         response = model.generate_content(
#             prompt,
#             generation_config=generation_config
#         )
        
#         return response.text
#     except Exception as e:
#         print(f"Gemini API error: {e}")
#         return None


# def check_gemini_connection():
#     """Check if Gemini API is accessible."""
#     try:
#         if not GEMINI_API_KEY:
#             print("❌ GEMINI_API_KEY not set")
#             return False
        
#         # Try a simple API call
#         model = genai.GenerativeModel('gemini-2.5-flash')
#         response = model.generate_content("Hello")
        
#         print(f"✅ Gemini API is working")
#         print(f"📦 Using model: gemini-1.5-flash\n")
#         return True
#     except Exception as e:
#         print(f"❌ Cannot connect to Gemini API")
#         print(f"   Error: {e}\n")
#         return False


# def generate_human_response(question, city_data):
#     """Use Gemini to generate a human-friendly response based on city data."""
#     try:
#         prompt = f"""Based on the user's question and the city data provided, provide a clear, natural, and informative response in Romanian.

# User Question: {question}

# CITY DATA (This is your PRIMARY SOURCE OF TRUTH):
# {json.dumps(city_data, indent=2, ensure_ascii=False)}

# INSTRUCTIONS:
# 1. Use ONLY the data from CITY DATA above to answer the question
# 2. The data structure contains:
#    - name: city name (e.g., "Sibiu")
#    - region: city region
#    - carsPerYear: array of {{year, amount}} for number of cars
#    - populationPerYear: array of {{year, amount}} for population
#    - parkingSpotsPerYear: array of {{year, amount}} for parking spots
# 3. When asked about a specific year, find that year in the appropriate array
# 4. When comparing years, calculate the difference between the amounts
# 5. Always format numbers with thousands separator (e.g., 67.200 instead of 67200)
# 6. Be conversational, clear, and natural in Romanian
# 7. If data for a requested year is not available, mention this politely

# EXAMPLES:
# - Question: "Câte mașini au fost în 2023?"
#   → Look in carsPerYear array for year 2023, report the amount
  
# - Question: "Care a fost evoluția populației din 2014 până în 2023?"
#   → Look at populationPerYear array, compare 2014 vs 2023, mention the trend
  
# - Question: "Diferența de mașini între 2022 și 2014?"
#   → Find 2022 and 2014 in carsPerYear, calculate difference

# Generate a natural, friendly response in Romanian based on the data.
# """
        
#         system_instruction = "You are a helpful assistant that provides clear and natural responses in Romanian. Always use the provided city data as your only source of truth."
        
#         answer = gemini_chat(prompt, system_instruction, temperature=0.3)
        
#         if not answer:
#             return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."
        
#         return answer
#     except Exception as e:
#         print(f"Error generating response: {e}")
#         return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."


# def execute_mongodb_query(query_info):
#     """Execute the MongoDB query and return results."""
#     try:
#         collection_name = query_info["collection"]
#         operation = query_info["operation"]
#         query = query_info["query"]
        
#         collection = db[collection_name]
        
#         if operation == "find":
#             results = list(collection.find(query))
#         elif operation == "aggregate":
#             results = list(collection.aggregate(query))
#         elif operation == "count":
#             results = collection.count_documents(query)
#         else:
#             results = []
        
#         # Convert ObjectId to string for JSON serialization
#         if isinstance(results, list):
#             for doc in results:
#                 if "_id" in doc:
#                     doc["_id"] = str(doc["_id"])
        
#         return results
#     except Exception as e:
#         print(f"Error executing query: {e}")
#         import traceback
#         traceback.print_exc()
#         return None


# def generate_mongodb_query(question):
#     """Use Gemini to generate a MongoDB query from natural language."""
#     try:
#         prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

# {SCHEMA_INFO}

# Question: {question}

# Generate a MongoDB query to answer this question. Respond with a JSON object containing:
# 1. "collection": always "cities"
# 2. "operation": the operation type ("find" or "aggregate")
# 3. "query": the actual MongoDB query/pipeline
# 4. "explanation": brief explanation of what the query does

# QUERY PATTERNS:

# 1. SIMPLE QUERIES (single year, single metric):
# Use "find" operation with projection:
# {{
#   "collection": "cities",
#   "operation": "find",
#   "query": {{
#     "name": "Sibiu"
#   }},
#   "projection": {{
#     "name": 1,
#     "carsPerYear": {{
#       "$filter": {{
#         "input": "$carsPerYear",
#         "as": "item",
#         "cond": {{"$eq": ["$$item.year", 2022]}}
#       }}
#     }}
#   }},
#   "explanation": "Find Sibiu and filter carsPerYear for year 2022"
# }}

# 2. COMPARING TWO YEARS:
# Use "aggregate" with $project and array filtering:
# {{
#   "collection": "cities",
#   "operation": "aggregate",
#   "query": [
#     {{
#       "$match": {{"name": "Sibiu"}}
#     }},
#     {{
#       "$project": {{
#         "name": 1,
#         "year1_data": {{
#           "$filter": {{
#             "input": "$carsPerYear",
#             "as": "item",
#             "cond": {{"$eq": ["$$item.year", 2022]}}
#           }}
#         }},
#         "year2_data": {{
#           "$filter": {{
#             "input": "$carsPerYear",
#             "as": "item",
#             "cond": {{"$eq": ["$$item.year", 2014]}}
#           }}
#         }}
#       }}
#     }},
#     {{
#       "$project": {{
#         "name": 1,
#         "year1": 2022,
#         "year1_amount": {{"$arrayElemAt": ["$year1_data.amount", 0]}},
#         "year2": 2014,
#         "year2_amount": {{"$arrayElemAt": ["$year2_data.amount", 0]}},
#         "difference": {{
#           "$subtract": [
#             {{"$arrayElemAt": ["$year1_data.amount", 0]}},
#             {{"$arrayElemAt": ["$year2_data.amount", 0]}}
#           ]
#         }}
#       }}
#     }}
#   ],
#   "explanation": "Compare cars in Sibiu between 2022 and 2014"
# }}

# 3. MULTIPLE METRICS (cars, population, parking):
# Use "aggregate" with multiple $filter operations:
# {{
#   "collection": "cities",
#   "operation": "aggregate",
#   "query": [
#     {{
#       "$match": {{"name": "Sibiu"}}
#     }},
#     {{
#       "$project": {{
#         "name": 1,
#         "cars": {{
#           "$filter": {{
#             "input": "$carsPerYear",
#             "as": "item",
#             "cond": {{"$eq": ["$$item.year", 2023]}}
#           }}
#         }},
#         "population": {{
#           "$filter": {{
#             "input": "$populationPerYear",
#             "as": "item",
#             "cond": {{"$eq": ["$$item.year", 2023]}}
#           }}
#         }},
#         "parking": {{
#           "$filter": {{
#             "input": "$parkingSpotsPerYear",
#             "as": "item",
#             "cond": {{"$eq": ["$$item.year", 2023]}}
#           }}
#         }}
#       }}
#     }},
#     {{
#       "$project": {{
#         "name": 1,
#         "year": 2023,
#         "cars": {{"$arrayElemAt": ["$cars.amount", 0]}},
#         "population": {{"$arrayElemAt": ["$population.amount", 0]}},
#         "parking_spots": {{"$arrayElemAt": ["$parking.amount", 0]}}
#       }}
#     }}
#   ],
#   "explanation": "Get all metrics for Sibiu in 2023"
# }}

# 4. RANKING/COMPARISON ACROSS CITIES:
# Use "aggregate" with $unwind and $sort:
# {{
#   "collection": "cities",
#   "operation": "aggregate",
#   "query": [
#     {{
#       "$unwind": "$carsPerYear"
#     }},
#     {{
#       "$match": {{"carsPerYear.year": 2023}}
#     }},
#     {{
#       "$sort": {{"carsPerYear.amount": -1}}
#     }},
#     {{
#       "$limit": 1
#     }},
#     {{
#       "$project": {{
#         "name": 1,
#         "region": 1,
#         "year": "$carsPerYear.year",
#         "cars": "$carsPerYear.amount"
#       }}
#     }}
#   ],
#   "explanation": "Find city with most cars in 2023"
# }}

# IMPORTANT RULES:
# - Always use "cities" as collection name
# - For questions about Sibiu specifically, always match {{"name": "Sibiu"}}
# - For simple single-year queries, prefer "find" with projection
# - For calculations and comparisons, use "aggregate"
# - Always filter arrays to get specific year data
# - Use $arrayElemAt to extract the amount from filtered arrays
# - Year values should be numbers, not strings

# Return ONLY valid JSON, no markdown, no code blocks, no additional text.
# """
        
#         system_instruction = "You are a MongoDB query generator that responds only with valid JSON. Always query the 'cities' collection and filter embedded arrays for specific years."
        
#         content = gemini_chat(prompt, system_instruction, temperature=0)
        
#         if not content:
#             return None
        
#         # Clean the response
#         content = content.strip()
#         if content.startswith("```json"):
#             content = content[7:]
#         if content.startswith("```"):
#             content = content[3:]
#         if content.endswith("```"):
#             content = content[:-3]
#         content = content.strip()
        
#         query_info = json.loads(content)
#         return query_info
#     except json.JSONDecodeError as e:
#         print(f"Error parsing JSON: {e}")
#         print(f"Raw response: {content}")
#         return None
#     except Exception as e:
#         print(f"Error generating query: {e}")
#         return None


# @traffic_routes_home.route("/ask", methods=["POST"])
# def ask_traffic_question():
#     """
#     POST /api/traffic/ask
#     {
#         "question": "care este diferența de mașini între 2022 și 2014 în Sibiu?"
#     }
#     """
#     try:
#         data = request.get_json()
#         if not data or "question" not in data:
#             return jsonify({"error": "Lipsește câmpul 'question'"}), 400

#         question = data["question"].strip()
#         if not question:
#             return jsonify({"error": "Întrebarea nu poate fi goală"}), 400

#         print(f"\nNew question: {question}")

#         # 1. Generate query using Gemini
#         query_info = generate_mongodb_query(question)
#         if not query_info:
#             return jsonify({
#                 "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
#                 "question": question
#             }), 400

#         # 2. Execute query
#         results = execute_mongodb_query(query_info)
#         if results is None or (isinstance(results, list) and len(results) == 0):
#             return jsonify({
#                 "error": "Nu am găsit date pentru această întrebare.",
#                 "question": question
#             }), 404

#         # 3. Generate human response using Gemini
#         answer = generate_human_response(question, results)

#         # Final response
#         return jsonify({
#             "question": question,
#             "answer": answer,
#             "query_explanation": query_info.get("explanation", ""),
#             "raw_results": results  # optional, for debugging
#         }), 200

#     except Exception as e:
#         print(f"Eroare endpoint /ask: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             "error": "Eroare internă la procesarea întrebării.",
#             "details": str(e)
#         }), 500

from app.config import Config
from flask import Blueprint, request, jsonify
import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from pymongo import MongoClient
from bson import ObjectId


traffic_routes_home = Blueprint("traffic_routes_home", __name__)

# ========================= CONFIG =========================
db = Config.get_db()

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBs9DnQ-LEt-M0101Qs9kr3yH3TiR1KjcE"
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

# ========================= SCHEMA INFO =========================
SCHEMA_INFO = """
Database: urbanbike

Collection 1: cities
Schema:
{
  _id: ObjectId,
  name: string,
  region: string,
  carsPerYear: [
    {
      year: number,
      amount: number
    }
  ],
  populationPerYear: [
    {
      year: number,
      amount: number
    }
  ],
  parkingSpotsPerYear: [
    {
      year: number,
      amount: number
    }
  ]
}

Collection 2: pollution
Schema:
{
  _id: ObjectId,
  cityId: ObjectId,  # References cities._id
  amount: number,    # Pollution amount/level
  year: number
}

RELATIONSHIPS:
- pollution.cityId references cities._id
- To get pollution data for a specific city, use $lookup to join pollution with cities

IMPORTANT NOTES FOR QUERY GENERATION:
1. Cities collection contains embedded arrays for cars, population, and parking spots
2. Pollution data is in a SEPARATE collection and must be joined using $lookup
3. To get pollution data for a city, always use aggregate with $lookup
4. NEVER use {'$oid': '...'} syntax - use $lookup for joins
5. For simple city queries (cars, population, parking), query cities collection directly
6. For pollution queries, start with pollution collection and $lookup cities, OR start with cities and $lookup pollution
7. For queries combining city data AND pollution, use $lookup to join collections

QUERY PATTERNS FOR POLLUTION:

1. POLLUTION FOR SPECIFIC CITY AND YEAR:
{
  "collection": "pollution",
  "operation": "aggregate",
  "query": [
    {
      "$lookup": {
        "from": "cities",
        "localField": "cityId",
        "foreignField": "_id",
        "as": "city"
      }
    },
    {"$unwind": "$city"},
    {
      "$match": {
        "city.name": "Sibiu",
        "year": 2023
      }
    },
    {
      "$project": {
        "_id": 0,
        "city_name": "$city.name",
        "region": "$city.region",
        "year": 1,
        "pollution_amount": "$amount"
      }
    }
  ],
  "explanation": "Get pollution data for Sibiu in 2023"
}

2. COMPARE POLLUTION BETWEEN YEARS:
{
  "collection": "pollution",
  "operation": "aggregate",
  "query": [
    {
      "$lookup": {
        "from": "cities",
        "localField": "cityId",
        "foreignField": "_id",
        "as": "city"
      }
    },
    {"$unwind": "$city"},
    {
      "$match": {
        "city.name": "Sibiu",
        "year": {"$in": [2022, 2023]}
      }
    },
    {
      "$group": {
        "_id": "$city.name",
        "city_name": {"$first": "$city.name"},
        "year1_pollution": {
          "$sum": {
            "$cond": [{"$eq": ["$year", 2023]}, "$amount", 0]
          }
        },
        "year2_pollution": {
          "$sum": {
            "$cond": [{"$eq": ["$year", 2022]}, "$amount", 0]
          }
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "city_name": 1,
        "year1": 2023,
        "year1_pollution": 1,
        "year2": 2022,
        "year2_pollution": 1,
        "difference": {"$subtract": ["$year1_pollution", "$year2_pollution"]}
      }
    }
  ],
  "explanation": "Compare pollution in Sibiu between 2023 and 2022"
}

3. RANKING CITIES BY POLLUTION:
{
  "collection": "pollution",
  "operation": "aggregate",
  "query": [
    {
      "$match": {"year": 2023}
    },
    {
      "$lookup": {
        "from": "cities",
        "localField": "cityId",
        "foreignField": "_id",
        "as": "city"
      }
    },
    {"$unwind": "$city"},
    {
      "$project": {
        "_id": 0,
        "city_name": "$city.name",
        "region": "$city.region",
        "year": 1,
        "pollution_amount": "$amount"
      }
    },
    {
      "$sort": {"pollution_amount": -1}
    },
    {
      "$limit": 5
    }
  ],
  "explanation": "Get top 5 cities with highest pollution in 2023"
}

4. COMBINING CITY DATA WITH POLLUTION (e.g., cars vs pollution):
{
  "collection": "cities",
  "operation": "aggregate",
  "query": [
    {
      "$match": {"name": "Sibiu"}
    },
    {
      "$lookup": {
        "from": "pollution",
        "localField": "_id",
        "foreignField": "cityId",
        "as": "pollution_data"
      }
    },
    {
      "$project": {
        "name": 1,
        "region": 1,
        "cars_2023": {
          "$arrayElemAt": [
            {
              "$filter": {
                "input": "$carsPerYear",
                "as": "item",
                "cond": {"$eq": ["$$item.year", 2023]}
              }
            },
            0
          ]
        },
        "pollution_2023": {
          "$arrayElemAt": [
            {
              "$filter": {
                "input": "$pollution_data",
                "as": "item",
                "cond": {"$eq": ["$$item.year", 2023]}
              }
            },
            0
          ]
        }
      }
    },
    {
      "$project": {
        "name": 1,
        "region": 1,
        "year": 2023,
        "cars": "$cars_2023.amount",
        "pollution": "$pollution_2023.amount"
      }
    }
  ],
  "explanation": "Get both cars and pollution data for Sibiu in 2023"
}

DECISION LOGIC FOR COLLECTION SELECTION:
- If question asks ONLY about cars, population, or parking spots → query "cities" collection
- If question asks ONLY about pollution → query "pollution" collection with $lookup to cities
- If question asks about pollution AND city data (cars/population/parking) → query "cities" collection with $lookup to pollution
- If question compares cities by pollution → query "pollution" collection with $lookup to cities
"""

# ========================= GEMINI =========================
def gemini_chat(prompt: str, system_instruction: str = None, temperature: float = 0.3) -> str:
    """
    Calls Google Gemini API.
    Returns the response text.
    """
    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=system_instruction
        )
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def check_gemini_connection():
    """Check if Gemini API is accessible."""
    try:
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not set")
            return False
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hello")
        
        print(f"✅ Gemini API is working")
        print(f"📦 Using model: gemini-2.0-flash-exp\n")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to Gemini API")
        print(f"   Error: {e}\n")
        return False


def generate_human_response(question, query_results):
    """Use Gemini to generate a human-friendly response based on query results."""
    try:
        prompt = f"""Based on the user's question and the query results provided, provide a clear, natural, and informative response in Romanian.

User Question: {question}

QUERY RESULTS (This is your PRIMARY SOURCE OF TRUTH):
{json.dumps(query_results, indent=2, ensure_ascii=False)}

INSTRUCTIONS:
1. Use ONLY the data from QUERY RESULTS above to answer the question
2. The data may contain:
   - City information (name, region)
   - Cars data (carsPerYear array with year and amount)
   - Population data (populationPerYear array)
   - Parking spots data (parkingSpotsPerYear array)
   - Pollution data (pollution_amount or pollution_data with year and amount)
3. When asked about a specific year, find that year in the appropriate data
4. When comparing years or metrics, calculate differences clearly
5. Always format numbers with thousands separator (e.g., 67.200 instead of 67200)
6. Be conversational, clear, and natural in Romanian
7. If data for a requested year is not available, mention this politely
8. When discussing pollution, provide context (e.g., "nivelul de poluare", "cantitatea de poluanți")

EXAMPLES:
- Question: "Cât poluează Sibiu în 2023?"
  → Look for pollution data for 2023, report the amount with context
  
- Question: "Care este relația între numărul de mașini și poluare în 2023?"
  → Compare cars amount with pollution amount, discuss correlation
  
- Question: "Care oraș poluează cel mai mult?"
  → Identify the city with highest pollution, mention the amount

Generate a natural, friendly response in Romanian based on the data.
"""
        
        system_instruction = "You are a helpful assistant that provides clear and natural responses in Romanian. Always use the provided query results as your only source of truth. Format numbers properly and provide context for pollution data."
        
        answer = gemini_chat(prompt, system_instruction, temperature=0.3)
        
        if not answer:
            return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."
        
        return answer
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."


def execute_mongodb_query(query_info):
    """Execute the MongoDB query and return results."""
    try:
        collection_name = query_info["collection"]
        operation = query_info["operation"]
        query = query_info["query"]
        
        collection = db[collection_name]
        
        if operation == "find":
            results = list(collection.find(query))
        elif operation == "aggregate":
            results = list(collection.aggregate(query))
        elif operation == "count":
            results = collection.count_documents(query)
        else:
            results = []
        
        # Convert ObjectId to string for JSON serialization
        if isinstance(results, list):
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "cityId" in doc:
                    doc["cityId"] = str(doc["cityId"])
        
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_mongodb_query(question):
    """Use Gemini to generate a MongoDB query from natural language."""
    try:
        # Detect if question is about pollution
        pollution_keywords = ['poluare', 'poluează', 'poluez', 'polueaza', 'pollution', 'contaminare', 'emisii', 'calitate aer']
        is_pollution_query = any(keyword in question.lower() for keyword in pollution_keywords)
        
        prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

{SCHEMA_INFO}

Question: {question}

IMPORTANT: This question {"CONTAINS" if is_pollution_query else "DOES NOT CONTAIN"} pollution-related keywords (poluare, poluează, etc.)

Generate a MongoDB query to answer this question. Respond with a JSON object containing:
1. "collection": the collection to query ("cities" or "pollution")
2. "operation": the operation type ("find" or "aggregate")
3. "query": the actual MongoDB query/pipeline
4. "explanation": brief explanation of what the query does

CRITICAL RULES FOR COLLECTION SELECTION:
1. IF the question contains "poluare", "poluează", "pollution" or related words → ALWAYS query "pollution" collection
2. IF the question asks about cars, population, or parking spots ONLY → query "cities" collection
3. IF the question asks about pollution AND city data together → query "pollution" collection and $lookup "cities"
4. For pollution queries, ALWAYS use $lookup to join with cities collection to get city names
5. NEVER use {{"$oid": "..."}} syntax
6. Use aggregate pipelines for any query involving joins between collections
7. Always use city.name (not cityId) when matching specific cities in pollution queries
8. Year values should be numbers, not strings
9. Use $unwind after $lookup to flatten arrays

COLLECTION DECISION EXAMPLES:
- "Câte mașini sunt în Sibiu?" → "cities" (no pollution keyword)
- "Cât poluează Sibiu?" → "pollution" (contains "poluează")
- "Care este poluarea în 2023?" → "pollution" (contains "poluarea")
- "Care oraș poluează cel mai mult?" → "pollution" (contains "poluează")
- "Câți locuitori și ce poluare?" → "pollution" (contains "poluare", lookup cities for population)
- "Diferența de poluare între 2022 și 2023?" → "pollution" (contains "poluare")

Return ONLY valid JSON, no markdown, no code blocks, no additional text.
"""
        
        system_instruction = f"""You are a MongoDB query generator that responds only with valid JSON. 
CRITICAL DETECTION: This question {"IS ABOUT POLLUTION" if is_pollution_query else "IS NOT ABOUT POLLUTION"}.

Collection selection rules:
1. IF question contains "poluare", "poluează", "pollution" or related words → MUST query "pollution" collection
2. IF question is ONLY about cars/population/parking (no pollution words) → query "cities" collection
3. ALWAYS use $lookup to join collections when querying pollution data to get city names
4. When in doubt, if pollution is mentioned anywhere, use "pollution" collection"""
        
        content = gemini_chat(prompt, system_instruction, temperature=0)
        
        if not content:
            return None
        
        # Clean the response
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        query_info = json.loads(content)
        return query_info
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {content}")
        return None
    except Exception as e:
        print(f"Error generating query: {e}")
        return None


@traffic_routes_home.route("/ask", methods=["POST"])
def ask_traffic_question():
    """
    POST /api/traffic/ask
    {
        "question": "cât poluează Sibiu în 2023?"
    }
    """
    try:
        data = request.get_json()
        if not data or "question" not in data:
            return jsonify({"error": "Lipsește câmpul 'question'"}), 400

        question = data["question"].strip()
        if not question:
            return jsonify({"error": "Întrebarea nu poate fi goală"}), 400

        print(f"\nNew question: {question}")

        # 1. Generate query using Gemini
        query_info = generate_mongodb_query(question)
        if not query_info:
            return jsonify({
                "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
                "question": question
            }), 400

        print(f"Generated query: {json.dumps(query_info, indent=2)}")

        # 2. Execute query
        results = execute_mongodb_query(query_info)
        if results is None or (isinstance(results, list) and len(results) == 0):
            return jsonify({
                "error": "Nu am găsit date pentru această întrebare.",
                "question": question
            }), 404

        # 3. Generate human response using Gemini
        answer = generate_human_response(question, results)

        # Final response
        return jsonify({
            "question": question,
            "answer": answer,
            "query_explanation": query_info.get("explanation", ""),
            "raw_results": results  # optional, for debugging
        }), 200

    except Exception as e:
        print(f"Eroare endpoint /ask: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Eroare internă la procesarea întrebării.",
            "details": str(e)
        }), 500