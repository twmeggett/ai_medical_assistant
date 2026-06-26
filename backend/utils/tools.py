from pydantic import ValidationError
from backend.models.tools import SearchJournalsInput, GetArticleInput, CiteSourcesInput
from backend.models.requests import ToolResultBlock
from backend.models.domain import SearchResult, Article, Author

async def tool_executor(tool_name: str, tool_use_id: str, raw_input: dict) -> ToolResultBlock:
    try:
        match tool_name:
            case 'search_journals':
                return await _search_journals(**raw_input)
            case 'get_article':
                return await _get_article(**raw_input)
            case 'cite_sources_input':
                return await _cite_sources_input(**raw_input)
            case _:
                return ToolResultBlock(
                    tool_use_id=tool_use_id,
                    content=f"Unknown tool: {tool_name}",
                    is_error=True
                )
    
    except ValidationError as e:
        # Claude sent bad input — return structured error, not a Python exception.
        # is_error=True tells Claude to self-correct on the next turn.
        return ToolResultBlock(
            tool_use_id=tool_use_id,
            content=f"Invalid input: {e.errors()}",
            is_error=True
        )


async def _search_journals(tool_use_id: str, raw_input: dict) -> ToolResultBlock:
    # TODO - remove once we create an actual search function to query the database         
    async def mock_search(query: str, max_results: int):
        return {}

    params = SearchJournalsInput(**raw_input)

    raw_result = await mock_search(params.query, params.max_results)

    result = SearchResult(**raw_result)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json()
    )


async def _get_article(tool_use_id: str, raw_input: dict) -> ToolResultBlock:
    # TODO - remove once we create an actual search function to query the database         
    async def mock_get_article(doi: str):
        return {}

    # Find medical article based on doi
    params = GetArticleInput(**raw_input)

    raw_result = await mock_get_article(params.doi)

    result = Article(**raw_result)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json()
    )

async def _cite_sources_input(tool_use_id: str, raw_input: dict):
     # TODO - remove once we create an actual search function to query the database         
    async def cite_sources(dois: list[str]):
        return {}

    params = CiteSourcesInput(**raw_input)

    raw_result = await cite_sources(params.dois)

    result = Author(**raw_result)

    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=result.model_dump_json()
    )
