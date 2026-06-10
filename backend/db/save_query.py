import logging
import json
import aiofiles
from models import MedicalQuery
from utils import timer

logger = logging.getLogger(__name__)

@timer
async def save_query_to_db(query: MedicalQuery) -> None:
    logger.info(f"Saving query for user {query.user_id} with session {query.session_id} at {query.timestamp}")
    json_string = json.dumps(query, indent=4)
    
    async with aiofiles.open('medical_queries', mode='w', encoding='utf-8') as file:
        await file.write(json_string)