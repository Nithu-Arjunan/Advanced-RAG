# PDF Parsing for RAG

PDF is the most common format for sharing structured knowledge in business and academia, yet it is one of the hardest to parse reliably. This module provides a comprehensive guide to extracting text from PDFs using multiple libraries, with practical examples focused on building RAG (Retrieval-Augmented Generation) pipelines.

## Why PDF Parsing Is Complex

PDFs were designed for **display fidelity**, not for content extraction. Under the hood, a PDF is a collection of positioned glyphs, images, and vector graphics -- there is no concept of "paragraph," "heading," or "table" at the file-format level. This creates several challenges:

| Challenge | Description |
|-----------|-------------|
| **Text encoding** | Characters may be stored as glyph IDs rather than Unicode. Ligatures, custom fonts, and CID-keyed fonts can produce garbled output. |
| **Layout reconstruction** | Text blocks have absolute positions on the page. Reading order, columns, and indentation must be inferred from spatial relationships. |
| **Scanned documents** | Image-based PDFs contain no extractable text at all -- OCR is required. |
| **Tables** | Table cells are just positioned text with drawn lines. Detecting row/column structure requires heuristic or ML-based analysis. |
| **Headers & footers** | Repeated page elements (page numbers, titles) pollute extracted text unless filtered by position. |
| **Multi-column layouts** | Text from parallel columns can be interleaved if extraction does not account for spatial layout. |
| **Embedded objects** | Annotations, form fields, watermarks, and overlapping layers add noise. |

## Method Comparison

| Library | Speed | Table Support | Layout-Aware | OCR Support | Best For |
|---------|-------|---------------|--------------|-------------|----------|
| **pypdf** | Medium | None | Basic | No | Simple text extraction, metadata, minimal dependencies |
| **pdfplumber** | Slow | Excellent | Good | No | Table extraction, character-level analysis, structured data |
| **PyMuPDF (fitz)** | Fast | Basic | Good | No | High-performance extraction, font analysis, batch processing |
| **pytesseract + pdf2image** | Very Slow | None | Basic | Yes | Scanned/image-based PDFs |

## When to Use Each Method

```
Is the PDF scanned / image-based?
├── Yes → pytesseract + pdf2image (05_ocr_extraction.py)
└── No
    ├── Does it contain tables you need structured data from?
    │   ├── Yes → pdfplumber (02_pdfplumber_extraction.py, 04_table_extraction.py)
    │   └── No
    │       ├── Need fastest extraction?
    │       │   ├── Yes → PyMuPDF (03_pymupdf_extraction.py)
    │       │   └── No → pypdf (01_pypdf_extraction.py)
    │       └── Need font/heading detection?
    │           └── Yes → PyMuPDF dict mode (03_pymupdf_extraction.py)
    └── Production pipeline?
        └── PyMuPDF for text + pdfplumber for tables (06_comparison.py)
```

## Scripts in This Module

| Script | Purpose |
|--------|---------|
| `sample_docs/generate_samples.py` | Generate 4 sample PDFs for testing |
| `01_pypdf_extraction.py` | Basic extraction with pypdf + chunking demo |
| `02_pdfplumber_extraction.py` | Layout-aware extraction + table detection |
| `03_pymupdf_extraction.py` | Fast extraction with blocks, fonts, headings |
| `04_table_extraction.py` | Dedicated table extraction and RAG preparation |
| `05_ocr_extraction.py` | OCR for scanned PDFs (optional dependencies) |
| `06_comparison.py` | Side-by-side comparison of all methods |

## Quick Start

```bash
# Generate sample PDFs
uv run python unstructured_documents/01_pdf/sample_docs/generate_samples.py

# Run any extraction script
uv run python unstructured_documents/01_pdf/01_pypdf_extraction.py
uv run python unstructured_documents/01_pdf/02_pdfplumber_extraction.py
uv run python unstructured_documents/01_pdf/03_pymupdf_extraction.py
uv run python unstructured_documents/01_pdf/04_table_extraction.py
uv run python unstructured_documents/01_pdf/06_comparison.py

# OCR (requires additional system dependencies)
uv run python unstructured_documents/01_pdf/05_ocr_extraction.py
```

## Code Examples

### Basic Text Extraction (pypdf)

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
for page in reader.pages:
    text = page.extract_text()
    print(text)

# Access metadata
meta = reader.metadata
print(f"Title: {meta.title}, Pages: {len(reader.pages)}")
```

### Table Extraction (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("tables.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            header = table[0]
            rows = table[1:]
            # Convert to list of dicts
            records = [dict(zip(header, row)) for row in rows]
```

### Fast Extraction with Position Info (PyMuPDF)

```python
import fitz

doc = fitz.open("document.pdf")
for page in doc:
    # Get text blocks with bounding boxes
    blocks = page.get_text("blocks", sort=True)
    for x0, y0, x1, y1, text, block_no, block_type in blocks:
        if block_type == 0:  # text block
            print(f"[{x0:.0f},{y0:.0f}] {text[:50]}")

    # Get detailed font info
    data = page.get_text("dict")
    for block in data["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    print(f"{span['font']} {span['size']}: {span['text']}")
```

