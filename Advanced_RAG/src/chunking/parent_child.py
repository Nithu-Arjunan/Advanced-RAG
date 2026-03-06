import os
import sys
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging
# Ensure project root is importable when running this file directly.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.base import Chunk, print_chunks

def parent_child_chunking(
    pages: list[dict],
    parent_chunk_size: int = 1500,
    parent_overlap: int = 100,
    child_chunk_size: int = 300,
    child_overlap: int = 50,
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Create a two-level hierarchy of parent and child chunks.

    Args:
        text: The input text.
        parent_chunk_size: Character size for parent chunks.
        parent_overlap: Overlap between parent chunks.
        child_chunk_size: Character size for child chunks.
        child_overlap: Overlap between child chunks.

    Returns:
        Tuple of (parent_chunks, child_chunks).
        Each child chunk has a 'parent_id' in its metadata.
    """
    documents=[]
    for item in pages:
        doc=Document(
            page_content=item["text"],
            metadata={"page":item["page"], "source": item.get("source", "unknown")},
        )
        documents.append(doc)

    

    # Step 1: Create parent chunks
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=parent_overlap,
    )
    parent_texts = parent_splitter.split_documents(documents)
    parent_chunks = []
    for i, pt in enumerate(parent_texts):
        parent_chunks.append(Chunk(
            text=pt.page_content,
            index=i,
            metadata={
                "method": "parent_child",
                "level": "parent",
                "page": pt.metadata.get("page"),
                "parent_id": f"parent_{i}",
                "source": pt.metadata.get("source", "unknown"),
            },
        ))
    logging.info(f"Created {len(parent_chunks)} parent chunks from {len(pages)} pages for source {pages[0]['source'] if pages else 'unknown'}.")
   
    # Step 2: Create child chunks from each parent
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=child_overlap,
    )

    child_chunks = []
    for parent in parent_chunks:
        child_texts = child_splitter.split_text(parent.text)
        for ct in child_texts:
            child_chunks.append(Chunk(
                text=ct,
                index=len(child_chunks),
                metadata={
                    "method": "parent_child",
                    "level": "child",
                    "parent_id": parent.metadata["parent_id"],
                    "parent_index": parent.index,
                    "page": parent.metadata.get("page"),
                    "source": parent.metadata.get("source", "unknown"),
                },
            ))
    print(f"Created {len(parent_chunks)} parent chunks and {len(child_chunks)} child chunks.")
    
    logging.info(f"Created {len(child_chunks)} child chunks from {len(parent_chunks)} parent chunks for source {pages[0]['source'] if pages else 'unknown'}.")  

    return parent_chunks, child_chunks


def retrieve_with_parent_context(
    query_chunk_index: int,
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
    if query_chunk_index < 0 or query_chunk_index >= len(child_chunks):
        raise IndexError(f"query_chunk_index {query_chunk_index} is out of range (0 to {len(child_chunks) - 1}).")

    child = child_chunks[query_chunk_index]
    parent_id = child.metadata["parent_id"]
    parent = next((p for p in parent_chunks if p.metadata["parent_id"] == parent_id), None)
    if parent is None:
        raise ValueError(f"No parent chunk found for parent_id '{parent_id}'.")
    return child, parent



# if __name__ == "__main__":
#     from src.ingestion import extract_text

#     sample_path = os.path.join(ROOT_DIR, "data", "technical_article.txt")
#     pages = extract_text(sample_path)
#     source_name = os.path.basename(sample_path)

#     parents, children = parent_child_chunking(
#         pages=pages,
#     )

#     print(f"Total parent chunks: {len(parents)}")
#     print(f"Total child chunks: {len(children)}")

#     if parents:
#         print("Sample parent metadata:", parents[0].metadata)
#     if children:
#         print("Sample child metadata:", children[0].metadata)




