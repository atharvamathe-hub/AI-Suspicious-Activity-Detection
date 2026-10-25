
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not token or not chat_id:
    raise ValueError("Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

url = f"https://api.telegram.org/bot{token}/sendMessage"

try:
    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": "AI Suspicious Activity Detection: Telegram test successful!"
        },
        timeout=20
    )

    print("HTTP status:", response.status_code)
    result = response.json()
    print("Telegram response:", {
        key: value for key, value in result.items()
        if key != "result"
    })

    if response.ok and result.get("ok"):
        print("[SUCCESS] Telegram message sent!")
    else:
        print("[FAILED] Check the error description above.")

except requests.RequestException as error:
    print("[NETWORK ERROR]", type(error).__name__, str(error))

