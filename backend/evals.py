"""
Ragas evaluation of the article_chunks retrieval + generation pipeline.

Uses langchain wrappers (ChatAnthropic, VoyageAIEmbeddings) so ragas' LLM
judge and embedding-based metrics run against this project's actual model
and embedding providers (Claude + Voyage) rather than the OpenAI defaults.

Prerequisites: articles must already be ingested and chunked
(scripts/save_articles.py, scripts/chunk_articles.py) — this evaluates
retrieval quality against what's actually in the database, it doesn't seed it.
"""

import asyncio
import os

from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings
from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import Faithfulness, ContextPrecision, ContextRecall, ResponseRelevancy

from backend.datasets.med_article_evals import EVAL_SET
from backend.db.connector import connect, disconnect, get_pool
from backend.services import search_article_chunks

JUDGE_MODEL = os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5-20251001")
GENERATION_MODEL = os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-5")
VOYAGE_MODEL = "voyage-3"
TOP_K = 8

# ContextPrecision scores one retrieved chunk at a time via sequential judge
# calls (not concurrent), so its per-job time scales with TOP_K — ragas'
# default 180s RunConfig timeout isn't enough headroom for TOP_K=8 chunks
# and was observed killing the job (silently scored as NaN) mid-run.
EVAL_TIMEOUT_SECONDS = 600

llm = LangchainLLMWrapper(ChatAnthropic(model=JUDGE_MODEL))
embeddings = LangchainEmbeddingsWrapper(VoyageAIEmbeddings(model=VOYAGE_MODEL))
async_anthropic_client = AsyncAnthropic()

METRICS = [
    Faithfulness(llm=llm),
    ContextPrecision(llm=llm),
    ContextRecall(llm=llm),
    ResponseRelevancy(llm=llm, embeddings=embeddings),
]

GENERATION_SYSTEM_PROMPT = (
    "Answer the user's question using only the information in the provided "
    "excerpts from medical literature. If the excerpts don't contain enough "
    "information to answer, say so explicitly rather than guessing."
)


async def generate_answer(question: str, contexts: list[str]) -> str:
    context_block = "\n\n---\n\n".join(contexts)
    response = await async_anthropic_client.messages.create(
        model=GENERATION_MODEL,
        max_tokens=500,
        system=GENERATION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"<excerpts>{context_block}</excerpts>\n\n<question>{question}</question>",
            }
        ],
    )
    return response.content[0].text.strip()  # type: ignore[union-attr]


async def build_dataset(conn) -> EvaluationDataset:
    samples = []
    for case in EVAL_SET:
        chunks = await search_article_chunks(conn, query=case["question"], top_k=TOP_K)
        retrieved_contexts = [chunk.chunk_text for chunk in chunks]
        response = await generate_answer(case["question"], retrieved_contexts)
        samples.append(
            SingleTurnSample(
                user_input=case["question"],
                retrieved_contexts=retrieved_contexts,
                response=response,
                reference=case["reference"],
            )
        )
    return EvaluationDataset(samples=samples)


async def run_eval():
    await connect()
    try:
        async with get_pool().acquire() as conn:
            dataset = await build_dataset(conn)
    finally:
        await disconnect()

    return evaluate(
        dataset=dataset,
        metrics=METRICS,
        run_config=RunConfig(timeout=EVAL_TIMEOUT_SECONDS),
    )


if __name__ == "__main__":
    result = asyncio.run(run_eval())
    print(result)
    print(result.to_pandas())
