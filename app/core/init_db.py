"""
Database initialization script.
Creates all tables if they don't exist.
"""

import logging
import uuid

from sqlalchemy import text

from app.core.database import engine, Base, AsyncSessionLocal
from app.models import Alert, AlertNotification, User, Watchlist, WatchlistItem  # noqa: F401 - imported for side effect (Base.metadata)

logger = logging.getLogger(__name__)

# Demo user ID used by frontend
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def init_db() -> None:
    """Create all database tables and seed demo data."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

    # Seed demo user
    await seed_demo_user()


async def seed_demo_user() -> None:
    """Create demo user if not exists."""
    async with AsyncSessionLocal() as session:
        # Check if demo user exists
        result = await session.execute(
            text("SELECT id FROM users WHERE id = :id"),
            {"id": DEMO_USER_ID}
        )
        if result.scalar() is None:
            logger.info("Seeding demo user...")
            demo_user = User(
                id=DEMO_USER_ID,
                username="demo",
                email="demo@example.com",
                # Pre-computed bcrypt hash for "demo123" (bcrypt 4.x format)
                password_hash="$2b$12$HYuTbwNSogO1UA3yOys.pOJVT7uB9MXGGO1Q9eRrePHb177ZZzSnG",
            )
            session.add(demo_user)
            await session.commit()
            logger.info("Demo user seeded successfully.")
        else:
            logger.info("Demo user already exists.")


async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
