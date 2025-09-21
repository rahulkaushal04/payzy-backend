import logging
from decimal import Decimal
from datetime import datetime, date
from contextlib import asynccontextmanager
from sqlalchemy import MetaData, event, inspect
from typing import AsyncGenerator, Optional, Any
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import DeclarativeBase, Mapper
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    AsyncConnection,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


def _serialize_value(value: Any):
    if value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif hasattr(value, "__dict__"):
        return str(value)
    else:
        return value


def model_to_dict(
    model: Any,
    exclude_columns: Optional[set[str]] = None,
    include_relationships: bool = False,
    max_depth: int = 1,
    _current_depth: int = 0,
):
    if model is None:
        return {}

    exclude_columns = exclude_columns or set()
    result = {}

    mapper: Mapper[Any] = inspect(model.__class__)

    for column in mapper.columns:
        column_name = column.name

        if column_name not in exclude_columns:
            try:
                value = getattr(model, column_name)
                result[column_name] = _serialize_value(value)
            except AttributeError:
                continue

        if include_relationships and _current_depth < max_depth:
            for relationship in mapper.relationships:
                rel_name = relationship.key
                if rel_name not in exclude_columns:
                    try:
                        rel_value = getattr(model, rel_name)
                        if rel_value is None:
                            result[rel_name] = None
                        elif hasattr(rel_value, "__iter__") and not isinstance(
                            rel_value, (str, bytes)
                        ):
                            result[rel_name] = [
                                model_to_dict(
                                    item,
                                    exclude_columns=exclude_columns,
                                    include_relationships=include_relationships,
                                    max_depth=max_depth,
                                    _current_depth=_current_depth + 1,
                                )
                                for item in rel_value
                            ]
                        else:
                            result[rel_name] = model_to_dict(
                                rel_value,
                                exclude_columns=exclude_columns,
                                include_relationships=include_relationships,
                                max_depth=max_depth,
                                _current_depth=_current_depth + 1,
                            )
                    except AttributeError:
                        continue
    return result


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models with enhanced metadata.
    """

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    def to_dict(
        self,
        exclude_columns: Optional[set[str]] = None,
        include_relationships: bool = False,
        max_depth: int = 1,
        _current_depth: int = 0,
    ):
        return model_to_dict(
            self,
            exclude_columns=exclude_columns,
            include_relationships=include_relationships,
            max_depth=max_depth,
            _current_depth=_current_depth,
        )


class DatabaseSessionManager:
    """
    Async database session manager with connection pooling.
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_initialized: bool = False

    def init_db(self, database_url: Optional[str] = None) -> None:
        """Initialize the database engine and session factory."""
        if self._is_initialized:
            logger.warning("Database already initialized")
            return

        db_url = database_url or self._get_async_database_url()

        self._engine = create_async_engine(
            db_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=getattr(settings, "DB_POOL_RECYCLE", 3600),
            pool_pre_ping=True,  # Verify connections before use
            echo=settings.DB_ECHO if hasattr(settings, "DB_ECHO") else False,
            echo_pool=settings.DEBUG if hasattr(settings, "DEBUG") else False,
            future=True,  # Use SQLAlchemy 2.0 style
            connect_args=(
                {
                    "server_settings": {
                        "application_name": f"{settings.PROJECT_NAME}_{settings.ENVIRONMENT}"
                    }
                }
                if "postgresql" in db_url
                else {}
            ),
        )

        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # Register event listeners for monitoring
        self._register_engine_events()

        self._is_initialized = True
        logger.info("Database session manager initialized successfully")

    def _get_async_database_url(self) -> str:
        """Convert sync DATABASE_URL to async version."""
        database_url = settings.effective_database_url

        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        return database_url

    def _register_engine_events(self) -> None:
        """Register engine events for monitoring and logging."""
        if not self._engine:
            return

        @event.listens_for(self._engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")

        @event.listens_for(self._engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")

        @event.listens_for(self._engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            logger.debug("Connection returned to pool")

        @event.listens_for(self._engine.sync_engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            logger.warning(f"Connection invalidated: {exception}")

    async def close(self) -> None:
        """Close the database engine and clean up resources."""
        if self._engine:
            logger.info("Closing database connections...")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            logger.info("Database connections closed successfully")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with proper lifecycle management.
        Includes automatic rollback on exceptions and session cleanup.
        """
        if not self._is_initialized or not self._session_factory:
            raise RuntimeError(
                "Database session manager is not initialized. Call init_db() first."
            )

        session = self._session_factory()
        try:
            yield session
            await session.commit()

        except Exception as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncConnection, None]:
        """
        Get a raw database connection for advanced operations.
        """
        if not self._is_initialized or not self._engine:
            raise RuntimeError("Database session manager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}", exc_info=True)
                await connection.rollback()
                raise


# Global session manager instance
sessionmanager = DatabaseSessionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    Provides clean session lifecycle management with proper error handling.
    """
    async with sessionmanager.get_session() as session:
        yield session


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    FastAPI dependency for raw database connections.
    Use for advanced operations that require direct connection access.
    """
    async with sessionmanager.get_connection() as connection:
        yield connection


async def close_db() -> None:
    """Close database connections on application shutdown."""
    logger.info("Shutting down database...")
    await sessionmanager.close()
    logger.info("Database shutdown completed")
