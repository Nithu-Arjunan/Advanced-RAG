# MegaParse - LLM-Optimized Document Parser

## What is MegaParse?

**MegaParse** is an open-source document parser by [Quivr](https://www.quivr.com/) designed specifically for LLM ingestion with **zero information loss**. It converts documents into clean Markdown that's immediately ready for RAG systems, fine-tuning, or LLM prompts.

- **Creator**: Quivr (open-source RAG platform)
- **License**: Apache 2.0 (fully open-source, commercial-friendly)
- **GitHub**: [QuivrHQ/MegaParse](https://github.com/QuivrHQ/MegaParse)
- **Python**: >= 3.11

## Key Features

| Feature | Description |
|---------|-------------|
| Zero information loss | Designed to preserve all content during parsing |
| Simple API | Single function call: `megaparse.load(filepath)` |
| Vision parsing | MegaParseVision uses GPT-4o/Claude for complex layouts |
| Multiple formats | PDF, DOCX, PPTX, XLSX, CSV, TXT |
| Table extraction | Tables preserved as Markdown tables |
| Apache 2.0 license | Free for commercial use |

## Two Parsing Modes

### 1. Standard Parsing (`MegaParse`)
- Uses rule-based extraction (Unstructured under the hood)
- Fast, free, runs locally
- Good for text-heavy documents with standard layouts

### 2. Vision Parsing (`MegaParseVision`)
- Renders pages as images, sends to multimodal LLM
- Handles complex layouts, charts, handwriting
- Requires API key (OpenAI or Anthropic)
- Higher accuracy but slower and costs money

### Benchmark Comparison

| Parser | Similarity Ratio |
|--------|:----------------:|
| MegaParse Vision (GPT-4o) | **0.87** |
| Unstructured (with table check) | 0.77 |
| Unstructured (standard) | 0.59 |
| LlamaParse | 0.33 |

## Installation

```bash
# Basic installation
uv pip install megaparse

# System dependencies required:
# macOS:
brew install poppler tesseract libmagic

# Ubuntu/Debian:
sudo apt install poppler-utils tesseract-ocr libmagic-dev

# For Vision parsing:
uv pip install megaparse langchain-openai    # for GPT-4o
uv pip install megaparse langchain-anthropic  # for Claude
```

## Quick Start

### Standard Parsing
```python
from megaparse import MegaParse

megaparse = MegaParse()
response = megaparse.load("document.pdf")  # Returns Markdown string
print(response)
```

### Vision-Enhanced Parsing
```python
from megaparse.parser.megaparse_vision import MegaParseVision
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", api_key="sk-...")
parser = MegaParseVision(model=model)
response = parser.convert("complex_document.pdf")
print(response)
```

## What Gets Extracted

- Text content (headings, paragraphs, lists)
- Tables (as Markdown tables)
- Table of contents
- Headers and footers
- Image descriptions (with vision mode)
- Document structure

## When to Use MegaParse

**Best for:**
- Quick, simple document-to-Markdown conversion
- When you want the simplest possible API
- Apache 2.0 license needed (vs Marker's GPL)
- When MegaParseVision's accuracy is needed for complex docs
- RAG pipeline preprocessing

**Not ideal for:**
- Fine-grained layout control (use Docling or Unstructured instead)
- Documents requiring specialized field extraction (use Azure)
- Offline processing without API for complex docs

## Pros and Cons

| Pros | Cons |
|------|------|
| Simplest API (one function call) | Fewer configuration options |
| Apache 2.0 license | Requires Python >= 3.11 |
| Vision mode for complex layouts | Vision mode requires API costs |
| Good benchmark scores | Standard mode less accurate than Docling |
| Built on proven tools (Unstructured) | System dependencies (poppler, tesseract) |

## Scripts in This Folder

| Script | Description |
|--------|-------------|
| `01_basic_parsing.py` | Basic document parsing with MegaParse |
| `02_vision_parsing.py` | Vision-enhanced parsing with GPT-4o/Claude |
| `03_rag_preparation.py` | End-to-end RAG preparation pipeline |

## Comparison with Other Tools

| Feature | MegaParse | Docling | Marker | Unstructured |
|---------|-----------|---------|--------|--------------|
| API simplicity | Simplest | Moderate | Moderate | Complex |
| Vision mode | Yes (LLM) | No | Optional LLM | No |
| License | Apache 2.0 | MIT | GPL | Apache 2.0 |
| Local execution | Yes | Yes | Yes | Yes |
| Cloud option | API server | No | No | Yes |
| Best accuracy | Vision mode | PDF layout | PDF to MD | hi_res mode |
