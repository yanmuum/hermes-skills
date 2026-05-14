# Tailscale Setup Walkthrough — WSL Open WebUI Remote Access

## Scenario

User wants to access Open WebUI (running in WSL2) from their phone browser when **away from the office** (not on same WiFi). Tailscale creates a virtual private network.

## Prerequisites

- Open WebUI already running in WSL on port 8080
- Startup script at `/tmp/start-webui.sh` using `--host 0.0.0.0` (not localhost-only)
- Windows port forwarding already set up for LAN access (optional — Tailscale doesn't need it, but doesn't hurt)

## Steps performed

### 1. Install Tailscale on Windows

```bash
# The file was already downloaded to C:\Users\Administrator\Downloads\
# Install silently:
powershell.exe -Command "Start-Process -FilePath 'C:\Users\Administrator\Downloads\TailscaleSetup.exe' -ArgumentList '/S' -Wait"
```

If not already downloaded:
```bash
powershell.exe -Command "Start-BitsTransfer -Source 'https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe' -Destination 'C:\Users\$env:USERNAME\Downloads\TailscaleSetup.exe' -Priority High"
```

### 2. Verify installation

```bash
powershell.exe -Command "Get-Service -Name Tailscale"
# Should show Status: Running
ls "/mnt/c/Program Files/Tailscale/"
# Should show tailscale.exe, tailscaled.exe, tailscale-ipn.exe, wintun.dll
```

### 3. Authenticate with Tailscale

```bash
powershell.exe -Command "& 'C:\Program Files\Tailscale\tailscale.exe' up"
```

Output provides an auth URL:
```
To authenticate, visit:
	https://login.tailscale.com/a/xxxxxxxxxx
```

Open this URL in a browser. Sign in with:
- Email (receives a verification code)
- Google / GitHub / Microsoft / Apple OAuth

### 4. Get the Tailscale IP

```bash
powershell.exe -Command "& 'C:\Program Files\Tailscale\tailscale.exe' ip -4"
# Returns e.g. 100.120.30.40
```

### 5. Ensure Open WebUI binds to 0.0.0.0

The startup script was modified from:
```
open-webui serve --host 127.0.0.1 --port 8080
```
to:
```
open-webui serve --host 0.0.0.0 --port 8080
```

### 6. Install Tailscale on phone

- iPhone: App Store → "Tailscale"
- Android: Google Play → "Tailscale"
- Log in with the **same Tailscale account**

### 7. Access from phone browser

`http://100.x.x.x:8080` (where 100.x.x.x is the Tailscale IP from step 4)

## Result

✅ Open WebUI is accessible from anywhere with internet — office, home, coffee shop, train.

## Notes

- The `tailscale` command is NOT in Windows PATH by default. Always use full path:
  `'C:\Program Files\Tailscale\tailscale.exe'`
- When invoking from WSL via PowerShell, use:
  `powershell.exe -Command "& 'C:\Program Files\Tailscale\tailscale.exe' status"`
- Tailscale free tier: up to 100 devices, unlimited users
- No port forwarding needed on router; Tailscale uses WireGuard tunnels (UDP-based, NAT-traversing)
- The Windows `netsh portproxy` on `0.0.0.0` DOES work with the Tailscale virtual interface — confirmed in real deployment. Test with `Test-NetConnection -ComputerName <TAILSCALE_IP> -Port 8080` from Windows to verify.
- If the phone shows "no response" despite setup being correct, the most likely cause is the phone's Tailscale app being disconnected. Run `tailscale status` to check — `offline, last seen Xh ago` means the phone needs to open the Tailscale app and tap Connect.
- **Proxy blocks curl/wget from WSL to external domains** — even with `unset http_proxy`, curl may still use the proxy because the terminal tool environment may set it at a higher level. For reliable downloads from WSL, use Start-BitsTransfer on Windows:
  ```bash
  powershell.exe -Command "Start-BitsTransfer -Source 'URL' -Destination 'C:\path\to\file.exe' -Priority High"
  ```
  Or set the proxy explicitly in the PowerShell environment before using Windows curl.exe.
- **Cannot install Tailscale inside WSL** if `sudo` requires a password — install on Windows host only. WSL services are reachable through the Windows Tailscale IP + netsh portproxy.
