# Feishu Bitable API Notes for Design Project Table

## Field IDs (used in API calls)

| Field Name  | Field ID        |
|-------------|-----------------|
| 项目名称    | `fldtMQZDbb`    |
| 日期        | `fldRRw6MpK`    |
| 序号        | `fldXtVOflp`    |
| 客户名称    | `fldGIfBRde`    |
| 项目总金额  | `fldLGu7TPu`    |
| 已收金额    | `fldV8a9vGi`    |
| 未收金额    | `fldHUysahA`    |
| 支出设计费  | `fldo71AiCr`    |
| 备注        | `fldL4YzJCB`    |

## View IDs

| View Name   | View ID        |
|-------------|----------------|
| 表格        | `vewIPBmqTD`   |
| 按日期排序  | `vewKz9qa86`   |

## Quick API Endpoints

```python
app_token = "NkcrbLj70aiyHwsgDpUc5ix9nQd"
table_id = "tblcbUJ0TsBcsGaW"

# List records
GET /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=20

# Create record
POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records
# Body: {"fields": {...}}

# Update field name
PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}
# Body: {"field_name": "新名称", "type": <type_id>}
```

## Permission Note

The app `cli_a977e0167e3a1bc4` has `bitable:app` permission enabled (已发布).
