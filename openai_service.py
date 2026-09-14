"""
openai_service.py
-------------------
OpenAI API ke saath saara communication is file mein hota hai.
Latest official 'openai' Python SDK (AsyncOpenAI client) use kiya gaya hai,
jo current recommended approach hai (deprecated `openai.ChatCompletion.create`
jaisa purana style use nahi kiya gaya).
"""

import logging
from typing import List, Tuple

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT

logger = logging.getLogger(__name__)

# Single shared async client (poore app mein reuse hota hai)
client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)

SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant chatting with a user on Telegram. "
    "Keep responses clear and reasonably concise unless the user asks for detail."
)


class OpenAIServiceError(Exception):
    """Custom exception - jab AI response generate karne mein koi problem ho."""


def _build_messages(history: List[Tuple[str, str]], user_message: str) -> list:
    """
    Database se aayi history (role, content) tuples ko OpenAI ke
    expected message format mein convert karta hai, system prompt ke saath.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


async def generate_response(history: List[Tuple[str, str]], user_message: str) -> str:
    """
    OpenAI Chat Completions API ko call karke AI ka response return karta hai.
    Conversation history context ke liye pehle se include ki jaati hai.

    Errors (auth, rate limit, timeout, generic API error) ko catch karke
    OpenAIServiceError raise kiya jata hai, jisse caller user-friendly
    message dikha sake.
    """
    messages = _build_messages(history, user_message)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        content = response.choices[0].message.content
        if not content:
            raise OpenAIServiceError("OpenAI se khaali response mila.")
        return content.strip()

    except AuthenticationError:
        logger.error("OpenAI authentication failed. Check OPENAI_API_KEY (value not logged).")
        raise OpenAIServiceError(
            "AI service authenticate nahi ho paayi. Bot admin ko OpenAI API key check karni chahiye."
        )

    except RateLimitError:
        logger.warning("OpenAI rate limit hit.")
        raise OpenAIServiceError(
            "Abhi AI service par bahut load hai (rate limit). Kripya thodi der baad try karein."
        )

    except APITimeoutError:
        logger.warning("OpenAI request timed out.")
        raise OpenAIServiceError(
            "AI response generate karne mein zyada time lag gaya. Kripya dobara try karein."
        )

    except APIError as e:
        logger.error("OpenAI API error: %s", e)
        raise OpenAIServiceError(
            "AI service se response lene mein ek error aayi. Kripya thodi der baad try karein."
        )

    except Exception as e:
        logger.exception("Unexpected error while calling OpenAI API: %s", e)
        raise OpenAIServiceError(
            "Ek unexpected error aayi. Kripya thodi der baad dobara try karein."
        )
