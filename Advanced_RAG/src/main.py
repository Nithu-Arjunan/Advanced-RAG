import logging
import os
import sys
import json
from pathlib import Path
import time
from typing import List, Literal, Optional
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .pipeline import run_pipeline 
from .pipeline import ingest_file as ingest_pipeline_file
from .ingestion import (
    extract_text,
    ALLOWED_EXTENSIONS,
    UPLOAD_DIR,
    add_uploaded_document,
    ensure_data_dirs,
    list_uploaded_documents as get_uploaded_documents,
)
from .generation import generate_answer
from .retrieval import search
from .reranking import rerank
from .base import Chunk
from .embedding import upsert_chunks, delete_all_vectors, delete_vectors_by_source
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from .config import (
    CACHE_ENABLED,
    EXACT_CACHE_TTL,
    SEMANTIC_CACHE_TTL,
    SEMANTIC_CACHE_THRESHOLD,
    RETRIEVAL_CACHE_TTL,
    RETRIEVAL_CACHE_THRESHOLD,
)

from .cache.redis_backend import RedisCacheBackend
from .cache.embedding_cache import embed_query, normalize_query, hash_query

logger = logging.getLogger(__name__)
_redis_cache_backend: RedisCacheBackend | None = None


def _get_cache_backend() -> RedisCacheBackend:
    """Redis-only cache backend for local testing."""
    global _redis_cache_backend
    if _redis_cache_backend is None:
        _redis_cache_backend = RedisCacheBackend()
    return _redis_cache_backend


def _namespace_for_stored_file(stored_file_name: str) -> Optional[str]:
    """Find namespace used when this stored file was ingested."""
    docs = get_uploaded_documents()
    matches = [d for d in docs if str(d.get("file_name", "")) == stored_file_name]
    if not matches:
        return None
    latest = max(matches, key=lambda d: str(d.get("uploaded_at", "")))
    namespace = str(latest.get("namespace", "")).strip()
    return namespace or None

