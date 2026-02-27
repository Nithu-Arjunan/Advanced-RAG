# HTML / Web Page Parsing for RAG

## Overview

HTML documents are one of the most common data sources for RAG systems — web scraping, saved pages, documentation sites, and exported content all produce HTML. The key challenge is **separating meaningful content from boilerplate** (navigation, ads, footers, sidebars) and converting the structured markup into text suitable for embedding.

## Method Comparison

| Library | Boilerplate Removal | Table Support | Markdown Output | Speed | Best For |
|---------|-------------------|---------------|-----------------|-------|----------|
| **BeautifulSoup** | Manual (you control) | Yes (manual) | No (manual) | Fast | Fine-grained control, custom extraction logic |
| **html2text** | No (converts everything) | Yes (auto) | Yes (native) | Fast | Quick HTML-to-markdown, heading-aware chunking |
| **Trafilatura** | Yes (automatic) | Yes | No | Medium | Web articles, automatic content detection |

## When to Use Each Method

### BeautifulSoup (`01_beautifulsoup_extraction.py`)
- You need **precise control** over which elements to extract
- You're building a **custom scraper** for a specific site structure
- You need to extract **specific elements** (tables, lists, code blocks) separately
- The HTML has a **known, consistent structure** (like API docs or product pages)

### html2text (`02_html2text_extraction.py`)
- You want **markdown output** for heading-aware chunking
- You need a **quick, reliable** HTML-to-text conversion
- The HTML is **well-structured** and you want to preserve formatting hierarchy
- You're processing **many pages** and need consistent output

### Trafilatura (`03_trafilatura_extraction.py`)
- You're processing **web articles/blog posts** and need automatic content extraction
- You want **boilerplate removed automatically** (nav, footer, ads, sidebars)
- You need **metadata extraction** (author, date, title) alongside content
- You're scraping **diverse websites** with varying structures

## Chunking Strategies for HTML

### 1. Heading-Aware Chunking (Recommended)
Convert HTML to markdown first (html2text), then chunk by headings. This preserves the document's logical structure.

```python
import html2text
from shared.chunking import chunk_by_headings

converter = html2text.HTML2Text()
converter.ignore_links = True
md_text = converter.handle(html_content)
chunks = chunk_by_headings(md_text)
```

### 2. Section-Based Chunking
Use BeautifulSoup to extract content by `<section>`, `<article>`, or `<div>` boundaries. Best when the HTML has clear semantic structure.

### 3. Boilerplate Removal + Recursive Split
Use trafilatura to get clean content, then apply recursive character splitting. Best for web articles where you just need the main text.

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Navigation/footer text pollutes chunks | Use trafilatura or manually remove `<nav>`, `<footer>`, `<aside>` tags |
| Table data becomes garbled text | Extract tables separately with BeautifulSoup, convert to structured text |
| Links and images add noise | Use `html2text` with `ignore_links=True` and `ignore_images=True` |
| JavaScript-rendered content | HTML parsers only see static HTML — use Playwright/Selenium for JS-heavy pages |
| Character encoding issues | Always specify encoding when reading files; use `chardet` for detection |
| Deeply nested divs | BeautifulSoup's `.get_text()` handles nesting, but manual traversal gives better control |

## Tips for Production

1. **Always remove boilerplate first** — navigation, ads, footers, and cookie banners add noise to embeddings
2. **Extract tables separately** — tables are better represented as structured text or natural language descriptions than raw cell dumps
3. **Preserve heading hierarchy** — headings provide the best natural chunk boundaries for HTML content
4. **Handle relative URLs** — if you need link context, resolve relative URLs to absolute before extraction
5. **Consider the source** — different strategies work for different HTML: articles (trafilatura), documentation (BeautifulSoup with section targeting), general pages (html2text)
6. **Metadata matters** — title, author, date, and description meta tags are valuable for RAG metadata filtering

## Files in This Module

| File | Description |
|------|-------------|
| `sample_docs/generate_samples.py` | Generates 3 sample HTML files (article, table-heavy, nested docs) |
| `01_beautifulsoup_extraction.py` | DOM parsing with fine-grained control |
| `02_html2text_extraction.py` | HTML to markdown conversion |
| `03_trafilatura_extraction.py` | Automatic content extraction with boilerplate removal |
