# 03 - PPTX (PowerPoint) Parsing for RAG

## Overview

PowerPoint files (`.pptx`) use the Office Open XML format -- a ZIP archive containing XML files that describe slides, shapes, text, tables, images, and metadata.  Understanding this structure is essential for extracting text reliably.

### PPTX Internal Structure

```
presentation.pptx (ZIP)
├── [Content_Types].xml
├── _rels/
├── docProps/              # Document properties (author, title, dates)
├── ppt/
│   ├── presentation.xml   # Slide ordering, slide size
│   ├── slides/
│   │   ├── slide1.xml     # Each slide's shapes and content
│   │   ├── slide2.xml
│   │   └── ...
│   ├── slideLayouts/      # Layout templates
│   ├── slideMasters/      # Master slide definitions
│   ├── notesSlides/       # Speaker notes (one per slide, if present)
│   ├── media/             # Embedded images, audio, video
│   └── tables/            # Table definitions (inline in slide XML)
```

Key concepts:

| Concept         | Description |
|-----------------|-------------|
| **Slide**       | A single page in the presentation |
| **Shape**       | Any object on a slide -- text box, placeholder, table, image, chart, group |
| **Text Frame**  | Container for paragraphs inside a shape |
| **Placeholder** | A shape pre-defined by the slide layout (title, body, footer, slide number) |
| **Group Shape** | A shape that contains other shapes as children |
| **Notes Slide** | A separate XML file holding speaker notes for a slide |

## Why PPTX is Tricky for RAG

Presentations pose unique challenges compared to documents like PDF or DOCX:

1. **Sparse, visual content** -- Slides favour short bullet points and keywords over full sentences.  The text alone may lack the context needed for accurate retrieval.

2. **Speaker notes carry context** -- The real explanation often lives in the speaker notes, not on the slide itself.  Ignoring notes throws away critical information.

3. **Tables and charts** -- Tabular data is stored as shape objects, not as running text.  Charts are embedded images with underlying data in XML -- extracting the data requires extra work.

4. **Grouped shapes** -- Designers frequently group text boxes, icons, and callouts.  A naive extractor that only checks top-level shapes will miss text inside groups.

5. **Layout-driven positioning** -- Text location depends on slide layouts and masters.  The same placeholder index can mean "title" in one layout and "body" in another.

6. **Images with text** -- Diagrams, screenshots, and infographics contain text that is invisible to text-only extraction.  OCR is needed to capture it.

7. **Non-linear reading order** -- Unlike a document, slides have no inherent paragraph flow.  Shape z-order and position are the only hints.

## Scripts in This Module

| Script | What it does |
|--------|-------------|
| `sample_docs/generate_samples.py` | Generates two sample PPTX files for testing |
| `01_python_pptx_extraction.py` | Basic text extraction from all shape types, tables, and notes |
| `02_slide_structured_extraction.py` | Structured per-slide extraction with RAG-ready chunking |

### Running

```bash
# 1. Generate sample files
uv run python unstructured_documents/03_pptx/sample_docs/generate_samples.py

# 2. Basic extraction
uv run python unstructured_documents/03_pptx/01_python_pptx_extraction.py

# 3. Structured extraction
uv run python unstructured_documents/03_pptx/02_slide_structured_extraction.py
```

## Method Comparison

### Method 1: Basic Text Extraction (`01_python_pptx_extraction.py`)

Iterates over every shape on every slide and pulls out raw text.

**Strengths:**
- Simple to implement
- Handles all shape types (text frames, tables, groups)
- Good for full-text search or keyword extraction

**Weaknesses:**
- Loses slide structure -- all text is flattened
- No distinction between title, body, and table content
- Harder to attribute a retrieved chunk back to a specific slide

### Method 2: Structured Slide Extraction (`02_slide_structured_extraction.py`)

Parses each slide into a structured dictionary with separate fields for title, body, tables, and notes.

**Strengths:**
- Preserves slide-level structure and metadata
- Tables are kept as structured data (can be rendered as text or kept as rows)
- Speaker notes are captured alongside slide content
- Produces richer metadata for retrieval (slide number, title, flags)

**Weaknesses:**
- Slightly more complex code
- Title detection depends on placeholder conventions (may fail on custom layouts)

### When to Use Each

