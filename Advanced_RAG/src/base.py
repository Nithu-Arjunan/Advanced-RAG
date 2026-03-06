"""Base class and utilities shared across all chunking strategies."""

import os
import tiktoken
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class Chunk:
    """Represents a single chunk of text with metadata."""
    text: str
    index: int
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def token_count(self) -> int:
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(self.text))

    def __repr__(self) -> str:
        preview = self.text[:80].replace("\n", " ")
        return f"Chunk(index={self.index}, chars={self.char_count}, tokens={self.token_count}, text='{preview}...')"


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in a text string."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))



def print_chunks(chunks: list[Chunk], max_preview: int = 100) -> None:
    """Pretty-print a list of chunks."""
    print(f"\n{'='*80}")
    print(f"Total chunks: {len(chunks)}")
    print(f"{'='*80}")
    for chunk in chunks:
        preview = chunk.text[:max_preview].replace("\n", " ")
        print(f"\n--- Chunk {chunk.index} (chars={chunk.char_count}, tokens={chunk.token_count}) ---")
        print(f"{preview}...")
        if chunk.metadata:
            print(f"  metadata: {chunk.metadata}")
    print(f"\n{'='*80}\n")