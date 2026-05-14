# Gateway Session Recovery

Full debugging transcript and context for the state.db session corruption fix.

## Error Signature

Feishu gateway fails to reply. Gateway log shows repeating pattern:

```
response ready: ... time=0.5s api_calls=1 response=213 chars
Transient agent failure in session 20260509_132743_f42bc05b — persisting user message
[Feishu] Sending response (213 chars) to ...
```

Errors log shows:

```
Non-retryable client error: Error code: 400 - {
  'error': {
    'message': "Messages with role 'tool' must be a response to a preceding message with 'tool_calls'",
    'type': 'invalid_request_error'
  }
}
```

## Diagnostic Steps

### 1. Check gateway state

```bash
cat ~/.hermes/gateway_state.json
```

Feishu should show `"state": "connected"`. If Feishu is disconnected, it's a different problem (auth/network/websocket).

### 2. Check the session file

```bash
ls -la ~/.hermes/sessions/
```

Identify the active session for the Feishu DM chat_id.

### 3. Check the session content

```python
import json
session_file = "~/.hermes/sessions/20260509_132743_f42bc05b.jsonl"
with open(session_file) as f:
    for line in f:
        msg = json.loads(line)
        role = msg.get("role", "?")
        content = msg.get("content", "")
        finish = msg.get("finish_reason", "")
        tc = msg.get("tool_calls", [])
        print(f"role={role} finish={finish} tc={bool(tc)} content='{str(content)[:60]}'")
```

Look for consecutive `role=user` messages without matching `role=assistant` between them.

### 4. Check state.db (authoritative source)

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/yanmuu/.hermes/state.db')
c = conn.cursor()
sessions = c.execute('SELECT id, message_count FROM sessions WHERE source=\"feishu\"').fetchall()
for s in sessions:
    msgs = c.execute('SELECT COUNT(*) FROM messages WHERE session_id=?', (s[0],)).fetchone()[0]
    print(f'Session {s[0]}: {msgs} messages (session table says {s[1]})')
"
```

### 5. Check request dumps for full API payload

```bash
python3 -c "
import json
with open('/home/yanmuu/.hermes/sessions/request_dump_<session_id>_<timestamp>.json') as f:
    data = json.load(f)
# Find the messages array (location varies)
msgs = ...  # drill into data['request'] structure
for i, m in enumerate(msgs):
    print(f'[{i}] role={m[\"role\"]} tc={bool(m.get(\"tool_calls\"))} tcid={bool(m.get(\"tool_call_id\"))}')
"
```

The request dump will show ALL messages sent to the LLM API — including orphaned user messages that got accumulated from repeated failed attempts.

## Root Cause

When a gateway platform provider API call fails midway through a conversation (e.g., HTTP 400, token limits, connection errors), the gateway:

1. Logs `Transient agent failure in session <id> — persisting user message`
2. Appends the user message to `state.db` (and the JSONL file)
3. On next message, loads the session from `state.db` — which now has the accumulated orphan messages
4. The orphaned consecutive user messages break the alternating message pattern
5. LLM API rejects with HTTP 400
6. Gateway retries, repeats the cycle, appending MORE orphan messages each time

## Complete Fix Script

```bash
# Stop gateway
hermes gateway stop

# Clean state.db
SESSION_ID="20260509_132743_f42bc05b"
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/state.db')
c = conn.cursor()
c.execute('DELETE FROM messages WHERE session_id=?', ('$SESSION_ID',))
c.execute('DELETE FROM sessions WHERE id=?', ('$SESSION_ID',))
conn.commit()
conn.close()
print('Cleaned session from state.db')
"

# Clean JSONL (optional, state.db is authoritative)
rm -f "$HOME/.hermes/sessions/$SESSION_ID.jsonl"

# Restart gateway
hermes gateway start
```

After restart, the next user message creates a brand-new session. The original conversation history is lost — this is a trade-off for recovering from corruption.

## Prevention

- If a gateway session starts failing repeatedly, **stop the user from sending more messages** — each one adds another orphan message to the corruption
- Clean the session quickly before many messages accumulate
- Consider adding rate-limiting or backoff in gateway agent retry logic to prevent rapid message accumulation during transient failures
