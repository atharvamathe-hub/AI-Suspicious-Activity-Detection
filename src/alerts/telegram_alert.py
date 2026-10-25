
import os
import requests
from dotenv import load_dotenv


class TelegramAlert:
    def __init__(self):
        load_dotenv()

        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.token or not self.chat_id:
            raise ValueError(
                "Telegram credentials are missing from .env"
            )

        self.base_url = (
            f"https://api.telegram.org/bot{self.token}"
        )

    def send_message(self, activity, video_path):
        message = (
            f"🚨 SUSPICIOUS ACTIVITY DETECTED\n\n"
            f"Activity: {activity}\n"
            f"Evidence: {os.path.basename(video_path)}"
        )

        response = requests.post(
            f"{self.base_url}/sendMessage",
            data={
                "chat_id": self.chat_id,
                "text": message,
            },
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()
        if not result.get("ok"):
            raise RuntimeError(
                f"Telegram message failed: {result}"
            )

    def send_video(self, video_path, activity):
        if not os.path.isfile(video_path):
            raise FileNotFoundError(video_path)

        message = f"Evidence clip: {activity}"

        with open(video_path, "rb") as video:
            response = requests.post(
                f"{self.base_url}/sendVideo",
                data={
                    "chat_id": self.chat_id,
                    "caption": message,
                },
                files={"video": video},
                timeout=120,
            )

        response.raise_for_status()

        result = response.json()
        if not result.get("ok"):
            raise RuntimeError(
                f"Telegram video upload failed: {result}"
            )
