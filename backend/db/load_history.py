import json
import aiofiles
import logging
from backend.models import ConversationHistory

logger = logging.getLogger(__name__)

async def load_history(session_id: str) -> ConversationHistory | None:
    # Simulate loading from a database
    logger.info("Query the database for the conversation history")
    async with aiofiles.open('conversation_history.json', mode='r', encoding='utf-8') as f:
        content = json.loads(await f.read())
        return next((h for h in content if h.session_id == session_id), None)
