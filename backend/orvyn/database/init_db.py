"""Database initialization and schema migration helper."""

from orvyn.core.logging import logger
from orvyn.database.base import Base
from orvyn.database.models import *  # noqa: F401, F403
from orvyn.database.session import engine


async def init_db() -> None:
    """Creates all tables defined in metadata if they do not exist."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")


async def drop_db() -> None:
    """Drops all tables. For testing only."""
    logger.warning("Dropping all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped.")
