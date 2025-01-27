from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from weather_agent import WeatherAgent  # Import your WeatherAgent class
from language_agent import LanguageAgent  # Import your LanguageAgent class
import os
from datetime import datetime, timezone

load_dotenv()
app = Flask(__name__)
CORS(app)



# Initialize both agents
weather_agent = WeatherAgent()
language_agent = LanguageAgent()

# Define API key
API_KEY="neha-2024"
# Weather agent routes
@app.route("/weather/query", methods=["POST"])
def weather_query():
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing query parameter"}), 400

    try:
        response = weather_agent.process_query(data["query"])
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }), 500

# Language agent routes
@app.route("/language/query", methods=["POST"])
def language_query():
    data = request.get_json()
    if not data or "user_input" not in data:  # Check for user_input
        return jsonify({"error": "Missing user_input parameter"}), 400

    try:
        # Extract user_input and language from request
        user_input = data["user_input"]
        language = data.get("language", "en")  # Default to English if not specified
        
        # Call the language agent with both parameters
        response = language_agent.process_query(user_input, language)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)