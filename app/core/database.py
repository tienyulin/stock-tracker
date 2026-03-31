"""
Async database connection using SQLAlchemy 2.0.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Determine SSL requirement based on host
# Render/Neon requires SSL, local Docker does not
_is_remote_db = not any(
    host in settings.database_url.lower()
    for host in ["localhost", "host.docker.internal", "db:", "127.0.0.1"]
)

_connect_args = {
    "server_settings": {
        "jit": "off"
    },
}
if _is_remote_db:
    # Remote databases (Render, Neon, etc.) require SSL
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
