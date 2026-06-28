from functools import partial
from backend.tools import search_journals_schema, get_article_schema, cite_sources_schema
from backend.utils.chat_helpers import chat_stream
from backend.prompts.system import ACTIVE_MED_ASSISTANT_SYSTEM

ai_med_assist_chat_stream = partial(
    chat_stream,
    system=[
        {
            "type": "text",
            "text": ACTIVE_MED_ASSISTANT_SYSTEM.content,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    tools=[search_journals_schema, get_article_schema, cite_sources_schema],
)
