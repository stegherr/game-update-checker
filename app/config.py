"""Configuration settings for the application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the application."""
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
    USER_AGENT = os.getenv('USER_AGENT')
    WIKI_PAGE_URL = os.getenv('WIKI_PAGE_URL')
    TEMPLATES_AUTO_RELOAD = True  # Ensure templates are reloaded on every request
    PORT = 5000
