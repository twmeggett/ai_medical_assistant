import logging
import asyncpg
from backend.models import Article, CreateArticleRequest, CreateArticleChunkRequest, ArticleChunk
from backend.utils import parse_article

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



async def save_article_chunk(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    chunk: CreateArticleChunkRequest,
) -> None:
    logger.info("Saving chunk index %s from article %s to article_chunks", chunk.chunk_index, chunk.article_id)

    try:
        await conn.execute(
            """
            INSERT INTO article_chunks
                (article_id, chunk_text, context_text, embedding, section, chunk_index, token_count, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            chunk.article_id,
            chunk.chunk_text,
            chunk.context_text,
            chunk.embedding,
            chunk.section,
            chunk.chunk_index,
            chunk.token_count,
            chunk.metadata
        )
    except asyncpg.UniqueViolationError:
        logger.exception("Chunk with index of %s in article %s section %s already exists", chunk.chunk_index, chunk.article_id, chunk.section)
        raise
    except asyncpg.ForeignKeyViolationError:
        logger.exception("Article %s does not exist", chunk.article_id)
        raise
    except asyncpg.PostgresError:
        logger.exception("Failed to save chunk")
        raise

async def vector_search_article_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    embedding: list[float],
    top_k: int = 10,
    article_id: str | None = None,
    section: str | None = None,
) -> list[ArticleChunk]:
    logger.info("Searching article chunks — top_k=%d", top_k)

    try:
        rows = await conn.fetch(
            """
            SELECT
                chunk_id,
                article_id,
                chunk_text,
                context_text,
                section,
                chunk_index,
                token_count,
                metadata,
                -(embedding <#> $1) AS score
            FROM article_chunks
            WHERE ($3::uuid IS NULL OR article_id = $3)
              AND ($4::text IS NULL OR section = $4)
            ORDER BY embedding <#> $1
            LIMIT $2
            """,
            embedding,
            top_k,
            article_id,
            section,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to search article chunks")
        raise

    return [
        ArticleChunk(
            chunk_id=str(row["chunk_id"]),
            article_id=str(row["article_id"]),
            chunk_text=row["chunk_text"],
            context_text=row["context_text"],
            section=row["section"],
            chunk_index=row["chunk_index"],
            token_count=row["token_count"],
            metadata=row["metadata"],
            score=row["score"],
        )
        for row in rows
    ]