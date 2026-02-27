# Module 06: Images & OCR

## Overview

Optical Character Recognition (OCR) converts images of text into machine-readable strings. This is essential for RAG pipelines that need to ingest scanned documents, image-based PDFs, photographs of text, or screenshots.

## When Do You Need OCR?

- **Scanned documents** - Paper documents digitized via scanner or camera
- **Image-based PDFs** - PDFs where text is stored as images (not selectable text)
- **Photos of text** - Signs, whiteboards, receipts, business cards
- **Screenshots** - Text captured as image rather than copyable text
- **Historical documents** - Digitized archives without text layers

## OCR Engines Compared

| Feature | Tesseract | EasyOCR | Cloud APIs (Google/AWS) | Vision LLMs (GPT-4V) |
|---------|-----------|---------|------------------------|-----------------------|
| **Cost** | Free | Free | Pay per request | Pay per request |
| **Speed** | Fast | Moderate | Depends on network | Slow |
| **Accuracy (printed)** | Good | Good | Excellent | Excellent |
| **Accuracy (handwriting)** | Poor | Fair | Good | Good |
| **Languages** | 100+ | 80+ | 50+ | Multi-language |
| **GPU needed** | No | Optional | No (cloud) | No (cloud) |
| **Offline** | Yes | Yes | No | No |
| **Layout analysis** | Basic | Good | Excellent | Excellent |
| **Setup complexity** | Medium | Easy | Easy (API key) | Easy (API key) |

### When to Use Each

- **Tesseract**: Standard printed documents, budget-conscious, need offline processing, high volume
- **EasyOCR**: Multi-language documents, scene text (signs/labels), when Tesseract struggles
- **Cloud APIs**: Production systems needing highest accuracy, complex layouts, handwriting
- **Vision LLMs**: Complex documents with mixed content, when you need understanding not just extraction

## Preprocessing: The Key to Good OCR

Raw scans often produce poor OCR results. Preprocessing dramatically improves accuracy:

### Essential Preprocessing Steps

1. **Grayscale conversion** - Remove color information that confuses OCR
2. **Binarization/Thresholding** - Convert to pure black text on white background
3. **Noise removal** - Remove speckles, dots, and scan artifacts
4. **Deskewing** - Straighten rotated text
5. **Resizing** - Scale very small text up to readable size (300 DPI minimum)

### Impact on Accuracy

```
Raw noisy scan:        ~70% word accuracy
+ Grayscale:           ~80% word accuracy
+ Threshold:           ~90% word accuracy
+ Noise removal:       ~95% word accuracy
+ Deskew + resize:     ~98% word accuracy
```

## Installation

### Tesseract

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows - Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Python wrapper
pip install pytesseract Pillow
```

### EasyOCR

```bash
# Installs PyTorch as a dependency (~1-2GB)
pip install easyocr

# For GPU acceleration (optional, requires CUDA)
pip install easyocr torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### This project (optional OCR dependencies)

```bash
uv pip install pytesseract easyocr
# or
uv sync --extra ocr
```

## Scripts in This Module

| Script | Library | Description |
|--------|---------|-------------|
| `sample_docs/generate_samples.py` | Pillow | Creates sample images with text |
| `01_tesseract_ocr.py` | pytesseract | Tesseract OCR with preprocessing |
| `02_easyocr_extraction.py` | EasyOCR | Deep learning-based OCR |

## Chunking Strategies for OCR Output

OCR output is inherently noisier than text from structured documents. Choose chunking strategies accordingly:

1. **Sentence-based chunking** (recommended) - Handles OCR errors better since sentence boundaries are more robust than paragraph detection
2. **Fixed-size character chunking** - Good fallback when OCR output lacks proper punctuation
3. **Page-level chunking** - One chunk per scanned page; preserves document structure
4. **Paragraph-based** - Only works well on high-quality OCR with reliable paragraph detection

## Common Pitfalls

1. **Poor scan quality** - Always preprocess images before OCR. Low DPI, uneven lighting, and skew dramatically reduce accuracy.
2. **Handwriting** - Standard OCR engines struggle with handwriting. Use specialized models or cloud APIs for handwritten text.
3. **Mixed languages** - Specify the correct language(s) for Tesseract. EasyOCR handles multi-language better out of the box.
4. **Tables in images** - OCR engines extract text line-by-line and lose table structure. Use specialized table detection (e.g., `img2table`, Azure Form Recognizer) for tabular data.
5. **Multi-column layouts** - Tesseract may read across columns. Use PSM mode 1 or 4 for multi-column documents.
6. **Confidence blindness** - Always check OCR confidence scores. Low-confidence words are likely errors.
7. **Over-relying on raw output** - Post-process OCR text (spell-check, regex cleanup) before feeding to RAG.

## Tips for Production

- **Set a minimum confidence threshold** (e.g., 0.6) to filter garbled detections
- **Batch processing**: Tesseract is faster per-image; EasyOCR amortizes model loading across batches
- **Cache OCR results** - OCR is expensive; store extracted text alongside source images
- **Log and monitor** accuracy metrics (average confidence) to detect quality degradation
- **Consider hybrid approaches**: Use fast OCR for bulk processing, cloud APIs for low-confidence pages
- **Always store the original image** alongside extracted text for re-processing as OCR improves
- **Use DPI of 300+** when scanning documents specifically for OCR
