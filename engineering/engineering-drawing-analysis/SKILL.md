---
name: engineering-drawing-analysis
description: "Extract quantities, dimensions, materials, and specifications from engineering drawings (DXF/CAD) for construction cost estimation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [CAD, DXF, Engineering, Construction, Cost-Estimate, Blueprint]
    related_skills: [ocr-and-documents]
---

# Engineering Drawing Analysis (DXF/CAD)

Extract construction data from engineering drawings — quantities, dimensions, materials, and design specifications. Used when the user provides blueprints for cost estimation, quantity takeoff, or project analysis.

## Step 1: Identify the Drawing Format

| Format | Approach | Success Rate |
|--------|----------|-------------|
| **DWG** (AutoCAD binary) | Ask user to save as DXF | N/A — can't open directly |
| **DXF** (ASCII) | ✓ Pure Python parsing | Excellent — all text/layers readable |
| **DXF** (Binary) | Needs ezdxf | Good — install `pip install ezdxf` |
| **PDF** (from CAD export) | See `ocr-and-documents` skill | Poor — scanned, text too small for OCR |

**Preference order**: DXF (ASCII) > DXF (binary) > PDF. Always ask user to provide DXF if possible.

## Step 2: Parse ASCII DXF (no dependencies)

ASCII DXF is a tagged text format with group codes and values. These sample key codes:

| Group Code | Meaning |
|-----------|---------|
| 0 | Entity type (TEXT, LINE, LWPOLYLINE, etc.) |
| 8 | Layer name |
| 1 | Primary text content |
| 10, 20, 30 | X, Y, Z coordinates |
| 40 | Text height / radius |
| 41 | X scale factor / width |
| 42 | Bulge / dimension value |
| 70 | Entity flags |

### Basic DXF Pair Reader

```python
def dxf_pairs(lines):
    """Convert DXF lines to (code, value) pairs."""
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        try:
            code = int(line)
            if i + 1 < len(lines):
                value = lines[i+1].strip()
                pairs.append((code, value))
                i += 2
            else:
                i += 1
        except ValueError:
            i += 1
    return pairs
```

### Entity Extraction

```python
# Walk pairs to find entities of specific types
entities = []
i = 0
while i < len(pairs):
    code, value = pairs[i]
    if code == 0:  # Entity start
        entity = {'type': value}
        i += 1
        while i < len(pairs):
            c, v = pairs[i]
            entity[c] = v
            if c == 0:  # Next entity
                break
            i += 1
        entities.append(entity)
    else:
        i += 1
```

### Encoding

Chinese engineering DXF files use **GBK encoding** (ANSI_936), **not UTF-8**:

```python
with open("drawing.dxf", "r", encoding="gbk", errors="replace") as f:
    lines = f.readlines()
```

## Step 3: Extract Key Information

### TEXT/MTEXT — All text labels

Layer `TEXT`, `PUB_TEXT`, `ZJ`, `路`, `0` typically contain:
- Design specifications
- Notes and construction requirements
- Material labels
- Dimension annotations

### Tianzheng CAD (天正) Entities

Chinese CAD drawings use 天正建筑 custom entities:

| Entity Type | Meaning | Key Group Codes |
|------------|---------|-----------------|
| `TCH_TEXT` | Tianzheng text | 1=text, 8=layer, 40=height |
| `TCH_DIMENSION2` | Tianzheng dimension | 42=dimension value, 1=override text |
| `TCH_MULTILEADER` | Multi-leader annotation | 1=text content |
| `TCH_COMPOSING` | Multi-line composition | 1=text with `^M^J` line breaks |
| `TCH_DRAWINGNAME` | Drawing title | 1=title text |
| `TCH_INDEXPOINTER` | Index/bubble pointer | 1=index number |
| `TCH_RUPTURE` | Break/section symbol | (symbol, no text) |

### Layout/Blocks (PUB_TAB)

Tables (工程量表 / quantity schedules) are often on `PUB_TAB` layer as individual `TCH_TEXT` entries. Read all entries in sequence to reconstruct the table.

### Polylines (LWPOLYLINE, POLYLINE)

Count and analyze for length calculations. LWPOLYLINE vertices are at (10, 20) pairs with optional bulge (42).

### Layers to Target

```python
target_layers = {
    'TEXT':     'ordinary text labels',
    'PUB_TEXT': 'published/printed text',
    'PUB_TAB':  'quantity tables',
    'PUB_DIM':  'dimensions',
    'DIM_LEAD': 'leader annotations',
    'DIM_SYMB': 'dimension symbols',
    'DIM_IDEN': 'drawing index markers',
    '路':       'design specifications (road layer)',
    '文字':     'text annotations',
    'ZJ':       '标注 (dimension annotations)',
    'JMD':      '截面 (section marks)',
    'SXSS':     '上下山 (terrain marks)',
    'A-图框':   'title block',
    '0-图签':   'drawing label',
}
```

## Step 4: Build the Cost Estimate

### Data Flow

```
DXF → Extract: (a) quantities from PUB_TAB
              (b) dimensions from TCH_DIMENSION2
              (c) materials/specs from TEXT/TCH_TEXT
              (d) total lengths from annotated text (e.g. "水沟总长：950.80米")
              
Material Prices → OCR'd from official price bulletin PDF

Cost Estimate → Structured workbook with:
  1. 分部分项工程量清单 (BOQ)
  2. 综合单价分析 (unit price breakdown)
  3. 总造价汇总 (total cost summary)
```

### Typical Water Channel (水渠) Cost Items

For retaining walls / drainage channels in Guangdong villages:
- 土方开挖 (earth excavation) — m³
- C15素混凝土垫层 100mm厚 — m³
- 浆砌块石挡土墙 MU20/M7.5 — m³
- C25钢筋混凝土压顶 — m³
- 墙后回填 (filter layer: geotextile + gravel) — m³
- Φ50 PVC泄水孔 — 个
- 变形缝 沥青木板30mm — m²
- 模板 (formwork) — m²
- 钢筋制安 (steel reinforcement) — t

## Pitfalls

- **Engineering blueprints in PDF → OCR fails** — CAD annotations are too small (~5-7px at 70 DPI). Don't retry OCR. Ask user for DXF or key parameters.
- **DXF encoding** — Always try GBK before UTF-8 for Chinese CAD files. Check `$DWGCODEPAGE` in HEADER section (mine ANSCI_936 → use `encoding="gbk"`).
- **Tianzheng dimensions (TCH_DIMENSION2)** — Dimension values are in drawing units, NOT real-world units. Must know the drawing scale (stored in TCH_DRAWINGINDEX entities or title block). Ask user for interpretation.
- **pdfFactory Pro** — These PDFs tile pages into 46 strips each. Don't try OCR on tiles — reconstruct full page first.
- **OCR.space rate limit** — 20 req/hr on free key `helloworld`. Once exhausted, wait ~55 minutes or use alternative. Don't retry excessively.
- **User prefers direct results** — When tools fail (OCR, install), state the problem and offer alternatives once. Don't iterate with explanations.

## Linked Files

- `scripts/parse_ascii_dxf.py` — Standalone DXF parser (no dependencies, 1 file)
- `references/dxf-group-codes.md` — Complete DXF group code + Tianzheng entity reference
