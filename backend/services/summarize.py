from backend.utils.chat_helpers import client, model
from backend.prompts.summarize import ACTIVE_SUMMARIZE_PROMPT


async def summarize_query(query: str) -> str:
    response = await client.messages.create(
        model=model,
        max_tokens=20,
        system=ACTIVE_SUMMARIZE_PROMPT.content,
        messages=[{"role": "user", "content": query}],
    )
    return response.content[0].text.strip()  # type: ignore[union-attr]
