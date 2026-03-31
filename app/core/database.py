"""
Async database connection using SQLAlchemy 2.0.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Determine if SSL is required (Render PostgreSQL requires SSL)
_connect_args = {
    "server_settings": {
        "jit": "off"
    },
}
# Render PostgreSQL requires SSL; local Docker does not
if "render" in settings.database_url.lower():
    _connect_args["ssl"] = True

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
