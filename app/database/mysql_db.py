"""MySQL connection and query helpers."""

from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector import Error

from app.config import settings


class DatabaseError(RuntimeError):
    """Raised when a database operation cannot be completed."""


@contextmanager
def connection(include_database: bool = True) -> Iterator[Any]:
    config = settings.mysql_config.copy()
    if not include_database:
        config.pop("database", None)
    conn = None
    try:
        conn = mysql.connector.connect(**config)
        yield conn
    except Error as exc:
        raise DatabaseError(f"MySQL operation failed: {exc}") from exc
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


@contextmanager
def cursor(dictionary: bool = True) -> Iterator[Any]:
    with connection() as conn:
        cur = conn.cursor(dictionary=dictionary)
        try:
            yield cur
        finally:
            cur.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with cursor() as cur:
        cur.execute(query, params)
        return list(cur.fetchall())


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None
