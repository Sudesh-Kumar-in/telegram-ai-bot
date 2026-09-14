"""
database.py
------------
SQLite database interaction.

Vercel/serverless runtime ke liye database schema ko har connection par
ensure kiya jata hai, taaki conversation_history table missing na ho.
"""

import sqlite3
import asyncio
import logging
from contextlib import contextmanager
from typing import List, Tuple

from config import DATABASE_PATH, MAX_HISTORY_MESSAGES

logger = logging.getLogger(__name__)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_user_id
ON conversation_history (user_id, id)
"""


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Required database tables/indexes ensure karta hai."""
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    cursor.execute(CREATE_INDEX_SQL)


@contextmanager
def get_connection():
    """SQLite connection with automatic schema initialization."""
    conn = sqlite3.connect(DATABASE_PATH)

    try:
        _ensure_schema(conn)
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def _init_db_sync() -> None:
    """Database schema initialize karta hai."""
    with get_connection():
        pass

    logger.info("Database initialized successfully.")


async def init_db() -> None:
    """Async database initialization."""
    await asyncio.to_thread(_init_db_sync)


def _save_message_sync(
    user_id: int,
    role: str,
    content: str,
) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversation_history
            (user_id, role, content)
            VALUES (?, ?, ?)
            """,
            (user_id, role, content),
        )


async def save_message(
    user_id: int,
    role: str,
    content: str,
) -> None:
    """User ya assistant ka message save karta hai."""
    await asyncio.to_thread(
        _save_message_sync,
        user_id,
        role,
        content,
    )


def _get_history_sync(
    user_id: int,
    limit: int,
) -> List[Tuple[str, str]]:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM conversation_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )

        rows = cursor.fetchall()

    return list(reversed(rows))


async def get_history(
    user_id: int,
    limit: int = MAX_HISTORY_MESSAGES,
) -> List[Tuple[str, str]]:
    """Recent conversation history return karta hai."""
    return await asyncio.to_thread(
        _get_history_sync,
        user_id,
        limit,
    )


def _clear_history_sync(user_id: int) -> None:

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM conversation_history
            WHERE user_id = ?
            """,
            (user_id,),
        )


async def clear_history(user_id: int) -> None:
    """User ki conversation history clear karta hai."""
    await asyncio.to_thread(
        _clear_history_sync,
        user_id,
    )
