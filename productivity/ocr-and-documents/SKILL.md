---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint, engineering-drawing-analysis]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## pdfFactory PDFs (Tiled Images)

Some PDFs (created by pdfFactory Pro virtual printer) store each page as 46+ small JPEG strips (tiles) rather than a single image. Use the helper script:

```bash
python scripts/extract_pdffactory.py document.pdf [output_dir]
```

Or inline (pypdf + Pillow):
```python
from PIL import Image
import io
from pypdf import PdfReader

reader = PdfReader("document.pdf")
for page_num in range(len(reader.pages)):
    page = reader.pages[page_num]
    images = list(page.images)
    if not images:
        print(f"Page {page_num+1}: no embedded images")
        continue
    
    # All tiles have same width; reconstruct vertically
    all_ims = [Image.open(io.BytesIO(img.data)) for img in images]
    tile_w = all_ims[0].width
    total_h = sum(im.height for im in all_ims)
    
    canvas = Image.new('RGB', (tile_w, total_h), (255, 255, 255))
    y = 0
    for im in all_ims:
        canvas.paste(im, (0, y))
        y += im.height
    
    canvas.save(f"page_{page_num+1}_reconstructed.png", "PNG")
```

**Check metadata** to identify pdfFactory PDFs: `reader.metadata['/Producer']` will contain "pdfFactory".

## Online OCR Fallback (when pymupdf/marker unavailable)

When local OCR tools fail (pymupdf not installed, marker too heavy), use **OCR.space free API**:

```python
import requests
url = "https://api.ocr.space/parse/image"
with open("page.jpg", "rb") as f:
    r = requests.post(url, data={
        "apikey": "helloworld",           # Free demo key, 20 req/hr
        "language": "chs",                # Chinese simplified
        "OCREngine": 2,                   # Engine 2 = best accuracy
        "isOverlayRequired": False,
    }, files={"file": ("page.jpg", f, "image/jpeg")}, timeout=60)

if r.status_code == 200:
    text = r.json()["ParsedResults"][0]["ParsedText"]
```

**Limits**: 20 requests/hour on free plan (HTTP 429). Good for tables and body text. **Fails on engineering blueprints** — thin CAD annotations at ~70 DPI are illegible. When OCR returns empty for blueprints, ask user for key parameters.

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
- pdfFactory tile reconstruction: `scripts/extract_pdffactory.py` (requires pypdf + Pillow, both usually pre-installed)
- OCR.space free API reference: `references/ocrspace-api.md` (demo key helloworld, 20 req/hr, good for Chinese text)
- **Engineering blueprints**: OCR almost always fails on CAD annotations at ~70 DPI. When empty, ask user for key dimensions rather than retrying.
