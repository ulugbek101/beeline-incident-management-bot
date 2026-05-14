import asyncpg
from typing import Any


class Database:
    """Async PostgreSQL interface backed by an asyncpg connection pool.

    Lifecycle::

        db = Database(host=..., port=..., user=..., password=..., db_name=...)
        await db.connect()   # call once on startup
        ...
        await db.close()     # call once on shutdown

    All query methods acquire a connection from the pool for the duration of
    the call and release it immediately after, so they are safe to call
    concurrently from multiple aiogram handlers.

    Note: asyncpg uses ``$1, $2, ...`` positional placeholders, not ``%s``.
    """

    def __init__(self, host: str, port: int, user: str, password: str, db_name: str) -> None:
        """Store connection parameters; pool is created lazily via :meth:`connect`.

        Args:
            host:     PostgreSQL server hostname or IP address.
            port:     PostgreSQL server port (typically 5432).
            user:     PostgreSQL username.
            password: PostgreSQL password.
            db_name:  Name of the database to connect to.
        """
        self._dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create the connection pool. Must be called once before any queries.

        Raises:
            asyncpg.PostgresError: If the connection parameters are invalid or
                the server is unreachable.
        """
        self.pool = await asyncpg.create_pool(dsn=self._dsn)

    async def close(self) -> None:
        """Gracefully close all connections in the pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, sql: str, *params: Any) -> str:
        """Execute a statement that returns no rows (INSERT / UPDATE / DELETE).

        Args:
            sql:    SQL string with ``$1, $2, ...`` placeholders.
            *params: Values bound to the placeholders in order.

        Returns:
            PostgreSQL command tag, e.g. ``"INSERT 0 1"`` or ``"UPDATE 3"``.

        Raises:
            asyncpg.PostgresError: On query failure.
        """
        async with self.pool.acquire() as conn:
            return await conn.execute(sql, *params)

    async def fetchone(self, sql: str, *params: Any) -> asyncpg.Record | None:
        """Fetch the first matching row.

        Args:
            sql:    SQL string with ``$1, $2, ...`` placeholders.
            *params: Values bound to the placeholders in order.

        Returns:
            A single :class:`asyncpg.Record` (dict-like), or ``None`` if no
            rows matched.

        Raises:
            asyncpg.PostgresError: On query failure.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(sql, *params)

    async def fetchall(self, sql: str, *params: Any) -> list[asyncpg.Record]:
        """Fetch all matching rows.

        Args:
            sql:    SQL string with ``$1, $2, ...`` placeholders.
            *params: Values bound to the placeholders in order.

        Returns:
            A list of :class:`asyncpg.Record` objects (each is dict-like).
            Returns an empty list when no rows match.

        Raises:
            asyncpg.PostgresError: On query failure.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql, *params)

    async def fetchval(self, sql: str, *params: Any) -> Any:
        """Fetch a single scalar value from the first column of the first row.

        Convenient for aggregates such as ``COUNT(*)``, ``MAX(id)``, etc.

        Args:
            sql:    SQL string with ``$1, $2, ...`` placeholders.
            *params: Values bound to the placeholders in order.

        Returns:
            The value of the first column of the first matching row, or
            ``None`` if no rows matched.

        Raises:
            asyncpg.PostgresError: On query failure.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(sql, *params)

    async def create_users_table(self) -> None:
        """Create the ``users`` table if it does not already exist.

        Columns:
            id          — SERIAL primary key, auto-increment, not null.
            telegram_id — TEXT, not null. Telegram user ID stored as text.
            fullname    — TEXT, not null. User's full name from Telegram.

        Raises:
            asyncpg.PostgresError: On query failure.
        """
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          SERIAL      PRIMARY KEY NOT NULL,
                telegram_id TEXT        NOT NULL,
                fullname    TEXT        NOT NULL
            )
        """)
