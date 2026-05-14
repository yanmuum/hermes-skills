# LAN / Phone Access Walkthrough — WSL Open WebUI

## Scenario

User wants to access Open WebUI (running in WSL2) from their phone browser on the same WiFi network.

## Steps performed

### 1. Find Windows LAN IP
```
powershell.exe -Command "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi','Ethernet','以太网' | Select-Object IPAddress"
```
Result: `192.168.1.4`

### 2. Find WSL IP
```
ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1
```
Result: `172.26.246.0`

### 3. Change service to bind 0.0.0.0
Modified `/tmp/start-webui.sh`:
- `--host 127.0.0.1` → `--host 0.0.0.0`

### 4. Kill and restart Open WebUI
```
pkill -f "open-webui serve"
# Start fresh (background mode)
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
open-webui serve --host 0.0.0.0 --port 8080
```

### 5. Set up Windows port forwarding (elevated)
```
echo 'netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8080 connectaddress=172.26.246.0 connectport=8080' > /mnt/c/Windows/Temp/addproxy8080.bat
echo 'netsh advfirewall firewall add rule name="Open WebUI" dir=in action=allow protocol=TCP localport=8080' >> /mnt/c/Windows/Temp/addproxy8080.bat
echo 'exit' >> /mnt/c/Windows/Temp/addproxy8080.bat
powershell.exe -Command "Start-Process cmd.exe -ArgumentList '/c C:\Windows\Temp\addproxy8080.bat' -Verb RunAs"
```

### 6. Verify
```
powershell.exe -Command "netsh interface portproxy show all"
# Expected: 0.0.0.0:8080 → 172.26.246.0:8080
powershell.exe -Command "netsh advfirewall firewall show rule name='Open WebUI'"
# Expected: Enabled, Allow, TCP port 8080
```

### 7. Access from phone
Browser → `http://192.168.1.4:8080`

### 8. Remote access via Tailscale (outside LAN)
If you want to access from outside the office (not on same WiFi), install Tailscale instead.
See the main SKILL.md → "Remote Access via Tailscale" section.

## Environment details
- Windows WSL2, Ubuntu
- Open WebUI via pip (Python)
- Hermes Gateway as API backend (port 8642)
- Windows proxy (Clash/7890) interferes with localhost — always unset before starting services
- Phone: same WiFi (192.168.1.x subnet)

## Notes for Tailscale integration

- The portproxy set up here (`0.0.0.0:8080 -> <WSL_IP>:8080`) also works through the Tailscale virtual interface. After setting up Tailscale for remote access, the phone can use `http://<TAILSCALE_IP>:8080` with the same portproxy rules in place — no extra configuration needed.
- If the phone can't connect via Tailscale IP, verify with `Test-NetConnection -ComputerName <TAILSCALE_IP> -Port 8080` from Windows. If True, the phone's Tailscale app is disconnected (check `tailscale status`).
