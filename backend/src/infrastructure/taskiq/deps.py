"""Task dependencies for taskiq integration."""

from collections.abc import AsyncGenerator
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from taskiq import TaskiqDepends

from ..config import get_settings

settings = get_settings()

taskiq_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

taskiq_session_factory = async_sessionmaker(bind=taskiq_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for taskiq tasks.

    Provides a database session with proper lifecycle management for
    taskiq tasks, ensuring clean connection handling and transaction management.

    Yields:
        AsyncSession: Database session configured for taskiq usage.
    """
    async with taskiq_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


DBSession = Annotated[AsyncSession, TaskiqDepends(get_db_session)]
