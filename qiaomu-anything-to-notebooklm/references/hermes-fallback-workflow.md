# Hermes 环境回退方案

当 weixin-read-mcp 或 notebooklm CLI 不可用时，使用本方案。

## WeChat 文章提取（无 MCP）

weixin-read-mcp 服务器不在克隆的仓库中（只有 feishu-read-mcp）。回退方案：

```bash
# 1. 用 curl 下载页面
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://mp.weixin.qq.com/" \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" -o /tmp/weixin.html

# 2. 提取文章内容
python3 << 'PYEOF'
import re
with open('/tmp/weixin.html', 'r', errors='ignore') as f:
    content = f.read()

# 找标题
t = re.search(r"var msg_title = '([^']+)'", content)
if t: print(f'标题: {t.group(1)}')

# 找正文
body_start = content.find('class="rich_media_content')
if body_start >= 0:
    div_start = content.find('>', body_start) + 1
    depth = 1; pos = div_start
    while depth > 0 and pos < len(content):
        if content[pos:pos+6] == '</div>': depth -= 1
        elif content[pos:pos+4] == '<div': depth += 1
        pos += 1
    body = content[div_start:pos-6]
    text = re.sub(r'<[^>]+>', '\n', body)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    with open('/tmp/weixin_article_clean.txt', 'w') as f:
        f.write(text)
    print(f'已保存 {len(text)} 字')
PYEOF
```

## 深度分析（无 NotebookLM）

当 notebooklm 未登录或不可用时，直接在本机执行分析：

核心模式：加载内容 → 生成 10 个深度问题 → 逐一回答 → 结构化输出
内容格式：标题 + 概览 + 10组 Q&A + 核心观点提炼 + 个人启发
推送格式：Markdown（用户偏好，方便存档）

## Feishu 推送格式

用户偏好用 Markdown 格式推送（方便存档），不要纯文本长消息。

## NotebookLM 安装与登录 (Hermes/WSL)

```bash
# 安装
pip3 install --break-system-packages notebooklm-py

# 创建 profile
notebooklm doctor --fix

# 登录（需要 WSLg 支持）
# 浏览器窗口会在 Windows 桌面弹出
notebooklm login --fresh  # --fresh 可清除损坏的浏览器缓存
# 手动在浏览器中登录 Google 账号
# 确认跳转到 notebooklm.google.com 后，回到终端按 Enter

# 验证
notebooklm doctor   # Auth 应为 ✓ pass
notebooklm list     # 应列出笔记本
```

已知限制：
- --browser msedge 需要 `playwright install msedge`（需要 sudo，WSL 中受限）
- --browser-cookies edge 尝试读取 Windows Edge cookies，但 rookipy 在 WSL 中找不到 Windows 路径
- **最可靠**：默认 chromium，通过 WSLg 弹出桌面浏览器 + `--fresh` 清理缓存
- fetch_url.sh 脚本在 WSL 中可能超时
- weixin-read-mcp 不在仓库中（只有 feishu-read-mcp）

### 浏览器闪退排查流程（WSL 专属）

症状：`notebooklm login` → Chromium 窗口闪现关闭

1. 先 clean: `notebooklm auth logout && rm -rf ~/.notebooklm/profiles/default/browser_profile`
2. 用 fresh 重试: `notebooklm login --fresh`
3. 如果 WSLg 挂了：检查 `/mnt/wslg/weston.log` 是否有错误
4. 终极备用：从 Windows 浏览器读 cookie: `notebooklm login --browser-cookies`
   - 前提：Windows 上的 Chrome/Edge 已登录 Google
   - 无需 WSLg 支持，纯文件读取
