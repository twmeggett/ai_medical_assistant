import os
import numpy as np
import voyageai

embedding_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"]) # type: ignore[attr-defined]
model = "voyage-3"

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def embed_chunks(chunks: list[str]):
    return embedding_client.embed(chunks, model=model, input_type="document")


def embed_query(query: str) -> list[float]:
    result = embedding_client.embed([query], model=model, input_type="query")
    return [float(x) for x in result.embeddings[0]]
