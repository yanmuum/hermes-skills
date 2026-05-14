# OCR.space Free API Reference

Endpoint: `https://api.ocr.space/parse/image`
Free Demo Key: `helloworld` (20 requests/hour limit; HTTP 429 = wait ~1 hour)

## Parameters

| Parameter | Value | Effect |
|-----------|-------|--------|
| apikey | "helloworld" | Free tier key |
| language | "chs" | Chinese simplified |
| OCREngine | 2 | Best accuracy engine |
| isOverlayRequired | false | Skip text overlay output |
| file | multipart upload | JPG/PNG, max ~2-3MB recommended |

## Known Behaviors

### Works well for:
- Scanned documents with body text (12pt+)
- Tables with clear column structure
- Government price announcements (信息价)
- Chinese text at reasonable resolution (2000px+ width)

### Fails for:
- Engineering blueprints (thin CAD annotations at ~70 DPI)
- Very small text (<8pt in original)
- Image-only pages with no clear text regions
- Pages over ~3MB (HTTP 413 Entity Too Large)

## Workaround for big images
Resize/crop before upload, keep width ~2000px for optimal balance.

## Rate Limiting
HTTP 429 response with `retryAfter` in seconds. Reset timer from first request, not from the 429.
