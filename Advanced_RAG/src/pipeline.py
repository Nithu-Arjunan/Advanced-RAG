import argparse
import os
from typing import Any, Dict, List, Literal, Optional, Tuple
import logging
from .config import TOP_K, RERANK_TOP_N,PINECONE_NAMESPACE
from .ingestion import extract_text
from .base import Chunk
from .chunking.parent_child import parent_child_chunking, retrieve_with_parent_context
from .chunking.sentence_window import sentence_window_chunking, build_sentence_window_records
from .embedding import _get_or_create_index, is_file_ingested, upsert_chunks
from .ingestion import mark_document_ingested
from .reranking import rerank
from .generation import generate_answer

logging.basicConfig(level=logging.INFO)


"""End-to-end pipeline with selectable chunking strategy."""

def _logical_source_name(source: str) -> str:
    """Normalize '<uuid>_<filename>' to '<filename>' for safe comparisons."""
    value = (source or "").strip()
    parts = value.split("_", 1)
    if len(parts) == 2 and len(parts[0]) == 32:
        try:
            int(parts[0], 16)
            return parts[1]
        except ValueError:
            return value
    return value


def _source_matches(hit_source: str, expected_source: str) -> bool:
    if not hit_source or not expected_source:
        return False
    if hit_source == expected_source:
        return True
    return _logical_source_name(hit_source) == _logical_source_name(expected_source)


