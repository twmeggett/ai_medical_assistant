from backend.models.tools import SearchJournalsInput, GetArticleInput, CiteSourcesInput
from backend.models.requests import ToolResultBlock
from backend.models.domain import SearchResult, Article, Author


async def search_journals(tool_use_id: str, **kwargs) -> ToolResultBlock:
    # TODO - remove once we create an actual search function to query the database
    async def mock_search(query: str, max_results: int):
        return {}

    params = SearchJournalsInput(**kwargs)
    raw_result = await mock_search(params.query, params.max_results)
    result = SearchResult(**raw_result)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json()
    )


async def get_article(tool_use_id: str, **kwargs) -> ToolResultBlock:
    # TODO - remove once we create an actual search function to query the database
    async def mock_get_article(doi: str):
        return {}

    params = GetArticleInput(**kwargs)
    raw_result = await mock_get_article(params.doi)
    result = Article(**raw_result)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json()
    )


async def cite_sources(tool_use_id: str, **kwargs) -> ToolResultBlock:
    # TODO - replace with real citation lookup once implemented
    async def mock_cite_sources(dois: list[str]) -> list[str]:
        return [f"Citation for {doi} (placeholder)" for doi in dois]

    params = CiteSourcesInput(**kwargs)
    citations = await mock_cite_sources(params.dois)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content="\n".join(citations)
    )
