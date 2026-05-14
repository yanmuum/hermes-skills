# Feishu File Attachment Diagnostics

When a user says they sent a file (PDF, image, document) in a Feishu chat but the agent didn't receive it, use this diagnostic technique to verify whether the file was actually received by the gateway.

## Quick Check

```bash
grep "Inbound.*media=1\|Inbound.*type=file\|Inbound.*type=photo\|Inbound.*type=document" ~/.hermes/logs/agent.log | tail -10
```

- **`media=1`** → message had a file/photo attachment
- **`media=0`** → text-only message, no attachment
- **`type=text`** → plain text message
- **`type=photo`** → image/photo message
- **`type=file`** → file attachment message
- **`type=document`** → document share message

## Full Diagnostic

```bash
# Check the most recent incoming messages
grep "Inbound" ~/.hermes/logs/agent.log | tail -20

# Sample output:
# Inbound group message received: id=om_xxx type=text chat_id=oc_xxx sender=user text='帮我审核一下这份PDF' media=0
#                                      ^^^^^^^^                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^
#                                      message type                               truncated text body          media flag
```

## Common Scenarios

| Log Pattern | Meaning | Action |
|---|---|---|
| `type=text media=0 text='帮我审核一下这份PDF'` | Text-only message. User **thought** they attached a file but didn't. | Ask user to re-send as file attachment (not in text) or paste text directly. |
| `type=photo media=1` | Image was received. Gateway should have auto-downloaded. | Check cache: `ls -lt ~/.hermes/cache/screenshots/` |
| `type=file media=1` | File attachment was received. | Check if gateway auto-downloaded it. If not, may be a gateway bug. |
| No matching log at all | Message never reached the gateway (WebSocket disconnect). | Check gateway connection state. |

## Why Files Sometimes Don't Arrive

1. **Gateway was disconnected** when the file was sent — Feishu does NOT replay messages sent during downtime. The file is lost forever.
2. **User sent file as a separate message** before the text message. If the file arrived during a disconnect period, only the text message (sent later) shows up.
3. **Gateway supports file download but only for certain file types** — check `_download_remote_document` in the Feishu platform code for supported extensions.
4. **Image cache cleanup** — the gateway periodically purges stale cached files. See `Image cache cleanup` in gateway.log.

## Prevention

When a user asks you to review a document:

1. **Don't assume the file arrived.** Check the logs first.
2. **Ask for the text directly** if the file can't be found: "请直接粘贴协议内容，不要以文件形式发送，我这边收不到文件附件。"
3. **If the user insists they sent a file**, run the grep diagnostic above and share the result with them.
