# Module 02 — DOCX Parsing for RAG

## Overview

A `.docx` file (Office Open XML) is **not** a single binary blob — it is a **ZIP archive** containing a collection of XML files, images, and metadata. The main document body lives in `word/document.xml`, styles are defined in `word/styles.xml`, and relationships (e.g. hyperlinks, images) are tracked in `word/_rels/document.xml.rels`.

This is fundamentally different from PDF:

| Aspect              | DOCX                                      | PDF                                       |
|---------------------|-------------------------------------------|-------------------------------------------|
| Internal format     | ZIP of XML files                          | Binary with text operators                |
| Text flow           | Logical paragraph order                   | Positioned glyphs — reading order is not guaranteed |
| Styles / semantics  | Named styles (Heading 1, Normal, Quote …) | No semantic tags (unless Tagged PDF)      |
| Tables              | Explicit `<w:tbl>` XML elements           | Visually arranged lines — no table model  |
| Image references    | Embedded or linked in the ZIP             | Embedded streams                          |

**Bottom line:** DOCX is far easier to parse reliably than PDF because the text is stored in reading order with semantic style names.

---

## Scripts in This Module

| # | Script                          | Library        | What it demonstrates                                |
|---|---------------------------------|----------------|-----------------------------------------------------|
| 0 | `sample_docs/generate_samples.py` | python-docx  | Generates three sample DOCX files for testing       |
| 1 | `01_python_docx_extraction.py`  | python-docx    | Full-featured extraction: paragraphs, styles, tables, heading hierarchy, chunking |
| 2 | `02_mammoth_extraction.py`      | mammoth        | Semantic conversion to HTML and markdown, comparison, chunking |
| 3 | `03_docx2txt_extraction.py`     | docx2txt       | Simplest plain-text extraction, preservation analysis, character chunking |

Run any script from the project root:

```bash
uv run python unstructured_documents/02_docx/sample_docs/generate_samples.py
uv run python unstructured_documents/02_docx/01_python_docx_extraction.py
uv run python unstructured_documents/02_docx/02_mammoth_extraction.py
uv run python unstructured_documents/02_docx/03_docx2txt_extraction.py
```

---

## Method Comparison

| Feature              | python-docx | mammoth  | docx2txt |
|----------------------|:-----------:|:--------:|:--------:|
| Preserves styles     | Yes         | Mapped to HTML/MD | No |
| Table support        | Full (rows, cols, merged cells) | Basic (HTML `<table>`) | Tab-separated text |
| Image extraction     | Yes (via relationships) | Yes (via callbacks) | Yes (to a directory) |
| Markdown output      | Manual conversion needed | Built-in | No |
| HTML output          | Manual conversion needed | Built-in | No |
| Heading hierarchy    | Via `style.name` | Via `<h1>`-`<h6>` | Not available |
| Run-level formatting | Yes (bold, italic, font) | Mapped to `<strong>`, `<em>` | No |
| Speed                | Fast | Fast | Fastest |
| Best for             | Full control, table extraction, metadata | Clean HTML/MD for downstream NLP | Quick text dump, search indexing |

---

## When to Use Each Method

### python-docx — "I need full control"

Choose python-docx when you need:
- Access to named styles (Heading 1, Normal, Quote, etc.)
- Run-level formatting (which words are bold or italic)
- Structured table extraction (headers, rows, merged cells)
- To build a heading-based document hierarchy
- To modify or generate DOCX files

### mammoth — "I need clean HTML or markdown"

Choose mammoth when you need:
- A one-step conversion to semantic HTML or markdown
- Output that is directly usable by a RAG chunker
- A format suitable for rendering in a web app
- Minimal boilerplate — mammoth handles the style mapping for you

### docx2txt — "I just need the text"

Choose docx2txt when you need:
- The fastest possible plain-text extraction
- Text for full-text search or keyword indexing
- No interest in structure, formatting, or styles
- A one-liner with zero configuration

---

## Key Concepts: DOCX Internals

### Paragraphs

Every block of text in a DOCX is a **paragraph** (`<w:p>`). Paragraphs have a **style** that determines their role in the document (Heading 1, Normal, List Bullet, etc.).

### Runs

A paragraph is composed of one or more **runs** (`<w:r>`). A run is a contiguous span of text that shares the same inline formatting (font, size, bold, italic, colour). For example, the sentence "This is **important** text" would be three runs: `"This is "`, `"important"` (bold), and `" text"`.