# -------------------App lifespan and setup------------------- 

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup/shutdown events."""
    # Startup: initialize cache and clean expired entries
    if CACHE_ENABLED:
        cache = _get_cache_backend()
        removed = cache.cleanup_expired()
        if removed:
            logger.info(f"Cache startup cleanup: removed {removed} expired entries")
    yield
    

# -------------------App Initialization------------------- 
app = FastAPI(
    title="RAG Chatbot",
    description="RAG API using selectable chunking strategy",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIST_DIR = Path(__file__).resolve().parents[1] / "UI" / "dist"





# -------------------Request/Response Models------------------- 

class IngestRequest(BaseModel):
    file_path: str
    strategy: Literal["parent_child", "sentence_window"] = "parent_child"
    username: str

class IngestResponse(BaseModel):
    file: str
    strategy: Literal["parent_child", "sentence_window"] = "parent_child"
    chunks: int
    message: str

class ChatRequest(BaseModel):
    query: str
    file_path: str
    namespace: Optional[str] = None
    top_k: int = 10
    top_n: int = 5
    batch_size: int = 100
    use_reranker: bool = True
    chunking_strategy: Literal["parent_child", "sentence_window"] = "parent_child"
    debug: bool = False
    source: Optional[str] = None

class SourceChunk(BaseModel):
    id: str = ""
    source: str = ""
    chunk_text: str = ""
    page: str | int | None = ""
    score: float = 0.0
    method: str = ""
    parent_id: str = ""


class ChatResponse(BaseModel):
    answer: str
    strategy: str
    file_name: str
    file_path: str
    chunk_count: int
    contexts: List[SourceChunk]
    cache_hit: bool = False
    cache_tier: Optional[str] = None
    response_time_ms: Optional[float] = None

class GenerateRequest(BaseModel):
    question: str
    top_k: int = 10
    top_n: int = 5
    use_reranker: bool = True


class GenerateResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]
    pipeline: str


class UploadedDocument(BaseModel):
    file_name: str
    file_path: str
    uploaded_at: str


class DocumentsResponse(BaseModel):
    total_documents: int
    documents: List[UploadedDocument]

# ──------ Helper functions─────────────────────────────────────────────────────
def print_chunks(chunks: list[Chunk]) -> None:
    for c in chunks:
        print(f"  - [{c.metadata.get('source', 'unknown')} - page {c.metadata.get('page', 'N/A')}] {c.text[:100]}...")

async def _save_uploaded_file(file: UploadFile) -> Path:
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: {sorted(ALLOWED_EXTENSIONS)}",
        )

    ensure_data_dirs()
    target = UPLOAD_DIR / f"{uuid4().hex}_{original_name}"
    content = await file.read()
    target.write_bytes(content)
    return target


def _to_source(c, idx):
    """Convert a chunk dict to a SourceChunk model."""
    return SourceChunk(
        id=str(c.get("id", "")),
        source=str(c.get("source", "")),
        chunk_text=str(c.get("chunk_text", "")),
        page=c.get("page", ""),
        score=float(c.get("score", 0.0) or 0.0),
        method=str(c.get("method", "")),
        parent_id=str(c.get("parent_id", "")),
    )


def _sources_to_json(sources: List[SourceChunk]) -> str:
    """Serialize SourceChunk list to JSON for cache storage."""
    return json.dumps([s.model_dump() for s in sources])


def _json_to_sources(sources_json: str) -> List[SourceChunk]:
    """Deserialize JSON back to SourceChunk list."""
    return [SourceChunk(**s) for s in json.loads(sources_json)]

#-------------API Endpoints-------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}



@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    chunking_strategy: Literal["parent_child", "sentence_window"] = Form("parent_child"),
    username: str = Form(...),
):
    try:
        saved_file = await _save_uploaded_file(file)
        resolved_path = str(saved_file)
        add_uploaded_document(resolved_path)

        source_name = Path(file.filename or "").name
        chunk_count, newly_ingested = ingest_pipeline_file(
            file_path=resolved_path,
            chunking_strategy=chunking_strategy,
            namespace=username,
            source_name=source_name,
            batch_size=100,
        )

        if newly_ingested:
            message = "Ingestion successful"
        else:
            message = "File already ingested. No new chunks added.Please proceed to query the document."

        return IngestResponse(
            file=resolved_path,
            strategy=chunking_strategy,
            chunks=chunk_count,
            message=message,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.post("/chat", response_model=ChatResponse)

async def chat(req : ChatRequest):

    try:
        if req.top_k < 1 or req.top_n < 1 or req.batch_size < 1:
            raise HTTPException(status_code=400, detail="top_k, top_n, and batch_size must be >= 1")
        if not req.query.strip():
            raise HTTPException(status_code=400, detail="query cannot be empty")

        resolved_file = Path(req.file_path)
        if not resolved_file.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        resolved_namespace = (req.namespace or "").strip() or _namespace_for_stored_file(resolved_file.name)

        start_time = time.time()
        cache = _get_cache_backend() if CACHE_ENABLED else None
        source_filter = req.source or ""
        query_hash = None

        # Tier 1: Exact Match Cache
        if cache:
            normalized = normalize_query(req.query)
            if req.source:
                normalized = f"{normalized}|source={req.source}"
            query_hash = hash_query(normalized)
            exact_hit = cache.get_exact(query_hash)

            if exact_hit:
                logger.info(f"Cache HIT (exact): {req.query[:50]}...")
                return ChatResponse(
                    answer=exact_hit["answer"],
                    strategy=req.chunking_strategy,
                    file_name=resolved_file.name,
                    file_path=str(resolved_file),
                    chunk_count=0,
                    contexts=_json_to_sources(exact_hit["sources_json"]),
                    cache_hit=True,
                    cache_tier="exact",
                    response_time_ms=round((time.time() - start_time) * 1000, 2),
                )

        # Tier 2: Semantic Match Cache
        embedding = None
        if cache:
            embedding = embed_query(req.query)
            semantic_hit = cache.get_semantic(embedding, SEMANTIC_CACHE_THRESHOLD, source_filter)

            if semantic_hit:
                logger.info(
                    f"Cache HIT (semantic, sim={semantic_hit['similarity']:.3f}): "
                    f"{req.query[:50]}..."
                )
                return ChatResponse(
                    answer=semantic_hit["answer"],
                    strategy=req.chunking_strategy,
                    file_name=resolved_file.name,
                    file_path=str(resolved_file),
                    chunk_count=0,
                    contexts=_json_to_sources(semantic_hit["sources_json"]),
                    cache_hit=True,
                    cache_tier="semantic",
                    response_time_ms=round((time.time() - start_time) * 1000, 2),
                )

        # Tier 3: Retrieval Cache
        if cache and embedding:
            retrieval_hit = cache.get_retrieval(embedding, RETRIEVAL_CACHE_THRESHOLD, source_filter)

            if retrieval_hit:
                logger.info(
                    f"Cache HIT (retrieval, sim={retrieval_hit['similarity']:.3f}): "
                    f"{req.query[:50]}..."
                )
                cached_chunks = json.loads(retrieval_hit["chunks_json"])
                answer = generate_answer(req.query, cached_chunks)
                sources = [_to_source(c, i) for i, c in enumerate(cached_chunks, 1)]

                # Promote to Tier 1 + 2 (we now have a full answer)
                doc_version = cache.get_doc_version()
                sources_json = _sources_to_json(sources)
                if query_hash:
                    cache.set_exact(query_hash, req.query, answer, sources_json, doc_version, EXACT_CACHE_TTL)
                cache.set_semantic(req.query, embedding, answer, sources_json, doc_version, SEMANTIC_CACHE_TTL, source_filter)

                return ChatResponse(
                    answer=answer,
                    strategy=req.chunking_strategy,
                    file_name=resolved_file.name,
                    file_path=str(resolved_file),
                    chunk_count=len(sources),
                    contexts=sources,
                    cache_hit=True,
                    cache_tier="retrieval",
                    response_time_ms=round((time.time() - start_time) * 1000, 2),
                )

        # Full RAG pipeline (all cache miss)
        logger.info(f"Cache MISS: {req.query[:50]}...")
        logging.info(f"Passing namespace to pipeline: {resolved_namespace}")
        chunks, answer, chunk_count = run_pipeline(
            query=req.query,
            file_path=str(resolved_file),
            chunking_strategy=req.chunking_strategy,
            top_k=req.top_k,
            top_n=req.top_n,
            batch_size=req.batch_size,
            namespace=resolved_namespace,
        )
        
        if not chunks:
            return ChatResponse(
                answer="I could not find any relevant information in the documents",
                strategy=req.chunking_strategy,
                file_name=resolved_file.name,
                file_path=str(resolved_file),
                chunk_count=0,
                contexts=[],
                response_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        sources = [_to_source(c, i) for i, c in enumerate(chunks, 1)]

        # Store in all 3 cache tiers
        if cache:
            doc_version = cache.get_doc_version()
            sources_json = _sources_to_json(sources)
            if embedding is None:
                embedding = embed_query(req.query)
            normalized = normalize_query(req.query)
            if req.source:
                normalized = f"{normalized}|source={req.source}"
            query_hash = hash_query(normalized)

            cache.set_exact(query_hash, req.query, answer, sources_json, doc_version, EXACT_CACHE_TTL)
            cache.set_semantic(req.query, embedding, answer, sources_json, doc_version, SEMANTIC_CACHE_TTL, source_filter)
            cache.set_retrieval(req.query, embedding, json.dumps(chunks), doc_version, RETRIEVAL_CACHE_TTL, source_filter)

        return ChatResponse(
            answer=answer,
            strategy=req.chunking_strategy,
            file_name=resolved_file.name,
            file_path=str(resolved_file),
            chunk_count=chunk_count,
            contexts=sources,
            #retrieved=None,
            #reranked=None,
            cache_hit=False,
            cache_tier='pipeline',
            response_time_ms=round((time.time() - start_time) * 1000, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=DocumentsResponse)
def list_uploaded_documents():
    docs = get_uploaded_documents()
    documents = [UploadedDocument.model_validate(d) for d in docs]
    return DocumentsResponse(total_documents=len(documents), documents=set(documents))



@app.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete a single document: file + Pinecone vectors + document hash."""
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # 1. Delete vectors from Pinecone
        vectors_deleted = delete_vectors_by_source(filename)
        logger.info(f"Deleted {vectors_deleted} vectors for {filename}")

        # 2. Remove document hash
        hash_removed = False
        if CACHE_ENABLED:
            cache = _get_cache_backend()
            hash_removed = cache.remove_document_hash_by_name(filename)
            cache.bump_doc_version()
            logger.info(f"Doc version bumped after deleting: {filename}")

        # 3. Delete file from disk
        os.remove(path)

        return {
            "message": f"Document '{filename}' deleted successfully",
            "vectors_deleted": vectors_deleted,
            "hash_removed": hash_removed,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cache Management Endpoints ─────────────────────────────────

@app.post("/cache/clear")
def cache_clear():
    """Clear all 3 cache tiers. Returns count of entries removed per tier."""
    if not CACHE_ENABLED:
        return {"message": "Cache is disabled", "cleared": {}}

    cache = _get_cache_backend()
    cleared = cache.clear_all()
    logger.info(f"Cache cleared: {cleared}")
    return {
        "message": "Cache cleared successfully",
        "cleared": cleared,
    }


@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics — per-tier entry counts, hit counts, backend info."""
    if not CACHE_ENABLED:
        return {"message": "Cache is disabled", "stats": {}}

    cache = _get_cache_backend()
    return cache.get_stats()


# ── Vector Store Management ───────────────────────────────────

@app.delete("/vectors")
def reset_vectors():
    """Delete all vectors from Pinecone namespace, clear cache, and remove uploaded files."""
    try:
        # 1. Delete all vectors from Pinecone
        delete_all_vectors()
        logger.info("All vectors deleted from Pinecone namespace")

        # 2. Clear all cache tiers
        cache_cleared = {}
        doc_hashes_cleared = 0
        if CACHE_ENABLED:
            cache = _get_cache_backend()
            cache_cleared = cache.clear_all()
            doc_hashes_cleared = cache.clear_document_hashes()
            logger.info(f"Cache cleared: {cache_cleared}, doc hashes: {doc_hashes_cleared}")

        # 3. Remove uploaded files
        files_removed = 0
        for f in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(path):
                os.remove(path)
                files_removed += 1

        return {
            "message": "Vector store reset successfully",
            "vectors_deleted": True,
            "cache_cleared": cache_cleared,
            "doc_hashes_cleared": doc_hashes_cleared,
            "files_removed": files_removed,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    






