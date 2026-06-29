from fastapi import APIRouter, HTTPException
from backend.db.connector import get_pool
from backend.db.conversations import get_full_conversation, get_conversations_by_user

router = APIRouter()


@router.get("/user/{user_id}")
async def get_user_conversations(user_id: str):
    async with get_pool().acquire() as conn:
        return await get_conversations_by_user(conn, user_id)


@router.get("/{conversation_id}")
async def get_history(conversation_id: str):
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation