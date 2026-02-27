# Module 09: EPUB

## Overview

EPUB (Electronic Publication) is the most widely used open ebook format. Under the hood, an EPUB file is a **ZIP archive** containing XHTML documents, CSS stylesheets, images, fonts, and XML metadata. This structured format makes EPUB one of the best document types for RAG because the content is already organized into chapters with clear headings.

## EPUB File Structure

```
sample_book.epub (ZIP archive)
  ├── META-INF/
  │   └── container.xml          # Points to the root file
  ├── OEBPS/
  │   ├── content.opf            # Package document (metadata, manifest, spine)
  │   ├── toc.ncx                # Table of contents (EPUB 2)
  │   ├── nav.xhtml              # Navigation document (EPUB 3)
  │   ├── ch01.xhtml             # Chapter 1 content
  │   ├── ch02.xhtml             # Chapter 2 content
  │   ├── styles/                # CSS stylesheets
  │   └── images/                # Embedded images
  └── mimetype                   # Always "application/epub+zip"
```

## Why EPUB is Good for RAG

1. **Pre-structured chapters** - Content is already divided into logical sections
2. **Clean HTML** - Text is in XHTML, easy to parse with BeautifulSoup
3. **Rich metadata** - Title, author, language, publisher via Dublin Core
4. **Table of contents** - Navigation structure maps to document hierarchy
5. **No OCR needed** - Text is selectable (unlike scanned PDFs)
6. **Standard format** - Consistent structure across publishers

## Extraction Approaches

### 1. Chapter-by-Chapter (ebooklib + BeautifulSoup)
- Parse each XHTML document individually
- Extract headings, paragraphs, lists, tables
- Preserve chapter boundaries as natural chunk divisions

### 2. Full Text with Markdown Conversion
- Convert entire book to markdown-like format
- Apply heading-aware chunking
- Good for books with sub-sections within chapters

### 3. Metadata-Enriched Chunks
- Attach book metadata (title, author) to each chunk
- Include chapter heading in chunk metadata
- Enables filtered retrieval (e.g., "search only in Chapter 3")

## Chunking Strategies

| Strategy | Chunks | Best For |
|----------|--------|----------|
| **Chapter-per-chunk** | 1 per chapter | Short chapters, preserving context |
| **Heading-aware** | 1 per section | Books with sub-headings |
| **Recursive split** | Many (uniform size) | Long chapters, token-limited embeddings |
| **Sentence-based** | Many (variable) | When chapters lack structure |

### Recommended Approach

For most ebooks, **heading-aware chunking** gives the best results:
- Natural semantic boundaries
- Chapter/section titles as metadata
- Consistent chunk sizes for most well-structured books

For very long chapters (10,000+ words), combine heading-aware splitting with a max chunk size to avoid oversized chunks.

## Metadata Extraction

EPUB metadata follows the Dublin Core standard:

```python
from ebooklib import epub

book = epub.read_epub("book.epub")
title = book.get_metadata("DC", "title")       # Book title
creator = book.get_metadata("DC", "creator")    # Author(s)
language = book.get_metadata("DC", "language")  # Language code
identifier = book.get_metadata("DC", "identifier")  # ISBN, UUID, etc.
description = book.get_metadata("DC", "description")
publisher = book.get_metadata("DC", "publisher")
```

This metadata is valuable for RAG: include it in chunk metadata for filtering and attribution.

## Scripts in This Module

| Script | Description |
|--------|-------------|
| `sample_docs/generate_samples.py` | Creates a 4-chapter sample EPUB |
| `01_ebooklib_extraction.py` | Chapter-by-chapter extraction with metadata |
| `02_epub_to_text.py` | Full text extraction, markdown conversion, chunking strategies |

## Common Pitfalls

1. **DRM-protected EPUBs** - Many commercial ebooks use DRM (Adobe ADEPT, Apple FairPlay). ebooklib cannot read DRM-protected files. You must legally remove DRM first or use publisher APIs.

2. **Image-heavy EPUBs** - Graphic novels, textbooks with diagrams, and children's books embed critical information in images. Extract and OCR these separately.

3. **CSS-heavy formatting** - Some EPUBs use CSS for layout (drop caps, sidebars, pull quotes). `get_text()` strips these, which is usually fine. If layout matters, parse the CSS.

4. **Nested HTML** - Some EPUBs use deeply nested `<div>` and `<span>` elements. Always use `get_text(separator="\n", strip=True)` rather than iterating through tags manually.

5. **Non-standard EPUBs** - Some tools generate EPUBs that violate the spec (missing spine, invalid XML). ebooklib handles most edge cases, but you may need error handling.

6. **Encoding issues** - Most EPUBs use UTF-8, but some older files use other encodings. BeautifulSoup handles encoding detection automatically.

7. **Navigation vs. content** - The nav/toc files appear as documents but are not book content. Always filter them out when extracting chapters.

## Comparison with Other Ebook Formats

| Format | Structure | Ease of Extraction | Notes |
|--------|-----------|-------------------|-------|
| **EPUB** | Excellent (XHTML chapters) | Easy | Best for RAG |
| **PDF** | Variable | Moderate | May need OCR for scanned books |
| **MOBI/AZW** | Good (HTML-based) | Moderate | Amazon format, often DRM |
| **DJVU** | Scanned pages | Hard (needs OCR) | Academic/archival use |
| **FB2** | Good (XML) | Easy | Popular in Russia/Eastern Europe |
| **TXT** | None | Trivial | No structure to leverage |

## Tips for Production

- **Always extract metadata** and store it alongside chunks for attribution and filtering
- **Respect copyright** - ebooks are copyrighted works; ensure you have rights to process them
- **Handle missing chapters gracefully** - some EPUBs have empty or placeholder chapters
- **Batch process** with error handling - when processing many EPUBs, catch and log failures
- **Store chapter boundaries** in metadata so you can reconstruct reading order from chunks
- **Consider ebook-specific embeddings** - chapter titles and book metadata can improve retrieval relevance when included in the embedding text
- **Use `ignore_ncx=True`** when reading EPUBs with ebooklib to avoid warnings about deprecated NCX files
