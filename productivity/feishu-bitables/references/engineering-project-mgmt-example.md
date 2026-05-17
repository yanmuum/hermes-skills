# Engineering Project Management Bitable — Working Example

This reference documents the complete creation of a 工程设计项目管理系统 (Engineering Project Management System) bitable, including all pitfalls encountered and their solutions.

## Bitable Created

- **Name**: 工程设计项目管理系统
- **App Token**: `Oo6ibAJtYad7P3sNscbcOQLKnYQ`
- **Table**: 项目总表 (ID: `tblqbxlJuSdQjA8D`)
- **URL**: https://bytedance.feishu.cn/base/Oo6ibAJtYad7P3sNscbcOQLKnYQ

## Field Schema (20 fields)

| # | Field Name | Type | Property |
|---|------------|------|----------|
| 1 | 工程项目名称 | Text (primary) | renamed from default |
| 2 | 序号 | AutoNumber (1005) | `auto_serial.type: "auto_increment_number"` |
| 3 | 项目负责人 | Text (fallback) | Person type failed — use Text, convert in UI |
| 4 | 规划设计要点 | Text | — |
| 5 | 工程设计进度 | SingleSelect (3) | Options: 未启动/方案设计/初步设计/施工图设计/施工配合/竣工验收/已完结 |
| 6 | 工程进度 | Progress (1001) | Visual percentage bar |
| 7 | 设计开始日期 | DateTime (5) | `date_formatter: "yyyy/MM/dd"` |
| 8 | 设计截止日期 | DateTime (5) | `date_formatter: "yyyy/MM/dd"` |
| 9 | 工程项目总造价 | Number (2) | `formatter: "0", decimal_places: 2` |
| 10 | 设计总费用 | Number (2) | `formatter: "0", decimal_places: 2` |
| 11-18 | 概算公司~施工公司 | Text (1) | 8 company role fields |
| 19 | 备注 | Text | — |
| 20 | 任务剩余天数 | Formula (20) | `DATETIME_DIFF({设计截止日期}, TODAY(), "days")` |
| 21 | 设计进度提醒 | Formula (20) | `IF({工程设计进度}="已完结", "✅已完成", IF(...))` |

## Views Created

| View | Type | Configuration |
|------|------|--------------|
| 项目总表 | Grid (default) | Renamed from "表格" |
| 进度看板 | Kanban | Grouped by 工程设计进度 field |
| 甘特图 | Gantt | Start: 设计开始日期, End: 设计截止日期 |
| 进行中项目 | Grid (filtered) | Filter: 工程设计进度 ≠ 已完结 |

## Verified Usage (2026-05-15)

Bulk-imported **19 projects** from F:\【建筑设计】 filesystem search (keyword: "绣缎") into this bitable via the records API. All field types confirmed working:

- **工程项目名称** (Text, primary) ✅
- **规划设计要点** (Text) — used for location/scope notes ✅
- **工程设计进度** (SingleSelect) — text value resolves correctly ✅
- **设计开始日期/设计截止日期** (DateTime) — millisecond timestamps confirmed ✅
- **备注** (Text) — multi-line notes work ✅

Key discovery: 0.2s delay between record inserts avoids throttling. 19 records inserted in ~4s with 0 failures.

## Pitfalls Encountered & Solutions

### 1. WSL Network Block
**DNS for `open.feishu.cn` hijacked to `198.18.0.28`** by Windows proxy software.
- Python `requests` times out after 1-2 successful calls.
- **Fix**: Use Windows curl.exe:
  ```python
  import subprocess, json
  cmd = ["/mnt/c/Windows/System32/curl.exe", "-s", "--connect-timeout", "10", "--max-time", "20",
         "-X", "POST",
         "-H", "Content-Type: application/json; charset=utf-8",
         "-d", json.dumps(request_body),
         url]
  result = subprocess.run(cmd, capture_output=True, text=True)
  response = json.loads(result.stdout)
  ```
- ⚠️ Must append the URL as the last argument in the cmd list.

### 2. AutoNumber Creation
**Error**: `field validation failed` — `property.auto_serial.type` value invalid.
- **Wrong**: `"type": "auto_increment"`
- **Correct**: `"type": "auto_increment_number"` or `"type": "custom"`
- Valid options: `["custom", "auto_increment_number"]`

### 3. Formula Field Creation
**Error**: `FormulaFieldPropertyError` (code 1254091)
- **Wrong**: Including `"formula_return_type"` in the property:
  ```python
  {"formula_expression": "...", "formula_return_type": 2}  # ❌
  ```
- **Correct**: Just `formula_expression`, no return type:
  ```python
  {"formula_expression": 'DATETIME_DIFF({截止日期}, TODAY(), "days")'}  # ✅
  ```
- Return type is determined implicitly by expression content.
- If all else fails, create the field with no property (empty formula), then PUT updates.

### 4. Person Field (type 18)
**Error**: `LinkFieldPropertyError`
- Creating Person fields via API fails unless app has `contact:user` scope and is re-published.
- **Fix**: Use Text (type 1) as fallback. User can right-click column → change to Person in UI.

### 5. Multi-step Field Creation Timeout
Creating 20+ fields sequentially causes total execution time > 60s.
- Timeout is per-API-call, but 20+ calls × ~2s ≈ long execution.
- Use minimal `time.sleep(0.2)` between calls, not 0.3+.
- Use retry logic (HTTPAdapter with Retry total=3, backoff_factor=1).

## Recommended Automation Rules (UI Setup)

Three automations to configure in the Feishu UI (右上角「自动化」):

1. **进度变更通知负责人**: Trigger: record update → condition: 工程设计进度 changes → action: send Feishu message to 项目负责人
2. **任务完成通知公司群**: Trigger: record update → condition: 工程设计进度 = 已完结 → action: send Feishu message to group chat
3. **每日到期提醒**: Trigger: scheduled (daily 09:00) → condition: 设计进度提醒 contains 🔴 or 🟡 → action: send Feishu message to 项目负责人
