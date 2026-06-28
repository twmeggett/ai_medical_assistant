from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic.types import MessageParam
from backend.utils.chat_helpers import add_user_message
from backend.services.conversation import run_conversation
from backend.services.streams import ai_med_assist_chat_stream
from backend.prompts.user import ACTIVE_MED_CHAT_USER_PROMPT

class ChatRequest(BaseModel):
    message: str
    history: list[MessageParam]

router = APIRouter()

@router.post("/stream")
async def stream_chat(body: ChatRequest):
    user_prompt = ACTIVE_MED_CHAT_USER_PROMPT.content.format(message=body.message)
    messages = add_user_message(body.history, user_prompt)
    return StreamingResponse(run_conversation(messages, ai_med_assist_chat_stream), media_type="text/event-stream")
