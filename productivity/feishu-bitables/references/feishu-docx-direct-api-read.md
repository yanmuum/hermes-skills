# Reading Feishu Doc Content via Direct API (When feishu_doc_read Fails)

## Problem

The `feishu_doc_read` tool sometimes fails with:
```
Feishu client not available (not in a Feishu comment context)
```

This happens when the request comes from a regular chat message rather than a Feishu document comment event.

## Workaround: Direct API Call

Use the Feishu Open API's docx raw_content endpoint directly.

### Prerequisites
- The Feishu app must have the `docx:document:readonly` permission scoped and **published**
- The document must be a Feishu Doc (URL format: `my.feishu.cn/docx/TOKEN` or `my.feishu.cn/wiki/TOKEN`)
- This will NOT work for uploaded files (URL format: `my.feishu.cn/file/TOKEN`) — those are Drive files and need `drive:file:readonly` permission

### Code

```python
import requests, os

# Step 1: Get tenant access token
app_id = os.environ.get("FEISHU_APP_ID", "")
app_secret = os.environ.get("FEISHU_APP_SECRET", "")

resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=15
)
token = resp.json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Read docx raw content
doc_token = "AVWYdQw12oHcPgxcCJnckZDznbv"  # from URL: my.feishu.cn/docx/{doc_token}
resp = requests.get(
    f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content",
    headers=headers,
    timeout=15
)
data = resp.json()  # data["data"]["content"] contains the document text
```

### Permission Check

Use batch_query metadata API to check file type:

```python
resp = requests.post(
    "https://open.feishu.cn/open-apis/drive/v1/metas/batch_query",
    headers={**headers, "Content-Type": "application/json"},
    json={"request_docs": [{"doc_token": doc_token, "doc_type": "file"}]},
    timeout=15
)
# resp.json()["data"]["metas"][0] contains: doc_type, title, create_time, etc.
```

### Common Error: 99991672

```
Access denied. One of the following scopes is required: [drive:drive, ...]
```

The app hasn't been granted the required permission AND re-published. Adding the permission in the dev console is NOT enough — the app must be **重新发布上线** (re-published) for the new scope to take effect.

### File-to-Doc Conversion Workflow

If the user shares a Drive file (URL: `my.feishu.cn/file/TOKEN`) and you can't read it:
1. Tell the user to open the file in Feishu → click **更多** → **转存为文档** (convert to Feishu Doc)
2. The new URL will be `my.feishu.cn/docx/NEW_TOKEN` — this CAN be read via the API
3. The `docx:document:readonly` permission is sufficient for reading converted docs
