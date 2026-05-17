# 付费墙绕过数据库

基于 `fetch_url.sh` 脚本的绕过策略（源自 Bypass Paywalls Clean 项目），整理 30+ 知名付费站点的爬取可行性。

## 绕过策略等级

| 等级 | 策略 | 说明 |
|------|------|------|
| L1 | r.jina.ai 代理 | 覆盖最广，常能绕过软付费墙 |
| L1b | defuddle.md 代理 | 备选代理，输出带 YAML 头 |
| L2a | Googlebot UA + X-Forwarded-For | SEO 白名单（~50站点）单站最有效 |
| L2b | Bingbot UA | 少数站点（Haaretz, NZ Herald）专供 |
| L3a | Facebook Referer | 社交引流豁免（少数专业站） |
| L3b | Twitter Referer | 社交引流豁免 |
| L3c | AMP 页面 | AMP 版付费墙通常更弱 |
| L3d | EU IP 伪装 | 部分站点对 EU 用户展示全文 |
| L4 | archive.today 存档 | 最后手段，可能触发 CAPTCHA |
| L5 | Google Cache | webcache.googleusercontent.com |
| L6 | agent-fetch | 本地工具兜底 |

## 站点分类

### ✅ 可爬（Soft Paywall — 自动绕过成功）

| 站点 | URL | 绕过方式 | 实测 |
|------|-----|---------|------|
| 纽约时报 | nytimes.com | L1 r.jina.ai → L2a Googlebot → JSON-LD | ✅ |
| 华尔街日报 | wsj.com | L2a Googlebot UA（脚本 GOOGLEBOT_DOMAINS） + L3c AMP | ✅ |
| 金融时报 | ft.com | L2a Googlebot UA（GOOGLEBOT_DOMAINS 白名单） | ✅ |
| 经济学人 | economist.com | L2a Googlebot UA（GOOGLEBOT_DOMAINS 白名单） | ✅ |
| 华盛顿邮报 | washingtonpost.com | L1 r.jina.ai + L3c AMP 页面 | ✅ |
| 今日美国 | usatoday.com | L2a Googlebot UA（GOOGLEBOT_DOMAINS 白名单） | ✅ |
| 南华早报 | scmp.com | L1 r.jina.ai（软付费墙） | ✅ |
| MIT 科技评论 | technologyreview.com | L1 r.jina.ai（软付费墙） | ✅ |
| WIRED | wired.com | L3c AMP 页面 | ✅ |
| 福布斯 | forbes.com | L1 r.jina.ai（SEO 全文策略） | ✅ |
| Business Insider | businessinsider.com | 大部分免费，付费文 L1 可绕 | ✅ |
| 纽约客 | newyorker.com | L3c AMP 页面 | ✅ |
| 大西洋月刊 | theatlantic.com | L3c AMP 页面 | ✅ |
| 外交事务 | foreignaffairs.com | L1 r.jina.ai | ✅ |
| 明镜周刊 | spiegel.de | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 时代周报 | zeit.de | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 南德意志报 | sueddeutsche.de | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 法兰克福汇报 | faz.net | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 商报 | handelsblatt.com | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 世界报 | lemonde.fr | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 费加罗报 | lefigaro.fr | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 巴黎人报 | leparisien.fr | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 澳大利亚人报 | theaustralian.com.au | L2a Googlebot UA（GOOGLEBOT_DOMAINS） | ✅ |
| 悉尼先驱晨报 | smh.com.au | L2a Googlebot UA + L3c AMP | ✅ |
| The Age | theage.com.au | L2a Googlebot UA + L3c AMP | ✅ |
| Brisbane Times | brisbanetimes.com.au | L2a Googlebot UA + L3c AMP | ✅ |
| 新西兰先驱报 | nzherald.co.nz | L2b Bingbot UA（BINGBOT_DOMAINS） | ✅ |
| 哈利茨报 | haaretz.com | L2b Bingbot UA（BINGBOT_DOMAINS） | ✅ |
| Medium | medium.com | L1 r.jina.ai（最容易绕过之一） | ✅ |

### ⚠️ 有条件

| 站点 | URL | 问题 | 建议 |
|------|-----|------|------|
| 彭博 | bloomberg.com | CAPTCHA 拦截经常触发（实测被 r.jina.ai 返回 403） | 多试几次 / 换文章 / 可能被临时封 IP |
| Quora | quora.com | 部分内容需登录 | L2a Googlebot UA 可试，但 Q&A 需登录才完整 |

### ❌ 不可爬（Hard Paywall — Cloudflare 硬墙）

| 站点 | URL | 原因 |
|------|-----|------|
| The Information | theinformation.com | Cloudflare WAF 拦截所有非浏览器请求，包括 r.jina.ai、archive.today、Google Cache |
| Stat News | statnews.com | Cloudflare 保护（已知同类问题） |

### ❓ 特殊情况

| 站点 | URL | 说明 |
|------|------|------|
| Statista | statista.com | 数据平台非新闻站。免费图表/预览可爬，但详细数据报告需付费订阅+登录 |

## 判断方法

在爬取前快速判断站点类型：

```bash
# 如果返回 CAPTCHA/Cloudflare 页面 → 硬墙
curl -sI "https://site.com/article" | grep -i "server: cloudflare"

# 如果看到付费墙指示词 → 软墙（脚本会尝试绕过）
# "subscribe to continue" / "remaining free articles" / "premium content"
```

## 回退方案（硬墙站点）

硬墙文章无法自动绕过。回退方案：
1. **手动复制全文** → 保存为 TXT → 上传 NotebookLM
2. **导出 PDF**（浏览器 Print / Read Aloud） → 上传 PDF
3. **Google Cache**：`webcache.googleusercontent.com/search?q=cache:<URL>`（但同样可能被 Cloudflare 拦）
