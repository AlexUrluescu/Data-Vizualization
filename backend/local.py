import os
import json
from pymongo import MongoClient
from openai import OpenAI

# MongoDB credentials
MONGO_USER = "alexurluescu23_db_user"
MONGO_PASSWORD = "y8MDoUisyGf2Gayo"
MONGO_CLUSTER = "cluster0.c9gvi0h.mongodb.net"
MONGO_DB = "urbanbike"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/v1"  # OpenAI-compatible API endpoint
OLLAMA_MODEL = "qwen3:30b"

# MongoDB connection
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?appName={MONGO_DB}"

print(MONGO_URI)
client_mongo = MongoClient(MONGO_URI)
db = client_mongo.urbanbike

# Ollama setup (OpenAI-compatible)
llm = OpenAI(
    base_url=OLLAMA_URL,
    api_key="ollama"  # Ollama doesn't require a real API key, but the client needs something
)

print(f"llm {llm}")

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
"""

def generate_mongodb_query(question):
    """Use Ollama to generate a MongoDB query from natural language."""
    try:
        prompt = f"""You are a MongoDB query generator. Given a natural language question, generate the appropriate MongoDB query.

{SCHEMA_INFO}

Question: {question}

Generate a MongoDB query to answer this question. Respond with a JSON object containing:
1. "collection": the collection to query (either "cities" or "cars")
2. "operation": the operation type ("find", "aggregate", "count", etc.)
3. "query": the actual MongoDB query/pipeline as a Python dictionary
4. "explanation": brief explanation of what the query does

IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks, no additional text.

Example response:
{{
  "collection": "cars",
  "operation": "aggregate",
  "query": [...],
  "explanation": "This query finds the total cars..."
}}
"""
        
        # Invoke the LLM using OpenAI-compatible API
        response = llm.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a MongoDB query generator that responds only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Extract content from response
        content = response.choices[0].message.content
        
        # Clean the response (remove markdown code blocks if present)
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
        return None

def generate_human_response(question, results):
    """Use Ollama to generate a human-friendly response."""
    try:
        prompt = f"""You are a helpful assistant. Based on the user's question and the data retrieved from the database, provide a clear, natural, and informative response.

User Question: {question}

Database Results: {json.dumps(results, indent=2)}

Generate a human-friendly response that answers the user's question based on the data. Be conversational and clear.
"""
        
        # Invoke the LLM using OpenAI-compatible API
        response = llm.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides clear and natural responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Extract content from response
        answer = response.choices[0].message.content
        
        return answer
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't generate a response based on the data."

def main():
    """Main function to run the AI-powered MongoDB assistant."""
    print("=" * 60)
    print("AI-Powered MongoDB Query Assistant (Ollama)")
    print("=" * 60)
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
        print(query_info)
        results = execute_mongodb_query(query_info)
        
        if results is None:
            print("❌ Failed to execute query.\n")
            continue
        
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