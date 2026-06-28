import os
import logging
import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

async def connect() -> None:
    global _pool
    _pool = await asyncpg.create_pool(dsn=os.environ["DATABASE_URL"])
    logger.info("Database pool created")


async def disconnect() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Call connect() first.")
    return _pool
