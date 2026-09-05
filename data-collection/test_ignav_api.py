import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("IGNAV_API_KEY")

url = "https://ignav.com/api/fares/one-way"

headers = {
    "X-Api-Key": api_key,
    "Content-Type": "application/json",
}

payload = {
    "origin": "BLR",
    "destination": "DEL",
    "departure_date": "2026-10-02",
    "market": "IN",
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30,
)

print("API key loaded:", bool(api_key))
print("Status code:", response.status_code)
print(response.json())