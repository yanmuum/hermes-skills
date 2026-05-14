# WSL → Feishu Proxy Interaction

## The Asymmetric Proxy Problem

WSL 通过代理连接飞书时会遇到一个 **不对称行为**:

| 连接类型 | 通过代理 | 结果 |
|----------|---------|------|
| WebSocket (接收消息) | ✅ 成功 | 可以正常接收飞书消息 |
| HTTPS API (发送消息) | ❌ 超时 | `open.feishu.cn` 连接池耗尽 |

**现象:**
- 飞书 bot 能收到消息（inbound message logged）
- 但无法发回响应（"Send attempt N/3 failed: ConnectTimeout"）
- `ping open.feishu.cn` 正常 (0.2-1ms)
- `curl https://open.feishu.cn` 返回 404（实际可达）
- 但 Python `requests` 通过代理向飞书 API 发 POST 超时

**根本原因:**
`requests` 库通过代理 (`http://172.26.240.1:7890`) 连接 `open.feishu.cn` 时，代理连接池在大并发下耗尽。WebSocket 走不同路径（不经过 same proxy pool），所以收消息正常。

## 诊断命令

```bash
# 1. 检查代理环境变量
env | grep -i proxy

# 2. 检查 gateway 能否收到消息
grep "inbound message" ~/.hermes/logs/gateway.log | tail -5

# 3. 检查消息是否发送成功
grep "Send attempt\|response ready" ~/.hermes/logs/gateway.log | tail -10

# 4. 检查有没有响应生成但发不出去
grep "response ready" ~/.hermes/logs/gateway.log | tail -5
# 有 "response ready" 但没有 "Sending response" → 发不出
```

## 修复

### 方案 A: 重启 Gateway (最快)

最直接的修复 — 清空连接池:

```bash
# 找到并杀掉旧进程
ps aux | grep "gateway run" | grep -v grep | awk '{print $2}'
kill <PID>

# 在当前 shell (有 proxy) 重新启动
cd ~/.hermes/hermes-agent && python -m hermes_cli.main gateway run --replace
```

⚠️ **不要 unset proxy 再启动** — 没代理连不上飞书 WebSocket。

### 方案 B: Windows curl 替代 Python requests（持久修复）

对于 `open.feishu.cn` 的 HTTPS API 调用（发消息、编辑消息、加 reaction），用 Windows 的 curl 绕过 Python 的代理连接池:

```python
import subprocess, json

# 用 Windows curl 发飞书消息
cmd = [
    "/mnt/c/Windows/System32/curl.exe", "-s",
    "--connect-timeout", "10", "--max-time", "20",
    "-X", "POST",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json; charset=utf-8",
    "-d", json.dumps(body),
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
]
result = subprocess.run(cmd, capture_output=True, text=True)
```

### 方案 C: no_proxy 白名单

在启动 gateway 前设置 `no_proxy` 包含 `open.feishu.cn`:

```bash
export no_proxy="localhost,127.0.0.1,open.feishu.cn,.feishu.cn,::1"
export NO_PROXY="$no_proxy"
hermes gateway run --replace
```

此方案未经验证 — 需测试 `requests` 是否遵守 `no_proxy` 中的域名通配。
