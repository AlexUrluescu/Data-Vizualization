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
1. ALWAYS extract and use the street name from the user's question
2. Use case-insensitive regex for street matching: {"name": {"$regex": "^StreetName$", "$options": "i"}}
3. ALWAYS use MongoDB aggregation pipelines - NO Python processing
4. Current date: 2025-11-07 (today), 2025-11-06 (yesterday)
5. Hours are strings "00" to "23" in hourlyCarCount object

QUERY PATTERNS:

A. Peak hour (single day):
   - $match street name
   - $unwind "$dailyStats"
   - $match date
   - $project with $objectToArray on hourlyCarCount
   - $unwind hourly array
   - $sort by value descending
   - $limit 1

B. Total cars (single day):
   - $match street name
   - $unwind "$dailyStats"
   - $match date
   - $project to show totalCars

C. Cars at specific hour:
   - $match street name
   - $unwind "$dailyStats"
   - $match date
   - $project to extract specific hour from hourlyCarCount (e.g., "$dailyStats.hourlyCarCount.15")

D. Difference between two days:
   - $match street name
   - $unwind "$dailyStats"
   - $match dates with $in
   - $group with $cond to separate days
   - $project with $subtract to calculate difference

E. Busiest day (find which day had most cars):
   - $match street name
   - $unwind "$dailyStats"
   - $sort by totalCars descending
   - $limit 1

F. Compare hourly data between two days:
   - $match street name
   - $unwind "$dailyStats"
   - $match dates with $in
   - $group with $cond for each hour
   - $project to calculate differences
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

# ========================= CHECK OLLAMA =========================
def check_ollama_connection():
    """Check if Ollama is running and model is available."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json()
        
        available_models = [model['name'] for model in models.get('models', [])]
        
        print(f"✅ Ollama is running")
        print(f"📦 Available models: {', '.join(available_models)}")
        
        if OLLAMA_MODEL not in available_models:
            print(f"⚠️  Warning: Model '{OLLAMA_MODEL}' not found!")
            print(f"💡 Pull the model: ollama pull {OLLAMA_MODEL}\n")
            return False
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"   Make sure Ollama is running: ollama serve")
        print(f"   Error: {e}\n")
        return False

# ========================= EXTRACT STREET NAME =========================
def extract_street_name(question: str) -> str:
    """Extract street name from user question using AI"""
    prompt = f"""Extract ONLY the street name from this question. Return just the street name, nothing else.

Question: {question}

Examples:
"care a fost cea mai aglomerata zi pe strada Emil Cioran?" → Emil Cioran
"câte mașini pe Bulevardul Corneliu Coposu azi?" → Bulevardul Corneliu Coposu
"vârful de trafic pe strada Octavian Goga" → Octavian Goga
"diferența pe bd. Coposu între azi și ieri" → Coposu
"pe Goga, câte mașini?" → Goga

Return ONLY the street name (no quotes, no extra text):"""
    
    messages = [
        {"role": "system", "content": "You extract street names from questions. Return ONLY the street name, no explanation, no quotes."},
        {"role": "user", "content": prompt}
    ]
    
    street = ollama_chat(messages, temperature=0.0).strip().strip('"').strip("'")
    print(f"📍 Extracted street: '{street}'")
    return street

# ========================= GENERATE QUERY =========================
def generate_mongodb_query(question: str, street_name: str) -> Dict[str, Any]:
    prompt = f"""{SCHEMA_INFO}

User question: {question}
Street name: {street_name}

Generate a MongoDB aggregation pipeline as JSON with this structure:
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [pipeline stages],
  "explanation": "brief Romanian explanation"
}}

CRITICAL RULES:
- ALWAYS use: {{"$match": {{"name": {{"$regex": "^{street_name}$", "$options": "i"}}}}}} as first stage
- ALWAYS use aggregation pipelines - return complete pipeline that gives final answer
- NEVER suggest Python processing - MongoDB must do ALL calculations
- Return ONLY valid JSON, no markdown, no code blocks

EXAMPLES:

