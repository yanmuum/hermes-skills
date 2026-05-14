#!/usr/bin/env python3
"""
Complete working example: Create a Feishu bitable with custom fields.

Run via terminal (inherits FEISHU_APP_SECRET from gateway process):
    cd /home/yanmuu/.hermes/hermes-agent
    source venv/bin/activate
    python /tmp/this_script.py

Environment variables (automatically set by Hermes gateway):
    FEISHU_APP_ID      — cli_a977e0167e3a1bc4
    FEISHU_APP_SECRET  — (automatically passed to terminal subprocess)
"""
import os, sys, json, time
from datetime import datetime
import requests

# === CONFIG ===
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a977e0167e3a1bc4")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
if not APP_SECRET:
    print("ERROR: FEISHU_APP_SECRET not found in environment.")
    print("Run this script from the terminal (inherits gateway env vars).")
    sys.exit(1)

# === STEP 1: Get token ===
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET}
)
token_data = resp.json()
if token_data.get("code") != 0:
    print(f"Token failed: {token_data}")
    sys.exit(1)
token = token_data["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
print("✅ Token obtained")

# === STEP 2: Create bitable ===
resp = requests.post(
    "https://open.feishu.cn/open-apis/bitable/v1/apps",
    headers=headers,
    json={"name": "设计项目收入与支出"}
)
data = resp.json()
if data.get("code") != 0:
    print(f"Create failed: {data}")
    sys.exit(1)
app_token = data["data"]["app"]["app_token"]
print(f"✅ Bitable created: {app_token}")

# === STEP 3: Get default table ===
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables",
    headers=headers
)
table_id = resp.json()["data"]["items"][0]["table_id"]
print(f"✅ Default table ID: {table_id}")

# Rename table (use PATCH)
resp = requests.patch(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}",
    headers=headers,
    json={"name": "项目记录"}
)
print(f"✅ Table renamed: {resp.json().get('msg')}")

# === STEP 4: Add fields ===
fields = [
    {"field_name": "序号", "type": 1, "property": {}},
    {"field_name": "日期", "type": 5, "property": {"auto_fill": True, "date_formatter": "yyyy/MM/dd"}},
    {"field_name": "客户名称", "type": 1, "property": {}},
    {"field_name": "项目总金额", "type": 2, "property": {"formatter": "0", "decimal_places": 2}},
    {"field_name": "已收金额", "type": 2, "property": {"formatter": "0", "decimal_places": 2}},
    {"field_name": "未收金额", "type": 2, "property": {"formatter": "0", "decimal_places": 2}},
    {"field_name": "支出设计费", "type": 2, "property": {"formatter": "0", "decimal_places": 2}},
    {"field_name": "备注", "type": 1, "property": {}},
]

for f in fields:
    resp = requests.post(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        headers=headers, json=f
    )
    d = resp.json()
    if d.get("code") == 0:
        print(f"  ✅ {f['field_name']}")
    else:
        print(f"  ❌ {f['field_name']}: {d.get('msg')}")

# === STEP 5: Rename primary field (default "文本" → "项目名称") ===
fields_resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
    headers=headers
)
for field in fields_resp.json()["data"]["items"]:
    if field.get("is_primary"):
        primary_id = field["field_id"]
        # Use PUT (not PATCH!) to rename
        requests.put(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{primary_id}",
            headers=headers,
            json={"field_name": "项目名称", "type": 1}
        )
        print(f"✅ Primary field renamed to '项目名称'")
        break

# === STEP 6: Delete default "单选" and "附件" fields ===
for f in fields_resp.json()["data"]["items"]:
    if f["field_name"] in ("单选", "附件"):
        requests.delete(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{f['field_id']}",
            headers=headers
        )
        print(f"✅ Deleted default '{f['field_name']}'")

# === STEP 7: Clean up empty placeholder records ===
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    headers=headers, params={"page_size": 50}
)
deleted = 0
for rec in resp.json()["data"]["items"]:
    if not rec.get("fields"):  # empty record
        requests.delete(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{rec['record_id']}",
            headers=headers
        )
        deleted += 1
        time.sleep(0.1)
if deleted:
    print(f"✅ Deleted {deleted} empty placeholder records")

print(f"\n{'='*50}")
print(f"🎉 All done!")
print(f"🔗 https://bytedance.feishu.cn/base/{app_token}")
print(f"{'='*50}")
