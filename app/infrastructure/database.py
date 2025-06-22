"""Database configuration and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def create_data_loading_session() -> async_sessionmaker[AsyncSession]:
    """Create a session factory for data loading with SQLAlchemy echo disabled."""
    # Create a separate engine for data loading without echo
    data_loading_engine = create_async_engine(
        settings.database_url,
        echo=False,  # Always disable echo for data loading
        pool_pre_ping=True,
    )

    return async_sessionmaker(
        data_loading_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
