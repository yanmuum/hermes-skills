# Feishu Group Chat Setup

Creating a group chat via the Feishu API, adding the bot and users, and configuring group message receiving.

## Prerequisites

The Feishu app needs these permissions (added in dev console + **re-published**):

| Permission | Purpose |
|-----------|---------|
| `im:chat` | Read chat info |
| `im:chat:create` | Create new groups |
| `im:message` | Send/receive messages |

## Step 1: Create the Group

```python
import os, json, subprocess

def api(method, path, token, data=None):
    url = f"https://open.feishu.cn{path}"
    cmd = ["/mnt/c/Windows/System32/curl.exe", "-s", "--connect-timeout", "10", "--max-time", "15"]
    cmd += ["-X", method]
    cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += ["-H", "Content-Type: application/json; charset=utf-8"]
    if data:
        cmd += ["-d", json.dumps(data, ensure_ascii=False)]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else {"error": "empty"}

# Get token
r = api("POST", "/open-apis/auth/v3/tenant_access_token/internal", None,
        {"app_id": APP_ID, "app_secret": APP_SECRET})
token = r["tenant_access_token"]

# Create group
r = api("POST", "/open-apis/im/v1/chats", token, {
    "name": "项目协作群",
    "description": "工程设计项目协作",
    "chat_mode": "group",
    "chat_type": "private"  # or "public"
})
chat_id = r["data"]["chat_id"]
```

The bot becomes the owner/creator automatically.

## Step 2: Add Members

Users are NOT auto-added. Explicitly add them:

```python
user_open_id = "ou_f70bbb3d901204df5c07de82364dc3da"
r = api("POST", f"/open-apis/im/v1/chats/{chat_id}/members?member_id_type=open_id",
        token, {"id_list": [user_open_id]})
```

The response `success_id_list` may be empty even on success if the user was already in the group.

## Step 3: Send Messages to Group

⚠️ Must specify `receive_id_type=chat_id` as a query parameter:

```python
# Text message
r = api("POST", f"/open-apis/im/v1/messages?receive_id_type=chat_id", token, {
    "receive_id": chat_id,
    "msg_type": "text",
    "content": json.dumps({"text": "欢迎！"}, ensure_ascii=False)
})

# Interactive card
card = json.dumps({
    "config": {"wide_screen_mode": True},
    "header": {"title": {"tag": "plain_text", "content": "标题"}, "template": "blue"},
    "elements": [
        {"tag": "markdown", "content": "内容"},
        {"tag": "hr"},
        {"tag": "note", "elements": [{"tag": "plain_text", "content": "备注"}]}
    ]
}, ensure_ascii=False)
r = api("POST", f"/open-apis/im/v1/messages?receive_id_type=chat_id", token, {
    "receive_id": chat_id,
    "msg_type": "interactive",
    "content": card
})
```

## Step 4: Configure Bot to Receive Group @Mentions

The bot will NOT receive group @mentions by default. The user must configure this in the developer console:

1. Go to [Developer Console](https://open.feishu.cn/app) → Your App → **事件与回调 (Events & Callbacks)**
2. Find **`im.message.receive_v1`** event → click 编辑 (Edit)
3. Under 聊天类型 (Chat Type), check **✅ 群聊 (Group)**
4. Save → **发布上线 (Publish new version)**

**Verification**: Check gateway logs for incoming messages from the group's chat_id:
```bash
grep "oc_xxx" /home/yanmuu/.hermes/logs/gateway.log
```

## Adding Bitables to the Group

Share the bitable link in the group:
```
https://bytedance.feishu.cn/base/{app_token}
```

For easy access, users can long-press the message → **置顶 (Pin)** in the group.
