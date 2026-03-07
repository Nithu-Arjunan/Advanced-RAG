# LlamaParse - Cloud-Based GenAI Document Parser

## Overview

LlamaParse is a cloud-based, GenAI-native document parsing service built by [LlamaIndex](https://www.llamaindex.ai/). It uses multimodal AI models to convert complex documents into clean, structured output optimized for retrieval-augmented generation (RAG) pipelines. Unlike traditional parsers that rely on heuristic rules, LlamaParse leverages large language models to understand document layout, extract tables, interpret charts/images, and produce high-fidelity structured text.

**Website:** [https://cloud.llamaindex.ai/](https://cloud.llamaindex.ai/)

## Supported Formats

LlamaParse handles a wide range of document types:

| Category   | Formats                                      |
|------------|----------------------------------------------|
| Documents  | PDF, DOCX, DOC, RTF, EPUB                    |
| Slides     | PPTX, PPT                                    |
| Sheets     | XLSX, XLS, CSV, TSV                           |
| Web        | HTML, XML                                     |
| Images     | PNG, JPG/JPEG, BMP, TIFF, HEIC               |
| Other      | TXT, Markdown, and more                       |

## Parsing Tiers

LlamaParse offers three parsing tiers with different speed/accuracy tradeoffs:

| Tier           | Speed  | Accuracy | Credit Cost | Best For                                     |
|----------------|--------|----------|-------------|----------------------------------------------|
| `fast`         | Fast   | Basic    | Lowest      | Simple text documents, quick previews         |
| `agentic`      | Medium | High     | Medium      | Documents with images, charts, diagrams       |
| `agentic_plus` | Slow   | Highest  | Highest     | Complex tables, multi-column layouts, forms   |

Higher tiers use more advanced multimodal AI models for better accuracy on complex documents.

## Output Formats

| Format     | Description                                        |
|------------|----------------------------------------------------|
| `markdown` | Clean Markdown with tables, lists, headings        |
| `text`     | Plain text extraction                               |
| `json`     | Structured JSON with page/block hierarchy and metadata |

## Key Features

- **AI-powered table extraction**: Reconstructs complex tables with merged cells, nested headers, and spanning rows/columns into clean Markdown or structured JSON.
- **Image and chart understanding**: Multimodal models interpret figures, charts, and diagrams, generating textual descriptions or structured data.
- **Custom parsing instructions**: Provide natural-language instructions to guide the parser (e.g., "Extract all financial figures and present them as a table").
- **Page selection**: Parse specific pages or page ranges instead of the entire document.
- **Language support**: Specify document language for improved accuracy on non-English content.
- **Watermark/diagonal text handling**: Option to skip diagonal or watermark text.
- **Multi-column layout handling**: Intelligent reading order detection for multi-column documents.
- **Caching**: Results are cached server-side; repeat parsing of the same document is instant.

## Authentication

LlamaParse requires a LlamaCloud API key:

1. Sign up at [https://cloud.llamaindex.ai/](https://cloud.llamaindex.ai/)
2. Navigate to the API Keys section in your dashboard
3. Generate a new key (format: `llx-...`)
4. Set the environment variable:

```bash
export LLAMA_CLOUD_API_KEY="llx-your-key-here"
```

### Free Tier Limits

- **1000 pages per day** across all parsing tiers
- No credit card required
- Paid plans available for higher volume

## Python API

### llama-parse package (legacy, stable)

```bash
uv pip install llama-parse
```

```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="llx-...",           # Or set LLAMA_CLOUD_API_KEY env var
    result_type="markdown",      # "markdown", "text", or "json"
    language="en",               # Document language
    parsing_instruction="...",   # Natural-language guidance for the AI
    skip_diagonal_text=True,     # Skip watermarks
    show_progress=True,          # Display progress bar
)

# Parse a file
documents = parser.load_data("document.pdf")
for doc in documents:
    print(doc.text)       # Extracted content
    print(doc.metadata)   # File metadata
```

### llama-cloud package (newer API)

```bash
uv pip install llama-cloud>=1.0
```

```python
from llama_cloud import AsyncLlamaCloud

client = AsyncLlamaCloud(api_key="llx-...")

# Upload and parse
file_obj = await client.files.upload("document.pdf")
result = await client.parsing.parse(
    file_id=file_obj.id,
    tier="agentic",        # "fast", "agentic", "agentic_plus"
    version="latest",
)
```

## LlamaIndex Integration

LlamaParse integrates natively with LlamaIndex to build complete RAG pipelines:

```python
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import MarkdownNodeParser

# 1. Parse
parser = LlamaParse(api_key="llx-...", result_type="markdown")
documents = parser.load_data("document.pdf")

# 2. Chunk (optional - use markdown-aware splitting)
node_parser = MarkdownNodeParser()
nodes = node_parser.get_nodes_from_documents(documents)

# 3. Index and query
index = VectorStoreIndex(nodes)
query_engine = index.as_query_engine()
response = query_engine.query("What is this document about?")
```

## When to Use LlamaParse

**Best suited for:**
- Complex PDFs with charts, images, and intricate table layouts
- Projects already using LlamaIndex for RAG
- When you want cloud simplicity without managing local models
- Multi-format document ingestion pipelines
- Scenarios where parsing accuracy on visual elements is critical

**Pros:**
- Highest accuracy on complex layouts, tables, and visual elements
- Simple API with minimal code required
- Cloud-managed infrastructure (no local GPU or model downloads)
- Native LlamaIndex integration for end-to-end RAG
- Supports 15+ document formats out of the box
- Built-in caching for repeat parsing

**Cons:**
- Requires internet connection (cloud-based service)
- API costs at scale beyond the free tier
- Document data is sent to LlamaCloud servers (privacy consideration)
- Rate limits on the free tier (1000 pages/day)
- Dependent on external service availability

## Scripts Overview

| Script                         | Description                                           |
|--------------------------------|-------------------------------------------------------|
| `01_basic_parsing.py`          | Basic PDF parsing, advanced options, multi-format demo |
| `02_llamaindex_integration.py` | Complete RAG pipeline with LlamaParse + LlamaIndex     |
| `03_parsing_tiers.py`          | Parsing tier comparison (fast, agentic, agentic_plus)  |

All scripts run in demo/documentation mode without an API key, printing example code and explanations. Set `LLAMA_CLOUD_API_KEY` to run live parsing.
