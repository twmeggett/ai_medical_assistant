from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.services import search_article_chunks
from backend.db.connector import get_pool
from backend.models import ArticleChunk
from backend.utils.embedding_helpers import embed_query

router = APIRouter()


class SearchChunksRequest(BaseModel):
    query: str
    top_k: int = 10
    article_id: str | None = None
    section: str | None = None


@router.post("/chunks/search", response_model=list[ArticleChunk])
async def search_chunks(body: SearchChunksRequest):
    async with get_pool().acquire() as conn:
        results = await search_article_chunks(
            conn,
            query=body.query,
            top_k=body.top_k,
            article_id=body.article_id,
            section=body.section,
        )
    return results
