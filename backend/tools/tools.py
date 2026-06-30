from backend.models.tools import SearchJournalsInput, GetArticleInput, CiteSourcesInput
from backend.models.requests import ToolResultBlock
from backend.models.domain import SearchResult
from backend.utils.pubmed import esearch, efetch, esummary, format_citation


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
