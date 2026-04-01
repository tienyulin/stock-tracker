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

    # Migration: Add line_notify_token column if it doesn't exist
    await run_migrations()

    # Seed demo user
    await seed_demo_user()


async def run_migrations() -> None:
    """Run database migrations for schema updates."""
    async with engine.begin() as conn:
        # Add line_notify_token column if it doesn't exist
        try:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS line_notify_token VARCHAR(255)")
            )
            logger.info("Migration: line_notify_token column added (if not exists)")
        except Exception as e:
            # Column might already exist or other issue - log but don't fail
            logger.warning(f"Migration note: {e}")


async def seed_demo_user() -> None:
    """Create demo user if not exists, or fix password hash if invalid."""
    # Pre-computed bcrypt hash for "demo123" (bcrypt 4.x format)
    DEMO_PASSWORD_HASH = "$2b$12$HYuTbwNSogO1UA3yOys.pOJVT7uB9MXGGO1Q9eRrePHb177ZZzSnG"

    async with AsyncSessionLocal() as session:
        # Check if demo user exists
        result = await session.execute(
            text("SELECT id, password_hash FROM users WHERE id = :id"),
            {"id": DEMO_USER_ID}
        )
        row = result.fetchone()

        if row is None:
            # User doesn't exist - create it
            logger.info("Seeding demo user...")
            demo_user = User(
                id=DEMO_USER_ID,
                username="demo",
                email="demo@example.com",
                password_hash=DEMO_PASSWORD_HASH,
            )
            session.add(demo_user)
            await session.commit()
            logger.info("Demo user seeded successfully.")
        else:
            # User exists - check if password hash is valid bcrypt
            existing_hash = row.password_hash
            if existing_hash and existing_hash.startswith("$2"):
                logger.info("Demo user already exists with valid password hash.")
            else:
                # Fix invalid password hash (e.g., "demo_password_hash" plaintext)
                logger.info("Fixing demo user password hash...")
                await session.execute(
                    text("UPDATE users SET password_hash = :hash WHERE id = :id"),
                    {"hash": DEMO_PASSWORD_HASH, "id": DEMO_USER_ID}
                )
                await session.commit()
                logger.info("Demo user password hash fixed.")


async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
