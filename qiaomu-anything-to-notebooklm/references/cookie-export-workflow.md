# Cookie 导出工作流

当 `notebooklm login --fresh` 在 WSL 环境无法弹出浏览器窗口时，从 Windows Chrome 手动导出 Cookie 并转换为 storage_state.json 的完整流程。

## 导出步骤

1. 在 **Windows Chrome** 中打开 <https://notebooklm.google.com>，确保已登录 Google 账号
2. F12 打开 DevTools → Application 标签 → Cookies → `notebooklm.google.com` / `.google.com`
3. 全选所有 Cookie（点击第一个，Shift + 点击最后一个）
4. 右键 → **Export as JSON**

## Chrome 导出格式（表格视图）

Chrome DevTools 默认以表格形式展示 Cookie。如果从 Application 面板**直接复制**，得到的是制表符分隔的表格数据，**不是 JSON**。

表格格式示例：
```
Name    Value    Domain    Path    Expires    Size    HttpOnly    Secure    SameSite    Priority
__Secure-1PSID    xxx    .google.com    /    2027-06-16T...    167    ✓    ✓            High
```

## 转换表格 → storage_state.json

用以下 Python 脚本转换：

```python
import json
from datetime import datetime

raw = '''__Secure-1PSID\txxx\t.google.com\t/\t2027-06-16T07:46:19.011Z\t167\t✓\t✓\t\t\tHigh'''

cookies = []
for line in raw.strip().split('\n'):
    parts = line.split('\t')
    name = parts[0].strip()
    value = parts[1].strip()
    domain = parts[2].strip()
    path = parts[3].strip()
    expires_str = parts[4].strip()
    http_only_str = parts[6].strip()
    secure_str = parts[7].strip()
    same_site_str = parts[8].strip() if len(parts) > 8 else ''

    dt = datetime.strptime(expires_str.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
    expires_ts = dt.timestamp()

    cookie = {
        'name': name,
        'value': value,
        'domain': domain,
        'path': path,
        'expires': expires_ts,
        'httpOnly': http_only_str == '✓',
        'secure': secure_str == '✓',
        'sameSite': same_site_str if same_site_str in ('Lax', 'Strict', 'None') else 'Lax'
    }
    cookies.append(cookie)

state = {'cookies': cookies, 'origins': []}
with open('/home/yanmuu/.notebooklm/profiles/default/storage_state.json', 'w') as f:
    json.dump(state, f, indent=2)
print(f'Written {len(cookies)} cookies')
```

## 关键注意事项

- Cookie **不保证有效**：即使写入 storage_state.json 且 `notebooklm doctor` 显示 `Auth: ✓ pass`，Token fetch 仍可能因 GFW 阻断而失败
- `notebooklm status` 正常 ≠ 实际 API 可用（它只读本地 context.json）
- 如果 Token fetch ✗ fail，需要从 Windows Chrome **重新导出**（Google 会定期轮换 SID cookie）
- 完整 cookie 集至少需要包含：SID、SSID、APISID、SAPISID、HSID 及其 Secure 变体（__Secure-1PSID 等）
- `sameSite` 缺失时默认设为 `Lax`
- `Priority` 列对 Playwright 无意义，可忽略
- 已测试：23 个 cookie（含 `.google.com` 和 `notebooklm.google.com` 域）全部成功写入
