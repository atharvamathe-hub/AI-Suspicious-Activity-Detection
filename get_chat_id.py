
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

if not token:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing from .env")

url = f"https://api.telegram.org/bot{token}/getUpdates"

response = requests.get(url, timeout=15)
response.raise_for_status()

data = response.json()

for update in data.get("result", []):
    message = update.get("message", {})
    chat = message.get("chat", {})

    if chat:
        print("Chat ID:", chat["id"])

