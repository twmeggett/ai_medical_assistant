from typing import Callable, Sequence, TypedDict, TypeVar
from rank_bm25 import BM25Okapi

T = TypeVar("T")

class SearchResult(TypedDict):
    index: int
    rank: float


def bm25_search(
    items: Sequence[T],
    text: Callable[[T], str],
    query: str,
    top_k: int = 10,
    min_score: float = 0.0,
) -> list[SearchResult]:
    tokenized_corpus = [text(item).lower().split() for item in items]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query.lower().split())

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        SearchResult(index=i, rank=score)
        for i, score in ranked
        if score >= min_score
    ]


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]],
    k: int = 60,
) -> list[SearchResult]:
    rrf_scores: dict[int, float] = {}

    for results in result_lists:
        for rank, result in enumerate(results):
            index = result["index"]
            rrf_scores[index] = rrf_scores.get(index, 0) + 1.0 / (k + rank + 1)

    sorted_indices = sorted(rrf_scores, key=lambda i: rrf_scores[i], reverse=True)

    return [
        SearchResult(index=index, rank=rrf_scores[index])
        for index in sorted_indices
    ]
