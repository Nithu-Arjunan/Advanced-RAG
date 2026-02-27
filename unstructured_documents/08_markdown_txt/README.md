# Markdown and Plain Text Parsing for RAG

## Overview

Markdown and plain text are the simplest document formats, yet they represent one of the most important cases for RAG systems. Unlike PDF, DOCX, or HTML, there is no complex parsing step -- the text is already available. The primary challenge shifts entirely to **chunking**: how to split raw text into segments that preserve semantic meaning, respect natural boundaries, and produce high-quality embeddings for retrieval.

Markdown adds a layer of lightweight structure (headings, code blocks, lists, tables) that can be leveraged for smarter, structure-aware chunking.

## Why This Is the Most Important Case

1. **Most documents can be converted to text/markdown** -- PDF, DOCX, HTML, and email extraction all ultimately produce text. The chunking strategies here apply to every upstream format.
2. **Chunking quality directly impacts RAG accuracy** -- poor chunks lead to poor embeddings, which lead to irrelevant retrieval and inaccurate answers.
3. **No parsing errors** -- unlike binary formats, text/markdown parsing never fails. The entire challenge is in the chunking strategy.
4. **Foundation for all other modules** -- the shared chunking utilities used throughout this project implement the strategies demonstrated here.

## Chunking Strategy Comparison

| Strategy | How It Works | Chunk Size Control | Semantic Coherence | Speed | Best For |
|----------|-------------|-------------------|-------------------|-------|----------|
| **Fixed Character** | Split at exact character count | Exact | Poor (breaks mid-sentence) | Very fast | Uniform token counts, simple baselines |
| **Sentence-Based** | Group N sentences per chunk | Approximate | Good (sentence boundaries) | Fast | General-purpose, well-punctuated text |
| **Paragraph-Based** | Split on double newlines | Variable | Very good (topic boundaries) | Fast | Documents with clear paragraph structure |
| **Recursive** | Try separators in order: para > newline > sentence > char | Configurable max | Good (best available boundary) | Fast | Balanced approach, unknown document structure |
| **Heading-Aware** | Split at heading boundaries (markdown) | Variable | Excellent (section = topic) | Fast | Structured markdown, documentation, papers |
| **Sliding Window** | Overlapping sentence groups | Approximate | Good (overlap preserves context) | Fast | When chunk boundary context matters |
| **Semantic** | Group by topic similarity (embeddings) | Variable | Excellent (topic-coherent) | Slow (requires embeddings) | High-quality retrieval, topic-diverse documents |

## When to Use Each Approach

### Fixed Character Chunking (`01_text_chunking_strategies.py`)
- You need **predictable token counts** for embedding models with strict limits
- You are building a **baseline** to compare against smarter strategies
- The text has **no structural markers** and you need something quick

### Sentence-Based Chunking (`01_text_chunking_strategies.py`)
- The text is **well-punctuated** with clear sentence boundaries
- You want a **good balance** between simplicity and semantic coherence
- You need **overlapping chunks** for boundary context preservation

### Paragraph-Based Chunking (`01_text_chunking_strategies.py`)
- The document has **clear paragraph structure** with blank line separators
- You want to **respect the author's natural topic organization**
- Paragraphs are a **reasonable size** (not too long, not too short)

### Recursive Splitting (`01_text_chunking_strategies.py`)
- You do not know the document structure in advance
- You want a **single strategy that works well across document types**
- This is the approach used by **LangChain's RecursiveCharacterTextSplitter**

### Heading-Aware Chunking (`02_markdown_parsing.py`)
- The document is **markdown with headings** or has been converted to markdown
- Each section covers a **distinct topic** (documentation, articles, papers)
- You want **section headings as metadata** for filtered retrieval

### Sliding Window Chunking (`03_semantic_chunking.py`)
- Context near **chunk boundaries** is important for retrieval accuracy
- You want a simple way to ensure **overlapping coverage** without complex logic
- You are willing to accept **some chunk redundancy** for better recall

