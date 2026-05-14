# WSL Network Dependencies — Polymarket API Access

## Architecture

```
┌──────────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│  WSL (Linux VM)      │  ──►   │  Windows Host     │  ──►   │  Internet        │
│                      │  :7890 │  Clash Proxy      │        │  (Polymarket API)│
│  Default gateway:    │        │  172.26.240.1     │        │                  │
│  172.26.240.1        │        │  (vEthernet IP)   │        │                  │
└──────────────────────┘        └──────────────────┘        └──────────────────┘
```

- WSL2 uses a virtual NIC with its own subnet (typically 172.x.x.x)
- The Windows host is reachable at the default gateway address (found via `ip route show default`)
- The Clash proxy (or similar tunnel) runs on the Windows host and listens on port 7890
- All outbound HTTPS from WSL **must** route through this proxy — there is no direct internet access via HTTPS

## Key Discovery Commands

```bash
# Find your WSL gateway (Windows host IP)
ip route show default

# Check if Clash proxy is listening
timeout 2 bash -c 'echo > /dev/tcp/{GATEWAY_IP}/7890' 2>/dev/null && echo "PROXY RUNNING" || echo "PROXY DOWN"

# Test general internet reachability (ICMP — may work even when HTTPS is blocked)
ping -c 1 -W 3 8.8.8.8

# Test HTTPS (will fail without proxy)
curl -s --connect-timeout 5 'https://google.com'

# Test HTTPS via proxy
curl -sx http://{GATEWAY_IP}:7890 --connect-timeout 10 'https://httpbin.org/ip'
```

## Troubleshooting Flowchart

Problem: Polymarket API calls time out from WSL
│
├─ Check proxy availability
│  └─ Port 7890 on Windows host OPEN?
│     ├─ YES → Proxy is running. Check if the proxy itself can reach the API.
│     │  (Try `curl -sx http://172.26.240.1:7890 ...` from WSL)
│     └─ NO  → Proxy service (Clash, V2Ray, etc.) is NOT running.
│              └─ Start the proxy on Windows host:
│                 - Clash: check system tray icon, right-click → "Start"
│                 - V2Ray/other: start the service/process manually

## Common Failure Patterns

### 1. Proxy Not Running (most common)
- **Symptom:** All HTTPS connections from WSL time out, including google.com
- **Diagnosis:** `timeout 2 bash -c 'echo > /dev/tcp/172.26.240.1/7890'` fails
- **Fix:** Start Clash or equivalent proxy on Windows

### 2. Proxy Running But Tunnel Down
- **Symptom:** Proxy port is open, but external HTTPS still fails
- **Diagnosis:** Proxy is running but the tunnel/vpn/proxy rule to Polymarket is down
- **Fix:** Check the proxy's connection status, restart if needed

### 3. DNS Resolution Issues
- **Symptom:** `getent hosts data-api.polymarket.com` returns no IPv4 address (only IPv6)
- **Context:** Polymarket's API sometimes resolves to IPv6 only, and WSL may not have IPv6 connectivity
- **Fix:** Force IPv4 with `curl -s4 ...` or use a proxy that handles IPv4<->IPv6 bridging

### 4. Script-embedded Proxy Fails But Shell Curl Works
- **Symptom:** Python script with hardcoded proxy times out, but `curl -sx ...` from shell works
- **Diagnosis:** Environment variable `http_proxy` may be interfering (script reads `http_proxy` env var)
- **Fix:** Clear the env var: `http_proxy='' python3 script.py`

## When All Else Fails

- **Bypass the API entirely:** Open the Polymarket wallet profile in a browser and use `browser_console` to extract data via `fetch()` — the browser's network stack handles the proxy layer automatically
- **Check from Windows side:** Run `curl` in PowerShell on Windows to see if the API is reachable outside WSL
- **Wait and retry:** Network conditions may be transient — the next cron run might succeed
