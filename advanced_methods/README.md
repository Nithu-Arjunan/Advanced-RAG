# Advanced Document Parsing Methods for RAG

## Overview

This section covers **production-grade document parsing libraries** that go beyond basic Python parsing. These tools use AI models, cloud services, and advanced algorithms to convert complex documents into LLM-ready text with high accuracy.

> **Prerequisite**: If you're new to document parsing, start with the [unstructured_documents/](../unstructured_documents/) folder which covers fundamental parsing methods for each file type.

## Library Comparison Matrix

| Library | Type | Formats | Table Detection | OCR | Chunking | License | Cost |
|---------|------|---------|:-:|:-:|:-:|---------|------|
| [Docling](#01-docling) | Local | PDF, DOCX, PPTX, XLSX, HTML, images, audio | Yes (TableFormer) | Yes (5 engines) | Yes (2 strategies) | MIT | Free |
| [Unstructured.io](#02-unstructured-io) | Local/Cloud | 15+ formats | Yes (hi_res) | Yes | Yes (by_title) | Apache 2.0 | Free (OSS) |
| [Azure Doc Intelligence](#03-azure-document-intelligence) | Cloud | PDF, images, Office | Yes (best accuracy) | Yes (130+ langs) | No (DIY) | Proprietary | Free tier + pay |
| [LlamaParse](#04-llamaparse) | Cloud | PDF, DOCX, PPTX, XLSX, images | Yes (AI) | Yes | Via LlamaIndex | Proprietary | Free tier + pay |
| [Marker](#05-marker) | Local | PDF, images, Office, EPUB | Yes | Yes | Chunks format | GPL | Free (research) |
| [MegaParse](#06-megaparse) | Local/API | PDF, DOCX, PPTX, XLSX, CSV | Yes | Yes | No (DIY) | Apache 2.0 | Free |

## Decision Guide: Which Library to Use?

### By Use Case

| Scenario | Recommended | Why |
|----------|-------------|-----|
| **Privacy-sensitive data** | Docling, Marker | Fully local, no data leaves your machine |
| **Production at scale** | Azure Doc Intelligence | Cloud-scalable, highest accuracy, SLA |
| **Simplest API** | MegaParse | One function call: `megaparse.load(file)` |
| **Complex PDFs (charts, images)** | LlamaParse, MegaParse Vision | AI-powered visual understanding |
| **Multi-format pipeline** | Unstructured.io, Docling | Widest format support, typed elements |
| **PDF to Markdown** | Marker | Purpose-built, excellent quality |
| **Invoice/receipt processing** | Azure Doc Intelligence | Specialized prebuilt models |
| **LlamaIndex RAG pipeline** | LlamaParse, Docling | Native framework integration |
| **LangChain RAG pipeline** | Unstructured.io, Docling | Native loaders available |
| **Budget-constrained** | Docling, Marker | Free, open-source, runs locally |
| **Best table extraction** | Azure Doc Intelligence | Structured table output with cell types |

### By Document Complexity

```
Simple text PDFs     -> Basic parsers (pypdf, pdfplumber) or Docling
Structured documents -> Unstructured.io or Docling
Complex layouts      -> Marker or Azure Doc Intelligence
Charts & diagrams    -> LlamaParse (agentic) or MegaParse Vision
Scanned documents    -> Azure Doc Intelligence or Docling (with OCR)
Invoices/receipts    -> Azure Doc Intelligence (prebuilt models)
Mixed format batch   -> Unstructured.io or Docling
```

## Quick Start

### Install Any Library

```bash
# Docling (IBM, local, MIT)
pip install docling

# Unstructured.io (local, Apache 2.0)
pip install "unstructured[all-docs]"

# Azure Document Intelligence (cloud, proprietary)
pip install azure-ai-documentintelligence

# LlamaParse (cloud, proprietary)
pip install llama-parse

# Marker (local, GPL)
pip install marker-pdf

# MegaParse (local, Apache 2.0)
pip install megaparse
```

### Parse a PDF with Each Library

```python
# --- Docling ---
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
result = converter.convert("document.pdf")
print(result.document.export_to_markdown())

# --- Unstructured.io ---
from unstructured.partition.auto import partition
elements = partition(filename="document.pdf")
print("\n".join([str(el) for el in elements]))

# --- Azure Document Intelligence ---
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
with open("document.pdf", "rb") as f:
    poller = client.begin_analyze_document("prebuilt-layout", body=f)
result = poller.result()

# --- LlamaParse ---
from llama_parse import LlamaParse
parser = LlamaParse(api_key="llx-...", result_type="markdown")
documents = parser.load_data("document.pdf")

# --- Marker ---
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("document.pdf")
text, metadata, images = text_from_rendered(rendered)

# --- MegaParse ---
from megaparse import MegaParse
megaparse = MegaParse()
response = megaparse.load("document.pdf")
```

## Folder Structure

```
advanced_methods/
|-- README.md                      <- This file
|-- 01_docling/                    <- IBM Docling (local, multi-format)
|   |-- 01_basic_conversion.py
|   |-- 02_pdf_advanced.py
|   |-- 03_chunking.py
|   |-- 04_integrations.py
|   |-- README.md
|-- 02_unstructured_io/            <- Unstructured.io (element-based parsing)
|   |-- 01_auto_partition.py
|   |-- 02_pdf_strategies.py
|   |-- 03_specific_partitioners.py
|   |-- 04_chunking_and_export.py
|   |-- README.md
|-- 03_azure_doc_intelligence/     <- Azure AI (cloud, highest accuracy)
|   |-- 01_layout_extraction.py
|   |-- 02_prebuilt_models.py
|   |-- 03_table_and_figure_extraction.py
|   |-- 04_rag_pipeline_example.py
|   |-- README.md
|-- 04_llamaparse/                 <- LlamaParse (cloud, GenAI-native)
|   |-- 01_basic_parsing.py
|   |-- 02_llamaindex_integration.py
|   |-- 03_parsing_tiers.py
|   |-- README.md
|-- 05_marker/                     <- Marker (local, PDF-to-Markdown)
|   |-- 01_basic_conversion.py
|   |-- 02_output_formats.py
|   |-- 03_specialized_converters.py
|   |-- README.md
|-- 06_megaparse/                  <- MegaParse (simplest API, vision mode)
|   |-- 01_basic_parsing.py
|   |-- 02_vision_parsing.py
|   |-- 03_rag_preparation.py
|   |-- README.md
```

## Architecture Comparison

### Local Processing Pipeline
```
Document -> [Layout Detection] -> [OCR] -> [Table Recognition] -> [Post-processing] -> Output
             Docling: DocLayNet     Docling: EasyOCR/Tesseract    Docling: TableFormer
             Marker: Custom YOLO    Marker: Surya OCR              Marker: Table model
             Unstructured: YOLOX    Unstructured: Tesseract        Unstructured: detectron2
```

### Cloud Processing Pipeline
```
Document -> [Upload] -> [AI Analysis] -> [Structured Result] -> Output
             Azure: REST API          Azure: Layout/Read models
             LlamaParse: REST API     LlamaParse: Multimodal AI
             MegaParse Vision: LLM    MegaParse: GPT-4o/Claude
```

## Performance Considerations

| Library | Cold Start | Per-Page Speed | GPU Benefit | Memory |
|---------|-----------|---------------|:-:|--------|
| Docling | ~10s (model load) | 1-5s | Yes | ~2GB |
| Unstructured (hi_res) | ~15s (model load) | 2-8s | Yes | ~3GB |
| Unstructured (fast) | <1s | <0.5s | No | ~200MB |
| Azure Doc Intelligence | N/A (cloud) | 1-3s (API) | N/A | N/A |
| LlamaParse | N/A (cloud) | 2-10s (API) | N/A | N/A |
| Marker | ~15s (model load) | 1-3s (GPU) | Yes (5-10x) | ~2GB |
| MegaParse | <1s | <1s (standard) | No | ~500MB |
| MegaParse Vision | N/A (API) | 5-15s (API) | N/A | N/A |

## Related Resources

- [Unstructured Documents Guide](../unstructured_documents/) - Fundamental parsing methods
- [RAG Data Sources Presentation](../unstructured_documents/RAG_Data_Sources_Presentation.pptx) - 75-slide overview
