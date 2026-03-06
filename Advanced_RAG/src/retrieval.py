import os,sys
from typing import Any, Dict, List
import logging
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
    TOP_K
)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(level=logging.INFO)
_pc=Pinecone(api_key=PINECONE_API_KEY)

def search(query: str, top_k: int = TOP_K) -> List[Dict]:
    index=_pc.Index(PINECONE_INDEX_NAME)

    results=index.search(
        namespace=PINECONE_NAMESPACE,
        query={"top_k":top_k,"inputs":{"text":query}},
        fields=["chunk_text","index","level","method","page","parent_id","source"]
    )

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

    hits=[]

    for item in payload.get("result",{}).get("hits",[]):
        fields=item.get("fields",{})
        hits.append(
            {
                # In search hits, id/score are top-level keys on each hit.
                "id": item.get("_id", item.get("id", "")),
                "score": item.get("_score", item.get("score", 0)),
                "chunk_text":fields.get("chunk_text",""),
                "index":fields.get("index",""),
                "level":fields.get("level",""),
                "method":fields.get("method",""),
                "parent_id":fields.get("parent_id",""),
                "source":fields.get("source",""),
                "page":fields.get("page","")
            }
        )
    logging.info(f"Search query: '{query}' returned {len(hits)} hits.")
    return hits


def retrieve_with_parent_context(
    child_chunk_index: int,
    child_chunks: list[Chunk],
    parent_chunks: list[Chunk],
) -> tuple[Chunk, Chunk]:
    """
    Simulate retrieval: given a matched child chunk, return it along with its parent.

    Args:
        query_chunk_index: Index of the matched child chunk.
        child_chunks: All child chunks.
        parent_chunks: All parent chunks.

    Returns:
        Tuple of (matched_child, parent_context).
    """
    if not child_chunks:
        raise ValueError("child_chunks is empty.")
    if child_chunk_index < 0 or child_chunk_index >= len(child_chunks):
        raise IndexError(f"query_chunk_index {child_chunk_index} is out of range (0 to {len(child_chunks) - 1}).")

    child = child_chunks[child_chunk_index]
    parent_id = child.metadata["parent_id"]
    parent = next((p for p in parent_chunks if p.metadata["parent_id"] == parent_id), None)
    if parent is None:
        raise ValueError(f"No parent chunk found for parent_id '{parent_id}'.")
    return child, parent



#============================ Demo================================
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
#     hits = search(query=query, top_k=TOP_K)
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