from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic.types import MessageParam
from backend.utils.chat_helpers import add_user_message, run_conversation

class ChatRequest(BaseModel):
    message: str
    history: list[MessageParam]

router = APIRouter()

@router.post("/stream")
async def stream_chat(body: ChatRequest):
    messages = add_user_message(body.history, body.message)
    return StreamingResponse(run_conversation(messages), media_type="text/event-stream")
