# AI Medical Assistant

A full-stack AI application that gives healthcare professionals evidence-based answers to clinical research questions. Built on Claude's streaming API with an agentic tool loop, real-time PubMed integration, a persistent conversation layer backed by PostgreSQL, and an offline ingestion pipeline that chunks and embeds full-text articles for hybrid vector + keyword retrieval.

https://github.com/user-attachments/assets/5b671b12-fa6d-4374-aedd-a8559d582118

*A live query against PubMed — the assistant searches for relevant studies, cites sources, and streams its response in real time.*

---

## What this project demonstrates

This project was built to demonstrate practical AI engineering across the full stack — not just calling an LLM endpoint, but designing the system around it responsibly and correctly.

---

## Architecture overview

```
frontend/          React + TypeScript + Tailwind CSS
backend/
  api/             FastAPI route handlers (thin layer, no business logic)
  services/        Agentic streaming loop; article ingestion, chunking, and hybrid search
  tools/           Tool schemas, executor, and PubMed implementations
  prompts/         Versioned system and user prompts
  db/              asyncpg queries for conversations, messages, and articles
  models/          Pydantic domain models, tool inputs, prompt versions
  utils/           Streaming helpers, PubMed client, batch API, chunking, embeddings, retrieval, sanitization
  evals.py         Ragas-based evaluation of the article_chunks retrieval + generation pipeline
sql/               PostgreSQL schema and seed data
scripts/           CLI entry points for seeding and chunking articles offline
```

---

## Core AI engineering decisions

### 1. Agentic tool loop

The assistant doesn't make a single LLM call per message. `backend/services/conversation.py` implements a loop that runs until the model stops requesting tools:

```python
while True:
    async with stream_fn(messages) as stream:
        ...
        if response.stop_reason == "tool_use":
            # execute tools, append results, continue loop
        else:
            break
```

This reflects how real agentic systems work — the model decides when it has enough information to answer, potentially calling multiple tools in sequence.

### 2. Three PubMed tools with real API integration

Rather than mocking tool results, all three tools call the NCBI E-utilities API:

| Tool | NCBI Endpoint | Purpose |
|---|---|---|
| `search_journals` | ESearch + EFetch | Keyword search returning full article metadata and abstracts |
| `get_article` | EFetch | Retrieve a specific article by PMID |
| `cite_sources` | ESummary | Format APA / MLA / Vancouver citations for a list of PMIDs |

The PubMed client (`backend/utils/pubmed.py`) handles XML parsing, rate-limit retry with exponential backoff, and an optional `NCBI_API_KEY` for higher throughput.

A fourth tool, `search_article_chunks`, gives the model access to the offline-ingested article corpus (see §8) rather than live PubMed — the model chooses between "search PubMed for new literature" and "search what's already been ingested and chunked" based on the question.

### 3. Versioned prompts with few-shot examples

Prompts are modelled as `PromptVersion` objects with version numbers, sprint tags, and change notes — treating them like code that evolves:

```python
class PromptVersion(BaseModel):
    content: str
    version: str
    sprint: int
    optimized_for: str
    notes: str
    changed_from: str | None = None
```

The active system prompt (v3) instructs the model to reason step-by-step, acknowledge conflicting evidence, and cite sources in a structured format. It also explicitly tells the model that multi-excerpt tool results (e.g. `search_article_chunks`) are relevance-ordered but not a cutoff, and to weigh every returned excerpt rather than anchoring on the first one or two — a direct mitigation for "lost in the middle," the documented tendency of LLMs to under-attend to information placed mid-context, which becomes a real risk once a single tool call can return up to 20 ranked excerpts. The user prompt (v2) supplies three few-shot medical examples — covering HFrEF beta-blockers, AF anticoagulation, and septic shock corticosteroids — to anchor the response format without relying solely on the system prompt.

Prompt templates are applied consistently across all turns of a conversation (not just the first), so historical context sent to the model always carries the formatting instructions.

### 4. Prompt injection defence

Tool outputs from PubMed are untrusted external content. Two layers of protection are applied:

- **Sanitization** (`backend/utils/sanitize.py`): strips known injection patterns (`"ignore previous instructions"`, `"you are now"`, etc.) from tool results before they are returned to the model, replacing them with `[FILTERED]`.
- **Prompt design**: the system prompt explicitly instructs the model to treat content inside `<tool_result>` and `<retrieved_document>` tags as data only, and to alert the user if it detects any attempt to override its instructions.