1. "care este diferența între 2025-11-07 și 2025-11-06 pe Emil Cioran?"
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": {{"$regex": "^Emil Cioran$", "$options": "i"}}}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": {{"$in": ["2025-11-07", "2025-11-06"]}}}}}},
    {{
      "$group": {{
        "_id": "$name",
        "streetName": {{"$first": "$name"}},
        "total_2025_11_07": {{
          "$sum": {{
            "$cond": [{{"$eq": ["$dailyStats.date", "2025-11-07"]}}, "$dailyStats.totalCars", 0]
          }}
        }},
        "total_2025_11_06": {{
          "$sum": {{
            "$cond": [{{"$eq": ["$dailyStats.date", "2025-11-06"]}}, "$dailyStats.totalCars", 0]
          }}
        }}
      }}
    }},
    {{
      "$project": {{
        "_id": 0,
        "street": "$streetName",
        "date_2025_11_07": "2025-11-07",
        "total_2025_11_07": 1,
        "date_2025_11_06": "2025-11-06",
        "total_2025_11_06": 1,
        "difference": {{"$subtract": ["$total_2025_11_07", "$total_2025_11_06"]}}
      }}
    }}
  ],
  "explanation": "Calculează diferența de mașini între 2025-11-07 și 2025-11-06"
}}

2. "în ce zi a fost mai aglomerat pe Emil Cioran?"
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": {{"$regex": "^Emil Cioran$", "$options": "i"}}}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$sort": {{"dailyStats.totalCars": -1}}}},
    {{"$limit": 1}},
    {{
      "$project": {{
        "_id": 0,
        "street": "$name",
        "busiest_date": "$dailyStats.date",
        "total_cars": "$dailyStats.totalCars"
      }}
    }}
  ],
  "explanation": "Găsește ziua cu cele mai multe mașini"
}}

3. "la ce oră a fost vârful de trafic azi pe Emil Cioran?"
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": {{"$regex": "^Emil Cioran$", "$options": "i"}}}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": "2025-11-07"}}}},
    {{"$project": {{"hourly": {{"$objectToArray": "$dailyStats.hourlyCarCount"}}, "street": "$name"}}}},
    {{"$unwind": "$hourly"}},
    {{"$sort": {{"hourly.v": -1}}}},
    {{"$limit": 1}},
    {{
      "$project": {{
        "_id": 0,
        "street": "$street",
        "peak_hour": "$hourly.k",
        "cars": "$hourly.v"
      }}
    }}
  ],
  "explanation": "Găsește ora cu cele mai multe mașini pe 2025-11-07"
}}

4. "câte mașini au fost ieri la ora 15 pe Emil Cioran?"
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": {{"$regex": "^Emil Cioran$", "$options": "i"}}}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": "2025-11-06"}}}},
    {{
      "$project": {{
        "_id": 0,
        "street": "$name",
        "date": "$dailyStats.date",
        "hour": "15",
        "cars": "$dailyStats.hourlyCarCount.15"
      }}
    }}
  ],
  "explanation": "Număr mașini la ora 15 pe 2025-11-06"
}}

5. "câte mașini au fost azi pe Emil Cioran?"
{{
  "collection": "streets",
  "operation": "aggregate",
  "query": [
    {{"$match": {{"name": {{"$regex": "^Emil Cioran$", "$options": "i"}}}}}},
    {{"$unwind": "$dailyStats"}},
    {{"$match": {{"dailyStats.date": "2025-11-07"}}}},
    {{
      "$project": {{
        "_id": 0,
        "street": "$name",
        "date": "$dailyStats.date",
        "total_cars": "$dailyStats.totalCars"
      }}
    }}
  ],
  "explanation": "Total mașini pe 2025-11-07"
}}

