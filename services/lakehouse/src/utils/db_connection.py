"""
PostgreSQL connection pool using psycopg v3 and psycopg_pool.

Provides a context-manager interface so callers never need to manually
acquire or release connections.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

from src.config import Settings

logger = logging.getLogger(__name__)


class PgConnectionPool:
    """Thread-safe PostgreSQL connection pool backed by psycopg v3.

    Args:
        config: Application settings with DB_* connection fields.
    """

    _MIN_SIZE = 2
    _MAX_SIZE = 10

    def __init__(self, config: Settings) -> None:
        self._config = config
        self._pool: ConnectionPool | None = None
        self._connect()

    def _connect(self) -> None:
        """Initialise the underlying psycopg_pool.ConnectionPool."""
        logger.info(
            "Connecting to PostgreSQL at %s:%d/%s",
            self._config.DB_HOST,
            self._config.DB_PORT,
            self._config.DB_NAME,
        )
        self._pool = ConnectionPool(
            conninfo=self._config.db_conninfo,
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
    def get_connection(self) -> Generator[psycopg.Connection]:
        """Context manager that yields a psycopg v3 Connection.

        Commits on clean exit; rolls back and re-raises on exception.
        The connection is always returned to the pool in the finally block.

        Yields:
            An open psycopg.Connection object.

        Raises:
            psycopg.OperationalError: If the pool is exhausted or unreachable.
        """
        if self._pool is None:
            self._connect()

        assert self._pool is not None
        with self._pool.connection() as conn:
            yield conn

    def health_check(self) -> bool:
        """Run SELECT 1 to verify the database is reachable.

        Returns:
            True if the database responds correctly, False otherwise.
        """
        try:
            with self.get_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result is not None and result[0] == 1
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return False

    def close(self) -> None:
        """Close all connections in the pool and release resources."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            logger.info("Connection pool closed.")