### Semantic Chunking (`03_semantic_chunking.py`)
- You need the **highest quality chunks** and have compute budget for embeddings
- Documents cover **multiple topics** that should not be mixed in a single chunk
- You are building a **production system** where retrieval quality is critical

## Markdown-Specific Features

### Heading Extraction
Headings provide the best natural chunk boundaries in markdown. The `chunk_by_headings()` utility splits text at heading lines and preserves the heading as metadata:

```python
from shared.chunking import chunk_by_headings

chunks = chunk_by_headings(md_text)
# [{"heading": "Introduction", "content": "..."}, {"heading": "Methods", "content": "..."}, ...]
```

### Code Block Handling
Code blocks in technical documentation are often the exact content users are searching for. Extract them separately for targeted retrieval:

```python
# Code blocks as standalone RAG chunks with section context
code_chunks = extract_code_blocks_for_rag(md_text)
# [{"section": "Authentication", "language": "python", "code": "...", "rag_text": "..."}]
```

### Table Extraction
Markdown tables can be parsed into structured data using mistune's AST:

```python
ast = parse_markdown_ast(md_text)
tables = extract_tables(ast)
# [{"headers": ["Method", "Purpose"], "rows": [["GET", "Retrieve"], ...]}]
```

## Common Pitfalls

| Pitfall | Description | Solution |
|---------|-------------|----------|
| **Sentence boundary detection** | Abbreviations (Dr., U.S., etc.) and decimal numbers (3.14) cause false sentence breaks | Use NLP libraries (spaCy, NLTK) for production; our regex approach handles common cases |
| **Unicode and encoding** | Files may use UTF-8, UTF-16, Latin-1, or other encodings | Always specify encoding when reading files; use `chardet` for detection |
| **Empty or very short chunks** | Aggressive splitting can produce chunks that are too small for meaningful embedding | Set minimum chunk sizes; merge short chunks with neighbors |
| **Very long chunks** | Single paragraphs or code blocks that exceed embedding model limits | Apply secondary splitting (recursive) to oversized chunks |
| **Lost context at boundaries** | Important information split across two chunks | Use overlapping strategies (sliding window, sentence overlap) |
| **Heading-less documents** | Plain text without headings cannot use heading-aware chunking | Fall back to paragraph or recursive splitting |
| **Inconsistent formatting** | Mixed use of tabs, spaces, and newline styles | Normalize whitespace before chunking |
| **Code blocks in markdown** | Code blocks may be split mid-function by character or sentence chunkers | Extract code blocks separately; do not apply text chunking to code |

## Tips for Production

1. **Start with recursive splitting at 500 chars** as a baseline, then evaluate domain-specific alternatives.
2. **Always include overlap** (10-20% of chunk size) to preserve context at boundaries.
3. **Test with real queries** -- the best chunking strategy depends on how users will search, not just the document structure.
4. **Preserve metadata** -- section headings, document titles, and file names should be stored alongside chunks for filtered retrieval.
5. **Handle edge cases** -- empty documents, single-line files, binary files with text extensions, and extremely long lines.
6. **Normalize before chunking** -- strip excessive whitespace, normalize Unicode, and remove non-printable characters.
7. **Monitor chunk size distribution** -- very skewed distributions (many tiny chunks + a few huge ones) indicate a poor chunking strategy.
8. **Consider the embedding model** -- different models have different optimal input lengths. Match your chunk size to your model's sweet spot.
9. **For markdown, use heading-aware chunking** -- it almost always outperforms blind text splitting because it respects the author's topic organization.
10. **Separate code from prose** -- in technical documents, extract code blocks as distinct chunks with section metadata.

## Files in This Module

| File | Description |
|------|-------------|
| `sample_docs/generate_samples.py` | Generates 4 sample files (2 markdown, 2 plain text) |
| `01_text_chunking_strategies.py` | Compares fixed-char, sentence, paragraph, and recursive chunking on plain text |
| `02_markdown_parsing.py` | Parses markdown AST with mistune; heading-aware chunking; code block extraction |
| `03_semantic_chunking.py` | Sliding window, paragraph-based semantic chunking, coherence analysis |
