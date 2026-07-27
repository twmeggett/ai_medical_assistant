import os
import numpy as np
import voyageai

embedding_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"]) # type: ignore[attr-defined]
model = "voyage-3"
rerank_model = "rerank-2.5-lite"

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def embed_chunks(chunks: list[str]):
    return embedding_client.embed(chunks, model=model, input_type="document")


def embed_query(query: str) -> list[float]:
    result = embedding_client.embed([query], model=model, input_type="query")
    return [float(x) for x in result.embeddings[0]]


def rerank_chunks(query: str, documents: list[str], top_k: int):
    # Cross-encoder rerank: scores each (query, document) pair jointly, unlike
    # embed_query's bi-encoder similarity which scores them independently.
    # More accurate but too expensive to run over a full corpus — callers
    # should only pass an already-narrowed candidate set.
    return embedding_client.rerank(query, documents, model=rerank_model, top_k=top_k)
