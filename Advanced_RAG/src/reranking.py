import logging
import os,sys
from typing import Any, Dict, List, Optional
from pinecone import Pinecone
from .base import Chunk
from .chunking.parent_child import retrieve_with_parent_context
from .config import(
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_EMBED_MODEL,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    PINECONE_REGION,
    PINECONE_RERANK_MODEL,
    TOP_K,
    RERANK_TOP_N
)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(level=logging.INFO)

_pc=Pinecone(api_key=PINECONE_API_KEY)


def _resolve_namespace(namespace: Optional[str] = None) -> str:
    if namespace is None:
        return PINECONE_NAMESPACE
    cleaned = namespace.strip()
    if not cleaned:
        raise ValueError("namespace cannot be empty")
    return cleaned

def rerank(
    query: str,
    top_k: int = TOP_K,
    top_n: int = RERANK_TOP_N,
    source: str | None = None,
    method: str | None = None,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
    logging.info(f"Starting reranking for query: '{query}' with top_k={top_k} and top_n={top_n}")
    index = _pc.Index(PINECONE_INDEX_NAME)
    namespace_value = _resolve_namespace(namespace)

    query = query.strip()
    if not query:
        return []
    if top_k <= 0:
        return []
    if top_n <= 0:
        return []

    top_n = min(top_n, top_k)

    if not _pc.has_index(PINECONE_INDEX_NAME):
        raise ValueError(f"Pinecone index '{PINECONE_INDEX_NAME}' does not exist.")

    index = _pc.Index(PINECONE_INDEX_NAME)

    query_params = {
        "top_k": top_k,
        "inputs": {"text": query},
    }
    # if source_filter:
    #     query_params["filter"] = {"source": {"$eq": source_filter}}
    logging.info(f"Executing search with query parameters: {query_params} in namespace: '{namespace_value}'")
    
    results = index.search(
        namespace=namespace_value,
        query=query_params,
        rerank={"model": PINECONE_RERANK_MODEL, "top_n": top_n, "rank_fields": ["chunk_text"]},
        fields=["chunk_text", "index", "level", "method", "page", "parent_id", "source"],
    )
    logging.info(f"Search completed. Total hits returned from reranking: {len(results.get('result', {}).get('hits', []))}")
    # Pinecone SDK may return dict or model object depending on version.
    payload: Dict[str, Any]
    if isinstance(results, dict):
        payload = results
    elif hasattr(results, "to_dict"):
        payload = results.to_dict()
    elif hasattr(results, "model_dump"):
        payload = results.model_dump()
    else:
        payload = {}

    hits = []

    for item in payload.get("result", {}).get("hits", []):
        fields = item.get("fields", {})
        hits.append(
            {
                "id": item.get("_id", item.get("id", "")),
                "score": item.get("_score", item.get("score", 0)),
                "chunk_text": fields.get("chunk_text", ""),
                "index": fields.get("index", ""),
                "level": fields.get("level", ""),
                "method": fields.get("method", ""),
                "parent_id": fields.get("parent_id", ""),
                "source": fields.get("source", ""),
                "page": fields.get("page", ""),
            }
        )

    return hits



#=========================== Demo ====================================
# if __name__=="__main__":
#     from src.ingestion import extract_text
#     from src.chunking.parent_child import parent_child_chunking
#     from src.embedding import upsert_chunks
#     import os

#     sample_path = os.path.join(ROOT_DIR, "data", "technical_article.txt")
#     pages = extract_text(sample_path)
#     source_name = os.path.basename(sample_path)
#     parent_chunks, child_chunks = parent_child_chunking(
#         pages=pages,
#     )

#     records: List[Dict] = []
#     for child in child_chunks:
#         records.append(
#             {
#                 "id": f"{source_name} :: chunk-{child.index + 1}",
#                 "chunk_text": child.text,
#                 "index": child.index,
#                 "method": "parent_child",
#                 "level": "child",
#                 "parent_id": child.metadata.get("parent_id", ""),
#                 "source": child.metadata.get("source", source_name),
#                 "page": child.metadata.get("page", ""),
#             }
#         )

#     upserted = upsert_chunks(records, batch_size=100)
#     print(f"Child chunks prepared: {len(child_chunks)}")
#     print(f"Records upserted: {upserted}")
    
#     # Seraching the pinecone database for a query and retrieving child-parent pairs.
#     query = "What are AI applications in mental health?"
#     hits = rerank(query=query, top_k=TOP_K, top_n=RERANK_TOP_N)
#     print(f"Search hits for query '{query}': {len(hits)}")

#     retrieved_parent_text=[]

#     for hit in hits:
#         idx_val = hit.get("index", None)
#         try:
#             child_index = int(idx_val)
#         except (TypeError, ValueError):
#             continue

#         try:
#             matched_child, parent = retrieve_with_parent_context(
#                 child_chunk_index=child_index,
#                 child_chunks=child_chunks,
#                 parent_chunks=parent_chunks,
#             )
#             retrieved_parent_text.append(parent.text)
#         except Exception:
#             continue

#     #print(f"Retrieved {len(set(retrieved_parent_text))} parent contexts for query: '{query}'")
#     print(f"Retrieved {len(retrieved_parent_text)} total parent context entries for query: '{query}'")

#     print(f"Parent chunks retrieved: {retrieved_parent_text}")


