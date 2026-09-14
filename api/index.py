import asyncio
import json

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start,
    help_command,
    clear,
    handle_message,
    error_handler,
)


async def create_application():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.add_error_handler(error_handler)

    await application.initialize()
    return application


def handler(request):
    if request.method == "GET":
        return setup_webhook(request)

    if request.method != "POST":
        return response(
            {"error": "Method not allowed"},
            405,
        )

    try:
        body = request.body

        if isinstance(body, bytes):
            body = body.decode("utf-8")

        update_data = json.loads(body or "{}")

    except Exception:
        return response(
            {"error": "Invalid JSON"},
            400,
        )

    async def process_update():
        application = await create_application()

        try:
            update = Update.de_json(
                update_data,
                application.bot,
            )

            await application.process_update(update)

        finally:
            await application.shutdown()

    try:
        asyncio.run(process_update())

        return response(
            {"ok": True},
            200,
        )

    except Exception as exc:
        print(f"Webhook error: {exc}")

        return response(
            {"ok": False},
            500,
        )


def setup_webhook(request):
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
    )

    if not host:
        return response(
            {"error": "Missing host"},
            400,
        )

    webhook_url = f"https://{host}/api/index"

    async def set_webhook():
        bot = Bot(TELEGRAM_BOT_TOKEN)

        try:
            await bot.initialize()
            await bot.set_webhook(webhook_url)
        finally:
            await bot.shutdown()

    try:
        asyncio.run(set_webhook())

        return response(
            {
                "ok": True,
                "webhook": webhook_url,
            },
            200,
        )

    except Exception as exc:
        print(f"Webhook setup error: {exc}")

        return response(
            {"ok": False},
            500,
        )


def response(data, status_code=200):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(data),
    }

app = handler