### Styles

DOCX styles are named formatting presets. They fall into two categories:
- **Paragraph styles** — applied to the whole paragraph (e.g. Heading 1, Normal, Quote)
- **Character styles** — applied to a run within a paragraph (e.g. Strong, Emphasis)

For RAG, paragraph styles are the most valuable because they tell you the *semantic role* of each block.

### Tables

Tables in DOCX are explicit XML structures (`<w:tbl>`) with rows (`<w:tr>`) and cells (`<w:tc>`). Each cell can contain paragraphs, images, or even nested tables. python-docx gives you direct access to this structure; mammoth converts it to HTML `<table>` elements; docx2txt flattens it to tab-separated text.

---

## Chunking Strategies for DOCX

### 1. Heading-based chunking (recommended)

Split the document at heading boundaries. Each section (heading + its body text) becomes one chunk. This preserves the author's intended structure and produces semantically meaningful chunks.

**How:** Use python-docx to detect `Heading 1/2/3` styles, or use mammoth to convert to markdown and split on `# / ## / ###` markers.

### 2. Paragraph-based chunking

Group N consecutive paragraphs into each chunk. Simpler than heading-based but may split across logical sections.

### 3. Character / sentence / recursive chunking

When the document has no headings (e.g. a plain letter), fall back to character-based, sentence-based, or recursive splitting. docx2txt output works well with these strategies since there are no structural markers to exploit.

### Decision flow

```
Does the document have headings?
  ├─ YES -> Use heading-based chunking (python-docx or mammoth)
  └─ NO  -> Does it have paragraphs of varying length?
              ├─ YES -> Use recursive splitting
              └─ NO  -> Use character-based splitting with overlap
```

---

## Common Pitfalls

### Nested tables
Some DOCX files (especially those exported from HTML or other tools) contain tables nested inside table cells. python-docx handles this, but you need to recursively walk cell contents. mammoth and docx2txt may flatten them.

### Tracked changes (revisions)
If "Track Changes" was enabled, the XML contains both the original and revised text. python-docx reads the *current* (accepted) text by default, but deleted runs may still appear in the raw XML. Always accept/reject changes before processing if accuracy is critical.

### Comments and annotations
Comments are stored separately (`word/comments.xml`) and linked to text ranges via anchors. None of the three libraries expose comments directly — you would need to parse the XML manually or use a different tool.

### Headers, footers, and footnotes
These live in separate XML files (`word/header1.xml`, `word/footer1.xml`, `word/footnotes.xml`). python-docx can access headers and footers via `document.sections`. docx2txt includes header/footer text. mammoth may or may not include them depending on the version.

### Merged cells in tables
Horizontally or vertically merged cells can cause columns to appear duplicated in python-docx (the same cell object is returned for each grid position it spans). Check for `cell._tc` identity to detect merged cells.

### Encoding and special characters
DOCX files are UTF-8 internally, so encoding is rarely a problem. However, some documents use special Unicode characters (e.g. non-breaking spaces, soft hyphens, smart quotes) that may need normalisation before embedding.

---

## Tips for Production Use

1. **Always prefer heading-based chunking** when the document has a heading structure. It produces the most meaningful chunks for retrieval.

2. **Include metadata in chunks.** When using python-docx, attach the heading text, heading level, and document filename to each chunk as metadata. This enables filtered retrieval (e.g. "find chunks from Section 3 of the Q3 report").

3. **Handle tables separately.** Tables are often better treated as structured data than as free text. Consider extracting tables into their own chunks with a "table" tag, or converting them to markdown tables for embedding.

4. **Normalise whitespace.** DOCX text can contain non-breaking spaces (`\xa0`), multiple consecutive spaces, and trailing whitespace. Strip and normalise before chunking.

5. **Validate with multiple documents.** Test your pipeline with documents from different authors and tools (Word, Google Docs export, LibreOffice). Style names and formatting conventions vary.

6. **Consider mammoth for web pipelines.** If your RAG system has a web frontend that needs to display source documents, mammoth's HTML output can be served directly with minimal CSS.

7. **Fall back gracefully.** Not all DOCX files have headings. Your pipeline should detect whether heading-based chunking is possible and fall back to recursive splitting if not.
