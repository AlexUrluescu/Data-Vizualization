# # app/routes/traffic_routes.py
# from app.config import Config
# from flask import Blueprint, request, jsonify
# import os
# import json
# import requests
# from typing import List, Dict, Any
# from pymongo import MongoClient
# from bson import ObjectId


# traffic_routes = Blueprint("traffic_routes", __name__)

# # ========================= CONFIG =========================


# db = Config.get_db()
# # ========================= SCHEMA INFO =========================
# SCHEMA_INFO = """
# Database: urbanbike
# Collection: streets

# Document example:
# {
#   "_id": ObjectId,
#   "name": "Bulevardul Corneliu Coposu",
#   "coordinates": [[lat, lon], ...],
#   "color": "#ffaa44",
#   "dailyStats": [
#     {
#       "date": "2025-11-07",
#       "hourlyCarCount": { "00": 3, "01": 1, ..., "23": 3 },
#       "totalCars": 380
#     },
#     {
#       "date": "2025-11-06",
#       "hourlyCarCount": { ... },
#       "totalCars": 346
#     }
#   ]
# }

# IMPORTANT RULES FOR QUERY GENERATION:
# 1. ALWAYS use "aggregate" for any question involving dailyStats
# 2. To access a specific date → $unwind "$dailyStats" → $match "dailyStats.date"
# 3. To get hourly data → $objectToArray on "dailyStats.hourlyCarCount"
# 4. Hours are strings "00" to "23"
# 5. Today = "2025-11-07", Yesterday = "2025-11-06"
# 6. For "peak hour" → $sort hourly.v descending → $limit 1
# 7. For "difference between two days" → fetch full document → Python calculates (recommended)
# 8. For "busiest day" → fetch full document → Python finds max totalCars
# """

# # ========================= OLLAMA =========================
# def ollama_chat(messages: List[Dict], temperature: float = 0.0) -> str:
#     url = f"{Config.OLLAMA_URL}/api/chat"
#     payload = {
#         "model": Config.OLLAMA_MODEL,
#         "messages": messages,
#         "stream": False,
#         "options": {"temperature": temperature, "num_ctx": 12888}
#     }
#     try:
#         resp = requests.post(url, json=payload, timeout=120)
#         resp.raise_for_status()
#         return resp.json()["message"]["content"]
#     except Exception as e:
#         print(f"Ollama error: {e}")
#         return ""



# def generate_human_response(question: str, results: Any) -> str:
#     if not results:
#         return "Nu am găsit date pentru Bulevardul Corneliu Coposu."

#     # Python processing
#     if len(results) == 1 and "dailyStats" in results[0]:
#         stats = results[0]["dailyStats"]
#         totals = {s["date"]: s["totalCars"] for s in stats}
#         q = question.lower()

#         if any(w in q for w in ["diferența", "compară", "față de", "între"]):
#             d1, d2 = "2025-11-07", "2025-11-06"
#             t1, t2 = totals.get(d1, 0), totals.get(d2, 0)
#             diff = t1 - t2
#             pct = round(diff / t2 * 100, 1) if t2 else 0
#             return f"**2025-11-07**: {t1} mașini\n**2025-11-06**: {t2} mașini\n\n**Diferența**: {diff:+} mașini ({pct:+.1f}%)"

#         if any(w in q for w in ["în ce zi", "cea mai aglomerată", "mai aglomerat"]):
#             best = max(stats, key=lambda x: x["totalCars"])
#             return f"Cea mai aglomerată zi a fost **{best['date']}** cu **{best['totalCars']} mașini**."

#     # Mongo processing
#     data = json.dumps(results, indent=2, ensure_ascii=False)
#     prompt = f"Răspunde clar în română:\nÎntrebare: {question}\nDate: {data}"
#     response = ollama_chat([{"role": "user", "content": prompt}], temperature=0.3)
#     return response.strip() or "Am găsit datele."


# def execute_mongodb_query(query_info: Dict) -> Any:
#     collection = db[query_info["collection"]]
#     processing = query_info.get("recommended_processing", "mongo")
    
#     if processing == "python":
#         doc = collection.find_one(query_info["query"], {"dailyStats": 1, "_id": 0})
#         return [doc] if doc else []
    
#     if query_info["operation"] == "aggregate":
#         results = list(collection.aggregate(query_info["query"]))
#         for r in results:
#             if "_id" in r: r["_id"] = str(r["_id"])
#         return results
    
