# Unstructured.io

## What is Unstructured.io?

[Unstructured](https://github.com/Unstructured-IO/unstructured) is an open-source ETL toolkit for document parsing, built by Unstructured Inc. It provides a unified interface to extract structured elements from virtually any document format -- PDFs, Word files, PowerPoints, HTML, emails, images, spreadsheets, and more.

The core design principle: every document is parsed into a flat list of **typed Element objects** (Title, NarrativeText, Table, ListItem, etc.), giving downstream pipelines structured, semantic access to document content.

## Core Concept: partition() and Element Objects

The universal entry point is the `partition()` function, which auto-detects file type and routes to the correct parser:

```python
from unstructured.partition.auto import partition

elements = partition(filename="report.pdf")

for el in elements:
    print(type(el).__name__, str(el)[:100])
```

Each element carries:
- **Type** -- what kind of content it represents
- **Text** -- the extracted text content
- **Metadata** -- rich per-element metadata (page number, coordinates, source file, etc.)

## Element Types

| Type | Description |
|------|-------------|
| `Title` | Document headings and titles |
| `NarrativeText` | Body paragraphs and flowing text |
| `Table` | Tabular data (with `.metadata.text_as_html` for HTML representation) |
| `ListItem` | Bulleted or numbered list items |
| `Image` | Image descriptions or OCR'd text from images |
| `Header` | Page headers |
| `Footer` | Page footers |
| `PageBreak` | Page boundary markers |
| `Address` | Postal or email addresses |
| `EmailAddress` | Email addresses specifically |
| `FigureCaption` | Captions for figures |
| `Formula` | Mathematical formulas |
| `UncategorizedText` | Text that doesn't fit other categories |

## Supported Formats

PDF, DOCX, PPTX, HTML, XLSX, CSV, TSV, EML, MSG, EPUB, Markdown, TXT, images (PNG, JPG, TIFF, BMP, HEIC), RTF, ODT, RST, ORG, XML, and more.

Unstructured has the widest format support of any open-source document parsing library.

## PDF Processing Strategies

Unstructured offers three strategies for PDF extraction, each with different speed/quality tradeoffs:

| Strategy | Method | Speed | Quality | Best For |
|----------|--------|-------|---------|----------|
| `fast` | Direct text extraction (pdfminer) | Fastest | Good for text-native PDFs | Text-heavy PDFs with simple layouts |
| `hi_res` | Layout detection models (detectron2/YOLOX) + OCR | Slowest | Best -- accurate structure recognition | Complex layouts, tables, mixed content |
| `ocr_only` | Full-page OCR (Tesseract) | Medium | Good for scanned docs | Scanned PDFs, image-only PDFs |

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf(filename="report.pdf", strategy="hi_res")
```

## Installation

**Basic (text-based formats only):**
```bash
uv pip install unstructured
```

**Per-format extras:**
```bash
uv pip install "unstructured[pdf]"       # PDF support
uv pip install "unstructured[docx]"      # Word documents
uv pip install "unstructured[pptx]"      # PowerPoint
uv pip install "unstructured[xlsx]"      # Excel
uv pip install "unstructured[epub]"      # EPUB ebooks
uv pip install "unstructured[md]"        # Markdown
```

**All document types:**
```bash
uv pip install "unstructured[all-docs]"
```

**System dependencies (for hi_res PDF and image OCR):**
- Tesseract OCR: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- poppler: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)
- libmagic: `brew install libmagic` (macOS) or `apt-get install libmagic-dev` (Linux)

## Chunking

Unstructured provides `chunk_by_title`, which groups elements under their nearest heading to produce semantically coherent chunks:

```python
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title

elements = partition(filename="report.pdf")
chunks = chunk_by_title(
    elements,
    max_characters=1000,            # Hard max chunk size
    new_after_n_chars=500,           # Soft limit to start a new chunk
    combine_text_under_n_chars=200,  # Merge small chunks together
)
```

This is structure-aware chunking -- it respects document headings rather than splitting on arbitrary token/character boundaries.

## Export Formats

```python
from unstructured.staging.base import elements_to_json, elements_to_dicts, convert_to_dataframe

# JSON string
json_str = elements_to_json(elements)

# List of Python dicts
dicts = elements_to_dicts(elements)

# Pandas DataFrame
df = convert_to_dataframe(elements)

# Plain text
text = "\n\n".join([str(el) for el in elements])
```

## Metadata

Every element has a `.metadata` attribute with rich information:

| Field | Description |
|-------|-------------|
| `filename` | Source file name |
| `file_directory` | Source directory |
| `page_number` | Page number (PDFs, DOCX, PPTX) |
| `coordinates` | Bounding box coordinates (hi_res strategy) |
| `text_as_html` | HTML representation of tables |
| `languages` | Detected languages |
| `sent_from` | Email sender (EML files) |
| `sent_to` | Email recipient (EML files) |
| `subject` | Email subject (EML files) |
| `detection_class_prob` | Model confidence score (hi_res) |

## Framework Integration

**LangChain:**
```python
from langchain_community.document_loaders import UnstructuredFileLoader

loader = UnstructuredFileLoader("report.pdf", mode="elements")
docs = loader.load()
```

**LlamaIndex:**
```python
from llama_index.readers.file import UnstructuredReader

reader = UnstructuredReader()
documents = reader.load_data(file="report.pdf")
```

## Hosted API vs Open Source

Unstructured offers both:
- **Open source library** (`uv pip install unstructured`) -- runs locally, full control, no API keys
- **Hosted API / Unstructured Platform** -- managed service at `api.unstructured.io`, higher throughput, no local dependency management, requires API key

The API accepts the same parameters (strategy, chunking, etc.) and returns the same Element structure.

## When to Use Unstructured

**Best for:**
- Multi-format pipelines where you need one interface for PDFs, DOCX, HTML, email, etc.
- Element-type-aware processing (e.g., treat tables differently from narrative text)
- Pipelines that benefit from rich per-element metadata
- Teams already using LangChain or LlamaIndex (first-class integrations)

**Pros:**
- Widest format support of any open-source document parser
- Typed Element objects give semantic structure to extracted content
- Rich metadata (page numbers, coordinates, table HTML, email headers)
- Active community and regular releases
- Structure-aware chunking with `chunk_by_title`
- Both open-source and hosted API options

**Cons:**
- `hi_res` strategy requires heavy dependencies (detectron2 or YOLOX, Tesseract, poppler)
- Installation can be complex, especially for the full `[all-docs]` extra
- Slower than basic text-extraction parsers when using `hi_res`
- `fast` strategy may miss layout structure in complex documents

## Scripts in This Module

| Script | Description |
|--------|-------------|
| `01_auto_partition.py` | Universal `partition()` function with auto file-type detection. Demonstrates partitioning PDFs, multiple formats, and element type overview. |
| `02_pdf_strategies.py` | Compares the three PDF strategies (fast, hi_res, ocr_only) with timing and quality analysis. Shows advanced hi_res options. |
| `03_specific_partitioners.py` | Dedicated partitioners for DOCX, PPTX, HTML, XLSX, Email, EPUB, and images with format-specific parameters. |
| `04_chunking_and_export.py` | Chunking with `chunk_by_title`, export to JSON/text/dicts/DataFrame, and metadata exploration. |

All scripts reference sample documents from `../../unstructured_documents/`.
