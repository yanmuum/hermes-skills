# Feishu Gateway Troubleshooting: "Bot Not Replying"

When the Feishu bot stops responding to messages even though the gateway appears connected, the most likely cause is a **corrupted session file** — one or more user messages were appended to the session without a corresponding assistant response, breaking the LLM API's message alternation requirement.

## Diagnosis

### 1. Check Gateway State

```bash
cat ~/.hermes/gateway_state.json
```

Look for:
- `"gateway_state": "running"`
- `"feishu": {"state": "connected"}` — if disconnected, check the error

### 2. Check Gateway Logs

```bash
tail -50 ~/.hermes/logs/gateway.log
tail -50 ~/.hermes/logs/errors.log
```

**Key signal**: The log shows messages being received and "response ready" being logged, but the session keeps failing:

```
response ready: ... time=0.6s api_calls=1 response=213 chars
Transient agent failure in session 20260509_132743_f42bc05b
```

Check for the specific API error in `errors.log`:

```
Non-retryable client error: Error code: 400 - {'error': {'message': "Messages with role 'tool' must be a response to a preceding message with 'tool_calls'"}}
```

This error means the conversation history sent to the LLM has tool/assistant messages without matching tool_calls/user messages, or consecutive user messages without assistant responses between them.

### 3. Locate the Corrupted Session

The session ID is shown in the transient failure log. Find the file:

```bash
ls -lt ~/.hermes/sessions/ | head -5
```

Open the session file and look for **consecutive user messages** without assistant responses between them:

```python
import json

with open("~/.hermes/sessions/20260509_132743_f42bc05b.jsonl") as f:
    messages = [json.loads(l) for l in f]

for msg in messages:
    role = msg.get("role")
    content = msg.get("content", "")
    finish = msg.get("finish_reason", "")
    print(f"  role={role} finish='{finish}' content='{content[:60]}...'")
```

### 4. Identify the Problem Pattern

A healthy session alternates: `user → assistant → tool → assistant → tool → ... → assistant(finish=stop)`.

A corrupted session has **2+ consecutive user messages** like this:

```
...
assistant(finish=stop)   ✓ last good message
user                     ✓ new message
user                     ✗ orphan — no assistant response before it
user                     ✗ orphan
user                     ✗ orphan
```

When the LLM API receives consecutive user messages, it rejects the request with the 400 error above.

## Fix: Clean the Session

**Python in-place fix** (run from a regular terminal that inherits `FEISHU_APP_SECRET`):

```python
import json, shutil

session_file = "/home/yanmuu/.hermes/sessions/20260509_132743_f42bc05b.jsonl"
backup_file = session_file + ".bak"
shutil.copy2(session_file, backup_file)

with open(session_file) as f:
    messages = [json.loads(l) for l in f]

# Find the last assistant message with finish_reason="stop"
last_good_idx = -1
for i in range(len(messages) - 1, -1, -1):
    msg = messages[i]
    if msg.get("role") == "assistant" and msg.get("finish_reason") == "stop":
        last_good_idx = i
        break

if last_good_idx == -1:
    print("ERROR: Could not find a clean assistant response")
    # Fallback: find any assistant with finish_reason
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "assistant" and messages[i].get("finish_reason"):
            last_good_idx = i
            break

# Find the last user message
last_user_idx = -1
for i in range(len(messages) - 1, -1, -1):
    if messages[i].get("role") == "user":
        last_user_idx = i
        break

# Keep: everything up to and including the last good assistant response,
# plus ONLY the last user message
orphan_user_start = last_good_idx + 1
orphan_count = last_user_idx - orphan_user_start

clean_messages = messages[:last_good_idx + 1] + [messages[last_user_idx]]

with open(session_file, "w") as f:
    for msg in clean_messages:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

print(f"Removed {orphan_count} orphan user message(s)")
print(f"Backup: {backup_file}")
print("Next Feishu message will start a fresh agent from cleaned session.")
```

### After Cleaning

Send a test message in Feishu. The gateway should load the cleaned session from disk and respond normally.

If the gateway still fails after cleaning, try restarting it to clear the in-memory agent cache:

```bash
hermes gateway restart
```

## Prevention

Session corruption typically happens when:
- The gateway receives messages in rapid succession before the agent can respond
- A transient error occurs during the first attempt but the user message is saved to the session file before the agent completes
- The gateway restarts mid-response

If rapid messages are common, consider asking the user to wait for the bot's response before sending the next message.
