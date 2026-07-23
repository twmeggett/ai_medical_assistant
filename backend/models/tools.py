from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class ToolResultBlock(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: bool = False

class SearchJournalsInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)
    date_from: Optional[str] = None    # "YYYY-MM-DD"
    date_to: Optional[str] = None   # "YYYY-MM-DD"

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()
    
class GetArticleInput(BaseModel):
    pmid: str = Field(..., description="e.g. '34567890'")

class CiteSourcesInput(BaseModel):
    pmids: list[str] = Field(..., min_length=1, max_length=10)
    format: str = Field(default="APA", pattern="^(APA|MLA|Vancouver)$")