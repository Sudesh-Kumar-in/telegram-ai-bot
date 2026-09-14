"""
handlers.py
------------
Saare Telegram command aur message handlers is file mein hain:
  - /start
  - /help
  - /clear
  - Normal text messages (AI chat)

Har handler async hai aur python-telegram-bot ke Update/ContextTypes
ke saath kaam karta hai.
"""

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

import database
from config import TELEGRAM_MESSAGE_LIMIT, MAX_HISTORY_MESSAGES
from openai_service import generate_response, OpenAIServiceError

logger = logging.getLogger(__name__)


WELCOME_MESSAGE = (
    "👋 Namaste! Main aapka AI-powered Telegram assistant hoon.\n\n"
    "Aap mujhe koi bhi sawal ya message bhej sakte hain, aur main OpenAI ki "
    "madad se aapko jawab dunga. Main hamari recent conversation yaad bhi "
    "rakhta hoon, taaki context ke saath baat kar sakoon.\n\n"
    "Shuru karne ke liye bas neeche message type karein, ya /help likhein "
    "available commands dekhne ke liye."
)

HELP_MESSAGE = (
    "🛠 *Available Commands*\n\n"
    "/start - Bot ka welcome message dikhaye\n"
    "/help - Ye help message dikhaye\n"
    "/clear - Aapki conversation history delete kare\n\n"
    "*Kaise use karein:*\n"
    "Bas normal message type karke bhej dein, bot AI-generated response "
    "dega. Bot pichle kuch messages ka context yaad rakhta hai, isliye aap "
    "follow-up questions bhi pooch sakte hain.\n\n"
    "Agar aap conversation history reset karna chahte hain (fresh start "
    "ke liye), to /clear command use karein."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start command handler."""
    await update.message.reply_text(WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help command handler."""
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/clear command handler - current user ki history delete karta hai."""
    user_id = update.effective_user.id
    try:
        await database.clear_history(user_id)
        await update.message.reply_text(
            "✅ Aapki conversation history delete kar di gayi hai. Fresh start!"
        )
    except Exception as e:
        logger.exception("Failed to clear history for user %s: %s", user_id, e)
        await update.message.reply_text(
            "⚠️ History clear karte waqt ek error aa gayi. Kripya dobara try karein."
        )


async def _send_long_message(update: Update, text: str) -> None:
    """
    Telegram ki message length limit (4096 chars) se bada text ho to
    usse multiple chunks mein split karke sequentially bhejta hai.
    """
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        await update.message.reply_text(text)
        return

    for i in range(0, len(text), TELEGRAM_MESSAGE_LIMIT):
        chunk = text[i : i + TELEGRAM_MESSAGE_LIMIT]
        await update.message.reply_text(chunk)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Normal (non-command) text messages ka handler.
    Flow:
      1. User ka message DB mein save karo.
      2. Typing indicator dikhao.
      3. Purani history fetch karke OpenAI ko bhejo.
      4. AI ka response user ko bhejo aur DB mein save karo.
    """
    user = update.effective_user
    user_id = user.id
    user_message = update.message.text

    if not user_message or not user_message.strip():
        await update.message.reply_text("Kripya ek valid text message bhejein.")
        return

    # Bahut lamba input safe limit tak truncate kar do (abuse/errors se bachne ke liye)
    if len(user_message) > 4000:
        user_message = user_message[:4000]

    logger.info("Received message from user_id=%s", user_id)

    try:
        # Typing indicator on karo jab tak AI response generate ho raha hai
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )

        # Pehle user ka message save karo
        await database.save_message(user_id, "user", user_message)

        # Context ke liye recent history lao (isi latest message samet)
        history = await database.get_history(user_id, limit=MAX_HISTORY_MESSAGES)
        # history mein humne abhi jo message save kiya wo bhi aa jayega,
        # isliye use history se hata kar generate_response ko current
        # message alag se pass karte hain (duplicate hone se bachne ke liye).
        history_without_current = history[:-1] if history else []

        ai_response = await generate_response(history_without_current, user_message)

        # AI ka response bhi save karo, taaki future context mein use ho
        await database.save_message(user_id, "assistant", ai_response)

        await _send_long_message(update, ai_response)

    except OpenAIServiceError as e:
        # openai_service.py mein already user-friendly message bana di gayi hai
        await update.message.reply_text(f"⚠️ {e}")

    except Exception as e:
        logger.exception("Unexpected error handling message from user_id=%s: %s", user_id, e)
        await update.message.reply_text(
            "⚠️ Kuch galat ho gaya. Kripya thodi der baad dobara try karein."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler - koi bhi unhandled exception (Telegram API errors
    included) yahan pakda jata hai, taaki bot crash na ho.
    """
    logger.error("Unhandled exception while processing update: %s", context.error, exc_info=context.error)

    # Agar possible ho to user ko bhi ek friendly message bhej do
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Ek unexpected error aa gayi. Kripya thodi der baad dobara try karein."
            )
        except Exception:
            # Agar ye bhi fail ho jaye, to bas log kar ke chhod do
            logger.exception("Failed to send error message to user.")
