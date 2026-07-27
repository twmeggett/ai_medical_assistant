import logging
import asyncpg

from backend.db.articles import get_articles, get_article
from backend.db.article_chunks import (
    save_article_chunk,
    vector_search_article_chunks,
    keyword_search_article_chunks,
    get_existing_chunk_hashes,
)
from backend.models import Article, ArticleChunk, CreateArticleChunkRequest
from backend.models.tools import DEFAULT_CHUNK_SEARCH_TOP_K
from backend.utils import chunk_by_sections, med_article_sections
from backend.utils.chunk_helpers import SectionChunk, generate_chunk_id
from backend.utils.embedding_helpers import embed_chunks, embed_query, rerank_chunks
from backend.utils.batch_helpers import build_chunk_context_request, create_batch, wait_for_batch, get_batch_results
from backend.utils.retrieval_helpers import reciprocal_rank_fusion, SearchResult
from backend.prompts import ACTIVE_CHUNK_CONTEXT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Candidates fetched per retrieval method before RRF fusion + truncation to
# the caller's requested top_k — wider than top_k so fusion has enough signal
# from each side (a chunk only one method ranks highly still needs to appear
# in its candidate pool to be found at all).
CANDIDATE_POOL_SIZE = 25

# Minimum Voyage rerank relevance_score for a chunk to be returned at all.
# Calibrated empirically (not derived from any guarantee about the score's
# scale): a specific, well-matched query shows a sharp cliff between truly
# relevant chunks (~0.8-0.96) and irrelevant ones (<=0.41), while a broad but
# legitimate query's real results can score as low as ~0.45. 0.4 sits below
# that broad-query floor while still cutting the weakest off-topic matches.
# Revisit once real usage queries or a larger labeled eval set exist.
DEFAULT_MIN_RERANK_SCORE = 0.4


async def _collect_new_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    articles: list[Article],
) -> list[tuple[Article, list[SectionChunk]]]:
    # Fetch full text, chunk each article, and drop any chunk whose content_hash
    # already exists — so already-ingested content skips the batch/embedding calls below.
    article_chunks: list[tuple[Article, list[SectionChunk]]] = []
    for article in articles:
        full_article = await get_article(conn, article.article_id)
        if full_article is None or full_article.full_text is None:
            logger.warning("Skipping article %s — no full text", article.article_id)
            continue
        chunks = chunk_by_sections(
            full_article.full_text, med_article_sections, CHUNK_SIZE, CHUNK_OVERLAP
        )

        existing_hashes = await get_existing_chunk_hashes(conn, full_article.article_id)
        new_chunks = [
            chunk for chunk in chunks
            if generate_chunk_id(full_article.article_id, chunk["content"]) not in existing_hashes
        ]
        if len(new_chunks) < len(chunks):
            logger.info(
                "Skipping %d/%d already-ingested chunks for article '%s'",
                len(chunks) - len(new_chunks), len(chunks), full_article.title,
            )
        if not new_chunks:
            continue

        article_chunks.append((full_article, new_chunks))

    return article_chunks


async def _generate_chunk_contexts(
    article_chunks: list[tuple[Article, list[SectionChunk]]],
) -> dict[str, str]:
    # Submits one batch request per chunk across all articles and returns the
    # generated context text keyed by custom_id ("{article_id}-{chunk_index}").
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

    return context_map


async def _embed_and_save_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    article_chunks: list[tuple[Article, list[SectionChunk]]],
    context_map: dict[str, str],
) -> None:
    for full_article, chunks in article_chunks:
        contexts = [
            context_map.get(f"{full_article.article_id}-{i}", "")
            for i in range(len(chunks))
        ]
        contextualised = [
            f"{ctx}\n\n{chunk['content']}" for ctx, chunk in zip(contexts, chunks)
        ]
        embed_result = embed_chunks(contextualised)

        saved_count = 0
        for chunk_index, (chunk, context, embedding) in enumerate(
            zip(chunks, contexts, embed_result.embeddings)
        ):
            inserted = await save_article_chunk(
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
            saved_count += inserted

        logger.info(
            "Saved %d/%d chunks for article '%s' (%d already existed)",
            saved_count, len(chunks), full_article.title, len(chunks) - saved_count,
        )


async def chunk_articles(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
) -> None:
    articles = await get_articles(conn, status="pending")
    logger.info("Found %d pending articles to chunk", len(articles))

    if not articles:
        return

    article_chunks = await _collect_new_chunks(conn, articles)
    if not article_chunks:
        return

    context_map = await _generate_chunk_contexts(article_chunks)
    await _embed_and_save_chunks(conn, article_chunks, context_map)


async def search_article_chunks(
    conn: asyncpg.Connection | asyncpg.pool.PoolConnectionProxy,
    query: str,
    top_k: int = DEFAULT_CHUNK_SEARCH_TOP_K,
    min_score: float = DEFAULT_MIN_RERANK_SCORE,
    article_id: str | None = None,
    section: str | None = None
):
    embedding = embed_query(query)
    fetch_k = max(CANDIDATE_POOL_SIZE, top_k)

    # Two independent rankings over the full corpus (not one reranking the
    # other) — vector search for semantic similarity, keyword search (Postgres
    # full-text search) for exact clinical terms embeddings can under-weight.
    # Each fetches `fetch_k` candidates (wider than top_k) so RRF has enough
    # signal to fuse over before truncating to the final top_k below.
    # Same `conn` can't run concurrent queries, so these are sequential.
    vector_chunks = await vector_search_article_chunks(
        conn,
        embedding=[float(x) for x in embedding],
        top_k=fetch_k,
        article_id=article_id,
        section=section,
    )
    keyword_chunks = await keyword_search_article_chunks(
        conn,
        query=query,
        top_k=fetch_k,
        article_id=article_id,
        section=section,
    )

    if not vector_chunks and not keyword_chunks:
        return []

    chunks_by_id: dict[str, ArticleChunk] = {
        chunk.chunk_id: chunk for chunk in [*vector_chunks, *keyword_chunks]
    }

    vector_results: list[SearchResult] = [
        SearchResult(id=chunk.chunk_id, rank=chunk.score or 0.0)
        for chunk in vector_chunks
    ]
    keyword_results: list[SearchResult] = [
        SearchResult(id=chunk.chunk_id, rank=chunk.score or 0.0)
        for chunk in keyword_chunks
    ]

    fused = reciprocal_rank_fusion([vector_results, keyword_results])

    # Cross-encoder rerank: RRF cheaply narrows two independent rankings down
    # to a shared candidate pool, then Voyage's rerank model scores each
    # (query, chunk) pair jointly for a much more precise final ranking than
    # RRF's rank-based fusion alone — too expensive to run over the full
    # corpus, which is why it only sees the already-narrowed fused candidates.
    # Reranks the whole pool (not capped to top_k) so the min_score filter
    # below can't shrink the result just because a qualifying candidate
    # happened to rank outside an early cutoff — scoring cost is the same
    # either way, only how many results Voyage returns changes.
    candidates = [chunks_by_id[fused_result["id"]] for fused_result in fused]
    reranked = rerank_chunks(query, [chunk.chunk_text for chunk in candidates], top_k=len(candidates))

    results = []
    for reranked_result in reranked.results:
        if reranked_result.relevance_score < min_score:
            break  # sorted descending — nothing after this qualifies either
        chunk = candidates[reranked_result.index]
        chunk.score = reranked_result.relevance_score
        results.append(chunk)
        if len(results) == top_k:
            break

    return results
