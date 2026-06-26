import asyncio
import logging
from backend.models import MedicalQuery
from backend.db import save_query, filter_by_user
from backend.utils import ai_med_assist_chat_stream, add_user_message, text_from_message, run_conversation

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

async def main():
    '''
    logger.info("Hello from ai-medical-assistant!")
    content = await filter_by_user("1")
    logger.info(f"Content: {content}")
    '''

    messages = []

    # await run_conversation(messages)


if __name__ == "__main__":
    asyncio.run(main())