| Scenario | Recommended method |
|----------|--------------------|
| Quick search over presentation content | Basic extraction |
| RAG pipeline with source attribution | Structured extraction |
| Presentations with heavy speaker notes | Structured (notes as separate field) |
| Heterogeneous slide layouts | Structured (handles edge cases better) |
| Simple keyword / topic extraction | Basic extraction |

## Chunking Strategies for Presentations

### Strategy 1: One Chunk per Slide

Each slide becomes a single chunk.  This is the most natural unit for presentations.

```
Chunk = Title + Body text + Table text + Speaker notes
Metadata = {slide_number, title, has_table, has_notes}
```

**Pros:** Preserves slide context, easy source attribution, natural boundary.
**Cons:** Chunk sizes vary widely (a title slide has ~10 words; a dense data slide may have 500+).

### Strategy 2: Merged Text with Sentence Chunking

Concatenate all slide text into one document, then apply sentence-based or recursive chunking.

**Pros:** Uniform chunk sizes, works well with embedding models that expect consistent length.
**Cons:** Loses slide boundaries, harder to attribute results to specific slides.

### Strategy 3: Hybrid

Use slide-per-chunk as the primary unit.  For slides that exceed a size threshold, split further with sentence chunking.  For very short slides (titles, transitions), merge with the next slide.

This is generally the best approach for production RAG systems.

## Common Pitfalls

### 1. Missing Group Shape Text

Group shapes contain child shapes that are invisible to a top-level iteration:

```python
# WRONG: misses text inside groups
for shape in slide.shapes:
    if shape.has_text_frame:
        print(shape.text)

# RIGHT: recurse into groups
def get_text(shape):
    if shape.shape_type == 6:  # GROUP
        for child in shape.shapes:
            yield from get_text(child)
    elif shape.has_text_frame:
        yield shape.text
```

### 2. Ignoring Speaker Notes

Notes are stored on a separate "notes slide" object, not on the main slide:

```python
if slide.has_notes_slide:
    notes = slide.notes_slide.notes_text_frame.text
```

### 3. Tables Treated as Plain Text

Calling `shape.text` on a table shape returns cell text concatenated without structure.  Always use `shape.table` to iterate rows and cells.

### 4. Embedded Objects and Charts

Charts (`shape.has_chart`) have underlying data in `shape.chart`, but extracting it requires navigating the chart's data model.  For RAG, consider using the chart title + any visible labels as a text proxy.

### 5. Images with Text

Shapes with `shape.shape_type == 13` (Picture) are images.  Any text rendered inside the image is invisible to python-pptx.  Use OCR (Tesseract, EasyOCR) on extracted images when visual text matters.

### 6. Slide Ordering

`prs.slides` returns slides in presentation order, but if slides have been reordered in PowerPoint, the internal XML numbering may not match.  Always use enumeration index, not the XML slide number.

## Tips for Production

1. **Always extract speaker notes** -- In many organizations, the notes are the most information-dense part of a presentation.  Include them in every chunk.

2. **Preserve slide number in metadata** -- Users expect to find "slide 12" when they search.  Store slide number alongside each chunk.

3. **Handle images** -- Extract images with `shape.image.blob`, save to disk, and run OCR if visual text is important.  Store image references in metadata.

4. **Detect and skip master/layout text** -- Footers, slide numbers, and copyright notices from master slides add noise.  Filter them out by checking `shape.placeholder_format.idx` for known layout placeholders (idx 10 = date, 11 = slide number, 12 = footer).

5. **Table rendering** -- For RAG, render tables as "Header: Value" pairs per row rather than raw grid format.  This gives embedding models better semantic signal.

6. **Metadata enrichment** -- Extract document properties (`prs.core_properties`) for author, title, creation date.  These make excellent metadata filters in a vector store.

7. **Slide thumbnails** -- For user-facing applications, generate slide thumbnail images so users can visually confirm which slide a retrieved chunk came from.

8. **Batch processing** -- For large slide decks (100+ slides), stream extraction rather than loading everything into memory at once.

## Library Reference

| Library | PyPI | Purpose |
|---------|------|---------|
| [python-pptx](https://python-pptx.readthedocs.io/) | `python-pptx>=1.0` | Read/write PPTX, full shape/slide/table/notes access |
