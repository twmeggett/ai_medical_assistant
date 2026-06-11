import aiofiles
import json
import logging
from backend.models import MedicalQuery

logger = logging.getLogger(__name__)

async def filter_by_user(user_id: str) -> list[MedicalQuery] | None:
    try:
        async with aiofiles.open('medical_queries.json', mode='r', encoding='utf-8') as f:
            queries = json.loads(await f.read())
        return [q for q in queries if q['user_id'] == user_id]
    except Exception as E:
        logger.exception('Error retrieving the user queries')