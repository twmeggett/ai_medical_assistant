from fastapi import APIRouter, HTTPException
from backend.db.connector import get_pool
from backend.db.conversations import get_full_conversation

router = APIRouter()

@router.get("/{conversation_id}")
async def get_history(conversation_id: str):
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation