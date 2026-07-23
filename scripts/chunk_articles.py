import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.connector import connect, get_pool, disconnect
from backend.services import chunk_articles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        await connect()
        async with get_pool().acquire() as conn:
            await chunk_articles(conn)
    except Exception as e:
        print(f"Failed to chunk articles: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await disconnect()


if __name__ == "__main__":
    asyncio.run(main())
