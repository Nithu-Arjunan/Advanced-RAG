# Azure AI Document Intelligence for RAG

## What Is Azure Document Intelligence?

Azure AI Document Intelligence (formerly Azure Form Recognizer) is Microsoft's cloud-based AI service for extracting text, structure, key-value pairs, and tables from documents. It uses advanced machine learning models trained on millions of documents to deliver high-accuracy extraction across a wide range of document types including PDFs, images, Office files, and HTML.

The service is part of Azure AI Services and is accessed via REST API or the Python SDK. It is designed for production workloads at scale, with built-in support for structured output (including native Markdown conversion), making it particularly well-suited for RAG pipeline document preparation.

---

## Prebuilt Models Overview

Azure provides specialized prebuilt models optimized for different document types:

| Model | Use Case | Key Outputs |
|---|---|---|
| `prebuilt-read` | Pure text extraction, OCR | Text, languages, text styles, reading order |
| `prebuilt-layout` | Full document structure analysis | Text, tables, paragraphs with roles, figures, selection marks, barcodes |
| `prebuilt-document` | General key-value pair extraction | Key-value pairs, tables, entities |
| `prebuilt-invoice` | Invoice processing | Vendor name, invoice ID, dates, totals, line items, tax amounts |
| `prebuilt-receipt` | Receipt scanning | Merchant name, date, items, subtotal, tax, tip, total |
| `prebuilt-idDocument` | ID cards, passports, driver's licenses | Name, DOB, address, document number, expiration date |
| `prebuilt-businessCard` | Business card extraction | Name, company, phone, email, address |
| `prebuilt-healthInsuranceCard.us` | US health insurance cards | Member ID, group number, plan, provider |
| `prebuilt-tax.*` | US tax forms (W2, 1098, 1099) | Tax-specific fields per form type |

### What Each Model Extracts

- **prebuilt-read**: Optimized OCR engine supporting 130+ languages including handwritten text. Returns plain text content with detected languages and font styles (handwritten vs. printed). Fastest and cheapest model.
- **prebuilt-layout**: The most comprehensive structural model. Returns pages, lines, words, tables (with row/column structure and merged cells), paragraphs with semantic roles, figures with captions, selection marks (checkboxes), and barcodes/formulas.
- **prebuilt-document**: Extends layout with automatic key-value pair detection. Useful for forms and structured documents where field labels and values need to be associated.
- **prebuilt-invoice / prebuilt-receipt / prebuilt-idDocument**: Domain-specific models that return strongly typed fields with high accuracy for their target document types. These models understand the semantics of the document, not just its structure.

---

## Authentication

### API Key + Endpoint

The primary authentication method uses an API key and endpoint URL from your Azure Document Intelligence resource:

```python
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

client = DocumentIntelligenceClient(
    endpoint="https://<your-resource>.cognitiveservices.azure.com/",
    credential=AzureKeyCredential("<your-api-key>")
)
```

### Azure Active Directory (Azure AD)

For production environments, Azure AD (Entra ID) authentication is recommended:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

client = DocumentIntelligenceClient(
    endpoint="https://<your-resource>.cognitiveservices.azure.com/",
    credential=DefaultAzureCredential()
)
```

---

## Python SDK

Install the SDK:

```bash
uv pip install azure-ai-documentintelligence
```

### Key Classes

| Class | Description |
|---|---|
| `DocumentIntelligenceClient` | Main client for analyzing documents. Call `begin_analyze_document()` with a model ID. |
| `AnalyzeResult` | Top-level result object containing all extracted data. |
| `DocumentPage` | Per-page data: dimensions, lines, words, selection marks, barcodes. |
| `DocumentTable` | Extracted table with `row_count`, `column_count`, and a list of `DocumentTableCell` objects. |
| `DocumentTableCell` | Individual table cell with `row_index`, `column_index`, `content`, `kind` (columnHeader, rowHeader, content, stubHead), and optional `row_span`/`column_span` for merged cells. |
| `DocumentParagraph` | Text paragraph with `content`, `role`, and `bounding_regions`. |
| `DocumentKeyValuePair` | A detected key-value pair with `key`, `value`, and `confidence`. |
| `DocumentFigure` | Detected figure with `bounding_regions` and optional `caption`. |

---

## Output Formats

### Plain Text Content

By default, `result.content` returns the full document text in reading order as a plain string.

### Markdown Output

Azure can return the document content as structured Markdown, which is highly useful for RAG pipelines:

```python
poller = client.begin_analyze_document(
    "prebuilt-layout",
    body=file_bytes,
    output_content_format="markdown"
)
result = poller.result()
print(result.content)  # Clean Markdown with headings, tables, lists
```

The Markdown output preserves:
- Headings (`#`, `##`, `###`) from paragraph roles
- Tables in Markdown table syntax
- Lists (ordered and unordered)
- Text formatting where detectable

This is one of the most valuable features for RAG, as it provides chunking-ready structured text without additional post-processing.

---

## Table Extraction Details

Azure provides detailed table structure:

- **Row/column indices**: Every cell has explicit `row_index` and `column_index`
- **Merged cells**: `row_span` and `column_span` indicate cells spanning multiple rows or columns
- **Cell kinds**: `columnHeader`, `rowHeader`, `content`, `stubHead` classify each cell's role
- **Bounding regions**: Exact coordinates for each table and cell on the page
- **Content**: Text content of each cell, already OCR-processed

