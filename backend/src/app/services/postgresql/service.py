import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.app.middleware.opentelemetry import instrument_sqlalchemy_engine
from src.settings import settings

logger = logging.getLogger(__name__)


class Database:
    # URL-encode password to handle special chars (#, &, etc.)
    _ENCODED_PASSWORD = quote_plus(settings.postgres_password.get_secret_value())
    _BASE_URL = (
        f"postgresql://{settings.postgres_user}:"
        f"{_ENCODED_PASSWORD}@"
        f"{settings.postgres_host}:{settings.postgres_port}/"
        f"{settings.postgres_db}"
    )
    # psycopg2 (sync) accepts sslmode as a URL query parameter
    DATABASE_URL = f"{_BASE_URL}?sslmode={settings.postgres_sslmode}"

    # Lazy-initialized engines and session factories
    _engine: Engine | None = None
    _async_engine: AsyncEngine | None = None
    _async_engine_loop_id: int | None = None
    _session_local: sessionmaker | None = None
    _async_session_local: async_sessionmaker | None = None

    # Create base class for models (this is safe to initialize at import time)
    Base = declarative_base()

    @classmethod
    def _get_engine(cls) -> Engine:
        """Lazy initialization of sync engine."""
        if cls._engine is None:
            cls._engine = create_engine(
                cls.DATABASE_URL,
                pool_size=10,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            try:
                instrument_sqlalchemy_engine(cls._engine)
            except Exception as e:
                logger.warning("Failed to instrument sync SQLAlchemy engine: %s", e)
        return cls._engine

    @classmethod
    def _get_async_engine(cls) -> AsyncEngine:
        """
        Lazy initialization of async engine.
        Recreates the engine if the event loop changes (happens in tests).
        """
        try:
            current_loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            current_loop_id = None

        # Recreate engine if event loop changed (happens in tests)
        if (
            cls._async_engine is not None
            and cls._async_engine_loop_id != current_loop_id
        ):
            try:
                # Note: We don't await dispose() here as we may not be in async context
                # The old engine will be garbage collected
                pass
            except Exception:
                pass
            cls._async_engine = None
            cls._async_session_local = None

        if cls._async_engine is None:
            async_url = cls._BASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            connect_args: dict[str, str] = {}
            if settings.postgres_sslmode != "disable":
                connect_args["ssl"] = settings.postgres_sslmode
            cls._async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
                connect_args=connect_args,
            )
            cls._async_engine_loop_id = current_loop_id
            try:
                instrument_sqlalchemy_engine(cls._async_engine)
            except Exception as e:
                logger.warning("Failed to instrument async SQLAlchemy engine: %s", e)
        return cls._async_engine

    @classmethod
    def _get_session_local(cls) -> sessionmaker:
        """Lazy initialization of sync session factory."""
        if cls._session_local is None:
            cls._session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=cls._get_engine()
            )
        return cls._session_local

    @classmethod
    def _get_async_session_local(cls) -> async_sessionmaker:
        """Lazy initialization of async session factory."""
        # Force engine check for event loop changes
        cls._get_async_engine()
        if cls._async_session_local is None:
            cls._async_session_local = async_sessionmaker(
                cls._get_async_engine(), autoflush=False, expire_on_commit=False
            )
        return cls._async_session_local

    @staticmethod
    @contextmanager
    def get_db() -> Generator[Session, None, None]:
        """
        Context manager for synchronous database sessions.
        Usage:
            with Database.get_db() as db:
                db.query(YourModel).all()
        """
        db = Database._get_session_local()()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    @asynccontextmanager
    async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.
        Usage:
            async with Database.get_async_db() as db:
                result = await db.execute(query)
        """
        async with Database._get_async_session_local()() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    def get_db_session() -> Session:
        """
        Get a synchronous database session.
        Usage:
            db = Database.get_db_session()
            try:
                # use db
                db.commit()
            finally:
                db.close()
        """
        return Database._get_session_local()()

    @staticmethod
    async def get_async_session() -> AsyncSession:
        """
        Get an async database session.
        Usage:
            db = await Database.get_async_session()
            try:
                # use db
                await db.commit()
            finally:
                await db.close()
        """
        return Database._get_async_session_local()()
