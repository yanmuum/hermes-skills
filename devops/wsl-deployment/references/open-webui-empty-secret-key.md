# Open WebUI: Empty .webui_secret_key File

## Error Signature

Open WebUI process reports:

```
Loading WEBUI_SECRET_KEY from file, not provided as an environment variable.
Loading WEBUI_SECRET_KEY from /home/yanmuu/.webui_secret_key
╭───────────────────── Traceback ─────────────────────╮
│ ...open_webui/env.py:602 in <module>                │
│     if WEBUI_AUTH and WEBUI_SECRET_KEY == '':       │
│ ❱   raise ValueError(ERROR_MESSAGES.ENV_VAR_NOT_FOUND)│
╰─────────────────────────────────────────────────────╯
```

The server appears to start (process runs, port 8080 shows LISTEN in `ss -tlnp`), but responds with empty reply — `curl -v` exits with code 52 ("Empty reply from server").

## Root Cause

The `~/.webui_secret_key` file exists in the filesystem but is **0 bytes** (empty). Open WebUI loads this file when `WEBUI_SECRET_KEY` env var is not set, and gets an empty string, triggering `ValueError`.

## Fix

```bash
openssl rand -base64 32 > ~/.webui_secret_key
# Then restart
bash /tmp/start-webui.sh
```

Or delete the file and use env var:

```bash
rm ~/.webui_secret_key
export WEBUI_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
open-webui serve --host 127.0.0.1 --port 8080
```

## Prevention

Always verify before starting:

```bash
ls -la ~/.webui_secret_key
```

If the file exists but is 0 bytes, it will cause a silent startup failure.

## Related: Connection Still Fails After Fix

If the server starts (returns 200) but you can't connect from Windows browser or curl:

1. **Proxy env vars** — check `http_proxy`, `https_proxy`, `all_proxy` are set.
   - `curl -v http://127.0.0.1:8080/` shows "Uses proxy env variable http_proxy" or "Uses proxy env variable all_proxy" → unset them all:
     ```bash
     unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
     ```
   - `all_proxy` is especially dangerous — it uses **SOCKS5 protocol** to tunnel ALL traffic, including non-HTTP connections. Even if `http_proxy` is unset, `all_proxy` alone will route traffic through the Windows proxy.
   - Even with `--noproxy 127.0.0.1`, the hostname string `localhost` still routes through proxy. Use `http://127.0.0.1:8080/` directly in the browser.

2. **Server not fully initialized** — Open WebUI runs DB migrations + downloads embedding model on first start. Takes 10–30 seconds before responding. Poll with:
   ```bash
   while ! curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/ 2>/dev/null; do
     sleep 2
   done
   echo "Server ready"
   ```

3. **Server-side proxy trap (trust_env=True)** — Even after you fix curl, the Open WebUI server's OWN HTTP requests (fetching model lists from Ollama/Hermes) may fail if proxy vars were set when the server started. The aiohttp client uses `trust_env=True`, meaning it checks proxy env vars internally. **Fix:** restart the server after unsetting proxy vars.
