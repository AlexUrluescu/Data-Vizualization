import os
import json
import requests
from typing import List, Dict
from pymongo import MongoClient
from bson import ObjectId

# MongoDB credentials
MONGO_USER = "alexurluescu23_db_user"
MONGO_PASSWORD = "y8MDoUisyGf2Gayo"
MONGO_CLUSTER = "cluster0.c9gvi0h.mongodb.net"
MONGO_DB = "urbanbike"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"

# MongoDB connection
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?appName={MONGO_DB}"

print(MONGO_URI)
client_mongo = MongoClient(MONGO_URI)
db = client_mongo.urbanbike

# Database schema information
SCHEMA_INFO = """
Database: urbanbike

Collection 1: cities
Schema:
{
  _id: ObjectId,
  name: string,
  region: string
}

Collection 2: cars
Schema:
{
  _id: ObjectId,
  cityId: ObjectId,  # References cities._id
  year: number,
  amount: number
}

Relationship: cars.cityId references cities._id

IMPORTANT NOTES FOR QUERY GENERATION:
1. When a question references a city name, you MUST use an aggregate pipeline with $lookup to join cities and cars collections
2. NEVER use {'$oid': '...'} syntax - this is invalid in PyMongo
3. For questions about specific cities, always use $lookup to match city names
4. Use aggregate pipelines for any query involving joins between collections
5. For questions comparing TWO YEARS, use $group with $cond to separate the years, then use $subtract to calculate the difference
"""

def ollama_chat(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    timeout: int = 360000,
) -> str:
    """
    Calls Ollama's native /api/chat endpoint using requests.
    Returns the assistant message content string.
    """
    print(messages)
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": 12000,
            "temperature": temperature,
            "top_k": 30,
            "top_p": 0.9,
            "num_predict": -1
        }
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["message"]["content"]
    except Exception:
        return f"[Unexpected response]\n{json.dumps(data, indent=2)}"


def check_ollama_connection():
    """Check if Ollama is running and model is available."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json()
        
        available_models = [model['name'] for model in models.get('models', [])]
        
        print(f"✅ Ollama is running")
        print(f"📦 Available models: {', '.join(available_models)}\n")
        
        if OLLAMA_MODEL not in available_models:
            print(f"⚠️  Warning: Model '{OLLAMA_MODEL}' not found!")
            print(f"💡 Please either:")
            print(f"   1. Pull the model: ollama pull {OLLAMA_MODEL}")
            print(f"   2. Change OLLAMA_MODEL to one of: {', '.join(available_models)}\n")
            return False
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"   Make sure Ollama is running: ollama serve")
        print(f"   Error: {e}\n")
        return False

def generate_mongodb_query(question):
    """Use Ollama to generate a MongoDB query from natural language."""
    try:
        prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

{SCHEMA_INFO}

Question: {question}

Generate a MongoDB query to answer this question. Respond with a JSON object containing:
1. "collection": the collection to query (either "cities" or "cars")
2. "operation": the operation type ("find", "aggregate", "count", etc.)
3. "query": the actual MongoDB query/pipeline as a Python list or dictionary
4. "explanation": brief explanation of what the query does

CRITICAL RULES:
- If the question mentions a city NAME (like "Sibiu", "București", etc.), you MUST use "aggregate" operation with $lookup
- NEVER use {{"$oid": "..."}} syntax - use direct ObjectId values or $lookup for joins
- For single year queries, use this pattern:
  {{
    "collection": "cars",
    "operation": "aggregate",
    "query": [
      {{
        "$lookup": {{
          "from": "cities",
          "localField": "cityId",
          "foreignField": "_id",
          "as": "city"
        }}
      }},
      {{"$unwind": "$city"}},
      {{
        "$match": {{
          "city.name": "CityName",
          "year": YearNumber
        }}
      }},
      {{
        "$group": {{
          "_id": null,
          "total": {{"$sum": "$amount"}}
        }}
      }}
    ]
  }}

- For COMPARING TWO YEARS (e.g., "difference between 2022 and 2014"), use this pattern:
  {{
    "collection": "cars",
    "operation": "aggregate",
    "query": [
      {{
        "$lookup": {{
          "from": "cities",
          "localField": "cityId",
          "foreignField": "_id",
          "as": "city"
        }}
      }},
      {{"$unwind": "$city"}},
      {{
        "$match": {{
          "city.name": "CityName",
          "year": {{"$in": [Year1, Year2]}}
        }}
      }},
      {{
        "$group": {{
          "_id": null,
          "year1_total": {{
            "$sum": {{
              "$cond": [{{"$eq": ["$year", Year1]}}, "$amount", 0]
            }}
          }},
          "year2_total": {{
            "$sum": {{
              "$cond": [{{"$eq": ["$year", Year2]}}, "$amount", 0]
            }}
          }}
        }}
      }},
      {{
        "$project": {{
          "_id": 0,
          "year1": Year1,
          "year1_total": "$year1_total",
          "year2": Year2,
          "year2_total": "$year2_total",
          "difference": {{"$subtract": ["$year1_total", "$year2_total"]}}
        }}
      }}
    ]
  }}

IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks, no additional text.

Example response for "What is the difference between 2022 and 2014 in Sibiu?":
{{
  "collection": "cars",
  "operation": "aggregate",
  "query": [
    {{
      "$lookup": {{
        "from": "cities",
        "localField": "cityId",
        "foreignField": "_id",
        "as": "city"
      }}
    }},
    {{"$unwind": "$city"}},
    {{
      "$match": {{
        "city.name": "Sibiu",
        "year": {{"$in": [2022, 2014]}}
      }}
    }},
    {{
      "$group": {{
        "_id": null,
        "total_2022": {{
          "$sum": {{
            "$cond": [{{"$eq": ["$year", 2022]}}, "$amount", 0]
          }}
        }},
        "total_2014": {{
          "$sum": {{
            "$cond": [{{"$eq": ["$year", 2014]}}, "$amount", 0]
          }}
        }}
      }}
    }},
    {{
      "$project": {{
        "_id": 0,
        "year_2022": 2022,
        "total_2022": "$total_2022",
        "year_2014": 2014,
        "total_2014": "$total_2014",
        "difference": {{"$subtract": ["$total_2022", "$total_2014"]}}
      }}
    }}
  ],
  "explanation": "This query joins cars with cities, filters for Sibiu in years 2022 and 2014, groups data to sum amounts for each year separately using $cond, then calculates the difference (2022 - 2014)"
}}
"""
        
        messages = [
            {"role": "system", "content": "You are a MongoDB query generator that responds only with valid JSON. Always use $lookup for queries involving city names. For comparing two years, use $group with $cond to separate the data, then $project with $subtract."},
            {"role": "user", "content": prompt}
        ]
        
        content = ollama_chat(
            base_url=OLLAMA_URL,
            model=OLLAMA_MODEL,
            messages=messages,
            temperature=0
        )
        
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