---

## Figure Detection

The `prebuilt-layout` model detects figures (images, charts, diagrams) within documents:

- `bounding_regions`: Coordinates locating the figure on the page
- `caption`: Associated caption text, if present
- `elements`: References to related content elements

Figures are not extracted as images by default, but their location and captions are identified for metadata purposes.

---

## Paragraph Roles

Paragraphs are classified with semantic roles:

| Role | Description |
|---|---|
| `title` | Document title |
| `sectionHeading` | Section or subsection heading |
| `pageHeader` | Running header at top of page |
| `pageFooter` | Running footer at bottom of page |
| `footnote` | Footnote text |
| `pageNumber` | Page number |
| `formulaBlock` | Mathematical formula |
| (none) | Regular body text |

These roles enable intelligent chunking -- for example, splitting on `sectionHeading` paragraphs or filtering out `pageHeader`/`pageFooter` content.

---

## OCR Capabilities

- **130+ languages** supported for printed text
- **Handwriting detection** for English and several other languages
- **Style detection**: Identifies whether text spans are handwritten or printed
- **Reading order**: Reconstructs natural reading order across complex layouts (multi-column, mixed content)
- **High accuracy**: Trained on millions of documents, consistently ranks among the most accurate OCR services

---

## Pricing Overview

| Tier | Pages/Month | Cost |
|---|---|---|
| Free (F0) | 500 | $0 |
| prebuilt-read | Pay-as-you-go | $0.001/page |
| prebuilt-layout | Pay-as-you-go | $0.01/page |
| prebuilt-invoice/receipt | Pay-as-you-go | $0.01/page |
| prebuilt-idDocument | Pay-as-you-go | $0.01/page |
| Custom models (training) | Pay-as-you-go | $0.05/page |
| Custom models (analysis) | Pay-as-you-go | $0.015/page |

The free tier (500 pages/month) is sufficient for development and testing.

---

## When to Use Azure Document Intelligence

**Best suited for:**
- Production RAG pipelines at scale requiring high accuracy
- Invoice, receipt, and ID document processing with structured field extraction
- Complex layouts with tables, multi-column text, figures, and mixed content
- Documents requiring OCR (scanned PDFs, images, handwriting)
- Enterprise environments already using Azure cloud services
- Applications needing Markdown output for downstream processing

**Not ideal for:**
- Simple text-only PDFs (native Python libraries like PyMuPDF are faster and free)
- Offline or air-gapped environments (cloud service requires internet)
- Cost-sensitive projects processing millions of pages
- Projects requiring full data sovereignty (documents are sent to Azure cloud)

---

## Pros and Cons

### Pros
- **Highest accuracy** among document extraction services, especially for complex layouts
- **Specialized prebuilt models** for invoices, receipts, IDs with strongly typed field extraction
- **Cloud-scalable** -- handles thousands of documents without infrastructure management
- **Native Markdown output** -- ideal for RAG pipelines, reduces post-processing
- **Handwriting support** -- detects and extracts handwritten text
- **Table structure preservation** -- row/column indices, merged cells, cell roles
- **130+ language OCR** with automatic language detection
- **Figure and caption detection** for comprehensive document understanding

### Cons
- **Requires Azure subscription** -- not available without a cloud account
- **Not free at scale** -- costs accumulate at high volumes ($0.01/page for layout)
- **Data sent to cloud** -- documents are transmitted to Microsoft servers for processing
- **API latency** -- network round-trip adds processing time vs. local libraries
- **No offline mode** -- requires internet connectivity
- **Vendor lock-in** -- API and SDK are Azure-specific

---

## Comparison with Open-Source Alternatives

| Feature | Azure Doc Intelligence | PyMuPDF / pdfplumber | Unstructured.io | Docling |
|---|---|---|---|---|
| Accuracy (complex layouts) | Highest | Moderate | Good | Good |
| Table extraction | Excellent (structured) | Good (pdfplumber) | Good | Good |
| OCR (scanned docs) | Built-in, 130+ langs | Requires Tesseract | Requires Tesseract | Built-in |
| Handwriting | Yes | No | No | Limited |
| Markdown output | Native | Manual | Yes | Yes |
| Invoice/Receipt fields | Yes (prebuilt models) | No | No | No |
| Cost | $0.001-0.01/page | Free | Free (open-source) | Free |
| Offline capable | No | Yes | Yes | Yes |
| Setup complexity | Azure account required | uv pip install | uv pip install | uv pip install |
| Scalability | Cloud-native | Single machine | Single machine | Single machine |

---

## Scripts in This Module

| Script | Description |
|---|---|
| `01_layout_extraction.py` | Layout extraction with prebuilt-layout model: pages, tables, paragraphs, and Markdown output |
| `02_prebuilt_models.py` | Overview of prebuilt models: read, document, invoice, with comparison guide |
| `03_table_and_figure_extraction.py` | Focused table extraction, grid reconstruction, and conversion to Markdown/natural language for RAG |
| `04_rag_pipeline_example.py` | End-to-end RAG preparation pipeline: analyze, extract, chunk, and prepare for embedding |

All scripts gracefully handle missing Azure credentials by displaying setup instructions and example code, so they can be reviewed and understood without an active Azure subscription.
