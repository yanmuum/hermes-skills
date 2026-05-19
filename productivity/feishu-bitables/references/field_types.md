# Feishu Bitable Field Type Reference

## Valid Type IDs (for Create/Update Field API)

| type | Name          | Notes | Working Example Property |
|------|---------------|-------|--------------------------|
| 13   | URL           | ⚠️ **Misleading** — Creates Phone (ui_type=\"Phone\"), rejects URL values. Use type=1 (Text) instead | `{}` |
| 2    | Number        | ✅ **Use for currency** | `{"formatter": "0", "decimal_places": 2}` |
| 3    | SingleSelect  | ✅ Works | `{"options": [{"name": "选项1", "color": 0}]}` |
| 4    | MultiSelect   | ✅ Works | Similar to SingleSelect |
| 5    | DateTime      | ✅ Works | `{"auto_fill": true, "date_formatter": "yyyy/MM/dd"}` |
| 7    | Checkbox      | ✅ | `{}` |
| 11   | Phone         | ✅ | `{}` |
| 13   | URL           | ⚠️ **Misleading** — Creates Phone (ui_type=\"Phone\"), rejects URL values. Use type=1 (Text) instead | `{}` |
| 15   | Location      | ✅ | `{"input_disabled": true}` |
| 17   | Attachment    | ✅ | `{}` |
| 18   | Person        | ✅ | `{}` |
| 20   | Formula       | ✅ | `{"formula_expression": "..."}` |
| 21   | DuplexLink    | ✅ | `{"link_table_id": "...", "link_field_id": "..."}` |
| 22   | CreatedTime   | ✅ | `{"date_formatter": "yyyy/MM/dd"}` |
| 23   | Group         | ✅ | `{}` |
| 1001 | Progress      | ✅ | `{}` |
| 1002 | Rating        | ✅ | `{}` |
| 1003 | Currency      | ❌ **Broken** — Returns `CreatedUserFieldPropertyError` | Use type=2 instead |
| 1004 | Email         | ✅ | `{}` |
| 1005 | AutoNumber    | ✅ | `{"auto_number_type": "custom", "custom_formula": "..."}` |

## Date Field Properties

```python
# Auto-fill with today
{"auto_fill": True, "date_formatter": "yyyy/MM/dd"}

# Available formatters:
# "yyyy/MM/dd"  → 2026/05/08
# "yyyy-MM-dd"  → 2026-05-08
# "yyyy/MM/dd HH:mm" → 2026/05/08 20:48
# "yyyy-MM-dd HH:mm" → 2026-05-08 20:48
# "MM/dd"       → 05/08
```

## Number Field Properties

```python
# Integer display
{"formatter": "0", "decimal_places": 0}

# 2 decimal places (currency-like)
{"formatter": "0", "decimal_places": 2}

# Display as percentage
{"formatter": "0%", "decimal_places": 0}
```

## Field Update (PUT) — Complete Examples

```python
# Rename a text field
{"field_name": "新名称", "type": 1}

# Rename + update date with auto-fill
{"field_name": "创建日期", "type": 5, "property": {"auto_fill": True, "date_formatter": "yyyy/MM/dd"}}

# Change number field properties
{"field_name": "金额", "type": 2, "property": {"formatter": "0", "decimal_places": 2}}
```

⚠️ PUT always requires at minimum: `field_name` + `type`. Omitting `type` returns:
```json
{"code": 99992402, "msg": "field validation failed",
 "error": {"field_violations": [{"field": "type", "description": "type is required"}]}}
```

## Default Table Fields

When you create a new bitable, the default table comes with:

| Name      | type | is_primary | Deletable? |
|-----------|------|------------|------------|
| 文本      | 1    | true       | ❌ No (error 1254046) |
| 单选      | 3    | false      | ✅ Yes |
| 日期      | 5    | false      | ✅ Yes |
| 附件      | 17   | false      | ✅ Yes |

The primary field can only be renamed (via PUT), never deleted.
