---
name: feishu-bitables
description: Create and manage Feishu/Lark 多维表格 (bitables) via the Open API — app creation, table management, field schema, permission setup.
category: productivity
tags:
  - feishu
  - lark
  - bitable
  - 多维表格
  - api
related_skills: [wsl-deployment]
---

# Feishu Bitable (多维表格) Operations

Create, configure, and manage Feishu bitables (多维表格 / Base) programmatically via the Feishu Open API.

## When to Use

- User asks to create a Feishu 多维表格 / bitable / base
- User asks to add fields/columns to an existing bitable
- User asks to import data into a bitable
- You need to set up a tracking spreadsheet in Feishu
- **User says "飞书不回消息" / Feishu bot is not replying** — see `references/gateway-troubleshooting.md` for session corruption diagnosis and fix

## Prerequisites

The Feishu app must have the **`bitable:app`** (多维表格) permission scoped. This is **not granted by default** — the user must:

1. Go to [Feishu Developer Console](https://open.feishu.cn/app) → Your App → **权限管理 (Permissions)**
2. Add **「多维表格 / bitable:app」** permission (查看、评论、编辑和管理多维表格)
3. **Publish a new version** of the app (版本管理与发布) for the permission to take effect

> ⚠️ **CRITICAL PITFALL**: Adding the permission is NOT enough. The app MUST be **re-published** (发布上线) before the API accepts the new scope. If you get error `99991672` (Access denied / bitable:app required) even after the user says they "开通了权限", the app hasn't been published yet. Guide them to publish.

## API Flow

### 1. Get Tenant Access Token

Environment variables (set by the gateway):
- `FEISHU_APP_ID` — the app's client ID
- `FEISHU_APP_SECRET` — the app's client secret

```python
import requests
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}
)
token = resp.json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
```

### 2. Create a Bitable App

```python
resp = requests.post(
    "https://open.feishu.cn/open-apis/bitable/v1/apps",
    headers=headers,
    json={"name": "你的表格名称"}
)
app_token = resp.json()["data"]["app"]["app_token"]
```

URL pattern: `https://bytedance.feishu.cn/base/{app_token}`

### 3. List / Rename Tables

Every new bitable has a default table (usually "表1" or "数据表" or "Table1").

```python
# List tables
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables",
    headers=headers
)
table_id = resp.json()["data"]["items"][0]["table_id"]

# Rename table — use PATCH, NOT PUT
# ❌ PUT .../tables/{table_id}/name returns 404
# ✅ PATCH .../tables/{table_id} works
requests.patch(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}",
    headers=headers,
    json={"name": "新工作表名"}
)
```

### 4. Add Fields

```python
fields = [
    {"field_name": "序号", "type": 1, "property": {}},
    {"field_name": "日期", "type": 5, "property": {"auto_fill": True, "date_formatter": "yyyy/MM/dd"}},
    {"field_name": "金额", "type": 2, "property": {"formatter": "0", "decimal_places": 2}},
]
for field in fields:
    requests.post(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        headers=headers,
        json=field
    )
```

New fields are always appended as the last column. To reorder, delete and recreate.

### 5. Update Fields

⚠️ **Use PUT, NOT PATCH** — PATCH on field endpoints returns 404. PUT requires complete field data.

```python
# Rename field
requests.put(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
    headers=headers,
    json={"field_name": "新名称", "type": 1}  # type is REQUIRED
)

# Update field properties (e.g., enable auto-fill for date)
requests.put(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
    headers=headers,
    json={
        "field_name": "日期", "type": 5,
        "property": {"auto_fill": True, "date_formatter": "yyyy/MM/dd"}
    }
)
```

### 6. Delete Fields

```python
requests.delete(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
    headers=headers
)
```

⚠️ **Primary field** (`is_primary=true`) cannot be deleted (error `1254046`). Rename it instead.
⚠️ **Idempotent deletion**: Delete may time out but succeed on server. Run DELETE again — if you get `FieldIdNotFound`, it's gone.

### 7. Record Operations

**Create a record:**
```python
from datetime import datetime
body = {"fields": {
    "序号": "PROJ-001",
    "日期": int(datetime.now().timestamp()),  # Unix timestamp in seconds
    "客户名称": "...",
    "项目总金额": 50000,
}}
resp = requests.post(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    headers=headers, json=body
)
```

**List records:**
```python
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    headers=headers, params={"page_size": 20}
)
```

**Delete records:**
```python
requests.delete(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
    headers=headers
)
```

### 8. View Operations

**List views:**
```python
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
    headers=headers
)
```

**Create views:**
```python
# Grid (table) view
resp = requests.post(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
    headers=headers,
    json={"view_name": "项目总表", "view_type": "grid"}
)

# Kanban view — great for visualizing SingleSelect progress
resp = requests.post(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
    headers=headers,
    json={"view_name": "进度看板", "view_type": "kanban"}
)
kanban_id = resp.json()["data"]["view"]["view_id"]

# Set kanban group field (must be SingleSelect, e.g. 工程设计进度)
requests.patch(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views/{kanban_id}",
    headers=headers,
    json={"property": {"kanban_field_id": "<single_select_field_id>"}}
)

# Gantt view — time-axis timeline
resp = requests.post(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
    headers=headers,
    json={"view_name": "甘特图", "view_type": "gantt"}
)
gantt_id = resp.json()["data"]["view"]["view_id"]

# Set gantt date range fields
requests.patch(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views/{gantt_id}",
    headers=headers,
    json={
        "property": {
            "gantt_start_date_field_id": "<start_date_field_id>",
            "gantt_end_date_field_id": "<end_date_field_id>"
        }
    }
)
```

**Create a filtered view:**
```python
resp = requests.post(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
    headers=headers,
    json={
        "view_name": "进行中项目",
        "view_type": "grid",
        "property": {
            "filter_info": {
                "conjunction": "and",
                "conditions": [{
                    "field_id": "<field_id>",
                    "operator": "isNot",         # or "is", "contains", "greater", etc.
                    "value": ["已完结"],
                    "condition_type": 1
                }]
            }
        }
    }
)
```

**Update view (e.g., rename):**
```python
requests.patch(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}",
    headers=headers,
    json={"view_name": "新视图名"}
)
```

**Set sort on view** — ⚠️ PATCH with `sort_info` returns 200 but the property doesn't persist in the API response (`property` stays `null`). The `AppTableViewProperty` model does NOT include `sort_info` — it only has `filter_info`, `hidden_fields`, `hierarchy_config`. For reliable sorting, instruct the user to set sort in the Feishu UI (click column header → sort descending).

### 9. Clean Up Empty Records

New bitables come with ~10 empty placeholder records. Remove them:
```python
resp = requests.get(list_url, headers=headers, params={"page_size": 50})
for rec in resp.json()["data"]["items"]:
    if not rec["fields"]:  # no field data = empty
        requests.delete(
            f"{list_url}/{rec['record_id']}",
            headers=headers
        )
```

## Field Type Reference

Valid type IDs for the Create/Update Field API:

| type | Name          | Notes |
|------|---------------|-------|
| 1    | Text          | 文本 |
| 2    | Number        | 数字 — use for currency/money values |
| 3    | SingleSelect  | 单选 |
| 4    | MultiSelect   | 多选 |
| 5    | DateTime      | 日期 — use `property.auto_fill` + `property.date_formatter` |
| 7    | Checkbox      | 复选框 |
| 11   | Phone         | 电话 |
| 13   | URL           | 链接 |
| 15   | Location      | 位置 |
| 17   | Attachment    | 附件 |
| 18   | Person        | 人员 — ❌ API创建返回 `LinkFieldPropertyError`，改用 Text(type=1) 并在 UI 中切换 |
| 20   | Formula       | 公式 |
| 21   | DuplexLink    | 双向关联 |
| 22   | CreatedTime   | 创建时间 |
| 23   | Group         | 分组 |
| 1001 | Progress      | 进度 |
| 1002 | Rating        | 评分 |
| 1003 | Currency      | ❌ **不工作** — 返回 `CreatedUserFieldPropertyError`，用 type=2 替代 |
| 1004 | Email         | 邮箱 |
| 1005 | AutoNumber    | 自动编号 |
```

## Pitfalls

1. **Permission delay**: After adding `bitable:app` in the dev console, you MUST publish a new app version. Publishing may take a few minutes to propagate. Adding the permission alone is NOT enough — the app must be re-published (发布上线) before the API accepts the new scope.

2. **Field ID != Field Name**: The API assigns a `field_id` automatically when you create a field. ⚠️ **When inserting records, you reference fields by their DISPLAY NAME as dict keys, NOT by field_id.** Using field_id as the key returns `FieldNameNotFound` (error 1254045). The correct format is `{"fields": {"我的字段名": value}}` — the dict key is what the user sees as the column header.

3. **Tenant token expiry**: Tenant access tokens expire after ~2 hours. Re-generate if you get 401 errors.

4. **Secret redaction**: The Hermes agent redacts `FEISHU_APP_SECRET` from terminal output and Python os.environ. To use it, write a Python script to a file and run it via terminal (inherits the environment from the gateway process).

5. **Field type 10 doesn't exist**: The error message lists type 10 as a valid option, but creating a field with type=10 returns a `field validation failed` error. Use type=2 (Number) for monetary values instead.

6. **type=1003 (Currency) is broken**: Returns `CreatedUserFieldPropertyError`. Use type=2 instead.

7. **Field update requires PUT, not PATCH**: PATCH returns 404. PUT requires the `type` parameter.

8. **Default bitable has empty placeholder records**: ~10 empty records are created automatically. Clean them up by querying and deleting records with empty `fields` dicts.

9. **Primary field can't be deleted**: The default `is_primary=true` field (e.g., "文本") returns error `1254046` on delete. Rename it instead.

10. **Sort on views doesn't persist via API**: PATCH with `sort_info` returns 200 but the setting doesn't stick. The `AppTableViewProperty` model has no `sort_info` field. Advise users to sort in the Feishu UI.

12. **New records go to the bottom**: API always appends at the end. Combine with UI sort (date desc) to show newest first.

13. **日期显示为 1970 年 — 时间戳单位问题**: 飞书 DateTime 字段期望的是 **毫秒（milliseconds）** 时间戳，不是秒。传秒（如 `1778169600`）显示为 1970 年。必须乘以 1000：`int(timestamp * 1000)`

14. **Person field (type=18) reliably fails**: Creating a Person field via the API returns `LinkFieldPropertyError` regardless of permissions. The `contact:user` scope alone does NOT enable it. **Fallback**: Use Text (type=1) for now. Tell the user to right-click the column header → 「字段类型」→ switch to 「人员」in the Feishu UI — this works after the column has data in it.

15. **WSL proxy blocks open.feishu.cn**: In WSL behind a Windows proxy client (Clash/V2Ray/Surge), DNS for `open.feishu.cn` gets hijacked to `198.18.x.x`, causing Python `requests` to hang/ timeout after 1-2 successful calls. Solution: route API calls through Windows curl — `CURL = "/mnt/c/Windows/System32/curl.exe"`, use `subprocess.run` instead of `requests`. Windows-side proxy handles the tunnel correctly. For comprehensive WSL proxy/networking patterns (conditional proxy aliases, DNS config, VPN disconnect recovery), see the **`wsl-deployment`** skill (this is its primary domain).

16. **AutoNumber field: `auto_serial.type` must be `auto_increment_number`**: The type value `"auto_increment"` is INVALID. The only valid options are `"custom"` and `"auto_increment_number"`. Using `"auto_increment"` returns error `99992402` with `field_violations` describing valid options.

17. **Formula field (`type=20`): DO NOT include `formula_return_type`**: Including `formula_return_type` in the `property` dict causes `FormulaFieldPropertyError` (code `1254091`). Create formulas with just `formula_expression`:
    ```python
    # ✅ Correct
    {"field_name": "剩余天数", "type": 20, "property": {"formula_expression": 'DATETIME_DIFF({截止日期}, TODAY(), "days")'}}
    
    # ❌ Wrong — formula_return_type causes FormulaFieldPropertyError
    {"field_name": "剩余天数", "type": 20, "property": {"formula_expression": "...", "formula_return_type": 2}}
    ```
    The return type is determined implicitly by the formula expression: number expressions produce numbers, text expressions produce text. If you need to control formatting, omit `formula_expression` initially (creates blank formula) and set it later via PUT.

18. **Group Chat creation requires `im:chat:create` permission**: Even if `im:chat` (get chat info) is enabled, creating groups needs the `im:chat:create` scope. Both must be added in the dev console AND the app must be re-published. The bot creates the group but the user is NOT auto-added — you must explicitly add them via `POST /im/v1/chats/{chat_id}/members?member_id_type=open_id`.

19. **Bot in groups: `im.message.receive_v1` needs group chat type**: The event subscription in the dev console must explicitly enable 「群聊(group)」 chat type for `im.message.receive_v1`. DM-only subscription silently drops group @mentions. After changing, re-publish. Verify by checking gateway logs for the group's chat_id.

20. **Sending messages to group requires `receive_id_type=chat_id`**: When sending to a group chat, the API query parameter `receive_id_type=chat_id` is required. Default is `open_id`, which won't match a group chat_id.
    ```
    POST /open-apis/im/v1/messages?receive_id_type=chat_id
    {"receive_id": "oc_xxx", "msg_type": "text", "content": "{\"text\":\"Hello\"}"}
    ```

21. **File attachments from users may not arrive**: When a user says they sent a PDF/photo/file in Feishu chat, do NOT assume it was received. The gateway logs show every inbound message with its `media` flag — `media=0` means no attachment, `media=1` means attachment present. If the gateway was disconnected when the file was sent, Feishu does NOT replay it. See `references/feishu-file-attachment-diagnostics.md` for the full diagnostic workflow. When in doubt, ask the user to paste content directly rather than sending as a file.

## Bulk Import from Filesystem Search

When the user asks to search Windows/local folders for projects matching a keyword (e.g. "绣缎") and import results into an existing bitable:

1. **Search the filesystem** — user's F:/G:/D: drives are under `/mnt/f/`, `/mnt/g/`, `/mnt/d/`. Use `find` with **`-maxdepth`** (4-8 depending on nesting) to avoid timeout on large directories:
   ```bash
   cd "/mnt/f/【建筑设计】" && find . -maxdepth 6 -iname '*绣缎*' 2>/dev/null
   ```

2. **Parse results into structured records** — group by directory/theme into a list of dicts mapping to the bitable's field names (not field_ids). Each record is one project row.

3. **Need a reliable entry point?** Write a Python script to `/tmp/`, run via `terminal` (inherits `FEISHU_APP_ID`/`FEISHU_APP_SECRET` from the gateway process, which is redacted from `os.environ` in Python).

4. **Use Windows curl for API calls** — Python `requests` to `open.feishu.cn` times out from WSL behind Windows proxy. Use `/mnt/c/Windows/System32/curl.exe` via `subprocess`:
   ```python
   CURL = ["/mnt/c/Windows/System32/curl.exe", "-s", "--connect-timeout", "10", "--max-time", "20"]
   cmd = CURL + ["-H", f"Authorization: Bearer {token}", url]
   result = subprocess.run(cmd, capture_output=True, text=True)
   ```

5. **Batch insert with rate limiting** — Feishu API accepts one record per POST. Add **`time.sleep(0.2)`** between records to avoid throttling. For 15-20 records expect ~3-4s total.

6. **Date field gotcha** — DateTime fields expect **millisecond** timestamps, not seconds. Convert:
   ```python
   from datetime import datetime, timezone
   def dt_ms(year, month, day):
       dt = datetime(year, month, day, tzinfo=timezone.utc)
       return int(dt.timestamp() * 1000)
   ```

7. **SingleSelect field reference by text** — When setting a SingleSelect field (e.g. "工程设计进度"), pass the option's display name as a string value, not its option ID. The API resolves it:
   ```python
   {"工程设计进度": "施工图设计"}  # ✅ not "optPdhrVNx"
   ```

## Reference

- `references/create_bitable.py` — complete reusable script to create a bitable with custom fields and tables
- `references/field_types.md` — detailed field type reference with working property formats
- `references/gateway-troubleshooting.md` — debug "bot not replying" issues: session corruption caused by orphan user messages, diagnosis via logs/gateway_state, and session cleaning fix
- `references/wsl-curl-workaround.md` — calling Feishu API from WSL when Windows proxy blocks `open.feishu.cn`, using Windows curl.exe
- `references/feishu-group-chat-setup.md` — creating groups, adding members, configuring group message receiving
- `references/engineering-project-mgmt-example.md` — complete working example: 20-field engineering project management bitable with kanban/gantt views
- `references/feishu-docx-direct-api-read.md` — reading Feishu Doc content via direct API when feishu_doc_read tool fails (e.g., "not in a Feishu comment context")
- `references/cron-sync-pattern.md` — automated daily data sync: cron + Python script + Feishu bitable — reading Feishu Doc content via direct API when feishu_doc_read tool fails (e.g., "not in a Feishu comment context")
