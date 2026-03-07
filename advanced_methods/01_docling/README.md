# Docling - Advanced Document Conversion for RAG

## What is Docling?

[Docling](https://github.com/DS4SD/docling) is an open-source document conversion library developed by IBM Research. Released under the MIT license, it provides a unified interface to parse and convert documents of various formats into a structured `DoclingDocument` representation. Docling is purpose-built for AI workflows, particularly RAG (Retrieval-Augmented Generation) pipelines, where accurate document understanding is critical.

Docling goes beyond simple text extraction: it understands document layout, preserves structural hierarchy (headings, sections, lists), detects and reconstructs tables, and supports OCR for scanned documents and images.

## Supported Input Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Native text and scanned (via OCR); advanced layout analysis |
| Word | `.docx` | Full structure preservation including tables and styles |
| PowerPoint | `.pptx` | Slide-by-slide extraction with text and table support |
| Excel | `.xlsx` | Spreadsheet data with sheet-level separation |
| HTML | `.html`, `.htm` | Web page parsing with structure detection |
| Images | `.png`, `.jpg`, `.tiff`, `.bmp` | OCR-based text extraction |
| AsciiDoc | `.adoc` | Technical documentation format |
| Markdown | `.md` | Parsed into DoclingDocument structure |
| LaTeX | `.tex` | Academic paper format support |
| Audio | `.mp3`, `.wav`, etc. | Transcription via speech-to-text models |

## Export Formats

Docling can export parsed documents to multiple output formats:

- **Markdown** -- Clean, readable output preserving headings and tables
- **Plain Text** -- Stripped-down text content
- **JSON** -- Lossless serialization of the full `DoclingDocument` model (via Pydantic)
- **HTML** -- Structured HTML output
- **DocTags** -- Docling's proprietary token format for document structure
- **WebVTT** -- Subtitle format (for audio transcriptions)

## Key Features

### Advanced PDF Layout Analysis
Docling uses deep learning models to analyze page layout, detecting reading order, columns, headers, footers, and body text regions. This goes far beyond simple text extraction from PDF streams.

### Table Structure Recognition (TableFormer)
The TableFormer model reconstructs table structures from PDFs, even when tables lack explicit grid lines. Two modes are available:

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| **FAST** | High | Good | Large batch processing, simple tables |
| **ACCURATE** | Lower | Excellent | Complex tables, financial documents |

### OCR Support
Docling supports multiple OCR engines for scanned documents and images:

| Engine | Install | Platform | Notes |
|--------|---------|----------|-------|
| EasyOCR | `pip install "docling[easyocr]"` | All | Default; GPU-accelerated; 80+ languages |
| Tesseract | `pip install "docling[tesserocr]"` | All | Classic OCR engine; fast on CPU |
| Tesseract CLI | Built-in (requires system Tesseract) | All | Uses command-line `tesseract` binary |
| OcrMac | `pip install "docling[ocrmac]"` | macOS only | Apple Vision framework; fast on Mac |
| RapidOCR | `pip install "docling[rapidocr]"` | All | Lightweight; no GPU required |

### Unified DoclingDocument Representation
All input formats are parsed into a single `DoclingDocument` model. This Pydantic-based representation includes:
- Document metadata (title, authors, etc.)
- Hierarchical structure (sections, headings, paragraphs)
- Tables with cell-level data
- Figures and images
- Page-level information

### Built-in Chunking for RAG
Docling provides structure-aware chunkers designed specifically for RAG:

- **HierarchicalChunker** -- Splits by document structure (headings, sections). Each chunk inherits the heading hierarchy as context.
- **HybridChunker** -- Combines structural splitting with token-based limits. Accepts a tokenizer (e.g., from an embedding model) and a `max_tokens` parameter to ensure chunks fit within model context windows.

## Installation

```bash
# Basic installation
pip install docling

# With specific OCR engines
pip install "docling[easyocr]"
pip install "docling[tesserocr]"
pip install "docling[ocrmac]"       # macOS only
pip install "docling[rapidocr]"

# For chunking
pip install docling-core

# Framework integrations
pip install llama-index-readers-docling   # LlamaIndex
pip install langchain-docling             # LangChain
```

**Requirements:** Python 3.10 or later. Note that Docling pulls in PyTorch and several deep learning model dependencies, which can be large (several GB).

## Architecture Overview

```
Input File (PDF, DOCX, PPTX, ...)
         |
         v
  DocumentConverter
         |
         v
  Format-specific Pipeline
  (PdfPipeline, DocxPipeline, etc.)
         |
         |-- Layout Analysis (PDF)
         |-- Table Detection (TableFormer)
         |-- OCR (if enabled)
         |
         v
    DoclingDocument
    (unified Pydantic model)
         |
         v
  Export / Chunking
  (Markdown, JSON, text, HTML, DocTags)
  (HierarchicalChunker, HybridChunker)
```

The `DocumentConverter` is the main entry point. It auto-detects the input format, routes the document through the appropriate pipeline, and returns a `ConversionResult` containing the `DoclingDocument`.

## Framework Integrations

| Framework | Package | Entry Point |
|-----------|---------|-------------|
| **LlamaIndex** | `llama-index-readers-docling` | `DoclingReader` for loading, `DoclingNodeParser` for chunking |
| **LangChain** | `langchain-docling` | `DoclingLoader` for document loading |
| **Haystack** | `haystack-docling` | `DoclingConverter` component |
| **CrewAI** | Native support | Via Docling tools |

## When to Use Docling

**Best suited for:**
- Local/private document processing (no data leaves your machine)
- Multi-format pipelines where you need one tool for PDF + DOCX + PPTX + HTML
- PDF-heavy workloads requiring accurate table extraction and layout understanding
- RAG pipelines needing structure-aware chunking
- Projects that benefit from a unified document representation (DoclingDocument)

**Consider alternatives when:**
- You need a lightweight solution without heavy dependencies
- You only process one format (format-specific tools may be simpler)
- You need a cloud API with no local setup
- You are on Python < 3.10

## Pros and Cons

### Pros
- Open source (MIT license) with active IBM Research backing
- Runs entirely locally -- no data sent to external services
- Excellent PDF understanding via deep learning layout analysis
- Multi-format support through a single unified API
- Built-in RAG chunkers that leverage document structure
- Lossless JSON serialization via Pydantic models
- Growing ecosystem of framework integrations

### Cons
- Requires Python 3.10+
- Heavy dependencies (PyTorch, deep learning models) -- large install footprint
- Slower than simple parsers (e.g., PyPDF) due to ML model inference
- No cloud/hosted API option
- Relatively new project; API may change between versions
- GPU recommended for best performance on large PDF batches

## Comparison with Other Tools

| Feature | Docling | PyPDF/pdfplumber | Unstructured | LlamaParse |
|---------|---------|------------------|--------------|------------|
| Multi-format | Yes (10+) | PDF only | Yes (20+) | Yes |
| Table extraction | Excellent (TableFormer) | Good (pdfplumber) | Good | Good |
| Layout analysis | Deep learning | Rule-based | ML-based | Cloud ML |
| OCR support | Multiple engines | No | Yes (Tesseract) | Cloud |
| Local execution | Yes | Yes | Yes | Cloud only |
| License | MIT | MIT/Various | Apache 2.0 | Proprietary |
| Dependencies | Heavy (PyTorch) | Light | Medium | Light (client) |
| Built-in chunking | Yes | No | Yes | No |
| Cost | Free | Free | Free | Paid |

## Scripts Overview

| Script | Description |
|--------|-------------|
| `01_basic_conversion.py` | Basic document conversion with `DocumentConverter`. Converts PDF, DOCX, PPTX, and HTML files. Demonstrates all export formats (Markdown, JSON, text, DocTags). |
| `02_pdf_advanced.py` | Advanced PDF options: FAST vs ACCURATE table detection, OCR configuration, image-to-text conversion. |
| `03_chunking.py` | RAG chunking with `HierarchicalChunker` and `HybridChunker`. Compares chunking strategies on the same document. |
| `04_integrations.py` | LlamaIndex and LangChain integration examples using `DoclingReader` and `DoclingLoader`. |

All scripts reference sample documents from `../../documents/` and include interactive menus for selecting demos.
