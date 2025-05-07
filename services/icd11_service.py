from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
app = Flask(__name__)
load_dotenv(override=True)
# Replace with your real ICD-11 API key
API_KEY = os.getenv("ClientId")
API_BASE_URL = "https://id.who.int/icd/release/11"

# ICD-11 Search Endpoint
def search_icd11(query):
    headers = {
        "Accept": "application/json",
        "API-Version": "v2",
        "Authorization": f"Bearer {API_KEY}"
    }
    params = {
        "q": query,
        "flatResults": "true"
    }
    response = requests.get(f"{API_BASE_URL}/browse/search", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"ICD-11 API error: {response.status_code}"}

# Route to handle ICD-11 search
@app.route("/icd11/search", methods=["GET"])
def icd11_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    result = search_icd11(query)
    if "error" in result:
        return jsonify(result), 500

    # Format the output for easier frontend integration
    entities = result.get("destinationEntities", [])
    formatted = [
        {
            "code": entity.get("theCode"),
            "title": entity.get("title", {}).get("@value"),
            "uri": entity.get("theUri")
        }
        for entity in entities
    ]
    return jsonify(formatted)

if __name__ == "__main__":
    app.run(debug=False)
