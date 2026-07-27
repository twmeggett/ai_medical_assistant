from typing import TypedDict

class SearchResult(TypedDict):
    id: str
    rank: float


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]],
    k: int = 60,
) -> list[SearchResult]:
    rrf_scores: dict[str, float] = {}

    for results in result_lists:
        for rank, result in enumerate(results):
            result_id = result["id"]
            rrf_scores[result_id] = rrf_scores.get(result_id, 0) + 1.0 / (k + rank + 1)

    sorted_ids = sorted(rrf_scores, key=lambda i: rrf_scores[i], reverse=True)

    return [
        SearchResult(id=result_id, rank=rrf_scores[result_id])
        for result_id in sorted_ids
    ]


def normalize_scores(results: list[SearchResult]) -> list[SearchResult]:
    # Min-max normalization to 0-100: raw RRF scores are tiny and clustered
    # (typically ~0.01-0.03), which is hard to read at a glance. Rescaling so
    # the weakest result in the set is 0 and the strongest is 100 turns that
    # into an intuitive "closeness to best match" percentage. Order-preserving
    # since it's a positive linear transform.
    if not results:
        return results

    scores = [result["rank"] for result in results]
    lo, hi = min(scores), max(scores)

    if hi == lo:
        return [SearchResult(id=result["id"], rank=100.0) for result in results]

    return [
        SearchResult(id=result["id"], rank=(result["rank"] - lo) / (hi - lo) * 100)
        for result in results
    ]
