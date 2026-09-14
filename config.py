"""
config.py
----------
Saari configuration aur environment variables yahin se load hoti hain.
Koi bhi secret (API key/token) is file ke andar hardcode NAHI hai.
Sab kuch ".env" file se read hota hai.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# .env file load karo (agar exist karti hai)
load_dotenv()

logger = logging.getLogger(__name__)

# ---- Required environment variables ----
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- Optional environment variables (with sensible defaults) ----
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

# Kitne purane messages context ke liye OpenAI ko bheje jayenge (per user)
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES") or "10")

# OpenAI request timeout (seconds)
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT") or "60")

# Telegram ka single message character limit (safety margin ke saath)
TELEGRAM_MESSAGE_LIMIT = 4000


def validate_config() -> None:
    """
    Startup par zaroori environment variables check karta hai.
    Agar koi required variable missing hai to clear error dekar
    process ko turant band kar deta hai (taaki bot silently fail na ho).
    """
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        logger.error(
            "Missing required environment variable(s): %s. "
            "Please set them in your .env file (see .env.example).",
            ", ".join(missing),
        )
        print(
            "\n[CONFIG ERROR] Ye environment variables .env file mein missing hain:\n"
            f"  - {', '.join(missing)}\n\n"
            "Steps:\n"
            "  1. '.env.example' ko copy karke '.env' banao.\n"
            "  2. '.env' file mein apni values fill karo.\n"
            "  3. Bot dobara run karo.\n"
        )
        sys.exit(1)
