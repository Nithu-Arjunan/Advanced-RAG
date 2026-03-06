import os
import sys
from typing import Any
try:
    import nltk
except ImportError:  # pragma: no cover - depends on environment
    nltk = None

# Ensure project root is importable when running this file directly.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.base import Chunk


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using NLTK when available, otherwise fallback."""
    try:
        if nltk is not None:
            return nltk.sent_tokenize(text)
        raise LookupError
    except LookupError:
        # Fallback when NLTK or punkt model is unavailable.
        return [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]


def sentence_window_chunking(
    pages_or_documents: list[Any],
    sentences_per_chunk: int = 3,
    window_size: int = 2,
) -> list[Chunk]:
    """
    Sentence-window chunking from page dicts or Document-like objects.

    Supported items:
    - dict: {"text": "...", "page": 1, "source": "..."}
    - Document-like: object with .page_content and .metadata
    """
    if not isinstance(pages_or_documents, list):
        raise TypeError("pages_or_documents must be a list of dicts or Document-like objects.")

    sentences: list[str] = []
    sentence_pages: list[int | None] = []
    sentence_sources: list[str] = []

    for i, item in enumerate(pages_or_documents):
        page_text = ""
        page_no: int | None = None
        source = "unknown"

        if isinstance(item, dict):
            page_text = item.get("text", "")
            page_no = item.get("page", i + 1)
            source = item.get("source", "unknown")
        elif hasattr(item, "page_content"):
            page_text = getattr(item, "page_content", "") or ""
            metadata = getattr(item, "metadata", {}) or {}
            page_no = metadata.get("page", i + 1)
            source = metadata.get("source", "unknown")
        else:
            raise TypeError(
                "Each item must be either a dict with 'text' or a Document-like object "
                "with 'page_content'."
            )

        page_sentences = split_into_sentences(page_text)
        sentences.extend(page_sentences)
        sentence_pages.extend([page_no] * len(page_sentences))
        sentence_sources.extend([source] * len(page_sentences))

    chunks: list[Chunk] = []
    chunk_index = 0
    for i in range(0, len(sentences), sentences_per_chunk):
        core = sentences[i : i + sentences_per_chunk]
        before = sentences[max(0, i - window_size) : i]
        after_start = i + sentences_per_chunk
        after = sentences[after_start : after_start + window_size]

        core_pages = [p for p in sentence_pages[i : i + sentences_per_chunk] if p is not None]
        unique_pages = sorted(set(core_pages))
        unique_sources = sorted(set(sentence_sources[i : i + sentences_per_chunk]))
        primary_page = unique_pages[0] if unique_pages else None
        primary_source = unique_sources[0] if unique_sources else "unknown"

        chunk_text = " ".join(core)
        window_before_text = " ".join(before) if before else ""
        window_after_text = " ".join(after) if after else ""
        combined_window_text = " ".join(
            part for part in [window_before_text, chunk_text, window_after_text] if part
        ).strip()

        chunks.append(
            Chunk(
                text=chunk_text,
                index=chunk_index,
                metadata={
                    "method": "sentence_window",
                    "level": "child",
                    "chunk_text": chunk_text,
                    "window_before": window_before_text,
                    "window_after": window_after_text,
                    "combined_window_text": combined_window_text,
                    "source": primary_source,
                    "page": primary_page,
                    "pages": unique_pages,
                    "page_start": unique_pages[0] if unique_pages else None,
                    "page_end": unique_pages[-1] if unique_pages else None,
                    "sources": unique_sources,
                },
            )
        )
        chunk_index += 1

    return chunks


def build_sentence_window_records(chunks: list[Chunk], source_name: str) -> list[dict[str, Any]]:
    """
    Convert sentence-window chunks to upsert-ready records compatible with upsert_chunks.
    """
    records: list[dict[str, Any]] = []
    for chunk in chunks:
        records.append(
            {
                "id": f"{source_name} :: sentence_window :: chunk-{chunk.index + 1}",
                "chunk_text": chunk.metadata.get("combined_window_text", chunk.text),
                "index": chunk.index,
                "method": "sentence_window",
                "level": "sentence",
                "parent_id": "",
                "source": chunk.metadata.get("source", source_name),
                "page": chunk.metadata.get("page", ""),
            }
        )
    return records

#=========================Demo ====================================
# if __name__ == "__main__":
#     from langchain_core.documents import Document
#     from src.ingestion import extract_text

#     sample_path = os.path.join(ROOT_DIR, "data", "technical_article.txt")
#     pages = extract_text(sample_path)

#     documents = [
#         Document(
#             page_content=item.get("text", ""),
#             metadata={
#                 "page": item.get("page"),
#                 "source": item.get("source", os.path.basename(sample_path)),
#             },
#         )
#         for item in pages
#     ]

#     chunks = sentence_window_chunking(
#         pages_or_documents=documents,
#         sentences_per_chunk=3,
#         window_size=2,
#     )
#     source_name = os.path.basename(sample_path)
#     records = build_sentence_window_records(chunks=chunks, source_name=source_name)

#     print("=" * 80)
#     print("SENTENCE-WINDOW CHUNKING DEMO")
#     print("=" * 80)
#     print(f"Pages loaded: {len(pages)}")
#     print(f"Documents created: {len(documents)}")
#     print(f"Chunks created: {len(chunks)}")
#     print(f"Records created: {len(records)}")

#     if not chunks:
#         print("No chunks created.")
#     else:
#         idx = min(2, len(chunks) - 1)
#         c = chunks[idx]
#         print(f"\nSample chunk index: {c.index}")
#         print(f"Source: {c.metadata.get('source')}")
#         print(f"Page: {c.metadata.get('page')}")
#         print(f"Chunk text: {c.text[:220]}...")
#         print(f"Upsert record sample: {records[idx]}")
