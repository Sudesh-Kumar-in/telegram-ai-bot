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
    start_command,
    help_command,
    clear_command,
    handle_message,
    error_handler,
)


async def create_application():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
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


def app(environ, start_response):
    """
    WSGI entrypoint required by Vercel Python runtime.
    """

    method = environ.get("REQUEST_METHOD", "GET")

    content_length = environ.get("CONTENT_LENGTH", "0")

    try:
        content_length = int(content_length)
    except (TypeError, ValueError):
        content_length = 0

    body = b""

    if content_length > 0:
        body = environ["wsgi.input"].read(content_length)

    headers = {}

    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].lower().replace("_", "-")
            headers[header_name] = value

    request = type(
        "Request",
        (),
        {
            "method": method,
            "body": body,
            "headers": headers,
        },
    )()

    result = handler(request)

    status_code = result.get("statusCode", 200)

    status_messages = {
        200: "OK",
        400: "Bad Request",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }

    status_text = status_messages.get(
        status_code,
        "OK",
    )

    response_headers = [
        (key, value)
        for key, value in result.get("headers", {}).items()
    ]

    start_response(
        f"{status_code} {status_text}",
        response_headers,
    )

    return [
        result.get("body", "").encode("utf-8")
    ]
