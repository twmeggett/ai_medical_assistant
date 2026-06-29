from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.services.conversation import run_conversation
from backend.services.streams import ai_med_assist_chat_stream
from backend.prompts.user import ACTIVE_MED_CHAT_USER_PROMPT


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


router = APIRouter()


@router.post("/stream")
async def stream_chat(body: ChatRequest):
    user_prompt = ACTIVE_MED_CHAT_USER_PROMPT.content.format(message=body.message)
    try:
        return StreamingResponse(run_conversation(body.conversation_id, user_prompt, ai_med_assist_chat_stream), media_type="text/event-stream")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
