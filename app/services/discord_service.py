import requests
from app.config import Config

class DiscordService:
    @staticmethod
    def send_message(message):
        """Send a message to Discord using the webhook"""
        try:
            payload = {
                "content": message,
                "username": "Fisch Update Checker"
            }
            response = requests.post(Config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except (requests.RequestException, requests.Timeout) as e:
            print(f"Error sending to Discord: {e}")
            return False

    @staticmethod
    def test_connection():
        """Test the Discord connection"""
        if DiscordService.send_message("🎮 Fisch Update Checker is now online and monitoring for updates!"):
            print("Successfully connected to Discord!")
            return True
        print("Failed to connect to Discord. Please check your webhook URL.")
        return False