def generate_human_response(question, results):
    """Use Ollama to generate a human-friendly response."""
    try:
        prompt = f"""You are a helpful assistant. Based on the user's question and the data retrieved from the database, provide a clear, natural, and informative response in Romanian.

User Question: {question}

Database Results: {json.dumps(results, indent=2)}

Generate a human-friendly response that answers the user's question based on the data. Be conversational and clear.
If the results contain totals or differences, use those numbers in your response.
If comparing two years, mention both years and their values, then state the difference.
"""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides clear and natural responses in Romanian."},
            {"role": "user", "content": prompt}
        ]
        
        answer = ollama_chat(
            base_url=OLLAMA_URL,
            model=OLLAMA_MODEL,
            messages=messages,
            temperature=0.3
        )
        
        if not answer:
            return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."
        
        return answer
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Îmi pare rău, nu am putut genera un răspuns pe baza datelor."

def main():
    """Main function to run the AI-powered MongoDB assistant."""
    print("=" * 60)
    print("AI-Powered MongoDB Query Assistant (Ollama)")
    print("=" * 60)
    
    # Check Ollama connection first
    if not check_ollama_connection():
        return
    
    print("Ask questions about cities and cars data.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        # Get user question
        question = input("Your question: ").strip()
        
        if question.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break
        
        if not question:
            continue
        
        print("\n🔍 Generating MongoDB query...")
        
        # Step 1: Generate MongoDB query
        query_info = generate_mongodb_query(question)
        
        if not query_info:
            print("❌ Failed to generate query. Please try rephrasing your question.\n")
            continue
        
        print(f"📊 Query type: {query_info['operation']} on '{query_info['collection']}' collection")
        print(f"💡 Explanation: {query_info['explanation']}\n")
        
        # Step 2: Execute query
        print("⚙️  Executing query...")
        print(f"Query details: {json.dumps(query_info['query'], indent=2)}\n")
        results = execute_mongodb_query(query_info)
        
        if results is None:
            print("❌ Failed to execute query.\n")
            continue
        
        print(f"✅ Query executed successfully. Found {len(results) if isinstance(results, list) else 1} result(s).")
        print(f"Results preview: {json.dumps(results, indent=2)}\n")
        
        # Step 3: Generate human response
        print("💬 Generating response...\n")
        human_response = generate_human_response(question, results)
        
        print("=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(human_response)
        print("=" * 60)
        print()

if __name__ == "__main__":
    main()