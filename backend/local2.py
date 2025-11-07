import os
import json
import requests
from typing import List, Dict, Any
from pymongo import MongoClient
from bson import ObjectId

# ========================= CONFIG =========================
MONGO_USER = "alexurluescu23_db_user"
MONGO_PASSWORD = "y8MDoUisyGf2Gayo"
MONGO_CLUSTER = "cluster0.c9gvi0h.mongodb.net"
MONGO_DB = "urbanbike"

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName={MONGO_DB}"
client_mongo = MongoClient(MONGO_URI)
db = client_mongo.urbanbike

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

# ========================= OLLAMA =========================
def ollama_chat(messages: List[Dict], temperature: float = 0.0) -> str:
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": 12888}
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        print(f"Ollama error: {e}")
        return ""

# ========================= GENERATE QUERY =========================
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
    
    messages = [
        {"role": "system", "content": "You are a senior MongoDB engineer. For day comparisons or busiest day → use 'find' + python. For hourly data → use aggregation with $objectToArray. Always return clean JSON."},
        {"role": "user", "content": prompt}
    ]
    
    content = ollama_chat(messages, temperature=0.0)
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    
    try:
        result = json.loads(content)
        print(f"AI decided: {result.get('recommended_processing', 'mongo')}")
        return result
    except Exception as e:
        print(f"Invalid JSON from AI: {e}\nRaw: {content}")
        return None

# ========================= EXECUTE QUERY =========================
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

# ========================= HUMAN RESPONSE =========================
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

    # Mongo processing
    data = json.dumps(results, indent=2, ensure_ascii=False)
    prompt = f"Răspunde clar în română:\nÎntrebare: {question}\nDate: {data}"
    response = ollama_chat([{"role": "user", "content": prompt}], temperature=0.3)
    return response.strip() or "Am găsit datele."

# ========================= MAIN =========================
def main():
    print("=" * 70)
    print("   AI TRAFFIC ASSISTANT - UrbanBike (streets)")
    print("=" * 70)
    
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        print("Ollama connected")
    except:
        print("Start Ollama: ollama serve")
        return

    print("\nExemple:")
    print("- la ce oră a fost vârful azi?")
    print("- câte mașini ieri?")
    print("- diferența între azi și ieri")
    print("- în ce zi a fost mai aglomerat?\n")

    while True:
        q = input("\nÎntrebare: ").strip()
        if q.lower() in ["exit", "quit", "stop"]: 
            print("Pa!")
            break
        if not q: continue

        print("AI generează query...")
        info = generate_mongodb_query(q)
        if not info:
            print("Nu am înțeles. Reformulează.")
            continue

        print(f"Metodă: {info.get('recommended_processing', 'mongo')}")
        results = execute_mongodb_query(info)
        print(f"Rezultate: {len(results)}")

        print("\n" + "="*70)
        print("RĂSPUNS:")
        print("="*70)
        print(generate_human_response(q, results))
        print("="*70)

if __name__ == "__main__":
    main()