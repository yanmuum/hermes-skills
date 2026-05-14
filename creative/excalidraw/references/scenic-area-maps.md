# Scenic Area / Geographic Maps

Creating hand-drawn scenic area planning maps, tourism maps, and geographic layouts with Excalidraw.

## When to use

User asks for a hand-drawn map of a geographic area: scenic spots, homestay clusters, tourist routes, park/campus layouts, or any location-based planning diagram.

## Getting Geographic Context

When you need real-world location data but web search is blocked:

### OpenStreetMap Nominatim API (no API key needed)

```bash
# Get town/village coordinates
curl -s "https://nominatim.openstreetmap.org/search?q=<location>&format=json&limit=5"

# Returns: lat, lon, boundingbox, display_name
# Rate limit: 1 req/sec
# Set User-Agent header for reliability
```

**Limitations:** Works for towns, rivers, mountains, major landmarks. Small businesses (homestays, local shops) typically aren't indexed — you'll need to position them relative to known landmarks.

### Estimating positions from known geography

- Use the town's bounding box from Nominatim to constrain the map area
- Position small landmarks by logical geography (e.g., "河畔基地" near water, "田野民宿" in fields)
- Use Chinese naming conventions to infer relative positions (畔=beside water, 田野=in fields)

## Map Layout Conventions

### Recommended canvas size
- 1200x900 for detailed scenic area maps
- Scale proportionally for larger/smaller areas

### Z-order (back to front)
1. Map background (cream/beige `#faf3e0`)
2. Natural terrain (mountains, forests — green ellipses)
3. Water features (rivers, lakes — blue winding lines)
4. Agricultural areas (orchards, fields — tinted ellipses)
5. Roads/paths (dashed lines)
6. Building compounds (labeled rectangles with `roundness: 3`)
7. Connection arrows between landmarks
8. Labels (text bound to shapes via containerId)
9. Map furniture: north arrow, scale bar, legend

### Essential Map Furniture

**Background**: warm cream `#faf3e0` with rounded corners
**Title**: fontSize 28, centered at top
**North Arrow**: arrow pointing up with "N" label, top-right corner
**Scale Bar**: horizontal line with tick marks and distance labels (e.g., "0" — "500m")
**Legend**: white rectangle in bottom-right corner with colored swatches

### Natural Features

| Feature | Element | Fill | Stroke |
|---------|---------|------|--------|
| Mountains/Forest | Large ellipses | `#b2f2bb` | `#2b8a3e` |
| Lakes/Ponds | Ellipses | `#a5d8ff` | `#1971c2` |
| Rivers | Line (winding) | — | `#74c0fc`, width 6-8 |
| Orchards/Fields | Ellipses, opacity 80 | `#ffd6e7` (peach) | `#e64980` |
| Roads | Line, strokeStyle="dashed" | — | `#e67700`, width 4-6 |

### Homestay / Building Compounds

Each compound should be visually distinct:
- **Base rectangle**: 150x100 with `roundness: 3`, `fillStyle: "solid"`
- **Sub-buildings**: 3-4 smaller rectangles (35x35) inside the compound
- **Name label**: container-bound text, fontSize 22, fontFamily=1 (hand-drawn)
- **Description label**: standalone text below, fontSize 14

Use different fill colors per compound for visual distinction:
| Compound | Fill | Stroke |
|----------|------|--------|
| Primary destination | `#d0bfff` (purple) | `#6741d9` |
| Secondary destination | `#a5d8ff` (blue) | `#1971c2` |
| Third destination | `#b2f2bb` (green) | `#2b8a3e` |
| Service facilities | `#ffc9c9` (red) | `#e03131` |
| Parking | `#fff3bf` (yellow) | `#e67700` |

## Example Workflow

1. **Search Nominatim** for the town/area coordinates
2. **Check bounding box** to determine map extent
3. **Position landmarks logically** based on naming and known geography
4. **Build the Excalidraw JSON** in this z-order: bg → terrain → water → orchards → road → compounds → labels → map furniture
5. **Save** as *.excalidraw file
6. **Upload** via `scripts/upload.py` for a shareable URL

## Chinese Content Tips

- Use fontFamily=1 (Virgil hand-drawn font) for all labels — supports Chinese characters
- Use descriptive Chinese in text labels (not pinyin) for clarity
- Emoji in text does NOT render in Excalidraw — use text descriptions instead
- For poetry-style taglines, keep them short (4-8 chars per line)

## Pitfalls / Known Issues

### ⚠️ Hand-drawn style may not suit all scenic planning maps

The Excalidraw `roughness: 1` default creates a deliberately sketchy, hand-drawn look. Some users expect a **smoother, more professional map style** (more like a tourism brochure or landscape architecture rendering).

**What went wrong in this session:**
The user asked for a scenic area planning map of 连平县上坪镇民宿集群. I created a detailed Excalidraw map with proper layout, legend, and map furniture — but the user rejected it with "这种手绘图的效果不行 不是要这种效果的" (this hand-drawn effect is no good, not the effect I want).

**How to prevent:**
- Before building a scenic planning map, **ask if they want Excalidraw hand-drawn style or a different visual style** (e.g., SVG-based map, HTML mockup, or real satellite map overlay)
- **Offer to let them share a reference image** first (via WSL path `/mnt/c/Users/...` for CLI sessions, or a URL)
- If they want a different style, suggest alternatives:
  - `architecture-diagram` skill for polished SVG-based diagrams
  - `sketch` skill for HTML mockups with multiple design variants
  - A custom HTML/CSS approach for more controlled visual output

### ⚠️ Cannot access real map / satellite imagery

Web search is often blocked via the browser tool, and map APIs (AMap, Google Maps, Baidu) typically require API keys. You'll need to build the map from:
- Nominatim coordinates (point-level only — works for towns, not individual POIs)
- Logical inference from Chinese naming conventions (e.g., 河畔 = riverside, 田野 = fields)
- Reference images the user provides

## Reference: This Session's Map

The map created in this session — "连平县上坪镇民宿集群规划图" — is saved at:
`/home/yanmuu/上坪镇民宿集群规划图.excalidraw`

Includes: 桃畔基地, 趣田野民宿, 桃乡民宿, parking, visitor center, viewpoint, river, peach orchards, mountains, road network, legend, north arrow, scale bar.
