"""
database.py
------------
SQLite database ke saath saara interaction is file mein hai.
Har user ki conversation history alag se store hoti hai (user_id ke basis par),
isliye ek user ki history kabhi doosre user ko nahi dikhti.

Async bot ke andar blocking SQLite calls seedha use na karne ke liye,
hum har DB operation ko a thread executor mein run karte hain
(asyncio.to_thread), taaki event loop block na ho.
"""

import sqlite3
import asyncio
import logging
from contextlib import contextmanager
from typing import List, Tuple

from config import DATABASE_PATH, MAX_HISTORY_MESSAGES

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """SQLite connection ka context manager (auto commit/close)."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_db_sync() -> None:
    """Database table create karta hai agar pehle se exist nahi karti."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Fast lookups ke liye index (per-user history fetch tezi se ho)
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_id
            ON conversation_history (user_id, id)
            """
        )
    logger.info("Database initialized successfully.")


async def init_db() -> None:
    """Async wrapper - bot startup par ek baar call hota hai."""
    await asyncio.to_thread(_init_db_sync)


def _save_message_sync(user_id: int, role: str, content: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )


async def save_message(user_id: int, role: str, content: str) -> None:
    """
    Ek message (user ya assistant ka) database mein save karta hai.
    role: 'user' ya 'assistant'
    """
    await asyncio.to_thread(_save_message_sync, user_id, role, content)


def _get_history_sync(user_id: int, limit: int) -> List[Tuple[str, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content FROM conversation_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
    # DB se latest-first aaya hai, chronological (oldest-first) order mein palat do
    return list(reversed(rows))


async def get_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> List[Tuple[str, str]]:
    """
    User ki recent conversation history return karta hai (oldest -> newest order mein)
    List of tuples: [(role, content), ...]
    """
    return await asyncio.to_thread(_get_history_sync, user_id, limit)


def _clear_history_sync(user_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))


async def clear_history(user_id: int) -> None:
    """Ek specific user ki puri conversation history delete karta hai."""
    await asyncio.to_thread(_clear_history_sync, user_id)
