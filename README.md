# AI Knowledge Inbox

A full-stack app for saving plain-text notes or webpage URLs, then asking questions that are answered **only** from what you've saved — a small, self-contained Retrieval-Augmented Generation (RAG) pipeline.

## 1. Project Overview

You paste in a note or a URL. The backend extracts the text, splits it into overlapping chunks, embeds each chunk with OpenAI's `text-embedding-3-small`, and stores the chunks and their embeddings in SQLite. When you ask a question, the backend embeds the question, finds the most semantically similar stored chunks (cosine similarity), and asks an OpenAI chat model to answer **using only those chunks** — never its own outside knowledge. The answer comes back with the exact sources (title, URL, snippet, similarity score) that were used.

## 2. Architecture

```
frontend/  (React + Vite)
  src/
    services/api.js        <- all HTTP calls (axios)
    components/            <- IngestForm, ItemsList, QuestionForm, AnswerCard, SourceCard
    App.jsx                <- page composition + top-level state

backend/   (FastAPI)
  app/
    main.py                <- app creation, CORS, router wiring, table creation
    database.py             <- SQLAlchemy engine/session
    models.py               <- Item, Chunk ORM models
    schemas.py               <- Pydantic request/response models + validation
    routers/
      ingestion.py           <- POST /ingest
      items.py                <- GET /items
      query.py                <- POST /query
    services/
      chunking_service.py     <- token-based chunk splitting
      embedding_service.py    <- OpenAI embeddings, JSON (de)serialization
      retrieval_service.py    <- cosine similarity + top-k retrieval
      llm_service.py           <- prompt construction + OpenAI chat call
      url_service.py            <- URL fetch + BeautifulSoup text extraction
    utils/
      logger.py                <- structured logging setup
  tests/                       <- pytest suite
```

Request flow for ingestion: `router -> url_service (if URL) -> chunking_service -> embedding_service -> DB`.
Request flow for a question: `router -> retrieval_service (embeds question, scores chunks) -> llm_service (answers from context) -> response with sources`.

## 3. Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- An OpenAI API key

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # Windows: copy, macOS/Linux: cp
```

Edit `backend/.env` and set `OPENAI_API_KEY`.

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env         # Windows: copy, macOS/Linux: cp
npm run dev
```

The app is now at `http://localhost:5173` and talks to the backend at the URL in `VITE_API_BASE_URL`.

## 4. Environment Variables

`backend/.env.example`:

```
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=sqlite:///./knowledge_inbox.db
SIMILARITY_THRESHOLD=0.30
```

- `OPENAI_API_KEY` — required, never hard-coded, never logged.
- `OPENAI_CHAT_MODEL` — chat model used to answer questions from context.
- `OPENAI_EMBEDDING_MODEL` — must stay `text-embedding-3-small` for embedding dimension consistency with stored vectors.
- `DATABASE_URL` — SQLAlchemy connection string.
- `SIMILARITY_THRESHOLD` — chunks scoring below this cosine similarity are never returned, no matter how high `top_k` is.

`frontend/.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## 5. API Examples

### Ingest a note

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_type": "note", "title": "Leave Policy", "content": "Employees receive 20 paid leave days every year."}'
```

```json
{
  "id": 1,
  "title": "Leave Policy",
  "source_type": "note",
  "source_url": null,
  "chunk_count": 1,
  "created_at": "2026-07-11T10:00:00"
}
```

### Ingest a URL

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_type": "url", "url": "https://example.com/article"}'
```

### List saved items

```bash
curl http://localhost:8000/items
```

### Ask a question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many paid leaves do employees receive?", "top_k": 3}'
```

```json
{
  "answer": "Employees receive 20 paid leave days every year.",
  "sources": [
    {
      "item_id": 1,
      "title": "Leave Policy",
      "source_type": "note",
      "source_url": null,
      "snippet": "Employees receive 20 paid leave days every year.",
      "similarity_score": 0.91
    }
  ]
}
```

### HTTP status codes used

| Code | Meaning |
|------|---------|
| 200  | Successful query |
| 201  | Successful ingestion |
| 400  | Invalid business input (bad URL scheme, unfetchable/empty page, empty question) |
| 404  | No saved content exists yet when a query is made |
| 422  | Pydantic schema validation failure (empty note fields, unsupported `source_type`, `top_k` out of 1–10 range) |
| 502  | OpenAI embedding or chat call failed |

## 6. Chunk Size and Overlap Rationale

Chunks are ~500 tokens with ~100-token overlap (`app/services/chunking_service.py`), using `tiktoken`'s `cl100k_base` encoding to count tokens accurately rather than approximating from characters or words.

