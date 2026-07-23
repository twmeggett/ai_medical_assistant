import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_articles import ARTICLES
from backend.services import save_articles
from backend.db.connector import connect, disconnect, get_pool

async def main():
    try:
        await connect()
        async with get_pool().acquire() as conn:
            article_ids = await save_articles(conn, ARTICLES)
        print(f"Saved {len(article_ids)} articles: {[a['article_id'] for a in article_ids]}")
    except Exception as e:
        print(f"Failed to save articles: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await disconnect()

if __name__ == "__main__":
    asyncio.run(main())