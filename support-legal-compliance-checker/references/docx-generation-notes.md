# .docx Generation Usage Notes

Session 2026-05-13: Reviewed 道衍保密协议 (Web3/crypto company NDA for individual partner).

The actual working script was at `/tmp/gen_legal_review.py`. Key techniques:

## python-docx Setup
```bash
pip3 install --user --break-system-packages python-docx
python3.12 /tmp/gen_legal_review.py
```

## Key Setup Patterns

```python
# Chinese font
style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

# A4 margins
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.17)
section.right_margin = Cm(3.17)

# Color-coded risk text
# High risk: RGBColor(0xCC, 0x00, 0x00)
# Medium risk: RGBColor(0xE6, 0x8A, 0x00)  
# Low risk/green suggestion: RGBColor(0x00, 0x64, 0x00)
# Quote/gray: RGBColor(0x66, 0x66, 0x66)

# Tables with alternating rows
table.style = 'Light Grid Accent 1'
```

## Feishu Doc Reading
```python
# Get content from a Feishu Doc (docx format)
GET https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content
Headers: Authorization: Bearer {tenant_access_token}
```

## Feishu File Sending
```
MEDIA:/tmp/法律审查意见书_<协议名>.docx
```
