from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    user_id: str

    @field_validator("message")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class CreateConversationRequest(BaseModel):
    user_id: str


class UpdateConversationRequest(BaseModel):
    title: str


class CreateArticleRequest(BaseModel):
    title: str
    authors: list[str]
    journal: str
    published_at: datetime
    full_text: str

class CreateArticleChunkRequest(BaseModel):
    article_id: str
    chunk_text: str
    context_text: str
    embedding: list[float]
    section: str
    chunk_index: int
    token_count: int
    metadata: str | None = None

    @field_validator("embedding")
    @classmethod
    def check_dimensions(cls, v: list[float]) -> list[float]:
        if len(v) != 1024:
            raise ValueError(f"Expected 1024 dimensions, got {len(v)}")
        return v