Generate the query for street: {street_name}
Return ONLY the JSON object."""
    
    messages = [
        {"role": "system", "content": f"You are a MongoDB aggregation expert. ALWAYS use street '{street_name}' with case-insensitive regex. ALWAYS return complete aggregation pipelines that calculate everything in MongoDB. NO Python processing. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ]
    
    content = ollama_chat(messages, temperature=0.0)
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    
    try:
        result = json.loads(content)
        return result
    except Exception as e:
        print(f"❌ Invalid JSON from AI: {e}")
        print(f"Raw response: {content}")
        return None

# ========================= EXECUTE QUERY =========================
def execute_mongodb_query(query_info: Dict) -> Any:
    try:
        collection = db[query_info["collection"]]
        operation = query_info["operation"]
        query = query_info["query"]
        
        if operation == "aggregate":
            results = list(collection.aggregate(query))
        elif operation == "find":
            results = list(collection.find(query))
        else:
            results = []
        
        # Convert ObjectId to string
        for r in results:
            if "_id" in r and isinstance(r["_id"], ObjectId):
                r["_id"] = str(r["_id"])
        
        return results
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return None

# ========================= HUMAN RESPONSE =========================
def generate_human_response(question: str, results: Any, street_name: str) -> str:
    if not results:
        return f"Nu am găsit date pentru strada '{street_name}'."

    try:
        prompt = f"""You are a helpful assistant. Based on the user's question and the data from MongoDB, provide a clear, natural response in Romanian.

User Question: {question}
Street: {street_name}

Database Results: {json.dumps(results, indent=2, ensure_ascii=False)}

Generate a human-friendly response that:
- Answers the question directly and naturally in Romanian
- Uses the actual numbers from the results
- Is conversational and clear
- For differences, mention both values and the difference with +/- sign
- For comparisons, state which is higher/lower
- Include the street name naturally in the response

Return ONLY the response text, no extra formatting."""
        
        messages = [
            {"role": "system", "content": "You provide clear, natural responses in Romanian based on MongoDB query results. Be conversational and direct."},
            {"role": "user", "content": prompt}
        ]
        
        response = ollama_chat(messages, temperature=0.3)
        return response.strip() or "Am găsit datele în baza de date."
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return json.dumps(results, indent=2, ensure_ascii=False)

# ========================= MAIN =========================
def main():
    print("=" * 70)
    print("   AI TRAFFIC ASSISTANT - UrbanBike (MongoDB Aggregation)")
    print("=" * 70)
    print()
    
    if not check_ollama_connection():
        return

    print("\nExemple de întrebări:")
    print("- la ce oră a fost vârful azi pe Emil Cioran?")
    print("- câte mașini ieri pe Bulevardul Coposu?")
    print("- diferența între azi și ieri pe strada Goga")
    print("- în ce zi a fost mai aglomerat pe Emil Cioran?")
    print("- câte mașini la ora 15 ieri pe Coposu?")
    print("\nType 'exit', 'quit', or 'stop' to exit.\n")

    while True:
        q = input("Întrebare: ").strip()
        if q.lower() in ["exit", "quit", "stop"]: 
            print("\n👋 Pa!")
            break
        if not q: 
            continue

        print("\n🔍 Extracting street name...")
        street = extract_street_name(q)
        if not street:
            print("❌ Nu am putut identifica strada. Menționează numele străzii în întrebare.\n")
            continue

        print(f"🤖 Generating MongoDB aggregation pipeline...")
        info = generate_mongodb_query(q, street)
        if not info:
            print("❌ Nu am putut genera query-ul. Reformulează întrebarea.\n")
            continue

        print(f"💡 Explanation: {info.get('explanation', 'N/A')}")
        print(f"📊 Query details:")
        print(json.dumps(info['query'], indent=2))
        print()

        print("⚙️  Executing aggregation pipeline...")
        results = execute_mongodb_query(info)
        
        if results is None:
            print("❌ Query execution failed.\n")
            continue
        
        print(f"✅ Query executed successfully. Found {len(results)} result(s).")
        print(f"Results preview: {json.dumps(results, indent=2, ensure_ascii=False)}\n")

        print("💬 Generating natural language response...\n")
        
        print("=" * 70)
        print("RĂSPUNS:")
        print("=" * 70)
        print(generate_human_response(q, results, street))
        print("=" * 70)
        print()

if __name__ == "__main__":
    main()