### Heading Detection via Font Size (PyMuPDF)

```python
import fitz
from collections import Counter

doc = fitz.open("document.pdf")

# Find the most common font size (body text)
sizes = Counter()
for page in doc:
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    sizes[round(span["size"], 1)] += len(span["text"])

body_size = sizes.most_common(1)[0][0]

# Anything larger than body size is likely a heading
for page in doc:
    for block in page.get_text("dict", sort=True)["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["size"] > body_size + 1:
                        print(f"HEADING: {span['text']}")
```

### Table-to-Natural-Language for RAG

```python
import pdfplumber

with pdfplumber.open("tables.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            header = table[0]
            for row in table[1:]:
                # Convert each row to a sentence
                parts = [f"{col}: {val}" for col, val in zip(header, row) if val]
                sentence = "Record: " + "; ".join(parts) + "."
                # This sentence can be embedded and retrieved via vector search
                print(sentence)
```

## Chunking Strategies for PDFs

The `unstructured_documents.shared.chunking` module provides four strategies. Here is how they apply to PDF content:

| Strategy | How It Works | Best For PDFs |
|----------|-------------|---------------|
| **Character chunking** | Fixed-size windows with overlap | Quick baseline, uniform chunk sizes |
| **Sentence chunking** | Split on sentence boundaries | Body-heavy documents, narrative text |
| **Recursive split** | Try paragraph > newline > sentence > character | General purpose, respects structure |
| **Heading-aware** | Split on detected headings | Structured documents with clear sections |

For PDFs, the recommended approach is:

1. **Extract text** with PyMuPDF or pdfplumber
2. **Detect headings** using font-size analysis (PyMuPDF dict mode)
3. **Insert markdown-style headings** into the extracted text
4. **Apply heading-aware chunking** for section-level passages
5. **Extract tables separately** with pdfplumber and convert to natural language
6. **Combine** text chunks and table passages into the final chunk set

```python
# Example: heading-aware chunking with PyMuPDF
import fitz
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from unstructured_documents.shared.chunking import chunk_by_headings, preview_chunks

doc = fitz.open("document.pdf")
# ... (detect headings, insert markdown markers) ...
# text_with_headings = "# Section 1\nContent...\n# Section 2\n..."
# chunks = chunk_by_headings(text_with_headings)
# preview_chunks(chunks)
```

## Common Pitfalls

### 1. Encoding Issues
Some PDFs use custom fonts that map glyph IDs to non-standard Unicode points. If you see garbled characters, try a different extraction library -- PyMuPDF handles edge cases better than most.

### 2. Scanned PDFs Producing Empty Text
If `page.extract_text()` returns an empty string, the PDF is likely image-based. Check with PyMuPDF:
```python
import fitz
doc = fitz.open("document.pdf")
page = doc[0]
text = page.get_text()
if not text.strip():
    print("This PDF is likely scanned -- use OCR")
```

### 3. Multi-Column Layout Interleaving
Without layout analysis, columns get merged left-to-right per line rather than top-to-bottom per column. Use `sort=True` in PyMuPDF or `layout=True` in pdfplumber to mitigate this.

### 4. Headers and Footers Polluting Chunks
Page headers, footers, and page numbers appear on every page and add noise. Filter them by position:
```python
import fitz
doc = fitz.open("document.pdf")
page = doc[0]
blocks = page.get_text("blocks")
page_height = page.rect.height
# Remove blocks in the top/bottom 10% of the page
content_blocks = [
    b for b in blocks
    if b[1] > page_height * 0.1 and b[3] < page_height * 0.9
]
```

### 5. Table Data Lost in Text Extraction
Standard text extraction flattens tables into space-separated values that lose row/column relationships. Always use pdfplumber's `extract_tables()` for structured table data.

### 6. Hyphenated Words Across Lines
PDFs often hyphenate words at line breaks. Post-process by joining lines that end with a hyphen:
```python
import re
text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
```

## Tips for Production Use

1. **Classify first, extract second.** Check whether a PDF is born-digital or scanned before choosing an extraction method. A quick heuristic: if `page.get_text()` returns substantial text, it is born-digital.

2. **Combine methods.** Use PyMuPDF for fast text extraction and pdfplumber for table-heavy pages. Route scanned pages through OCR.

3. **Preserve provenance.** Attach page numbers, bounding boxes, and source file paths to each chunk. This enables citation and debugging.

4. **Handle errors gracefully.** Corrupted PDFs, password-protected files, and unusual encodings are common in the wild. Wrap extraction in try/except and log failures.

5. **Benchmark on your data.** Extraction quality varies dramatically across PDF types. Test all methods on a representative sample of your actual documents.

6. **Convert tables to natural language.** Raw table grids are poorly matched by vector search. Convert each row to a descriptive sentence for better retrieval.

7. **Remove boilerplate.** Filter out headers, footers, page numbers, disclaimers, and table-of-contents entries that add noise without value.

8. **Respect rate limits and memory.** For large PDF batches, process files sequentially or in small batches. PyMuPDF is the most memory-efficient option.
