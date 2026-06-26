from typing import Optional
from pydantic import BaseModel, Field, field_validator

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
    doi: str = Field(..., description="e.g. '10.1056/NEJMoa2034577'")

    @field_validator("doi")
    @classmethod
    def doi_must_have_prefix(cls, v: str) -> str:
        if not v.startswith("10."):
            raise ValueError(f"Invalid DOI format: {v}")
        return v.strip()

class CiteSourcesInput(BaseModel):
    dois: list[str] = Field(..., min_length=1, max_length=10)
    format: str = Field(default="APA", pattern="^(APA|MLA|Vancouver)$")