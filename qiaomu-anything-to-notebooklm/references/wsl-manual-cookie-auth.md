# WSL 环境 NotebookLM 手动 Cookie 认证（替代 Playwright 登录）

## 问题

在 WSL/WSLg 环境中运行 `notebooklm login` 时，Playwright 启动的 Chromium 浏览器窗口经常：
- 弹出后立即关闭（WSLg 渲染异常或浏览器 profile 损坏）
- 持续闪退，无法完成 Google OAuth 交互

## 解决方案：从 Windows 浏览器手动导出 Cookie

无需依赖 WSLg 的 GUI 渲染，直接从 Windows 上的 Chrome/Edge 导出已登录 Google 账号的 cookies。

### 步骤

**1. 确保在 Windows Chrome 中已登录 Google 账号**
   打开 https://notebooklm.google.com/ 确认可访问。

**2. 导出 Cookies（两种方法）**

**方法 A — Chrome DevTools Application 面板（推荐）：**
- F12 → Application → Storage → Cookies → 选中 `notebooklm.google.com`
- 点击任意 cookie → Ctrl+A 全选 → 右键 Export as JSON（新版 Chrome/Vivaldi 有此选项）
- 把导出的 JSON 内容贴给 Hermes Agent
- Hermes 会解析并写入 `~/.notebooklm/profiles/default/storage_state.json`

**方法 B — Cookie-Editor 插件：**
- Chrome 商店安装 Cookie-Editor 插件
- 打开 notebooklm.google.com → 点插件图标 → Export → 复制 JSON → 贴给 Hermes

**3. Hermes 生成认证文件**

执行：
```bash
python3 -c "
import json
# 把导出的 cookies JSON 赋值到这里... 
# 然后:
storage_state = {
    'cookies': parsed_cookies,
    'origins': []
}
path = f'{os.environ[\"HOME\"]}/.notebooklm/profiles/default/storage_state.json'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(storage_state, f, indent=2)
os.chmod(path, 0o600)
"
```

**4. 验证**
```bash
notebooklm auth check --test
# 所有 check ✓ pass 即成功
notebooklm list
# 能看到你的 Notebooks 列表
```

## Cookie 过期处理

Google cookies 的有效期通常较长（数月到 1-2 年），但可能因以下原因提前失效：
- Google 会话变更（换设备、换 IP、安全策略触发）
- 手动登出 Google 账号
- RotateCookies POST 返回 401

### 症状
```log
Keepalive RotateCookies POST failed: 401 Unauthorized
Authentication expired or invalid. Redirected to: https://accounts.google.com/v3/signin/...
notebooklm auth check --test → Token fetch ✗ fail
```

### 修复
重新导出 cookies（重复上述步骤 1-4）。无需删除旧文件，直接覆盖。

## 关键 Cookies 清单

NotebookLM 认证需要以下 cookies（由 `notebooklm-py` 库校验）：

| Cookie | 必要性 | 说明 |
|--------|--------|------|
| `SID` | ✅ 必需 | 基础认证 cookie |
| `__Secure-1PSIDTS` | ✅ 必需 | 安全会话令牌 |
| `OSID` | ✅ 次级绑定 | （或同时有 APISID + SAPISID） |
| `APISID` / `SAPISID` | ⚠️ 次级绑定 | 当 OSID 缺失时需两者同时存在 |
| `HSID` / `SSID` | 推荐 | 用于保持会话 |
| `__Secure-1PSID` / `__Secure-3PSID` | 推荐 | 安全 cookie 变体 |
| `SIDCC` / `__Secure-1PSIDCC` | 推荐 | 会话一致性 |

## 关于 --browser-cookies 方案

`notebooklm login --browser-cookies` 使用 `rookiepy` 库从已安装的浏览器中读取 cookies。
但在 WSL 环境中，rookiepy 只能读取 Linux 端安装的浏览器（通常没有），无法读取 Windows 端的 Chrome/Edge。
因此在 WSL 下此方法通常不可用。