- **500 tokens** is small enough to keep each chunk topically focused (so a similarity match is meaningful and a snippet is readable), while being large enough to avoid slicing a sentence or idea into many disconnected fragments. It also keeps a handful of retrieved chunks comfortably inside a chat model's context window alongside the system prompt and question.
- **100-token overlap (20%)** prevents information that straddles a chunk boundary from being lost entirely from both neighboring chunks. Without overlap, a sentence like "...as described above, employees receive **20 paid leave days**" could be split so the fact lands only in a truncated, low-signal chunk. The overlap gives boundary-spanning context a fair chance of being retrieved intact from whichever chunk it primarily belongs to.
- Chunking is isolated in its own service (`chunking_service.py`) so the algorithm can be swapped (e.g., for semantic/sentence-aware chunking) without touching ingestion, embedding, or retrieval code.

## 7. Why SQLite

SQLite was chosen because this is a single-user, local-first application with no concurrent multi-writer requirement:

- Zero setup — no separate database server to install, configure, or run.
- The entire knowledge base is one file, trivial to inspect, back up, or delete.
- SQLAlchemy makes it a drop-in swap for PostgreSQL later (see "Production Improvements") without changing application code, only `DATABASE_URL` and the model layer's dialect-specific bits (there are none here).
- Sufficient performance for the expected scale (single user, hundreds to low thousands of chunks).

## 8. Known Limitations

- Retrieval is brute-force: every stored chunk's embedding is loaded and scored against the question on every query. Fine at small scale, not at large scale.
- No authentication — anyone with network access to the API can read/write all data.
- No de-duplication of ingested URLs or notes; re-ingesting the same content creates duplicate chunks.
- No background processing — URL fetching, chunking, and embedding all happen synchronously inside the `POST /ingest` request, so slow pages or slow embedding calls block the HTTP response.
- No retry/backoff around OpenAI calls; a single failure surfaces immediately as a 502.
- Webpage extraction is a heuristic (BeautifulSoup tag stripping) and won't handle JavaScript-rendered pages, paywalls, or heavily templated sites well.

## 9. What Would Break at Scale

- **SQLite supports limited concurrent writes.** Multiple simultaneous ingestions will serialize or contend on the single write lock; this does not scale to many concurrent users.
- **Loading all embeddings into memory becomes slow.** `retrieval_service` currently pulls every chunk row and its embedding on every query — fine for thousands of chunks, unworkable for millions.
- **Python cosine similarity does not scale to millions of chunks.** A pure-Python/NumPy linear scan is O(n) per query with no indexing; it needs an approximate nearest-neighbor index (HNSW, IVF, etc.) to stay fast as the corpus grows.
- **URL processing should move to background workers.** Synchronous fetch + parse + embed inside the request handler ties up a web worker for the duration of a slow page fetch or OpenAI call, and offers no retry on transient failure.
- **LLM and embedding requests require retries and rate limiting.** As request volume grows, transient OpenAI failures and rate limits will surface directly to users instead of being smoothed over.

## 10. Production Improvements

- PostgreSQL with the `pgvector` extension, or a managed vector database (Pinecone, Weaviate, Qdrant), for indexed similarity search at scale.
- Redis caching for repeated questions and hot item/chunk lookups.
- Background job processing (Celery, RQ, or a managed queue) for URL fetching, chunking, and embedding, decoupled from the HTTP request/response cycle.
- Authentication and per-user data isolation, so the knowledge base is scoped to the person who created it.
- Rate limiting on `/ingest` and `/query` to protect against abuse and control OpenAI spend.
- Monitoring and tracing (structured metrics, request tracing, OpenAI latency/error dashboards).
- Containerized deployment (Docker/Docker Compose) for reproducible environments.
- A fuller automated test suite, including integration tests against a real (test) OpenAI account or recorded fixtures.
- CI/CD pipelines running lint, type checks, and tests on every change.
- Proper secret management (a vault or cloud secrets manager) instead of a local `.env` file.
- Content safety checks on ingested text and generated answers.

## 11. Testing

```bash
cd backend
pytest
```

Tests cover: note ingestion, invalid ingestion input (empty note, bad URL scheme, unsupported source type), `GET /items` (including the empty state and newest-first ordering), empty questions, querying with no saved data, the chunking algorithm, and the cosine similarity calculation. Tests stub out the OpenAI embedding calls so the suite runs without a real API key or network access.

## 12. Project Structure

```
Turium Assessment/
  backend/
    app/
      main.py, database.py, models.py, schemas.py, config.py
      routers/ingestion.py, items.py, query.py
      services/chunking_service.py, embedding_service.py, retrieval_service.py, llm_service.py, url_service.py
      utils/logger.py
    tests/
    requirements.txt
    .env.example
    .gitignore
  frontend/
    src/
      services/api.js
      components/IngestForm.jsx, ItemsList.jsx, QuestionForm.jsx, AnswerCard.jsx, SourceCard.jsx
      App.jsx, App.css, main.jsx
    package.json
    vite.config.js
    index.html
    .env.example
    .gitignore
  README.md
```
