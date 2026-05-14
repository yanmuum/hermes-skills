---
name: design-project-bitables
description: 自动将设计项目收入与支出记录写入飞书多维表格
---

# 设计项目多维表格管理

此技能是 `feishu-bitables`（通用多维表格操作）的实例化领域技能。通用 API 知识见 umbrella skill，此处仅记录本表特有信息。

## 表格结构

飞书多维表格「设计项目收入与支出」
- App Token: `NkcrbLj70aiyHwsgDpUc5ix9nQd`
- Table ID: `tblcbUJ0TsBcsGaW`
- 链接: https://bytedance.feishu.cn/base/NkcrbLj70aiyHwsgDpUc5ix9nQd

### 字段列表 (按显示顺序)

| # | 字段名 | API 类型 | 说明 |
|---|--------|----------|------|
| 1 | 项目名称 | Text (type=1) ⭐主字段 | 原默认"文本"字段重命名 |
| 2 | 日期 | DateTime (type=5) | 已启用自动填入今天 |
| 3 | 序号 | Text (type=1) | 自动生成 "PROJ-XXX" |
| 4 | 客户名称 | Text (type=1) | — |
| 5 | 项目总金额 | Number (type=2) | 合同总金额 |
| 6 | 已收金额 | Number (type=2) | 已到账金额 |
| 7 | 未收金额 | Number (type=2) | 建议在 UI 中用公式: 总金额 - 已收 |
| 8 | 支出设计费 | Number (type=2) | 设计师费用 |
| 9 | 备注 | Text (type=1) | 已移到末列 |

## 认证

```python
import os, requests
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": "cli_a977e0167e3a1bc4", "app_secret": os.environ["FEISHU_APP_SECRET"]}
)
token = resp.json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
```

## 自动插入记录

当用户发送设计项目信息时，按以下流程处理：

1. **解析自然语言** — 从用户消息中提取: 客户名称、金额、已收、设计费、日期、备注
2. **获取序号** — 查询已有记录，取最大序号+1，格式 `PROJ-XXX`
3. **构建记录对象** — 日期用 Unix 秒级时间戳，未收金额自动计算
4. **POST 插入** — 调用记录 API

### 解析常见格式

用户习惯用中文自然语言表达，如:
- "新项目：张三 总价50000 已收20000 设计费8000"
- "设计新项目:大湖曾涛 设计费1000元，已收款1000元"
- "3月1日 李四设计 总60000 已收20000 设计费8000"

### ⚠️ 日期字段注意

日期字段 (DateTime type=5) **必须使用当天 UTC+8 午夜的时间戳**（`00:00:00 CST`），否则表格上会显示具体时间而非纯日期。

### ⚠️ 关键：时间戳单位必须是毫秒

飞书 DateTime 字段期望的是 **毫秒 (milliseconds)** 时间戳，不是秒！传秒会导致显示为 **1970 年**。

```python
from datetime import datetime, timezone, timedelta
tz_cn = timezone(timedelta(hours=8))
today_midnight = datetime.now(tz_cn).replace(hour=0, minute=0, second=0, microsecond=0)
date_ts = int(today_midnight.timestamp() * 1000)  # ✅ 乘以 1000 转为毫秒！
```

### ⚠️ auto_fill 陷阱

**不要给日期字段设置 `auto_fill: True`！** 如果字段开启了自动填入今天，已存储的日期时间戳会被覆盖。解决方法：

1. 关闭 `auto_fill`：PUT 更新字段属性 `{"auto_fill": false}`
2. 重新写入正确的毫秒时间戳
3. 后续插入记录时在代码中手动设置日期

### 插入代码

```python
from datetime import datetime, timezone, timedelta

# 日期必须用 UTC+8 午夜时间戳的毫秒值（否则表格显示为1970年）
tz_cn = timezone(timedelta(hours=8))
today_midnight = datetime.now(tz_cn).replace(hour=0, minute=0, second=0, microsecond=0)
date_ts = int(today_midnight.timestamp() * 1000)  # ✅ 毫秒！

# 获取当前最大序号
list_resp = requests.get(list_url, headers=headers, params={"page_size": 20, "field_names": '["序号"]'})
max_seq = 0
for item in list_resp.json()["data"]["items"]:
    seq_str = item.get("fields", {}).get("序号", "PROJ-000")
    try:
        num = int(seq_str.split("-")[-1])
        max_seq = max(max_seq, num)
    except: pass
seq = f"PROJ-{max_seq + 1:03d}"

# 插入记录
body = {"fields": {
    "序号": seq,
    "日期": date_ts,  # UTC+8 午夜时间戳，纯日期格式
    "客户名称": "客户名",
    "项目总金额": 50000,
    "已收金额": 20000,
    "未收金额": 30000,
    "支出设计费": 8000,
    "备注": "备注内容",
}}
resp = requests.post(url, headers=headers, json=body)
```

## 通用 API 参考

见 umbrella skill `feishu-bitables`:
- 字段类型表
- 字段操作 (PUT 更新、DELETE 删除)
- 记录 CRUD
- 权限配置踩坑
