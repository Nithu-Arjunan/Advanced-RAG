import os
import sys
import time
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pinecone import Pinecone


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from src.config import (
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_EMBED_MODEL,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    PINECONE_REGION,
    PINECONE_RERANK_MODEL,
)
logging.basicConfig(level=logging.INFO)

load_dotenv()


_pc = Pinecone(api_key=PINECONE_API_KEY)
#PINECONE_INDEX_NAME="advancedragindex"


def _resolve_namespace(namespace: Optional[str] = None) -> str:
    if namespace is None:
        return PINECONE_NAMESPACE
    cleaned = namespace.strip()
    if not cleaned:
        raise ValueError("username cannot be empty")
    return cleaned


def _get_or_create_index():

    if not _pc.has_index(PINECONE_INDEX_NAME):
        print(f"Creating pinecone index {PINECONE_INDEX_NAME} with integrated embedding")
        
        _pc.create_index_for_model(
            name=PINECONE_INDEX_NAME,
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION,
            embed={
                "model": PINECONE_EMBED_MODEL,
                "field_map": {"text": "chunk_text"},
            },
        )
        print("Index created")

        while not _pc.describe_index(PINECONE_INDEX_NAME).status.get("ready",False):
            time.sleep(1)

        print("Index created and ready")

    return _pc.Index(PINECONE_INDEX_NAME)


def is_file_ingested(
    source: str,
    method: Optional[str] = None,
    namespace: Optional[str] = None,
) -> bool:
    index = _get_or_create_index()
    namespace_value = _resolve_namespace(namespace)
    try:
        # Deterministic duplicate check by ID prefix inside the target namespace.
        if method in ("parent_child", "sentence_window"):
            prefix = f"{source} :: {method} ::"
        else:
            prefix = f"{source} ::"

        for id_batch in index.list(prefix=prefix, namespace=namespace_value):
            if id_batch:
                return True

        # Backward compatibility for older ID formats.
        probe_ids = [f"{source} :: chunk-1"]
        if method in ("parent_child", "sentence_window"):
            probe_ids.append(f"{source} :: {method} :: chunk-1")
        results = index.fetch(ids=probe_ids, namespace=namespace_value)

        payload: Dict[str, Any]
        if isinstance(results, dict):
            payload = results
        elif hasattr(results, "to_dict"):
            payload = results.to_dict()
        elif hasattr(results, "model_dump"):
            payload = results.model_dump()
        else:
            payload = {}

        # vectors = payload.get("vectors", {})
        # if isinstance(vectors, dict) and probe_id in vectors:
        #     return True

        # Fallback for data previously inserted without stable IDs:
        # some SDK versions support filters only inside the query object.
        search_results = index.search(
            namespace=PINECONE_NAMESPACE,
            query={
                "top_k": 1,
                "inputs": {"text": source},
                "filter": {"source": source},
            },
            fields=["source"],
        )

        if isinstance(search_results, dict):
            search_payload = search_results
        elif hasattr(search_results, "to_dict"):
            search_payload = search_results.to_dict()
        elif hasattr(search_results, "model_dump"):
            search_payload = search_results.model_dump()
        else:
            search_payload = {}

        hits = search_payload.get("result", {}).get("hits", [])
        if hits:
            return True
    except Exception as exc:
        print(f"Duplicate-check failed for source '{source}': {exc}")
    return False

# Upserting records to Pinecone

def upsert_chunks(records: List[Dict], batch_size: int, namespace: Optional[str] = None) -> int:
    if not records:
        return 0

    namespace_value = _resolve_namespace(namespace)
    source = records[0].get("source", "")
    method = records[0].get("method", "")

    if source and is_file_ingested(source, namespace=namespace_value):
        print(f"{source} already exists in the Index. Skip Ingestion")
        return 0

    index=_get_or_create_index()

    total=0

    for i in range(0,len(records),batch_size):
        batch=records[i:i+batch_size]

        pinecone_records=[]

        for rec in batch:
            pinecone_records.append({
                "_id": rec["id"],
                "chunk_text": rec["chunk_text"],
                "index": rec["index"],
                "method": rec.get("method", "parent_child"),
                "level": rec.get("level", "child"),
                "parent_id": rec.get("parent_id", ""),
                "source": rec['source'],
                "page": rec.get('page', "")
            })

        index.upsert_records(namespace_value, pinecone_records)
        total += len(pinecone_records)

    print(f"Upserted {total} records into {PINECONE_NAMESPACE}")

    return total


def delete_all_vectors(namespace: Optional[str] = None):
    """Delete all vectors from the configured Pinecone namespace."""
    index = _get_or_create_index()
    namespace_value = _resolve_namespace(namespace)
    index.delete(delete_all=True, namespace=namespace_value)


def delete_vectors_by_source(source: str, namespace: Optional[str] = None) -> int:
    """Delete all vectors for a specific source document.

    IDs may vary by strategy (e.g., '{filename} :: parent_child :: chunk-{N}').
    Uses index.list(prefix=...) to find them, then batch deletes.
    """
    index = _get_or_create_index()
    namespace_value = _resolve_namespace(namespace)
    all_ids = []
    for id_batch in index.list(prefix=f"{source} ::", namespace=namespace_value):
        all_ids.extend(id_batch)
    if not all_ids:
        return 0
    for i in range(0, len(all_ids), 1000):
        index.delete(ids=all_ids[i:i + 1000], namespace=namespace_value)
    return len(all_ids)



#===============================Demo =====================================
# if __name__ == "__main__":
#     from src.ingestion import extract_text
#     from src.chunking.parent_child import parent_child_chunking

#     sample_path = os.path.join(ROOT_DIR, "data", "technical_article.txt")
#     pages = extract_text(sample_path)
#     source_name = os.path.basename(sample_path)
#     _, child_chunks = parent_child_chunking(
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




    
   





