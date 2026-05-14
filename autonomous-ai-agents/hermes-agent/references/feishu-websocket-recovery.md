# Feishu WebSocket Recovery After Network Changes

Full debugging transcript for recovering Feishu gateway connections after network changes (VPN toggle, WiFi switch, proxy change).

## Error Signature

Feishu outbound works (you can send messages from Hermes → Feishu group), but inbound messages from Feishu never arrive. Gateway log shows:

```
INFO gateway.run: ✓ feishu connected        # seems fine
```

...but no `Received raw message` or `Inbound dm/group message` entries appear for new messages sent in Feishu.

Earlier disconnection trace:

```
ERROR Lark: receive message loop exit, err: sent 1011 (internal error) keepalive ping timeout; no close frame received
WARNING gateway.platforms.feishu: [Feishu] Send attempt 1/3 failed ... ConnectTimeoutError ... Connection to open.feishu.cn timed out.
```

## Root Causes

### 1. VPN/Network Toggle Kills WebSocket

Turning VPN on/off while the gateway is running causes the Feishu WebSocket's TCP connection to break. Key log signal: `keepalive ping timeout`. The gateway doesn't always detect this immediately — it may show "Connected" while the connection is actually dead on Feishu's side.

### 2. `--replace` Process Management Hell

When multiple `hermes gateway run --replace` are spawned from `background=true` terminal commands, the bash wrappers (`bash -lic set +m; hermes gateway run --replace 2>&1`) stay alive as orphan processes. Each one sends SIGTERM to any running gateway, causing a destructive restart cascade:

```
PID 1: hermes gateway run --replace  (background)
  → PID 2 starts (gateway)
  → Terminal command runs, spawns bash wrapper
  → Bash wrapper's --replace kills PID 2
  → PID 3 starts
  → Some other process' --replace kills PID 3
  → ... endless loop
```

Each restart triggers a new Feishu WebSocket handshake.

### 3. Feishu Rate Limiting

6+ rapid WebSocket reconnections in 15 minutes can trigger Feishu-side throttling. The WebSocket connects successfully (`Connected in websocket mode` + `Lark: connected to wss://...`) but Feishu stops pushing events to it. Outbound HTTP API messaging still works because it uses a different channel.

## Recovery Procedure

### Step 1: Kill ALL gateway processes

```bash
# Kill ALL hermes gateway processes (not just the latest one)
pkill -9 -f "hermes.*gateway"
sleep 3
```

Wait for the dust to settle — orphaned bash wrappers from old `--replace` calls may briefly restart a gateway before dying themselves.

### Step 2: Start fresh WITHOUT --replace

```bash
# Run in background - NO --replace flag
hermes gateway run
```

Verify:

```bash
# Check logs for Feishu connection
tail -20 ~/.hermes/logs/gateway.log | grep -E "feishu|connected|Lark"
```

Expected output:

```
[Feishu] Connected in websocket mode (feishu)
Lark: connected to wss://msg-frontier.feishu.cn/ws/v2?...
```

### Step 3: Verify bidirectional communication

Send a test message from Hermes → Feishu group:

```
send_message(message="测试", target="feishu:oc_4463c4b7c8cb82ff1fd40a5a82bb4a4c")
```

If the group sees the message, outbound works.

### Step 4: Test inbound

Ask the user to send a message in the Feishu group. Check logs:

```bash
tail -20 ~/.hermes/logs/gateway.log | grep -iE "inbound|receive|raw message"
```

If no inbound after 30 seconds, proceed to Step 5.

### Step 5: User-side checks (Feishu app)

If gateway is healthy (connected, outbound works) but no inbound messages arrive, the problem is likely on the Feishu side:

1. **Is the bot still in the group?** In Feishu group → group settings → members. The bot may have been removed or left during the connection storm.
2. **Try removing and re-adding the bot** to the group. This resets the bot's event subscription.
3. **Wait** — if rate-limited, Feishu may resume event delivery after a few minutes.
4. **Check group message type** — ensure the group allows bot messages (not set to "only members" message mode).

### Step 6: Re-verify Feishu app credentials

If all else fails, re-authorize:

```bash
# Check environment
env | grep FEISHU

# Restart with fresh token acquisition
pkill -9 -f "hermes.*gateway"
sleep 3
hermes gateway run
```

Wait 2 full minutes before testing inbound — Feishu needs to re-establish the event push channel.

## Prevention

### Never mix `--replace` with background spawning

When starting a gateway from within a Hermes terminal tool call:

```bash
# ❌ BAD - causes orphaned replacements
hermes gateway run --replace

# ✅ GOOD - fresh start after killing old ones
pkill -9 -f "hermes.*gateway"
sleep 2
hermes gateway run
```

### Before toggling VPN/proxy

If you know you're about to change networks:

```bash
# Check current Feishu connection
grep "feishu" ~/.hermes/logs/gateway.log | tail -5

# Plan: after network change, restart gateway cleanly
```

### Monitoring for silent disconnection

```bash
# Watch for keepalive timeout
tail -f ~/.hermes/logs/errors.log | grep -i "keepalive\|ping timeout\|disconnect"
```

## Diagnostics Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Outbound works, inbound dead | Feishu rate limit / stale WebSocket | Wait + clean restart |
| `keepalive ping timeout` in errors.log | VPN/network change | Restart gateway |
| Gateway keeps restarting | Orphaned `--replace` processes | `pkill -9` all, start fresh |
| `Received raw message` in logs but no reply | Different issue (session corruption, API error) | Check agent/errors.log |
