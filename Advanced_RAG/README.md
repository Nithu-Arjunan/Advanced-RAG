# Advanced RAG

Retrieval-Augmented Generation (RAG) project with:
- FastAPI backend (`src/main.py`)
- React + Vite frontend (`UI/`)
- Pinecone for vector search/reranking
- Redis for multi-tier caching
- Gemini (Vertex AI) for answer generation

## Project Structure

```text
Advanced_RAG/
  src/
    main.py                # FastAPI app and endpoints
    pipeline.py            # Ingest + query pipeline
    ingestion.py           # File extraction and upload tracking
    embedding.py           # Pinecone index/upsert/delete
    retrieval.py           # Vector retrieval
    reranking.py           # Retrieval rerank
    generation.py          # LLM answer generation
    chunking/              # parent_child and sentence_window strategies
    cache/                 # Redis cache backend
  UI/                      # React dashboard
  data/                    # uploaded docs metadata and runtime data
  main.py                  # ASGI loader for src/main.py
```

## Prerequisites

- Python 3.13+
- Node.js 18+ and npm
- Docker (for Redis via compose)
- Pinecone API key
- Vertex AI / Google project access for Gemini

## Environment Variables

Create `.env` in repo root:

```env
PINECONE_API_KEY=your_pinecone_api_key
PROJECT_ID=your_gcp_project_id
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

Optional values are loaded from `src/config.py`.

## Run Locally

### 1. Start Redis

```bash
docker compose up -d redis
```

### 2. Start Backend

Using `uv`:

```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Or with Python directly:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Swagger docs:
- http://127.0.0.1:8000/docs

### 3. Start Frontend

```bash
cd UI
npm install
npm run dev
```

UI:
- http://localhost:5173

## Main API Endpoints

- `POST /ingest`  
  Upload file, chunk with selected strategy, and upsert vectors.

- `POST /chat`  
  Query document with cache-aware RAG pipeline.

- `GET /documents`  
  List uploaded documents.

- `DELETE /documents/{filename}`  
  Delete one document and its vectors.

- `POST /cache/clear`  
  Clear all cache tiers.

- `GET /cache/stats`  
  Cache stats.

- `DELETE /vectors`  
  Reset vector namespace and cleanup files/cache.

## Notes

- Chunking strategies:
  - `parent_child`
  - `sentence_window`
- Namespace support is used for ingestion/chat isolation.
- Frontend deduplicates displayed document names by logical filename.
