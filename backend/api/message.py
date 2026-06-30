from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.connector import get_pool
from backend.db.messages import save_message
from backend.models.domain import ChatMessage, MessageRole

router = APIRouter()


class SaveMessageRequest(BaseModel):
    conversation_id: str
    role: MessageRole
    content: str


@router.post("")
async def save_message_route(body: SaveMessageRequest):
    message = ChatMessage(role=body.role, content=body.content)
    try:
        async with get_pool().acquire() as conn:
            await save_message(conn, body.conversation_id, message)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save message")
    return {"message_id": message.id}
