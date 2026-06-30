from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.db.connector import get_pool
from backend.db.conversations import get_full_conversation
from backend.db.messages import save_message
from backend.models.domain import MessageRole
from backend.services.conversation import run_conversation
from backend.services.streams import ai_med_assist_chat_stream
from backend.prompts.user import ACTIVE_MED_CHAT_USER_PROMPT


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


router = APIRouter()


@router.post("/stream")
async def stream_chat_route(body: ChatRequest):
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, body.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail=f"Conversation {body.conversation_id} not found")

        user_message = conversation.add_message(MessageRole.USER, body.message)
        await save_message(conn, body.conversation_id, user_message)

    conversation.truncate_to_token_budget()
    messages = conversation.to_anthropic_messages()

    for msg in messages:
        if msg["role"] == "user" and isinstance(msg["content"], str):
            msg["content"] = ACTIVE_MED_CHAT_USER_PROMPT.content.format(message=msg["content"])

    async def save_assistant_message(text: str) -> None:
        assistant_message = conversation.add_message(MessageRole.ASSISTANT, text)
        async with get_pool().acquire() as conn:
            await save_message(conn, body.conversation_id, assistant_message)

    return StreamingResponse(
        run_conversation(messages, ai_med_assist_chat_stream, on_assistant_message=save_assistant_message),
        media_type="text/event-stream",
    )
