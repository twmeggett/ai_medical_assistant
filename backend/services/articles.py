import logging
import asyncpg

from backend.db.articles import save_article
from backend.utils import parse_article

logger = logging.getLogger(__name__)


async def save_articles(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    articles: list[str]
) -> list[dict]:
    results = []
    for article in articles:
        try:
            parsed_article = parse_article(article)
        except ValueError as e:
            logger.warning("Skipping article — parse failed: %s", e)
            continue

        try:
            article_id = await save_article(conn, parsed_article)
            results.append({"article_id": article_id})
        except Exception as e:
            logger.warning("Skipping article '%s' — save failed: %s", parsed_article.title, e)
            continue

    return results