### 5. Streaming with tool use

Responses stream token-by-token from Claude to the browser using `StreamingResponse`. The stream handler yields text chunks, tool call names, and partial JSON input as they arrive, so the UI updates in real time without waiting for the full response. Tool calls are surfaced inline (`>>> Tool Call: "search_journals"`) so the user can see what the model is doing.

### 6. DB-decoupled service layer

`run_conversation` is a pure async generator — it takes a messages list and a stream function, and knows nothing about the database. All persistence is handled by the API layer via an `on_assistant_message` callback:

```python
async def run_conversation(
    messages: list[MessageParam],
    stream_fn: ChatStreamFn,
    on_assistant_message: Callable[[str], Awaitable[None]] | None = None,
) -> AsyncGenerator[str, None]:
```

This makes the service independently testable and reusable across different storage backends.

### 7. Batch API utility

`backend/utils/batch_helpers.py` implements the Anthropic Message Batches API — creating batches, polling for completion, streaming results, and cancelling in-flight jobs. This reflects awareness of cost and throughput tradeoffs: batch processing is suited to offline workloads like bulk summarisation or evaluation runs where latency is not critical.

### 8. Contextual chunking, hybrid retrieval, and reranking

Full-text articles are ingested offline (`scripts/save_articles.py`, `scripts/chunk_articles.py`) rather than embedded on demand, so retrieval quality work doesn't sit on the request path:

