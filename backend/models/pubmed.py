from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class PubMedArticleType(str, Enum):
    RESEARCH = "research"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    META_ANALYSIS = "meta_analysis"


class PubMedAuthor(BaseModel):
    name: str
    affiliation: str | None = None


class PubMedArticle(BaseModel):
    pmid: str
    title: str
    authors: list[PubMedAuthor]
    journal: str
    published_at: datetime | None = None
    abstract: str | None = None
    doi: str | None = None
    article_type: PubMedArticleType = PubMedArticleType.RESEARCH
