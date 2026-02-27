# RAG Source

The definitive single-repository guide for parsing and preparing documents for Retrieval-Augmented Generation (RAG). Contains working code examples, generated sample documents, and comprehensive guides for every major document type.

## What's Inside

### [Unstructured Documents](unstructured_documents/)

9 document types, 26+ extraction methods, all with working Python code and sample documents:

| Type | Methods | Key Libraries |
|------|---------|---------------|
| PDF | pypdf, pdfplumber, PyMuPDF, OCR, table extraction, comparison | pypdf, pdfplumber, pymupdf, pytesseract |
| Word (DOCX) | python-docx, mammoth, docx2txt | python-docx, mammoth |
| PowerPoint (PPTX) | Basic extraction, structured slide parsing | python-pptx |
| HTML / Web | BeautifulSoup, html2text, trafilatura | bs4, html2text, trafilatura |
| Spreadsheets | openpyxl, pandas, csv stdlib | openpyxl, pandas |
| Images (OCR) | Tesseract, EasyOCR | pytesseract, easyocr |
| Email (EML) | stdlib email parsing, structured extraction | email (stdlib) |
| Markdown / Text | Chunking strategies, AST parsing, semantic chunking | mistune |
| EPUB | ebooklib extraction, full text pipeline | ebooklib |

## Getting Started

```bash
# Install dependencies
uv sync

# Install optional OCR dependencies
uv sync --extra ocr

# Generate all sample documents
for f in unstructured_documents/*/sample_docs/generate_samples.py; do
  uv run python "$f"
done

# Run any extraction script
uv run python unstructured_documents/01_pdf/01_pypdf_extraction.py
```

## Focus

This repo focuses on **document parsing and extraction strategies** — how to get text out of various file formats and prepare it for RAG. It does not implement RAG pipelines, vector databases, or embedding models. The goal is to be the only guide you need for the "parse and chunk" phase of any RAG system.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
