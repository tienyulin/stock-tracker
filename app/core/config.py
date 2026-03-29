"""
Database configuration.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/stocktracker"
    )
    
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )
    
    api_version: str = "v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
