from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.database.base import Base

logger = get_logger(__name__)


def create_engine_and_session() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initializes the async engine and sessionmaker based on settings."""
    db_url = settings.DATABASE_URL
    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG and False,
        future=True,
        connect_args=connect_args,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return engine, session_factory


engine, AsyncSessionLocal = create_engine_and_session()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Verifies that the database is reachable and accepting queries."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def init_db() -> None:
    """Creates database tables directly if not using Alembic migrations (e.g. for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
