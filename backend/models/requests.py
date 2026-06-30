from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    user_id: str

    @field_validator("message")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class ToolResultBlock(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: bool = False
