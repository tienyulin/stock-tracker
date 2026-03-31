"""
Database configuration.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    def _fix_database_url(url: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// for SQLAlchemy async.
        
        Note: asyncpg does NOT support libpq URL parameters like sslmode.
        All connection parameters must be passed via connect_args instead.
        """
        # Remove ALL query parameters from URL - asyncpg doesn't support them
        if "?" in url:
            url = url.split("?")[0]
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    database_url: str = _fix_database_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/stocktracker",
        )
    )

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    api_version: str = "v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
