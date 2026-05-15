import asyncpg
from typing import Any


class Database:
    """Асинхронный интерфейс к PostgreSQL на основе пула соединений asyncpg.

    Жизненный цикл::

        db = Database(host=..., port=..., user=..., password=..., db_name=...)
        await db.connect()   # вызвать один раз при старте
        ...
        await db.close()     # вызвать один раз при завершении

    Все методы запросов захватывают соединение из пула на время выполнения
    и сразу освобождают его, поэтому их можно безопасно вызывать параллельно
    из нескольких обработчиков aiogram.

    Примечание: asyncpg использует позиционные плейсхолдеры ``$1, $2, ...``, а не ``%s``.
    """

    def __init__(self, host: str, port: int, user: str, password: str, db_name: str) -> None:
        """Сохраняет параметры подключения; пул создаётся отложенно через :meth:`connect`.

        Аргументы:
            host:     Имя хоста или IP-адрес сервера PostgreSQL.
            port:     Порт сервера PostgreSQL (обычно 5432).
            user:     Имя пользователя PostgreSQL.
            password: Пароль PostgreSQL.
            db_name:  Название базы данных для подключения.
        """
        self._dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Создаёт пул соединений. Должен быть вызван один раз перед любыми запросами.

        Исключения:
            asyncpg.PostgresError: Если параметры подключения неверны или сервер недоступен.
        """
        self.pool = await asyncpg.create_pool(dsn=self._dsn)

    async def close(self) -> None:
        """Корректно закрывает все соединения в пуле."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, sql: str, *params: Any) -> str:
        """Выполняет SQL-запрос, не возвращающий строк (INSERT / UPDATE / DELETE).

        Аргументы:
            sql:     SQL-строка с плейсхолдерами ``$1, $2, ...``.
            *params: Значения, подставляемые в плейсхолдеры по порядку.

        Возвращает:
            Тег команды PostgreSQL, например ``"INSERT 0 1"`` или ``"UPDATE 3"``.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        async with self.pool.acquire() as conn:
            return await conn.execute(sql, *params)

    async def fetchone(self, sql: str, *params: Any) -> asyncpg.Record | None:
        """Получает первую подходящую строку.

        Аргументы:
            sql:     SQL-строка с плейсхолдерами ``$1, $2, ...``.
            *params: Значения, подставляемые в плейсхолдеры по порядку.

        Возвращает:
            Один объект :class:`asyncpg.Record` (работает как словарь), или ``None``,
            если строки не найдены.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(sql, *params)

    async def fetchall(self, sql: str, *params: Any) -> list[asyncpg.Record]:
        """Получает все подходящие строки.

        Аргументы:
            sql:     SQL-строка с плейсхолдерами ``$1, $2, ...``.
            *params: Значения, подставляемые в плейсхолдеры по порядку.

        Возвращает:
            Список объектов :class:`asyncpg.Record` (каждый работает как словарь).
            Возвращает пустой список, если строки не найдены.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql, *params)

    async def fetchval(self, sql: str, *params: Any) -> Any:
        """Получает одно скалярное значение из первого столбца первой строки.

        Удобно для агрегатов: ``COUNT(*)``, ``MAX(id)`` и т.п.

        Аргументы:
            sql:     SQL-строка с плейсхолдерами ``$1, $2, ...``.
            *params: Значения, подставляемые в плейсхолдеры по порядку.

        Возвращает:
            Значение первого столбца первой подходящей строки, или ``None``,
            если строки не найдены.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(sql, *params)

    async def create_users_table(self) -> None:
        """Создаёт таблицу ``users``, если она ещё не существует.

        Столбцы:
            id           — SERIAL, первичный ключ, автоинкремент, not null.
            telegram_id  — TEXT, not null, уникальный. ID пользователя Telegram в виде текста.
            fullname     — TEXT, not null. Полное имя пользователя из Telegram.
            phone_number — TEXT, not null. Номер телефона пользователя.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           SERIAL      PRIMARY KEY NOT NULL,
                telegram_id  TEXT        NOT NULL UNIQUE,
                fullname     TEXT        NOT NULL,
                phone_number TEXT        NOT NULL
            )
        """)

    async def create_incidents_table(self) -> None:
        """Создаёт таблицу ``incidents``, если она ещё не существует.

        Столбцы:
            id                        — SERIAL, первичный ключ, автоинкремент, not null.
            user_id                   — INT, not null. Внешний ключ на users(id).
            incident_description_type — TEXT, not null. Тип описания инцидента.
            incident                  — TEXT, not null. Описание инцидента.
            floor                     — INTEGER, not null. Этаж из QR-кода.
            datetime                  — TIMESTAMP, not null. Время регистрации инцидента.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        await self.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id                          SERIAL      PRIMARY KEY NOT NULL,
                user_id                     INT         NOT NULL,
                incident_description_type   TEXT        NOT NULL,
                incident                    TEXT        NOT NULL,
                floor                       INTEGER     NOT NULL,
                datetime                    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT incident_user FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

    async def add_user(self, telegram_id: str, fullname: str, phone_number: str) -> None:
        """Добавляет нового пользователя в таблицу ``users``.

        Аргументы:
            telegram_id:  ID пользователя Telegram (число или строка).
            fullname:     Полное имя пользователя.
            phone_number: Номер телефона пользователя.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        await self.execute(
            "INSERT INTO users (telegram_id, fullname, phone_number) VALUES ($1, $2, $3)",
            str(telegram_id), fullname, phone_number
        )

    async def get_user(self, telegram_id: str) -> asyncpg.Record | None:
        """Получает одну строку пользователя по Telegram ID.

        Аргументы:
            telegram_id: ID пользователя Telegram в виде строки.

        Возвращает:
            Объект :class:`asyncpg.Record` со столбцами ``id``, ``telegram_id``,
            ``fullname`` и ``phone_number``, или ``None``, если пользователь не найден.

        Исключения:
            asyncpg.PostgresError: При ошибке выполнения запроса.
        """
        return await self.fetchone(
            "SELECT * FROM users WHERE telegram_id = $1", str(telegram_id)
        )
