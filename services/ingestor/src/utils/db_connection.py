"""
PostgreSQL connection pool management using psycopg v3.

Wraps psycopg_pool.ConnectionPool with a context manager interface
so callers never need to manually acquire or release connections.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg_pool import ConnectionPool as _PsycoPgPool

from src.config import Settings

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Thread-safe PostgreSQL connection pool backed by psycopg v3.

    Provides a context-manager-based interface so connections are always
    returned to the pool, even if an exception is raised.

    Args:
        config: Application settings object with DB_* fields.
    """

    _MIN_SIZE = 2
    _MAX_SIZE = 10

    def __init__(self, config: Settings) -> None:
        self._config = config
        conninfo = (
            f"host={config.DB_HOST} port={config.DB_PORT} "
            f"dbname={config.DB_NAME} user={config.DB_USER} "
            f"password={config.DB_PASSWORD} connect_timeout=10"
        )
        logger.info(
            "Connecting to PostgreSQL at %s:%d/%s",
            config.DB_HOST,
            config.DB_PORT,
            config.DB_NAME,
        )
        self._pool = _PsycoPgPool(
            conninfo=conninfo,
            min_size=self._MIN_SIZE,
            max_size=self._MAX_SIZE,
            open=True,
        )
        logger.info(
            "Connection pool created (min=%d, max=%d)",
            self._MIN_SIZE,
            self._MAX_SIZE,
        )

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Context manager that yields a psycopg v3 Connection.

        Commits on clean exit; rolls back and re-raises on exception.
        The connection is always returned to the pool in the finally block.

        Yields:
            An open psycopg.Connection object.

        Raises:
            psycopg.OperationalError: If the pool is exhausted or unreachable.
        """
        with self._pool.connection() as conn:
            yield conn

    def health_check(self) -> bool:
        """Run SELECT 1 to verify the database is reachable.

        Returns:
            True if the database responds correctly, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None and result[0] == 1
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return False

    def close(self) -> None:
        """Close all connections in the pool and release resources."""
        self._pool.close()
        logger.info("Connection pool closed.")
