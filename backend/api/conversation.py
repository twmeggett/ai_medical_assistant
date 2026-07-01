from fastapi import APIRouter, HTTPException
from backend.db.connector import get_pool
from backend.db.conversations import create_conversation, delete_conversation, get_full_conversation, get_conversations_by_user, update_conversation_title
from backend.models.domain import ConversationHistory
from backend.models.requests import CreateConversationRequest, UpdateConversationRequest

router = APIRouter()


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



@router.patch("/{conversation_id}")
async def update_conversation_route(conversation_id: str, body: UpdateConversationRequest):
    async with get_pool().acquire() as conn:
        updated = await update_conversation_title(conn, conversation_id, body.title)

    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"conversation_id": conversation_id, "title": body.title}


@router.delete("/{conversation_id}")
async def delete_conversation_route(conversation_id: str):
    async with get_pool().acquire() as conn:
        deleted = await delete_conversation(conn, conversation_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"conversation_id": conversation_id}


@router.get("/{conversation_id}")
async def get_history_route(conversation_id: str):
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation