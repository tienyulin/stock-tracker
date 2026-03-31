"""
Async database connection using SQLAlchemy 2.0.
"""

import ssl
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import URL

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Parse the database URL and ensure no query params are passed to asyncpg
# asyncpg.connect() does NOT accept sslmode - it only accepts ssl (boolean)
_database_url = settings.database_url
if "?" in _database_url:
    # Strip ALL query params - asyncpg doesn't support them
    # They were causing: TypeError: connect() got an unexpected keyword argument 'sslmode'
    _database_url = _database_url.split("?")[0]
    print(f"[DB] Stripped query params from database URL")

# Convert postgresql:// to postgresql+asyncpg:// if needed
if _database_url.startswith("postgresql://") and "+asyncpg" not in _database_url:
    _database_url = _database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    print(f"[DB] Converted driver to asyncpg")

# Determine SSL requirement based on host
_is_remote_db = not any(
    host in _database_url.lower()
    for host in ["localhost", "host.docker.internal", "db:", "127.0.0.1"]
)

_connect_args: dict = {
    "server_settings": {
        "jit": "off"
    },
}
if _is_remote_db:
    # Remote databases (Render, Neon, etc.) require SSL
    # Use ssl=True (boolean) - asyncpg.connect() accepts this, NOT sslmode
    _connect_args["ssl"] = True
    print(f"[DB] Enabled SSL for remote database")

engine = create_async_engine(
    _database_url,
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
