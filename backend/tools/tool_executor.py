from pydantic import ValidationError
from backend.models.requests import ToolResultBlock
from backend.tools.tools import search_journals, get_article, cite_sources
from backend.utils.sanitize import strip_injection_patterns

def wrap_tool_output(content: str, source: str = "tool") -> str:
    """
    XML wrapper signals to Claude: this is external data, not instructions.
    Especially important once you add PubMed or pgvector retrieval in Sprint 3.
    """
    sanitized = strip_injection_patterns(content)
    return f"<tool_result source='{source}'>{sanitized}</tool_result>"

async def tool_executor(tool_name: str, tool_use_id: str, raw_input: dict) -> ToolResultBlock:
    try:
        match tool_name:
            case "search_journals":
                result = await search_journals(tool_use_id, **raw_input)
            case "get_article":
                result = await get_article(tool_use_id, **raw_input)
            case "cite_sources":
                result = await cite_sources(tool_use_id, **raw_input)
            case _:
                return ToolResultBlock(
                    tool_use_id=tool_use_id,
                    content=f"Unknown tool: {tool_name}",
                    is_error=True,
                )
    except ValidationError as e:
        return ToolResultBlock(
            tool_use_id=tool_use_id,
            content=f"Invalid input: {e.errors()}",
            is_error=True,
        )

    result.content = wrap_tool_output(result.content, tool_name)
    return result
