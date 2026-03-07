# Marker - Local AI-Powered Document Converter

## Overview

Marker is an open-source document conversion tool created by [Vik Paruchuri](https://github.com/VikParuchuri) at [datalab.to](https://www.datalab.to/). It converts documents to clean Markdown, JSON, HTML, or chunked output using a pipeline of specialized AI models that run locally on your machine. Unlike cloud-based parsers, Marker processes everything on-device, making it suitable for sensitive documents and offline workflows.

**Repository:** [https://github.com/VikParuchuri/marker](https://github.com/VikParuchuri/marker)

## Supported Formats

### Input

| Category   | Formats                          |
|------------|----------------------------------|
| Documents  | PDF, DOCX, EPUB                  |
| Slides     | PPTX                             |
| Sheets     | XLSX                             |
| Web        | HTML                             |
| Images     | PNG, JPG/JPEG, TIFF, BMP, WEBP   |

Note: DOCX, PPTX, and XLSX support requires `pip install marker-pdf[full]`.

### Output Formats

| Format     | Description                                          | Best For                            |
|------------|------------------------------------------------------|-------------------------------------|
| `markdown` | Clean Markdown with tables, LaTeX equations, code    | RAG text extraction, human reading  |
| `json`     | Tree structure: pages, blocks with types and coords  | Programmatic processing, layout analysis |
| `html`     | Rendered HTML with images, tables, math              | Web display, document preview       |
| `chunks`   | Flat list of top-level blocks with HTML per block    | Direct RAG ingestion, embedding pipelines |

## Architecture

Marker uses a pipeline of specialized AI models, each handling a different aspect of document understanding:

1. **Layout Detection** - Identifies text blocks, tables, figures, equations, headers, footers, and other structural elements on each page.
2. **OCR** - Recognizes text in scanned documents or image-based PDFs. Automatically activated when needed.
3. **Table Recognition** - Detects table structure (rows, columns, merged cells) and reconstructs tables in the output format.
4. **Equation Detection** - Identifies mathematical equations and converts them to LaTeX notation.
5. **Post-processing** - Removes headers/footers, determines reading order, merges blocks, and cleans up output.

Models are downloaded automatically on first use (~1.5GB total).

## Installation

```bash
# Basic installation (PDF and image support)
pip install marker-pdf

# Full installation (adds DOCX, PPTX, XLSX support)
pip install marker-pdf[full]
```

**Requirements:**
- Python 3.10+
- PyTorch (CPU or GPU)
- ~1.5GB disk space for model downloads (automatic on first run)

## Converters

Marker provides several converter classes for different use cases:

| Converter              | Purpose                                              |
|------------------------|------------------------------------------------------|
| `PdfConverter`         | General-purpose document conversion (default)        |
| `TableConverter`       | Extract only tables from documents                   |
| `OCRConverter`         | Force full OCR processing on entire document         |
| `ExtractionConverter`  | Structured data extraction using Pydantic schemas + LLM |

### PdfConverter (default)

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("document.pdf")
text, metadata, images = text_from_rendered(rendered)
```

### TableConverter

```python
from marker.converters.table import TableConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = TableConverter(artifact_dict=create_model_dict())
rendered = converter("document.pdf")
text, metadata, images = text_from_rendered(rendered)
# Output contains ONLY tables found in the document
```

### ExtractionConverter

```python
from marker.converters.extraction import ExtractionConverter
from marker.config.parser import ConfigParser
from pydantic import BaseModel

class InvoiceData(BaseModel):
    vendor_name: str
    total_amount: float

schema = InvoiceData.model_json_schema()
config_parser = ConfigParser({"page_schema": schema})

converter = ExtractionConverter(
    artifact_dict=create_model_dict(),
    config=config_parser.generate_config_dict(),
    llm_service=config_parser.get_llm_service(),
)
rendered = converter("invoice.pdf")
```

## Configuration Options

Configuration is passed via the `ConfigParser` class:

```python
from marker.config.parser import ConfigParser

config = {
    "output_format": "markdown",         # "markdown", "json", "html", "chunks"
    "page_range": "0-2,5,10-15",         # Specific pages (0-indexed)
    "force_ocr": False,                  # Force OCR on all pages
    "disable_image_extraction": False,   # Skip image extraction
    "use_llm": False,                    # Use LLM for enhanced accuracy
}

config_parser = ConfigParser(config)
converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
)
```

## CLI Usage

Marker includes command-line tools for quick conversion:

```bash
# Convert a single file
marker_single input.pdf --output_format markdown

# Batch convert a directory
marker /path/to/pdfs --output_dir /path/to/output --workers 4

# Launch the GUI
marker_gui
```

## GPU vs CPU Performance

| Setup          | Speed (approximate)           | Notes                              |
|----------------|-------------------------------|------------------------------------|
| NVIDIA GPU     | ~5-15 pages/second            | Best performance, CUDA required    |
| Apple Silicon  | ~2-5 pages/second             | MPS backend, good performance      |
| CPU only       | ~0.5-2 pages/second           | Functional but significantly slower |

GPU acceleration requires PyTorch with CUDA (NVIDIA) or MPS (Apple Silicon) support.

## Model Details

Marker downloads and uses the following specialized models:

| Model               | Purpose                              | Size (approx.) |
|----------------------|--------------------------------------|-----------------|
| Layout detection     | Page element classification          | ~300MB          |
| OCR                  | Text recognition in images/scans     | ~500MB          |
| Table structure      | Row/column/cell detection in tables  | ~300MB          |
| Equation recognition | Math equation to LaTeX conversion    | ~300MB          |

All models are cached locally after the first download.

## When to Use Marker

**Best suited for:**
- Local/offline document processing where data cannot leave your machine
- PDF-heavy workloads requiring high-quality Markdown output
- Documents with mathematical equations (LaTeX output)
- Batch processing large document collections
- Projects where you want to avoid recurring API costs

**Pros:**
- Runs entirely locally -- no data sent to external servers
- No API costs or usage limits
- Excellent Markdown output quality
- Handles equations with LaTeX conversion
- GPU-accelerated for fast processing
- Multiple output formats including RAG-optimized chunks
- Specialized converters (table-only, OCR-only, structured extraction)

**Cons:**
- Heavy model downloads on first run (~1.5GB)
- Requires PyTorch installation
- GPL license for open-source use; commercial use requires a paid license from [datalab.to](https://www.datalab.to/)
- Slower on CPU-only machines
- Less accurate than cloud AI services on highly complex visual layouts

## Licensing

Marker is released under the **GPL license** for research and personal use. **Commercial use requires a separate license** purchased from [datalab.to](https://www.datalab.to/). Review the license terms before deploying in production or commercial products.

## Scripts Overview

| Script                        | Description                                              |
|-------------------------------|----------------------------------------------------------|
| `01_basic_conversion.py`      | Basic PDF to Markdown conversion, custom configuration   |
| `02_output_formats.py`        | Overview and comparison of all four output formats        |
| `03_specialized_converters.py`| TableConverter, OCRConverter, ExtractionConverter demos   |

All scripts fall back to printing example code and documentation if `marker-pdf` is not installed.
