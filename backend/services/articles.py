import logging
import asyncpg

from backend.db.articles import get_articles, get_article, save_article_chunk, vector_search_article_chunks
from backend.models import Article, CreateArticleChunkRequest
from backend.utils import chunk_by_sections, med_article_sections, parse_article
from backend.utils.chunk_helpers import SectionChunk
from backend.utils.embedding_helpers import embed_chunks, embed_query
from backend.utils.batch_helpers import build_chunk_context_request, create_batch, wait_for_batch, get_batch_results
from backend.utils.retrieval_helpers import bm25_search, reciprocal_rank_fusion, SearchResult
from backend.prompts import ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT
from backend.db import save_article

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


async def chunk_articles(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
) -> None:
    articles = await get_articles(conn, status="pending")
    logger.info("Found %d pending articles to chunk", len(articles))

    if not articles:
        return

    # Step 1: fetch full text and generate chunks for each article
    article_chunks: list[tuple[Article, list[SectionChunk]]] = []
    for article in articles:
        full_article = await get_article(conn, article.article_id)
        if full_article is None or full_article.full_text is None:
            logger.warning("Skipping article %s — no full text", article.article_id)
            continue
        chunks = chunk_by_sections(
            full_article.full_text, med_article_sections, CHUNK_SIZE, CHUNK_OVERLAP
        )
        article_chunks.append((full_article, chunks))

    # Step 2: build one batch request per chunk across all articles
    # custom_id format: "{article_id}-{chunk_index}" — must match ^[a-zA-Z0-9_-]{1,64}$
    batch_requests = [
        build_chunk_context_request(
            custom_id=f"{full_article.article_id}-{chunk_index}",
            resource=full_article.full_text,  # type: ignore[arg-type]
            chunk=chunk["content"],
            system=ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT.content,
        )
        for full_article, chunks in article_chunks
        for chunk_index, chunk in enumerate(chunks)
    ]

    logger.info("Submitting batch of %d context requests", len(batch_requests))
    batch = await create_batch(batch_requests)
    await wait_for_batch(batch.id)

    # Step 3: build context map keyed by custom_id
    context_map: dict[str, str] = {}
    for batch_result in await get_batch_results(batch.id):
        if batch_result.result.type != "succeeded":
            logger.warning(
                "Context request %s failed: %s",
                batch_result.custom_id,
                batch_result.result.type,
            )
            continue
        text = batch_result.result.message.content[0].text  # type: ignore[union-attr]
        context_map[batch_result.custom_id] = text.strip()

    # Step 4: embed contextualised chunks and save per article
    for full_article, chunks in article_chunks:
        contexts = [
            context_map.get(f"{full_article.article_id}-{i}", "")
            for i in range(len(chunks))
        ]
        contextualised = [
            f"{ctx}\n\n{chunk['content']}" for ctx, chunk in zip(contexts, chunks)
        ]
        embed_result = embed_chunks(contextualised)

        for chunk_index, (chunk, context, embedding) in enumerate(
            zip(chunks, contexts, embed_result.embeddings)
        ):
            await save_article_chunk(
                conn,
                CreateArticleChunkRequest(
                    article_id=full_article.article_id,
                    chunk_text=chunk["content"],
                    context_text=context,
                    embedding=[float(x) for x in embedding],
                    section=chunk["section"],
                    chunk_index=chunk_index,
                    token_count=len(chunk["content"]) // 4,
                ),
            )

        logger.info("Saved %d chunks for article '%s'", len(chunks), full_article.title)


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


async def search_article_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    query: str,
    top_k: int = 10,
    article_id: str | None = None,
    section: str | None = None
):
    embedding = embed_query(query)
    results = await vector_search_article_chunks(
        conn,
        embedding=[float(x) for x in embedding],
        top_k=top_k,
        article_id=article_id,
        section=section,
    )

    if not results:
        return results

    # Both ranked lists reference chunks by their index into `results`, so
    # reciprocal_rank_fusion can merge them without knowing about ArticleChunk.
    vector_results: list[SearchResult] = [
        SearchResult(index=i, rank=chunk.score or 0.0)
        for i, chunk in enumerate(results)
    ]

    bm25_results = bm25_search(results, text=lambda chunk: chunk.chunk_text, query=query, top_k=top_k)

    fused = reciprocal_rank_fusion([vector_results, bm25_results])

    return [results[fused_result["index"]] for fused_result in fused]