#     if query_info["operation"] == "find":
#         return list(collection.find(query_info["query"], {"_id": 0}))
    
#     return []


# def generate_mongodb_query(question: str) -> Dict[str, Any]:
#     prompt = f"""{SCHEMA_INFO}

# User question: {question}

# Generate a MongoDB aggregation pipeline as JSON with this structure:
# {{
#   "collection": "streets",
#   "operation": "aggregate" or "find",
#   "query": [pipeline] or {{filter}},
#   "explanation": "short Romanian explanation",
#   "recommended_processing": "mongo" or "python"
# }}

# CRITICAL RULES:
# - If question asks about "diferența", "compară", "în ce zi a fost mai aglomerat", "cea mai aglomerată zi" → use "find" + "recommended_processing": "python"
# - For peak hour, hourly list, specific hour → use "aggregate" + $objectToArray
# - Return ONLY valid JSON. No markdown. No extra text.

# EXAMPLES:

# 1. "care este diferența între 2025-11-07 și 2025-11-06?" →
# {{
#   "collection": "streets",
#   "operation": "find",
#   "query": {{"name": "Bulevardul Corneliu Coposu"}},
#   "explanation": "Încarc documentul complet pentru calcul diferență în Python",
#   "recommended_processing": "python"
# }}

# 2. "în ce zi a fost mai aglomerat pe Bulevardul Corneliu Coposu?" →
# {{
#   "collection": "streets",
#   "operation": "find",
#   "query": {{"name": "Bulevardul Corneliu Coposu"}},
#   "explanation": "Găsesc ziua cu totalCars maxim în Python",
#   "recommended_processing": "python"
# }}

# 3. "la ce oră a fost vârful de trafic azi?" →
# {{
#   "collection": "streets",
#   "operation": "aggregate",
#   "query": [
#     {{"$match": {{"name": "Bulevardul Corneliu Coposu"}}}},
#     {{"$unwind": "$dailyStats"}},
#     {{"$match": {{"dailyStats.date": "2025-11-07"}}}},
#     {{"$project": {{"hourly": {{"$objectToArray": "$dailyStats.hourlyCarCount"}}}}}},
#     {{"$unwind": "$hourly"}},
#     {{"$sort": {{"hourly.v": -1}}}},
#     {{"$limit": 1}},
#     {{"$project": {{"ora": "$hourly.k", "mașini": "$hourly.v", "_id": 0}}}}
#   ],
#   "explanation": "Găsesc ora cu cele mai multe mașini pe 2025-11-07",
#   "recommended_processing": "mongo"
# }}

# 4. "câte mașini au fost ieri la ora 15?" →
# {{
#   "collection": "streets",
#   "operation": "aggregate",
#   "query": [
#     {{"$match": {{"name": "Bulevardul Corneliu Coposu"}}}},
#     {{"$unwind": "$dailyStats"}},
#     {{"$match": {{"dailyStats.date": "2025-11-06"}}}},
#     {{"$project": {{"mașini": "$dailyStats.hourlyCarCount.15", "_id": 0}}}}
#   ],
#   "explanation": "Număr mașini la ora 15 pe 2025-11-06",
#   "recommended_processing": "mongo"
# }}

# Return ONLY the JSON object."""
    
#     messages = [
#         {"role": "system", "content": "You are a senior MongoDB engineer. For day comparisons or busiest day → use 'find' + python. For hourly data → use aggregation with $objectToArray. Always return clean JSON."},
#         {"role": "user", "content": prompt}
#     ]
    
#     content = ollama_chat(messages, temperature=0.0)
#     content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    
#     try:
#         result = json.loads(content)
#         print(f"AI decided: {result.get('recommended_processing', 'mongo')}")
#         return result
#     except Exception as e:
#         print(f"Invalid JSON from AI: {e}\nRaw: {content}")
#         return None


# @traffic_routes.route("/ask", methods=["POST"])
# def ask_traffic_question():
#     """
#     POST /api/traffic/ask
#     {
#         "question": "care este diferența de mașini între azi și ieri?"
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

#         # 1. Generează query-ul cu AI-ul tău
#         query_info = generate_mongodb_query(question)
#         if not query_info:
#             return jsonify({
#                 "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
#                 "question": question
#             }), 400

