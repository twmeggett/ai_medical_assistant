from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from anthropic.types import MessageParam
import uuid


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ArticleType(str, Enum):
    RESEARCH = "research"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    META_ANALYSIS = "meta_analysis"


class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None


class Article(BaseModel):
    doi: str
    title: str
    authors: list[Author] = Field(default_factory=list)
    journal: str
    published_date: datetime
    abstract: str
    article_type: ArticleType = ArticleType.RESEARCH
    url: Optional[str] = None
    citation_count: Optional[int] = None

    @field_validator("doi")
    @classmethod
    def doi_must_have_prefix(cls, v: str) -> str:
        if not v.startswith("10."):
            raise ValueError("DOI must start with '10.'")
        return v


class SearchResult(BaseModel):
    query: str
    total_results: int
    articles: list[Article]
    relevance_scores: dict[str, float] = Field(
        default_factory=dict,
        description="DOI -> relevance score (0.0-1.0)"
    )


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls_made: list[str] = Field(default_factory=list)
    cited_dois: list[str] = Field(default_factory=list)


class ConversationHistory(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: list[ChatMessage] = Field(default_factory=list)
    title: Optional[str] = None

    def to_anthropic_messages(self) -> list[MessageParam]:
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]

    def add_message(self, role: MessageRole, content: str, **kwargs) -> ChatMessage:
        msg = ChatMessage(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def truncate_to_token_budget(self, max_messages: int = 20) -> None:
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
