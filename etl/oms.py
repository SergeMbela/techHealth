import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Get the API key from environment variables
API_KEY = os.getenv("ClientSecret")
API_BASE_URL = "https://id.who.int/icd/release/11"

# ICD-11 Search Endpoint Function
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

    try:
        response = requests.get(f"{API_BASE_URL}/browse/search", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}

# Example usage
if __name__ == "__main__":
    result = search_icd11("diabetes")
    print(result)

