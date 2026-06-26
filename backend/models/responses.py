from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from .domain import Article


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ChatResponse(BaseModel):
    conversation_id: str
    assistant_message: str
    cited_articles: list[Article] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    token_usage: Optional[TokenUsage] = None
