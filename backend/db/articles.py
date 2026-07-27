import logging
import asyncpg
from backend.models import Article, CreateArticleRequest

logger = logging.getLogger(__name__)

async def save_article(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    article: CreateArticleRequest,
) -> str:
    logger.info("Saving article %s to articles", article.title)

    try:
        row = await conn.fetchrow(
            """
            INSERT INTO articles
                (title, authors, journal, published_at, full_text)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING article_id
            """,
            article.title,
            article.authors,
            article.journal,
            article.published_at,
            article.full_text
        )
        if row is None:
            raise RuntimeError(f"INSERT for article '{article.title}' returned no row")
        return str(row["article_id"])
    except asyncpg.UniqueViolationError:
        logger.exception("Article %s already exists", article.title)
        raise
    except asyncpg.PostgresError:
        logger.exception("Failed to save article %s", article.title)
        raise


async def get_articles(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    status: str | None = None,
) -> list[Article]:
    logger.info("Fetching articles%s", f" with status '{status}'" if status else "")

    try:
        if status is not None:
            rows = await conn.fetch(
                """
                SELECT article_id, title, authors, journal, published_at, chunk_status
                FROM articles
                WHERE chunk_status = $1
                """,
                status,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT article_id, title, authors, journal, published_at, chunk_status
                FROM articles
                """,
            )
    except asyncpg.PostgresError:
        logger.exception("Failed to fetch articles")
        raise

    return [
        Article(
            article_id=str(row["article_id"]),
            title=row["title"],
            authors=list(row["authors"]),
            journal=row["journal"],
            published_at=row["published_at"],
            chunk_status=row["chunk_status"],
        )
        for row in rows
    ]


async def get_article(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    article_id: str,
) -> Article | None:
    logger.info("Fetching article %s", article_id)

    try:
        row = await conn.fetchrow(
            """
            SELECT article_id, title, authors, journal, published_at, chunk_status, full_text
            FROM articles
            WHERE article_id = $1
            """,
            article_id,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to fetch article %s", article_id)
        raise

    if row is None:
        return None

    return Article(
        article_id=str(row["article_id"]),
        title=row["title"],
        authors=list(row["authors"]),
        journal=row["journal"],
        published_at=row["published_at"],
        chunk_status=row["chunk_status"],
        full_text=row["full_text"],
    )