#         # 2. Execută query-ul
#         results = execute_mongodb_query(query_info)
#         if results is None or (isinstance(results, list) and len(results) == 0):
#             return jsonify({
#                 "error": "Nu am găsit date pentru această întrebare.",
#                 "question": question
#             }), 404

#         # 3. Generează răspunsul uman
#         answer = generate_human_response(question, results)

#         # Răspuns final
#         return jsonify({
#             "question": question,
#             "answer": answer,
#             "ai_method": query_info.get("recommended_processing", "mongo"),
#             "raw_results": results  # opțional, pentru debug
#         }), 200

#     except Exception as e:
#         print(f"Eroare endpoint /ask: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             "error": "Eroare internă la procesarea întrebării.",
#             "details": str(e)
#         }), 500


# app/routes/traffic_routes.py
from configs.config import Config
from flask import Blueprint, request, jsonify
import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from pymongo import MongoClient
from bson import ObjectId


traffic_routes = Blueprint("traffic_routes", __name__)

# ========================= CONFIG =========================
db = Config.get_db()

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBs9DnQ-LEt-M0101Qs9kr3yH3TiR1KjcE"   # Set this in your environment variables
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

# ========================= SCHEMA INFO =========================
SCHEMA_INFO = """
Database: urbanbike
Collection: streets

Document example:
{
  "_id": ObjectId,
  "name": "Bulevardul Corneliu Coposu",
  "coordinates": [[lat, lon], ...],
  "color": "#ffaa44",
  "dailyStats": [
    {
      "date": "2025-11-07",
      "hourlyCarCount": { "00": 3, "01": 1, ..., "23": 3 },
      "totalCars": 380
    },
    {
      "date": "2025-11-06",
      "hourlyCarCount": { ... },
      "totalCars": 346
    }
  ]
}

IMPORTANT RULES FOR QUERY GENERATION:
1. ALWAYS use "aggregate" for any question involving dailyStats
2. To access a specific date → $unwind "$dailyStats" → $match "dailyStats.date"
3. To get hourly data → $objectToArray on "dailyStats.hourlyCarCount"
4. Hours are strings "00" to "23"
5. Today = "2025-11-07", Yesterday = "2025-11-06"
6. For "peak hour" → $sort hourly.v descending → $limit 1
7. For "difference between two days" → fetch full document → Python calculates (recommended)
8. For "busiest day" → fetch full document → Python finds max totalCars
"""

# ========================= GEMINI =========================
def gemini_chat(prompt: str, system_instruction: str = None, temperature: float = 0.0) -> str:
    """
    Calls Google Gemini API.
    Returns the response text.
    """
    try:
        # Use gemini-1.5-flash for faster responses
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
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
        return ""


def check_gemini_connection():
    """Check if Gemini API is accessible."""
    try:
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not set")
            return False
        
        # Try a simple API call
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        
        print(f"✅ Gemini API is working")
        print(f"📦 Using model: gemini-1.5-flash\n")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to Gemini API")
        print(f"   Error: {e}\n")
        return False


def generate_human_response(question: str, results: Any) -> str:
    if not results:
        return "Nu am găsit date pentru Bulevardul Corneliu Coposu."

    # Python processing
    if len(results) == 1 and "dailyStats" in results[0]:
        stats = results[0]["dailyStats"]
        totals = {s["date"]: s["totalCars"] for s in stats}
        q = question.lower()

        if any(w in q for w in ["diferența", "compară", "față de", "între"]):
            d1, d2 = "2025-11-07", "2025-11-06"
            t1, t2 = totals.get(d1, 0), totals.get(d2, 0)
            diff = t1 - t2
            pct = round(diff / t2 * 100, 1) if t2 else 0
            return f"**2025-11-07**: {t1} mașini\n**2025-11-06**: {t2} mașini\n\n**Diferența**: {diff:+} mașini ({pct:+.1f}%)"

        if any(w in q for w in ["în ce zi", "cea mai aglomerată", "mai aglomerat"]):
            best = max(stats, key=lambda x: x["totalCars"])
            return f"Cea mai aglomerată zi a fost **{best['date']}** cu **{best['totalCars']} mașini**."

    # Gemini processing
    data = json.dumps(results, indent=2, ensure_ascii=False)
    prompt = f"Răspunde clar în română:\nÎntrebare: {question}\nDate: {data}"
    response = gemini_chat(prompt, temperature=0.3)
    return response.strip() or "Am găsit datele."


