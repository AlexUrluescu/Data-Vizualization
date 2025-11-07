# app/routes/traffic_routes.py
from flask import Blueprint, request, jsonify
from app.ai.traffic_assistant import generate_mongodb_query, execute_mongodb_query, generate_human_response

traffic_routes = Blueprint("traffic_routes", __name__)

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

        # 1. Generează query-ul cu AI-ul tău
        query_info = generate_mongodb_query(question)
        if not query_info:
            return jsonify({
                "error": "Nu am înțeles întrebarea. Încearcă să reformulezi.",
                "question": question
            }), 400

        # 2. Execută query-ul
        results = execute_mongodb_query(query_info)
        if results is None or (isinstance(results, list) and len(results) == 0):
            return jsonify({
                "error": "Nu am găsit date pentru această întrebare.",
                "question": question
            }), 404

        # 3. Generează răspunsul uman
        answer = generate_human_response(question, results)

        # Răspuns final
        return jsonify({
            "question": question,
            "answer": answer,
            "ai_method": query_info.get("recommended_processing", "mongo"),
            "raw_results": results  # opțional, pentru debug
        }), 200

    except Exception as e:
        print(f"Eroare endpoint /ask: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Eroare internă la procesarea întrebării.",
            "details": str(e)
        }), 500