# WSL Curl Workaround — Calling Feishu API from WSL

## Problem

In WSL2 behind a Windows proxy client (Clash, V2Ray, Surge, corporate VPN), DNS for `open.feishu.cn` gets hijacked to `198.18.0.x` (RFC 2544 benchmarking range used by intercepting proxies). 

- Python's `requests.get()` works for 1-2 calls then hangs/timeouts.
- `curl` from WSL also hangs.
- Environment vars `HTTP_PROXY`/`HTTPS_PROXY` may be empty.

## Root Cause

Windows proxy software intercepts TLS connections and re-routes traffic through a local proxy. DNS resolves `open.feishu.cn` → `198.18.0.28` inside WSL, but this IP is only reachable from Windows, not from WSL's network namespace.

## Solution: Use Windows curl.exe

The Windows-side curl binary at `/mnt/c/Windows/System32/curl.exe` uses Windows networking (including the proxy tunnel), so it can reach `open.feishu.cn` reliably.

### Helper Pattern

```python
import os, sys, json, subprocess

def call_feishu(method, path, token=None, data=None):
    """Call Feishu API via Windows curl to bypass WSL proxy issues."""
    url = f"https://open.feishu.cn{path}"
    cmd = ["/mnt/c/Windows/System32/curl.exe",
           "-s", "--connect-timeout", "10", "--max-time", "20"]
    cmd += ["-X", method]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += ["-H", "Content-Type: application/json; charset=utf-8"]
    if data:
        cmd += ["-d", json.dumps(data, ensure_ascii=False)]
    cmd += [url]  # ⚠️ URL must be the LAST argument
    result = subprocess.run(cmd, capture_output=True, text=True)
    out = result.stdout.strip()
    if not out:
        return {"error": f"Empty response. stderr: {result.stderr[:200]}"}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"error": f"JSON parse error: {out[:300]}"}
```

### Getting Token

```python
r = call_feishu("POST", "/open-apis/auth/v3/tenant_access_token/internal",
                data={"app_id": APP_ID, "app_secret": APP_SECRET})
token = r["tenant_access_token"]
```

### Calling the Bitable API

```python
r = call_feishu("POST",
    f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
    token,
    {"field_name": "新字段", "type": 1})
```

### Calling the IM (Chat) API

```python
r = call_feishu("POST", "/open-apis/im/v1/chats", token, {
    "name": "新群", "chat_mode": "group", "chat_type": "private"
})
```

## Pitfalls

1. **URL must be the LAST argument** — curl parses positional args; if another flag follows the URL it may not work.
2. **`--max-time` sets per-transfer timeout** — 20s is usually enough for Feishu API.
3. **Windows curl path** — `/mnt/c/Windows/System32/curl.exe` exists on all modern Windows 10/11 builds.
4. **Rate limits** — Windows curl is still subject to Feishu's API rate limits (same as Python requests).
5. **No proxy env need** — Windows curl auto-detects Windows system proxy settings, so no `HTTP_PROXY` needed.
