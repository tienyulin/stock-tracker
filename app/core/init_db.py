"""
Database initialization script.
Creates all tables if they don't exist.
"""

import logging
from sqlalchemy import text

from app.core.database import engine, Base
from app.models import Alert, AlertNotification, User, Watchlist, WatchlistItem

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all database tables."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")


async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