- **Section-aware chunking** — `chunk_by_sections` splits each article at recognised medical headings (Abstract, Methods, Results, ...) before recursively sub-chunking any section that exceeds the token budget, so chunk boundaries respect document structure instead of falling at arbitrary character offsets.
- **Contextual retrieval** — before embedding, each chunk is paired with a short, model-generated blurb describing how it relates to the source article (Anthropic's contextual retrieval technique), submitted as a batch job via the same Message Batches utility from §7. The blurb and raw chunk are stored separately (`context_text` / `chunk_text`) but concatenated for embedding, improving recall for chunks that are ambiguous in isolation.
- **Idempotent re-ingestion** — each chunk's `content_hash` (`sha256(article_id + chunk_text)`) is enforced unique at the DB level via `ON CONFLICT ... DO NOTHING`, and `chunk_articles` checks existing hashes *before* the expensive context-generation and embedding steps, not just at insert time — so re-running ingestion after a partial failure skips already-processed chunks instead of reprocessing (and re-paying for) the whole article. The hash is deliberately computed from only `chunk_text`, not the LLM-generated `context_text`, since the latter is non-deterministic across runs and would otherwise defeat idempotency entirely.
- **Hybrid retrieval** — `search_article_chunks` runs two independent full-corpus queries — a pgvector ANN search (Voyage `voyage-3`, 1024-dim, HNSW index) and a Postgres full-text search (`tsvector`/`ts_rank_cd`, GIN index) — rather than one reranking the other's candidates, then merges the two rankings with Reciprocal Rank Fusion (RRF). Keyword matches surface exact clinical terms (drug names, dosages) that dense embeddings can under-weight, and running it as an independent query means a strong keyword match isn't lost just because it fell outside the vector search's top-k. Each method fetches a wider candidate pool than the final result count so RRF has enough signal to fuse over before narrowing down.
- **Cross-encoder reranking** — RRF's fused order is not the final answer: the fused candidates are re-scored by Voyage's `rerank-2.5-lite`, a cross-encoder that scores each `(query, chunk)` pair jointly rather than independently (as bi-encoder embeddings and lexical rank both do), producing a substantially more precise final ranking. Two cutoffs are applied together, each catching a different failure mode: an absolute floor (`DEFAULT_MIN_RERANK_SCORE = 0.4`) rejects a chunk regardless of rank — this is what lets a query with no genuinely relevant content return zero results instead of padding out to `top_k` with noise — and a relative floor (`DEFAULT_RERANK_RELATIVE_FACTOR = 0.7` of the query's own top score) trims the tail once there is a good match, since a lower-ranked chunk can clear the absolute floor on its own while still belonging to a different article than the top result. The relative floor can never rescue a bad *top* result, since rank 1 is always 100% of itself — that failure mode is what the absolute floor exists for. Both values were calibrated by inspecting the model's score distribution across specific, broad, and deliberately off-topic queries against the ingested corpus (see `backend/evals.py`), since `relevance_score` isn't a calibrated probability and a fixed cutoff has to be chosen from real score behaviour, not assumed.

### 9. RAG pipeline evaluation

`backend/evals.py` evaluates the `article_chunks` retrieval + generation pipeline with Ragas, scoring:

- **`Faithfulness`** and **`ResponseRelevancy`** — is the generated answer actually supported by the retrieved chunks, and does it address the question asked (generation quality).
- **`ContextPrecision`** and **`ContextRecall`** — are the retrieved chunks relevant, and do they collectively contain what's needed to answer correctly (retrieval quality).

For each eval case it runs the real pipeline — `search_article_chunks` against the live database, then a single-shot Claude call constrained to answer only from those chunks — rather than testing against pre-canned contexts, so a regression anywhere in retrieval shows up in the score. The LLM judge and embeddings are wired to this project's actual providers (`ChatAnthropic`, `VoyageAIEmbeddings`) via Ragas' langchain integration, rather than the OpenAI defaults most Ragas examples assume.

---

## Frontend engineering

### Custom hook architecture

All state logic is lifted out of components into composable hooks:

| Hook | Responsibility |
|---|---|
| `useConversation` | Orchestrates the full conversation lifecycle |
| `useChatStream` | Manages streaming state and the fetch loop |
| `useUserConversations` | Fetches and refreshes the conversation list |
| `useConversationHistory` | Loads persisted messages for the active conversation |
| `useUser` | Provides the current user identity |

### Optimistic UI with post-stream refresh

When a user submits a message, it appears in the chat immediately before any server round-trip. After streaming completes, the conversation history is re-fetched from the database — replacing the optimistic entry with the fully persisted version that includes the assistant's response. This keeps the UI responsive without holding stale client-side state indefinitely.

### API layer separation

Raw `fetch` calls live in `frontend/src/api/` and are never called directly from hooks or components. Hooks consume the API layer; components consume hooks. This mirrors the backend's layered architecture.

---

## Data model

Conversations and messages are persisted in PostgreSQL (Supabase). Each `ChatMessage` carries the role, content, timestamp, tool calls made, and cited DOIs. Each `ConversationHistory` carries a token-budget-aware message list with a `truncate_to_token_budget` method to prevent context overflow on long conversations.

Ingested literature is persisted separately: `articles` stores full text and metadata with a `chunk_status` (`pending` / `processing` / `complete` / `failed`) tracking ingestion progress, and `article_chunks` stores each chunk's text, generated context, 1024-dim embedding, section/index position, and a `content_hash` (unique, for idempotent re-ingestion — see §8), with a foreign key cascade back to its parent article, an HNSW index for approximate nearest-neighbour search, and a GIN index over a generated `tsvector` column for full-text keyword search.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Claude (Anthropic) — streaming + tool use |
| Backend | FastAPI, asyncpg, Pydantic v2 |
| Database | PostgreSQL (Supabase) with pgvector (HNSW) |
| Embeddings | Voyage AI (`voyage-3`, 1024-dim) |
| Keyword search | Postgres full-text search (`tsvector`, GIN), fused with vector search via Reciprocal Rank Fusion |
| Reranking | Voyage AI cross-encoder (`rerank-2.5-lite`) |
| Evaluation | Ragas (Faithfulness, ContextPrecision, ContextRecall, ResponseRelevancy) |
| External API | NCBI PubMed E-utilities |
| Frontend | React 18, TypeScript, Tailwind CSS v4 |
| Runtime | Python 3.12, uv |

---

## Running locally

**Backend**
```bash
export DATABASE_URL=postgresql://...
export ANTHROPIC_API_KEY=sk-ant-...
export VOYAGE_API_KEY=pa-...       # required for article embedding
export NCBI_API_KEY=...            # optional — raises PubMed rate limit to 10 req/s

uv run fastapi dev backend/api/app.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Ingesting articles** (offline, run once per batch of new articles)
```bash
uv run python scripts/save_articles.py     # parse + persist raw articles
uv run python scripts/chunk_articles.py    # section-chunk, contextualise, embed, and store chunks
```

**Evaluating retrieval quality** (requires articles already ingested; installs the `eval` dependency group for the langchain provider wrappers)
```bash
uv sync --group eval
uv run python -m backend.evals
```
