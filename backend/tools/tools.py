from pydantic import TypeAdapter
from backend.db.connector import get_pool
from backend.models.tools import SearchArticleChunksInput, SearchJournalsInput, GetArticleInput, CiteSourcesInput
from backend.models import ArticleChunk, ToolResultBlock
from backend.models.domain import SearchResult
from backend.utils.pubmed import esearch, efetch, esummary, format_citation

_ARTICLE_CHUNKS_ADAPTER = TypeAdapter(list[ArticleChunk])


async def search_article_chunks(tool_use_id: str, **kwargs) -> ToolResultBlock:
    # Imported locally: backend.services imports backend.tools (for tool_executor),
    # so a module-level import here would create a circular import.
    from backend.services import search_article_chunks as search_chunks

    params = SearchArticleChunksInput(**kwargs)
    async with get_pool().acquire() as conn:
        results = await search_chunks(
            conn,
            query=params.query,
            top_k=params.top_k,
            article_id=params.article_id,
            section=params.section,
        )

    if not results:
        return ToolResultBlock(
            tool_use_id=tool_use_id,
            content="No matching chunks found.",
        )

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=_ARTICLE_CHUNKS_ADAPTER.dump_json(results).decode(),
    )

async def search_journals(tool_use_id: str, **kwargs) -> ToolResultBlock:
    params = SearchJournalsInput(**kwargs)
    pmids = await esearch(params.query, params.max_results, params.date_from, params.date_to)
    articles = await efetch(pmids)

    result = SearchResult(
        query=params.query,
        total_results=len(articles),
        articles=articles,
    )

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json(),
    )


async def get_article(tool_use_id: str, **kwargs) -> ToolResultBlock:
    params = GetArticleInput(**kwargs)
    articles = await efetch([params.pmid])

    if not articles:
        return ToolResultBlock(
            tool_use_id=tool_use_id,
            content=f"No article found for PMID {params.pmid}.",
            is_error=True,
        )

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=articles[0].model_dump_json(),
    )


async def cite_sources(tool_use_id: str, **kwargs) -> ToolResultBlock:
    params = CiteSourcesInput(**kwargs)
    result = await esummary(params.pmids)

    citations = []
    for pmid in params.pmids:
        summary = result.get(pmid)
        if summary:
            citations.append(format_citation(summary, params.format))

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content="\n".join(citations) if citations else "No citations found.",
    )
