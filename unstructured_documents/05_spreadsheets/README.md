# Spreadsheet Parsing for RAG (XLSX / CSV)

## Overview

Spreadsheets are semi-structured data sources that present unique challenges for RAG. Unlike text documents, spreadsheets contain **tabular data** where meaning comes from the relationship between cells, columns, and rows. The key challenge is converting this tabular structure into text that retains meaning for embedding and retrieval.

## Method Comparison

| Library | File Types | Dependencies | Memory Usage | Type Inference | Best For |
|---------|-----------|--------------|-------------|----------------|----------|
| **openpyxl** | .xlsx only | Lightweight | Moderate | Basic | Cell-level access, formatting, merged cells |
| **pandas** | .xlsx, .csv, .xls, + more | Heavy (numpy) | Higher | Excellent | Data analysis, aggregation, large datasets |
| **csv (stdlib)** | .csv only | None | Minimal | None (all strings) | Simple CSV, zero dependencies, streaming |

## When to Use Each Method

### openpyxl (`01_openpyxl_extraction.py`)
- You need access to **cell formatting** (bold, colors, merged cells)
- You're working with **multi-sheet workbooks** and need sheet-level control
- You need to handle **merged cells** or **formulas**
- You want **moderate dependencies** without pulling in pandas/numpy

### pandas (`02_pandas_extraction.py`)
- You need **data analysis** alongside extraction (filtering, aggregation, statistics)
- You're processing **large datasets** and need efficient operations
- You want **automatic type inference** (numbers, dates, etc.)
- You need to read **multiple file formats** with one API

### csv module (`03_csv_extraction.py`)
- You have **simple CSV files** with no complex features
- You want **zero external dependencies**
- You need to **stream large files** row-by-row (low memory)
- You're building a **lightweight pipeline** without pandas

## Key RAG Strategy: Converting Tables to Text

The most critical decision for spreadsheet RAG is **how to represent tabular data as text**. Raw cell dumps create poor embeddings. Here are the approaches demonstrated:

### 1. Natural Language Descriptions (Recommended)
Convert each row to a descriptive sentence. Best for retrieval quality.
```
- Name: Alice Johnson; Department: Engineering; Title: Senior Developer; Salary: 125000
```

### 2. Row-Based Chunks
Group N rows per chunk with headers repeated. Good balance of context and chunk size.
```
[Employee Directory - rows 1 to 5]
Columns: ID, Name, Department, Title
- ID: 101; Name: Alice Johnson; Department: Engineering; Title: Senior Developer
```

### 3. Markdown Tables
Convert to markdown table format. Good when preserving visual structure matters.

### 4. Summary + Detail
Create a summary chunk (column names, row count, statistics) plus individual row chunks. Best for large spreadsheets.

## Chunking Strategies for Spreadsheets

| Strategy | When to Use | Chunk Size |
|----------|-------------|------------|
| **One chunk per sheet** | Small sheets (< 20 rows) | Variable |
| **N rows per chunk** | Medium sheets, uniform data | Fixed row count |
| **Row as sentence** | Each row is a meaningful entity | One row per chunk |
| **Summary + rows** | Large sheets, need overview + detail | Mixed |

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Merged cells return `None` for non-primary cells | Use openpyxl's `merged_cells` attribute to detect and handle merges |
| Formulas return formula text instead of values | Use `data_only=True` in openpyxl (values from last save) |
| CSV encoding issues (non-UTF8) | Detect encoding with `chardet`, specify `encoding` parameter |
| Empty rows/columns add noise | Filter out rows where all values are None/empty |
| Headers missing or in wrong row | Inspect first few rows before assuming row 0 is headers |
| Large files exhaust memory | Use pandas `chunksize` parameter or csv's row-by-row streaming |

## Tips for Production

1. **Always include column headers in chunks** — without headers, "125000" is meaningless; with headers, "Salary: 125000" is retrievable
2. **Convert numbers to descriptions** — "$125,000 annual salary" embeds better than "125000"
3. **Handle multi-sheet workbooks** — treat each sheet as a separate document with its own metadata
4. **Add sheet-level summaries** — a summary chunk helps retrieval when users ask about the overall data
5. **Filter empty and header rows** — many spreadsheets have blank rows, merged title cells, or multi-row headers
6. **Preserve data types** — dates, currencies, and percentages should be formatted meaningfully in text

## Files in This Module

| File | Description |
|------|-------------|
| `sample_docs/generate_samples.py` | Generates XLSX (multi-sheet) and CSV files |
| `01_openpyxl_extraction.py` | Cell-level extraction with formatting awareness |
| `02_pandas_extraction.py` | DataFrame-based extraction with analysis |
| `03_csv_extraction.py` | Lightweight CSV parsing with stdlib |
