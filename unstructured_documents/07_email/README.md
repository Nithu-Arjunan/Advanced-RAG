# Email (.eml) Parsing for RAG

## Overview

Email is one of the most information-dense document types in enterprise environments. Parsing `.eml` files for RAG involves understanding the MIME (Multipurpose Internet Mail Extensions) structure, extracting headers and body content, handling multipart messages (plain text + HTML alternatives), and processing attachments. The key challenge is combining structured metadata (sender, recipient, date, subject) with unstructured body text into coherent, retrievable chunks.

## EML File Format

The `.eml` format is a standard text-based representation of email messages following RFC 5322 (Internet Message Format) and RFC 2045-2049 (MIME). An `.eml` file contains:

- **Headers**: Key-value pairs (From, To, Subject, Date, Message-ID, Content-Type, etc.)
- **Body**: The message content, which may be plain text, HTML, or both
- **Attachments**: Binary or text files encoded (usually Base64) within the MIME structure

## MIME Structure

| Structure | Description | Example |
|-----------|-------------|---------|
| `text/plain` | Simple single-part plain text email | Personal messages, automated alerts |
| `multipart/alternative` | Multiple representations of the same content (plain + HTML) | Newsletters, marketing emails |
| `multipart/mixed` | Main body + attachments | Business emails with file attachments |
| `multipart/related` | HTML body with inline images/resources | Rich HTML emails with embedded images |
| Nested multipart | Mixed containing alternative containing related | Complex corporate emails |

## Extraction Challenges

| Challenge | Description | Solution |
|-----------|-------------|----------|
| **Multipart messages** | Emails often contain multiple body parts (plain text + HTML) | Walk the MIME tree, prefer plain text, fall back to HTML-stripped text |
| **HTML body content** | HTML emails contain tags, styles, and scripts mixed with content | Strip HTML tags using `html.parser` or regex; extract text from semantic elements |
| **Encoded headers** | Subject and other headers may use RFC 2047 encoded words (e.g., `=?UTF-8?B?...?=`) | Use Python's `email.policy.default` which decodes automatically |
| **Attachment handling** | Attachments are Base64-encoded within the MIME structure | Decode with `get_payload(decode=True)`, handle text vs binary separately |
| **Character encodings** | Different parts may use different encodings (UTF-8, ISO-8859-1, etc.) | Check `charset` parameter in Content-Type; fall back gracefully |
| **Inline images** | Images referenced in HTML via `cid:` URLs | Identify by Content-Disposition or Content-ID; usually skip for RAG |
| **Nested MIME parts** | Complex emails have deeply nested multipart structures | Use recursive `.walk()` method to traverse all parts |
| **Thread context** | Individual emails lack the context of the full thread | Group by In-Reply-To / References headers for thread reconstruction |

## Method Overview

### Python's `email` Module (Built-in)

The standard library provides everything needed for email parsing:

```python
from email import policy
from email.parser import BytesParser

with open("message.eml", "rb") as f:
    msg = BytesParser(policy=policy.default).parse(f)

# Headers
subject = msg["Subject"]        # Automatically decoded
sender = msg["From"]

# Body
for part in msg.walk():
    if part.get_content_type() == "text/plain":
        body = part.get_content()
```

**Important**: Always use `policy.default` rather than the legacy `policy.compat32` -- it handles header decoding and provides a cleaner API.

## Chunking Strategies for Email RAG

### Strategy 1: One Chunk Per Email
Each email becomes a single chunk with metadata prefix:
```
Email from alice@co.com to bob@co.com on 2025-03-10.
Subject: Q1 Review.

Body:
The Q1 results exceeded expectations...
```
- **Best for**: Short emails, search-style retrieval, preserving full context
- **Limitation**: Long emails may exceed embedding model token limits

### Strategy 2: Body Chunking with Metadata Prefix
Split the email body into smaller chunks, prepending metadata to each:
- **Best for**: Long emails, fine-grained retrieval within a single message
- **Limitation**: Metadata prefix is repeated, increasing storage

### Strategy 3: Sentence-Based Chunking
Apply sentence-based splitting to the combined metadata + body text:
- **Best for**: Consistent chunk sizes, general-purpose retrieval
- **Limitation**: May split logical sections awkwardly

### Strategy 4: Thread-Based Chunking
Group related emails by thread (using In-Reply-To / References headers) and chunk the entire conversation:
- **Best for**: Customer support threads, ongoing discussions
- **Limitation**: Requires thread reconstruction logic

## Common Pitfalls

1. **Using `policy.compat32`** -- the legacy policy does not auto-decode headers and returns raw bytes for some operations. Always use `policy.default`.
2. **Ignoring multipart structure** -- calling `get_content()` on a multipart message returns `None`. You must `.walk()` through parts.
3. **Not handling missing headers** -- emails may lack CC, Date, or even Subject. Always provide defaults.
4. **Assuming UTF-8 everywhere** -- older emails may use ISO-8859-1, Windows-1252, or other encodings. Check the charset parameter.
5. **Including HTML tags in chunks** -- if you use the HTML body, always strip tags first or the embeddings will be polluted with markup noise.
6. **Forgetting attachments** -- text attachments (meeting notes, logs, CSVs) often contain valuable information. Include them in your RAG pipeline.

## Tips for Production

1. **Metadata as filters**: Store sender, recipient, date, and subject as metadata fields in your vector database for filtered retrieval (e.g., "find emails from Alice about the budget").
2. **De-duplicate quoted text**: Reply emails often quote the original message. Detect and remove quoted sections (lines starting with `>`) to avoid indexing the same content multiple times.
3. **Handle inline forwarding**: Forwarded emails embed the original message in the body. Parse the `---------- Forwarded message ----------` pattern.
4. **Attachment-aware chunking**: For emails with attachments, consider creating separate chunks for the email body and each attachment, linked by a shared email ID.
5. **Date normalization**: Email dates come in many formats. Parse them into ISO 8601 for consistent filtering and sorting.
6. **Privacy and PII**: Email content is highly sensitive. Implement PII detection and redaction before indexing into a RAG system.

## Files in This Module

| File | Description |
|------|-------------|
| `sample_docs/generate_samples.py` | Generates 3 sample .eml files (plain text, HTML newsletter, with attachment) |
| `01_email_parsing.py` | Full email parsing: headers, body (plain + HTML), attachments |
| `02_structured_email_extraction.py` | RAG-optimized extraction with metadata-enriched text blocks and chunking strategies |
