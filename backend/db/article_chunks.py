import logging
import asyncpg
from backend.models import CreateArticleChunkRequest, ArticleChunk
from backend.models.tools import DEFAULT_CHUNK_SEARCH_TOP_K
from backend.utils.chunk_helpers import generate_chunk_id

logger = logging.getLogger(__name__)

async def get_existing_chunk_hashes(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    article_id: str,
) -> set[str]:
    rows = await conn.fetch(
        "SELECT content_hash FROM article_chunks WHERE article_id = $1",
        article_id,
    )
    return {row["content_hash"] for row in rows}

async def save_article_chunk(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    chunk: CreateArticleChunkRequest,
) -> bool:
    # Deliberately excludes context_text/embedding: those are regenerated (and
    # non-deterministic) on every pipeline run, so hashing them would defeat
    # idempotency across retries. chunk_text is the stable, deterministic output
    # of the chunking step.
    content_hash = generate_chunk_id(chunk.article_id, chunk.chunk_text)
    logger.info("Saving chunk index %s from article %s to article_chunks", chunk.chunk_index, chunk.article_id)

    try:
        row = await conn.fetchrow(
            """
            INSERT INTO article_chunks
                (article_id, chunk_text, context_text, embedding, section, chunk_index, token_count, content_hash, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (content_hash) DO NOTHING
            RETURNING chunk_id
            """,
            chunk.article_id,
            chunk.chunk_text,
            chunk.context_text,
            chunk.embedding,
            chunk.section,
            chunk.chunk_index,
            chunk.token_count,
            content_hash,
            chunk.metadata
        )
    except asyncpg.ForeignKeyViolationError:
        logger.exception("Article %s does not exist", chunk.article_id)
        raise
    except asyncpg.PostgresError:
        logger.exception("Failed to save chunk")
        raise

    if row is None:
        logger.info(
            "Chunk index %s from article %s already exists (hash %s) — skipping",
            chunk.chunk_index, chunk.article_id, content_hash,
        )
        return False
    return True

def _row_to_article_chunk(row: asyncpg.Record) -> ArticleChunk:
    return ArticleChunk(
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

async def vector_search_article_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    embedding: list[float],
    top_k: int = DEFAULT_CHUNK_SEARCH_TOP_K,
    article_id: str | None = None,
    section: str | None = None,
) -> list[ArticleChunk]:
    logger.info("Vector-searching article chunks — top_k=%d", top_k)

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
        logger.exception("Failed to vector-search article chunks")
        raise

    return [_row_to_article_chunk(row) for row in rows]

async def keyword_search_article_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    query: str,
    top_k: int = DEFAULT_CHUNK_SEARCH_TOP_K,
    article_id: str | None = None,
    section: str | None = None,
) -> list[ArticleChunk]:
    logger.info("Keyword-searching article chunks — top_k=%d", top_k)

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
                ts_rank_cd(search_vector, websearch_to_tsquery('english', $1)) AS score
            FROM article_chunks
            WHERE search_vector @@ websearch_to_tsquery('english', $1)
              AND ($3::uuid IS NULL OR article_id = $3)
              AND ($4::text IS NULL OR section = $4)
            ORDER BY score DESC
            LIMIT $2
            """,
            query,
            top_k,
            article_id,
            section,
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to keyword-search article chunks")
        raise

    return [_row_to_article_chunk(row) for row in rows]
