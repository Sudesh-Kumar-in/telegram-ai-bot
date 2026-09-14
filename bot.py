"""
bot.py
-------
Application ka main entry point.
Ye file:
  1. Logging setup karti hai (bina kisi sensitive info ke).
  2. Config validate karti hai (.env se required variables check).
  3. Database initialize karti hai.
  4. Telegram bot application banake handlers register karti hai.
  5. Bot ko polling mode mein run karti hai.

Run karne ke liye:
    python bot.py
"""

import logging
import asyncio

from telegram.ext import Application, CommandHandler, MessageHandler, filters

import config
import database
import handlers


def setup_logging() -> None:
    """
    Application-wide logging configure karta hai.
    IMPORTANT: Kahin bhi API keys ya tokens print/log nahi kiye jaate.
    """
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    # Third-party libraries ka verbose (DEBUG) logging chup kar do
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)


async def _post_init(application: Application) -> None:
    """Bot start hone ke turant baad database initialize karta hai."""
    await database.init_db()


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Telegram AI bot...")

    # Zaroori environment variables check karo; missing hone par clear
    # error message dekar process exit kar dega.
    config.validate_config()

    # Telegram Application banao (token .env se aata hai, kabhi hardcode nahi)
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # ---- Command handlers ----
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("clear", handlers.clear_command))

    # ---- Normal text messages (commands ke alawa sab) ----
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    # ---- Global error handler ----
    application.add_error_handler(handlers.error_handler)

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Polling mode mein run karo (simple aur deployment ke liye kaafi hai)
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
