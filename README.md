# AI Medical Assistant

A full-stack AI application that gives healthcare professionals evidence-based answers to clinical research questions. Built on Claude's streaming API with an agentic tool loop, real-time PubMed integration, and a persistent conversation layer backed by PostgreSQL.

---

## What this project demonstrates

This project was built to demonstrate practical AI engineering across the full stack — not just calling an LLM endpoint, but designing the system around it responsibly and correctly.

---

## Architecture overview

```
frontend/          React + TypeScript + Tailwind CSS
backend/
  api/             FastAPI route handlers (thin layer, no business logic)
  services/        Agentic streaming loop
  tools/           Tool schemas, executor, and PubMed implementations
  prompts/         Versioned system and user prompts
  db/              asyncpg queries for conversations and messages
  models/          Pydantic domain models, tool inputs, prompt versions
  utils/           Streaming helpers, PubMed client, batch API, sanitization
sql/               PostgreSQL schema and seed data
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

The active system prompt instructs the model to reason step-by-step, acknowledge conflicting evidence, and cite sources in a structured format. The user prompt (v2) supplies three few-shot medical examples — covering HFrEF beta-blockers, AF anticoagulation, and septic shock corticosteroids — to anchor the response format without relying solely on the system prompt.

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

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Claude (Anthropic) — streaming + tool use |
| Backend | FastAPI, asyncpg, Pydantic v2 |
| Database | PostgreSQL (Supabase) |
| External API | NCBI PubMed E-utilities |
| Frontend | React 18, TypeScript, Tailwind CSS v4 |
| Runtime | Python 3.12, uv |

---

## Running locally

**Backend**
```bash
export DATABASE_URL=postgresql://...
export ANTHROPIC_API_KEY=sk-ant-...
export NCBI_API_KEY=...   # optional — raises PubMed rate limit to 10 req/s

uv run fastapi dev backend/api/app.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