def _build_parent_child_records(child_chunks: List[Chunk], source_name: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for child in child_chunks:
        records.append(
            {
                "id": f"{source_name} :: parent_child :: chunk-{child.index + 1}",
                "chunk_text": child.text,
                "index": child.index,
                "method": "parent_child",
                "level": "child",
                "parent_id": child.metadata.get("parent_id", ""),
                "source": child.metadata.get("source", source_name),
                "page": child.metadata.get("page", ""),
            }
        )
    return records


def _resolve_unique_parent_chunks(
    reranked_child_hits: List[Dict[str, Any]],
    child_chunks: List[Chunk],
    parent_chunks: List[Chunk],
    source_name: str,
) -> List[Dict[str, Any]]:
    unique_parent_chunks: List[Dict[str, Any]] = []
    seen_parent_ids = set()

    for hit in reranked_child_hits:
        if not _source_matches(hit.get("source", ""), source_name):
            continue
        if hit.get("method", "") != "parent_child":
            continue

        idx_val = hit.get("index", None)
        try:
            child_index = int(idx_val)
        except (TypeError, ValueError):
            continue

        try:
            _, parent = retrieve_with_parent_context(
                query_chunk_index=child_index,
                child_chunks=child_chunks,
                parent_chunks=parent_chunks,
            )
        except Exception:
            continue

        parent_id = parent.metadata.get("parent_id", "")
        if not parent_id or parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        unique_parent_chunks.append(
            {
                "id": f"{source_name} :: {parent_id}",
                "score": hit.get("score", 0),
                "chunk_text": parent.text,
                "index": parent.index,
                "level": "parent",
                "method": "parent_child",
                "parent_id": parent_id,
                "source": parent.metadata.get("source", source_name),
                "page": parent.metadata.get("page", ""),
            }
        )
    return unique_parent_chunks


def _resolve_sentence_window_chunks(
    reranked_hits: List[Dict[str, Any]],
    source_name: str,
) -> List[Dict[str, Any]]:
    sentence_chunks: List[Dict[str, Any]] = []
    seen_ids = set()

    for hit in reranked_hits:
        if not _source_matches(hit.get("source", ""), source_name):
            continue
        if hit.get("method", "") != "sentence_window":
            continue

        hit_id = hit.get("id", "")
        if hit_id and hit_id in seen_ids:
            continue
        if hit_id:
            seen_ids.add(hit_id)

        sentence_chunks.append(
            {
                "id": hit_id,
                "score": hit.get("score", 0),
                "chunk_text": hit.get("chunk_text", ""),
                "index": hit.get("index", ""),
                "level": hit.get("level", "child"),
                "method": "sentence_window",
                "parent_id": "",
                "source": hit.get("source", source_name),
                "page": hit.get("page", ""),
            }
        )
    return sentence_chunks


def run_pipeline(
    query: str,
    file_path: str,
    chunking_strategy: Literal["parent_child", "sentence_window"] = "parent_child",
    top_k: int = TOP_K,
    top_n: int = RERANK_TOP_N,
    batch_size: int = 100,
    namespace: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, int]:
    source_name = os.path.basename(file_path)
    parts = source_name.split("_", 1)
    if len(parts) == 2 and len(parts[0]) == 32:
        try:
            int(parts[0], 16)
            source_name = parts[1]
        except ValueError:
            pass
    namespace = PINECONE_NAMESPACE
    if chunking_strategy not in ("parent_child", "sentence_window"):
        raise ValueError("chunking_strategy must be either 'parent_child' or 'sentence_window'.")

    # Ingestion/chunking/upsert happens in the ingest endpoint.
    # Chat pipeline starts from retrieval + generation.
    _get_or_create_index()
    logging.info(f"Starting pipeline for query '{query}' on file '{file_path}' with strategy '{chunking_strategy}'.")
   
    if not is_file_ingested(source_name, namespace=namespace):
        raise ValueError(f"File '{source_name}' is not ingested. Please ingest it first.")

    # Step 4: Retrieve relevant chunks from Pinecone via reranking.
    reranked_hits = rerank(
        query=query,
        top_k=top_k,
        top_n=top_n,
        source=source_name,
        method=chunking_strategy,
        namespace=namespace,
    )
    logging.info(f"Reranking returned {len(reranked_hits)} hits for query '{query}' with strategy '{chunking_strategy}'.")
    # Step 5: Strategy-specific context resolution from reranked hits.
    if chunking_strategy == "parent_child":
        context_chunks: List[Dict[str, Any]] = []
        seen_ids = set()
        logging.info(f"Source: {source_name}")
        for hit in reranked_hits:
            if not _source_matches(hit.get("source", ""), source_name):
                continue
            if hit.get("method", "") != "parent_child":
                continue
            hit_id = hit.get("id", "")
            if hit_id and hit_id in seen_ids:
                continue
            if hit_id:
                seen_ids.add(hit_id)
            context_chunks.append(
                {
                    "id": hit_id,
                    "score": hit.get("score", 0),
                    "chunk_text": hit.get("chunk_text", ""),
                    "index": hit.get("index", ""),
                    "level": hit.get("level", "child"),
                    "method": "parent_child",
                    "parent_id": hit.get("parent_id", ""),
                    "source": hit.get("source", source_name),
                    "page": hit.get("page", ""),
                }
            )
    else:
        context_chunks = _resolve_sentence_window_chunks(
            reranked_hits=reranked_hits,
            source_name=source_name,
        )

    # Step 6: Generation
    logging.info(f"Generating answer for query '{query}' using {len(context_chunks)} context chunks with strategy '{chunking_strategy}'.")
    answer = generate_answer(query, context_chunks)
    logging.info(f"Generated answer for query '{answer}' with strategy '{chunking_strategy}'.")
    return context_chunks, answer, len(context_chunks)


def ingest_file(
    file_path: str,
    chunking_strategy: Literal["parent_child", "sentence_window"] = "parent_child",
    batch_size: int = 100,
    namespace: Optional[str] = None,
    source_name: Optional[str] = None,
) -> Tuple[int, bool]:
    pages = extract_text(file_path)
    effective_source = source_name or os.path.basename(file_path)

    if chunking_strategy not in ("parent_child", "sentence_window"):
        raise ValueError("chunking_strategy must be either 'parent_child' or 'sentence_window'.")

    _get_or_create_index()

    if chunking_strategy == "parent_child":
        _, child_chunks = parent_child_chunking(pages=pages)
        chunk_count = len(child_chunks)
        if is_file_ingested(effective_source, namespace=namespace):
            return chunk_count, False
        records = _build_parent_child_records(child_chunks=child_chunks, source_name=effective_source)
        upsert_chunks(records=records, batch_size=batch_size, namespace=namespace)
        mark_document_ingested(effective_source, "parent_child")
        return chunk_count, True

    sentence_chunks = sentence_window_chunking(pages_or_documents=pages)
    chunk_count = len(sentence_chunks)
    if is_file_ingested(effective_source, namespace=namespace):
        return chunk_count, False
    records = build_sentence_window_records(chunks=sentence_chunks, source_name=effective_source)
    upsert_chunks(records=records, batch_size=batch_size, namespace=namespace)
    mark_document_ingested(effective_source, "sentence_window")
    return chunk_count, True



# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="RAG pipeline with chunking-strategy switch")
#     parser.add_argument("--query", type=str, required=False, default="How are employees bound?")
#     parser.add_argument(
#         "--file",
#         type=str,
#         required=False,
#         default=os.path.join(os.path.dirname(__file__), "..", "data", "HR_Handbook.pdf"),
#     )
#     parser.add_argument(
#         "--chunking_strategy",
#         type=str,
#         choices=["parent_child", "sentence_window"],
#         default=None,
#     )
#     parser.add_argument("--top_k", type=int, required=False, default=TOP_K)
#     parser.add_argument("--top_n", type=int, required=False, default=RERANK_TOP_N)
#     parser.add_argument("--batch_size", type=int, required=False, default=100)
#     args = parser.parse_args()

#     strategy = args.chunking_strategy
#     if strategy is None:
#         print("Choose chunking strategy:")
#         print("1. parent_child")
#         print("2. sentence_window")
#         user_choice = input("Enter 1 or 2: ").strip()
#         strategy = "sentence_window" if user_choice == "2" else "parent_child"

#     contexts, answer, created_chunk_count = run_pipeline(
#         query=args.query,
#         file_path=args.file,
#         chunking_strategy=strategy,
#         top_k=args.top_k,
#         top_n=args.top_n,
#         batch_size=args.batch_size,
#     )

#     print(f"Contexts passed to generation ({strategy}): {len(contexts)}")
#     print(f"Chunks created ({strategy}): {created_chunk_count}")
#     for i, c in enumerate(contexts, start=1):
#         print(
#             f"\n[{i}] method={c.get('method')} parent_id={c.get('parent_id')} "
#             f"source={c.get('source')} page={c.get('page')}"
#         )
#         print(f"text={c.get('chunk_text', '')[:220]}...")

#     print("\nFinal response:")
#     print(answer)










