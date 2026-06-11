import logging
import json
import aiofiles
from dataclasses import asdict
from datetime import datetime
from backend.models import MedicalQuery
from backend.utils import timer

logger = logging.getLogger(__name__)

@timer
async def save_query(query: MedicalQuery) -> None:
    logger.info(f"Saving query for user {query.user_id} with session {query.session_id} at {query.timestamp}")

    try:
        json_string = json.dumps(asdict(query), indent=4, default=lambda o: o.isoformat() if isinstance(o, datetime) else TypeError(f"Object of type {type(o)} is not JSON serializable"))
        try:
            async with aiofiles.open('medical_queries.json', mode='r', encoding='utf-8') as file:
                content = await file.read()
        except FileNotFoundError:
            content = ''
        async with aiofiles.open('medical_queries.json', mode='w', encoding='utf-8') as file:
            await file.write('[\n' + content + ',\n' + json_string + '\n]')
    except Exception as e:
        logger.exception("Error saving query")