def execute_mongodb_query(query_info: Dict) -> Any:
    collection = db[query_info["collection"]]
    processing = query_info.get("recommended_processing", "mongo")
    
    if processing == "python":
        doc = collection.find_one(query_info["query"], {"dailyStats": 1, "_id": 0})
        return [doc] if doc else []
    
    if query_info["operation"] == "aggregate":
        results = list(collection.aggregate(query_info["query"]))
        for r in results:
            if "_id" in r: r["_id"] = str(r["_id"])
        return results
    
    if query_info["operation"] == "find":
        return list(collection.find(query_info["query"], {"_id": 0}))
    
    return []


def generate_mongodb_query(question: str) -> Dict[str, Any]:
    prompt = f"""{SCHEMA_INFO}

User question: {question}

Generate a MongoDB aggregation pipeline as JSON with this structure:
{{
  "collection": "streets",
  "operation": "aggregate" or "find",
  "query": [pipeline] or {{filter}},
  "explanation": "short Romanian explanation",
  "recommended_processing": "mongo" or "python"
}}

CRITICAL RULES:
- If question asks about "diferența", "compară", "în ce zi a fost mai aglomerat", "cea mai aglomerată zi" → use "find" + "recommended_processing": "python"
- For peak hour, hourly list, specific hour → use "aggregate" + $objectToArray
- Return ONLY valid JSON. No markdown. No extra text.

EXAMPLES:

1. "care este diferența între 2025-11-07 și 2025-11-06?" →
{{
  "collection": "streets",
  "operation": "find",
  "query": {{"name": "Bulevardul Corneliu Coposu"}},
  "explanation": "Încarc documentul complet pentru calcul diferență în Python",
  "recommended_processing": "python"
}}

2. "în ce zi a fost mai aglomerat pe Bulevardul Corneliu Coposu?" →
{{
  "collection": "streets",
  "operation": "find",
  "query": {{"name": "Bulevardul Corneliu Coposu"}},
  "explanation": "Găsesc ziua cu totalCars maxim în Python",
  "recommended_processing": "python"
}}

3. "la ce oră a fost vârful de trafic azi?" →
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": "Bulevardul Corneliu Coposu"}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": "2025-11-07"}}}},
    {{"$project": {{"hourly": {{"$objectToArray": "$dailyStats.hourlyCarCount"}}}}}},
    {{"$unwind": "$hourly"}},
    {{"$sort": {{"hourly.v": -1}}}},
    {{"$limit": 1}},
    {{"$project": {{"ora": "$hourly.k", "mașini": "$hourly.v", "_id": 0}}}}
  ],
  "explanation": "Găsesc ora cu cele mai multe mașini pe 2025-11-07",
  "recommended_processing": "mongo"
}}

4. "câte mașini au fost ieri la ora 15?" →
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": "Bulevardul Corneliu Coposu"}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": "2025-11-06"}}}},
    {{"$project": {{"mașini": "$dailyStats.hourlyCarCount.15", "_id": 0}}}}
  ],
  "explanation": "Număr mașini la ora 15 pe 2025-11-06",
  "recommended_processing": "mongo"
}}

Return ONLY the JSON object."""
    
    system_instruction = "You are a senior MongoDB engineer. For day comparisons or busiest day → use 'find' + python. For hourly data → use aggregation with $objectToArray. Always return clean JSON."
    
    content = gemini_chat(prompt, system_instruction, temperature=0.0)
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    
    try:
        result = json.loads(content)
        print(f"AI decided: {result.get('recommended_processing', 'mongo')}")
        return result
    except Exception as e:
        print(f"Invalid JSON from AI: {e}\nRaw: {content}")
        return None


@traffic_routes.route("/ask", methods=["POST"])
def ask_traffic_question():
    """
    POST /api/traffic/ask
    {
        "question": "care este diferența de mașini între azi și ieri?"
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

        # 2. Execute query
        results = execute_mongodb_query(query_info)
        if results is None or (isinstance(results, list) and len(results) == 0):
            return jsonify({
                "error": "Nu am găsit date pentru această întrebare.",
                "question": question
            }), 404

        # 3. Generate human response
        answer = generate_human_response(question, results)

        # Final response
        return jsonify({
            "question": question,
            "answer": answer,
            "ai_method": query_info.get("recommended_processing", "mongo"),
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