# Cron-Triggered Bitable Data Sync

Pattern for automatically scanning data and updating a Feishu bitable on a schedule.

## Use Case

Regularly scan for new items (e.g., newly added AI skills) and append them to a bitable daily at a fixed time.

## Architecture

```
cron (17:00 daily)
  └─ cronjob: 每日技能新增检查
       └─ script: ~/.hermes/scripts/skills_daily_check.py
            ├─ 1. Get Feishu token (via Windows curl.exe for WSL proxy)
            ├─ 2. List existing records → build set of known items
            ├─ 3. Scan ~/.hermes/skills/ → find new items by mtime
            ├─ 4. Insert new items as records
            └─ 5. Print status (cron captures stdout)
```

## Key Design Decisions

1. **Windows curl.exe for API calls** — Python `requests` hangs in WSL after 1-2 calls due to proxy DNS hijacking (see `wsl-curl-workaround.md`). Always use `/mnt/c/Windows/System32/curl.exe` via `subprocess.run`.

2. **Field names as keys** — `{"fields": {"技能名称": "value"}}` — the dict key is the **column header visible in the Feishu UI**, NOT the internal `field_id`.

3. **Frontmatter vs directory name** — Skills' display names come from SKILL.md frontmatter `name:` field, not the directory name. Always parse frontmatter for the canonical name when comparing with bitable records.

4. **Cutoff timestamp** — Skip bulk-initialized items by comparing mtime against a known batch-install timestamp. Use `>` comparison on floats (file mtime includes fractional seconds).

## Cron Setup

```bash
# Create via the cronjob tool (NOT system cron):
cronjob action=create \
  name="每日技能新增检查" \
  schedule="0 17 * * *" \
  script="skills_daily_check.py" \
  deliver="origin"
```

- `deliver=origin` sends the script's stdout back to the original conversation
- Script must be in `~/.hermes/scripts/` and referenced by filename only
- Cron job runs in the gateway process environment (has access to `FEISHU_APP_ID`/`FEISHU_APP_SECRET`)

## Script Template

```python
#!/usr/bin/env python3
import os, sys, json, subprocess

CURL = "/mnt/c/Windows/System32/curl.exe"
APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
APP_TOKEN = "your_bitable_app_token"
TABLE_ID = "your_table_id"

def call_feishu(method, path, token=None, data=None):
    url = f"https://open.feishu.cn{path}"
    cmd = [CURL, "-s", "--connect-timeout", "15", "--max-time", "30",
           "-X", method]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += ["-H", "Content-Type: application/json; charset=utf-8"]
    if data:
        cmd += ["-d", json.dumps(data, ensure_ascii=False)]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}

def get_token():
    r = call_feishu("POST", "/open-apis/auth/v3/tenant_access_token/internal",
                     data={"app_id": APP_ID, "app_secret": APP_SECRET})
    return r["tenant_access_token"]

# ↑ Extend this template with your data-scraping logic ↓
```

## Pitfalls

- **Token expiry**: Token lasts ~2 hours. If script runs for >2h, it'll 401. Regenerate inside loop.
- **Empty records**: New bitables have ~10 empty placeholder records. Delete them first or they'll appear as blank rows.
- **Rate limits**: Multiple rapid POST requests may trigger Feishu rate limiting. Add `time.sleep(0.3)` between inserts if >20 records.
- **Curl args order**: URL must be the LAST argument to curl.exe.
- **No proxy config needed**: Windows curl auto-detects Windows system proxy.
