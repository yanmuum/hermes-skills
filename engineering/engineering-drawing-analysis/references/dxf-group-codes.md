# DXF Group Code Quick Reference for Engineering Drawings

## Common Entity Group Codes

| Code | Name | Type | Description |
|------|------|------|-------------|
| 0 | ENTITY_TYPE | str | Entity type marker (starts each entity) |
| 1 | TEXT | str | Primary text content |
| 2 | BLOCK_NAME | str | Block/insert name |
| 3 | TEXT_ALT | str | Alternate text / font name |
| 8 | LAYER | str | Layer name |
| 10 | X | float | Start X / insertion X / X coord |
| 11 | X2 | float | End X / alignment point X |
| 20 | Y | float | Start Y / insertion Y |
| 21 | Y2 | float | End Y |
| 30 | Z | float | Elevation |
| 40 | HEIGHT | float | Text height / radius / dash len |
| 41 | SCALE_X | float | X scale / width factor |
| 42 | BULGE/VAL | float | Bulge (polyline arc) or dimension value |
| 43 | SCALE_Y | float | Y scale / dim sub-value |
| 50 | ANGLE | float | Rotation angle (degrees) |
| 70 | FLAGS | int | Entity flags (categorical) |
| 71-77 | SUB_FLAGS | int | Sub-type flags |
| 100 | SUBCLASS | str | Subclass marker (AcDbEntity, etc.) |
| 210 | EXTRUDE_X | float | Extrusion direction X |
| 220 | EXTRUDE_Y | float | Extrusion direction Y |
| 230 | EXTRUDE_Z | float | Extrusion direction Z |

## Standard DXF Entity Types

| Type | Description | Key Data |
|------|-------------|----------|
| TEXT | Single-line text | 1=text, 10/20=pos, 40=height, 50=angle |
| MTEXT | Multi-line text | 1=text with \\P line breaks |
| LINE | Line segment | 10/20=start, 11/21=end |
| LWPOLYLINE | Lightweight polyline | 90=vertex count, 10/20=vertices, 42=bulge |
| POLYLINE | Polyline (heavy) | 66=vertex follow flag, 70=type |
| VERTEX | Polyline vertex | 10/20=pos, 42=bulge, 70=flags |
| ARC | Circular arc | 10/20=center, 40=radius, 50/51=start/end angle |
| CIRCLE | Circle | 10/20=center, 40=radius |
| INSERT | Block reference | 2=block name, 10/20=pos, 41/42/43=X/Y/Z scale |
| HATCH | Hatch pattern | 2=pattern name, 91=boundary loops |
| DIMENSION | Standard dimension | 1=text, 42=value, 10/20=def point |
| BLOCK | Block definition start | 2=block name, 70=flags |
| ENDBLK | Block definition end | — |
| ATTRIB | Block attribute | 1=value, 2=tag, 40=height |
| ATTDEF | Attribute definition | 1=default, 2=tag, 40=height |

## Tianzheng (天正建筑) Custom Entity Types

| Entity Type | Description | Key Codes |
|-------------|-------------|-----------|
| TCH_TEXT | Tianzheng text label | 1=text, 8=layer, 40=height |
| TCH_DIMENSION2 | Tianzheng dimension | 42=value, 1=override text |
| TCH_MULTILEADER | Multi-leader with text | 1=text, 11/21=arrow tip |
| TCH_COMPOSING | Multi-line composition | 1=text (^M^J = newline) |
| TCH_DRAWINGNAME | Drawing title annotation | 1=title text |
| TCH_INDEXPOINTER | Index reference (bubble) | 1=index number |
| TCH_DRAWINGINDEX | Drawing index | 1=index number |
| TCH_RUPTURE | Break/section line | (graphical, no text) |
| TCH_MTEXT | Tianzheng multi-line | 1=text content |

## Layer Naming Conventions (Chinese CAD)

| Layer | Content |
|-------|---------|
| 0 | Title block / border elements |
| PUB_TEXT | Published/printed text |
| PUB_TAB | Quantity tables (工程量表) |
| PUB_DIM | Published dimensions |
| PUB_TITLE | Title annotations |
| DIM_LEAD | Leader annotations (引线标注) |
| DIM_SYMB | Dimension symbols (标注符号) |
| DIM_IDEN | Drawing index markers |
| TEXT | General text |
| 路 | Design specifications (usually on the "road" layer) |
| 文字 | Chinese text annotations |
| ZJ | 标注 (dimension/label annotations) |
| JMD | 截面 marking |
| SXSS | 上下山 (terrain/elevation marks) |
| A-图框 | A-size title block |
| 0-图签 | Drawing label block |
| 0-图名 | Drawing name block |
| 0-图框 | Drawing frame border |
| AXIS_TEXT | Axis labels (A, B, C... or 1, 2, 3...) |
| BEAM | Beam structural elements |
| COLUMN | Column elements |
| DLSS | 道路 (road pavement) |
| GCD | 高程点 (elevation points) |

## Tianzheng Scale Interpretation

TCH_DRAWINGNAME entities store scale info:
- Group code 2 = scale string (e.g. "1:30")
- Group code 40 = text height (dimension text height in mm)
- Group code 41 = arrowhead size
- Group code 42 = extension line offset

Dimension values in TCH_DIMENSION2 (code 42) are in **drawing units**. To get real-world mm:
- If scale is 1:30 and value is 23.41, real = 23.41 * 30 = 702mm
- Check title block for exact scale (常见比例: 1:20, 1:30, 1:50, 1:100)

## pdfFactory Pro Metadata Detection

```python
# Check if PDF was created by pdfFactory (tiled images)
from pypdf import PdfReader
reader = PdfReader("file.pdf")
producer = reader.metadata.get('/Producer', '')
is_pdffactory = 'pdfFactory' in producer  # → True = tile extraction needed
```

## Sample DXF: Pairs Mode vs File Size

| DXF Size | Est. Lines | Parse Time |
|----------|-----------|------------|
| 1 MB | ~125K | <1s |
| 4 MB | ~450K | ~2s |
| 10 MB | ~1.2M | ~5s |
