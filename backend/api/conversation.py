from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.connector import get_pool
from backend.db.conversations import create_conversation, get_full_conversation, get_conversations_by_user
from backend.models.domain import ConversationHistory

router = APIRouter()


class CreateConversationRequest(BaseModel):
    user_id: str


@router.post("")
async def create_conversation_route(body: CreateConversationRequest):
    conversation = ConversationHistory(user_id=body.user_id)
    async with get_pool().acquire() as conn:
        await create_conversation(conn, conversation)
    return {"conversation_id": conversation.conversation_id}


@router.get("/user/{user_id}")
async def get_user_conversations_route(user_id: str):
    async with get_pool().acquire() as conn:
        return await get_conversations_by_user(conn, user_id)


@router.get("/{conversation_id}")
async def get_history_route(conversation_id: str):
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation