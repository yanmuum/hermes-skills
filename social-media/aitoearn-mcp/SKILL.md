---
name: aitoearn-mcp
description: AiToEarn MCP 集成 — 内容营销 SaaS 平台，支持多平台发布、内容变现、自动化互动
tags:
  - MCP
  - Content Marketing
  - Social Media
  - OPC
  - Monetization
related_skills:
  - native-mcp
  - tiktok-slideshow-automation
---

# AiToEarn MCP 集成

[AiToEarn](https://aitoearn.ai) 是一个面向 OPC（一人公司）的内容营销智能体平台，通过 AI Agent 自动化帮助创作者在全网主流平台构建、分发并变现内容。

## 是什么

AiToEarn **不是 Hermes 技能**，而是一个完整的 SaaS 平台。Hermes 通过 MCP（Model Context Protocol）协议集成其能力，让 Agent 可以直接调用 AiToEarn 的工具。

支持渠道：抖音、小红书、快手、B站、视频号、TikTok、YouTube、Facebook、Instagram、Threads、Twitter/X、Pinterest、LinkedIn

## 接入方式

### 方式 1：MCP 协议（推荐 — 当前配置）

在 `~/.hermes/config.yaml` 中配置 MCP 服务器：

```yaml
mcp_servers:
  aitoearn:
    url: "https://aitoearn.cn/api/unified/mcp"  # 国内版
    headers:
      x-api-key: "<你的 API Key>"
    timeout: 120
```

### 方式 2：直接使用网站
- 国内用户：https://aitoearn.cn
- 国际用户：https://aitoearn.ai

### 方式 3：Docker 私有化部署
项目根目录有 `docker-compose.yml`，参考 `DOCKER_DEPLOYMENT_CN.md` / `DOCKER_DEPLOYMENT_EN.md`。

## 配置说明

### 环境区分（⚠️ 重要）

| 环境 | 域名 | API Key 类型 | WSL 可达性 |
|------|------|-------------|-----------|
| 中国版 | `aitoearn.cn` | 中国版 Key | ✅ 可达 |
| 国际版 | `aitoearn.ai` | 国际版 Key | ❌ GFW 阻断 |

**规则**：中国版 API Key 只能搭配 `aitoearn.cn` 的 URL；国际版 API Key 只能搭配 `aitoearn.ai` 的 URL。环境和 Key 不匹配会返回 **401 Unauthorized**。

### 获取 API Key
1. 打开 [aitoearn.cn](https://aitoearn.cn/)（国内）或 [aitoearn.ai](https://aitoearn.ai/)（国际）
2. 注册并登录
3. 进入 Settings / API Keys 页面生成 Key
4. 新生成的 Key 可能需要在 Settings 中手动激活后才能用

### 验证连通性

```bash
# 1. 先用初始化请求（不需要 Accept header）
curl -s --max-time 15 -X POST "https://aitoearn.cn/api/unified/mcp" \
  -H "x-api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hermes-agent","version":"1.0"}}}'

# 2. 列出所有可用工具
curl -s --max-time 30 -X POST "https://aitoearn.cn/api/unified/mcp" \
  -H "x-api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

> ⚠️ `Accept: application/json, text/event-stream` 头是必需的。不带会返回 `Not Acceptable` 错误。
> ⚠️ `tools/list` 是 MCP 初始化级别的请求方法，**不是可调用的工具**（用 `tools/call` 来调工具，`tools/list` 只能用原始 curl 请求）。

## MCP 工具清单（40+ 个）

### 账号管理
- `getAllAccounts` — 获取所有关联账号
- `getAccountDetail` — 获取单个账号详情
- `getAccountGroupList` / `getAccountListByGroupId` — 账号分组管理

### 内容发布（直接 MCP 发布）
| 平台 | MCP 工具 | 备注 |
|------|---------|------|
| 抖音 | `publishPostToDouyin` | 返回 URL，需用户在手机确认 |
| B站 | `publishPostToBilibili` | 仅支持视频 |
| YouTube | `publishPostToYoutube` | 仅支持视频 |
| TikTok | `publishPostToTiktok` | 仅支持视频 |
| Twitter/X | `publishPostToTwitter` | — |
| Facebook | `publishPostToFacebook` | 支持 post/reel/story |
| Instagram | `publishPostToInstagram` | 支持 post/reel/story |
| Threads | `publishPostToThreads` | — |
| Pinterest | `publishPostToPinterest` | — |
| 快手 | `publishPostToKwai` | 封面图必填 |
| 微信公众号 | `publishPostToWxGzh` | — |

**⚠️ 无直发 MCP 工具的平台**：小红书(xhs)、视频号(wxSph)、LinkedIn 等 — 需要通过 AiToEarn Web 端手动发布

### 发布工具
- `publishRestrictions` — 各平台发布限制规则（图片数、视频大小、文字长度等）
- `getPublishingTaskStatus` — 查询发布任务状态
- `createThumbnailTask` / `getThumbnailTaskStatus` — 自动生成封面图

### AI 内容生成
- `createImageTextDraft` — AI 生成图文草稿（支持指定模型、数量、平台）
- `createVideoDraft` — AI 生成视频草稿
- `getDraftGenerationPricing` — 查看可用模型和价格
- `getDraftTaskStatus` — 查询生成任务状态
- `createDraft` / `listDrafts` / `getDraftDetail` / `deleteDraft` — 草稿箱管理
- `listDraftGroups` / `getDraftGroupInfoByName` — 草稿分组管理
- `listMediaGroups` / `listMedia` — 素材管理

### 内容抓取
- `createCrawlTask` — 从社交平台链接下载视频/图片（支持 B站/YouTube/TikTok/抖音/小红书/快手）
- `getCrawlTaskStatus` — 查询抓取状态（轮询间隔建议 30s）

### 任务市场和结算
- `listTaskMarket` — 浏览任务市场（支持按平台/类型筛选）
- `getTaskDetail` — 查看任务详情（含推广要求、产品说明）
- `acceptTask` — 接受任务（可能需要粉丝数门槛）
- `listMyUserTasks` — 查看已接任务列表
- `getMyUserTaskDetail` — 查看单个已接任务详情
- `submitTask` — 提交普通任务（通过 workLink 或 publishRecordId）
- `submitInteractionTask` — 提交互动任务（截图为证）
- `submitFollowAccountTask` — 提交关注任务（截图为证）
- `submitBrandCommentTask` — 提交品牌评论任务
- `applyFreeSample` — 申请免费样品
- `listMySampleOrders` / `getMySampleOrderDetail` — 样品订单管理
- `listMyPublishedTasks` / `getMyPublishedTaskDetail` — 已发布任务作品

### 数据
- `getMyProfile` — 获取个人资料
- `getMyCreditsBalance` — 查看积分余额
- `getMyBalance` — 查看余额/收入
- `listChannelPosts` / `getPostDetail` — 查看各平台帖子和详情
- `getTaskPostsDataCube` / `getTaskPostsTrend` — 任务帖子数据看板
- `listPromotionPosts` / `getPromotionPostDetail` / `getPromotionPostTrend` — 推广帖子数据

### 互动记录
- `createInteractionRecord` / `listInteractionRecords` / `deleteInteractionRecord` — 互动证据管理

### 联盟推广
- `getAffiliateLink` / `bindAffiliateInviteCode` — 邀请码管理
- `getAffiliateOverview` / `listAffiliateCommissions` / `getAffiliateSettlement` — 联盟收益

### 品牌营销
- `listCampaignMarket` / `getCampaignDetail` / `applyCampaign` — 品牌活动市场
- `getCampaignVerifyCode` / `submitCampaignContent` — 活动执行

## CPE 任务工作流（小红书/其他无直发MCP的平台）

当用户接受了 xhs 等无直发 MCP 工具平台的 CPE 任务时：

1. **查任务详情**：`getTaskDetail` / `listTaskMarket` 查看任务描述和要求
2. **查账号**：`getAllAccounts` 确认有关联的对应平台账号
3. **用 AI 生成草稿**：可在 aitoearn.cn Web 端用 AI 生成图文/视频草稿
4. **引导用户在 Web 端发布**：告诉用户去 [aitoearn.cn](https://aitoearn.cn) 创建并发布内容
5. **获取发布链接**：用户发布后提供小红书笔记链接
6. **提交任务**：用 `submitTask(userTaskId, workLink=发布链接)`
7. **查询状态**：用 `getMyUserTaskDetail` 确认提交结果

## 当前配置状态

已成功配置：国内版 aitoearn.cn，API Key 已验证通过。WSL 环境中 .cn 可达。

## 使用示例

### 查账号
```bash
curl -s --max-time 40 -X POST "https://aitoearn.cn/api/unified/mcp" \
  -H "x-api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"getAllAccounts","arguments":{}}}'
```

### 查已接任务
```bash
curl -s --max-time 60 -X POST "https://aitoearn.cn/api/unified/mcp" \
  -H "x-api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"listMyUserTasks","arguments":{"pageNo":1,"pageSize":20}}}'
```

### 浏览任务市场
```bash
curl -s --max-time 60 -X POST "https://aitoearn.cn/api/unified/mcp" \
  -H "x-api-key: <KEY>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"listTaskMarket","arguments":{"type":"promotion","platform":"xhs","pageNo":1,"pageSize":10}}}'
```

## 自动化能力矩阵

接任务前先看清楚类型，不同类型自动化程度不同：

| 任务类型 | 能否自动完成 | 需要用户配合 | 提交流程 |
|---------|------------|------------|---------|
| **Promotion (发布推广)** | ✅ 部分平台可 | 提供内容/素材 | `submitTask(workLink=发布链接)` |
| **Interaction (互动)** | ❌ 必须手动 | 用户自己点赞/收藏/评论 | `submitInteractionTask(截图)` |
| **Follow Account (关注)** | ❌ 必须手动 | 用户自己关注账号 | `submitFollowAccountTask(截图)` |
| **Brand Comment (品牌评论)** | ❌ 必须手动 | 用户写评论+截图 | `submitBrandCommentTask(...)` |

### Promotion 自动发布支持

| 平台 | 自动发布 | 说明 |
|------|---------|------|
| 抖音 | ✅ | 需手机扫码确认 |
| B站 | ✅ | 仅视频 |
| YouTube | ✅ | 仅视频 |
| TikTok | ✅ | 仅视频 |
| Twitter/X | ✅ | — |
| Facebook | ✅ | 图文/Reels/Story |
| Instagram | ✅ | 图文/Reels/Story |
| Threads | ✅ | — |
| Pinterest | ✅ | — |
| 快手 | ✅ | 封面必填 |
| 微信公众号 | ✅ | — |
| 小红书 | ❌ | Web端手动发布后提交链接 |
| 视频号 | ❌ | Web端手动发布后提交链接 |
| LinkedIn | ❌ | Web端手动发布后提交链接 |

### Interaction 任务工作流

互动任务（点赞/收藏/评论/关注）**无法通过 MCP 自动执行**，流程：

1. 告诉用户任务内容（链接、需要做什么操作）
2. 用户手动在平台完成操作
3. 用户截图发回来
4. 调用 `submitInteractionTask(userTaskId, screenshotUrls=[...])` 
5. 或 `submitFollowAccountTask(userTaskId, screenshotUrls=[...])` 提交关注任务

## 和已有技能的关系

| 技能 | 关系 |
|------|------|
| `tiktok-slideshow-automation` | TikTok 幻灯片创作工作流（本地 Node.js Canvas 生成幻灯片） |
| `aitoearn-mcp`（本技能） | 全平台内容营销 SaaS，包含发布/变现/互动/创作 |
| `native-mcp` | 底层 MCP 客户端连接和工具注册 |

## 坑

- **MCP 请求需 Accept header**：`Accept: application/json, text/event-stream` 是必需的。漏掉返回 `Not Acceptable` 错误
- **tools/list 不是 callable tool**：只能用原始 curl 请求，不能用 `tools/call`
- **超时问题**：部分 MCP 调用（如 listMyUserTasks）需要 60s+ 超时
- **环境不匹配 = 401**：国际版 Key 不能用于 `.cn` 端点，反之亦然
- **Key 需激活**：新生成的 Key 在 MCP 端点可能返回 401，需要先在 Dashboard 确认激活
- **GFW 阻断**：WSL 环境下 `.ai` 国际域名不可达，需代理或改用国内版 `.cn`
- **配置变更需重启 gateway**：修改 `mcp_servers` 后需要重启 Hermes gateway 才生效
- **小红书/视频号等平台无直发 MCP**：部分平台需通过 AiToEarn Web 端手动发布后提交链接
- **抖音发布需手机确认**：`publishPostToDouyin` 返回 URL，用户必须在手机上打开确认
- **快手封面图必填**：`publishPostToKwai` 要求必须提供 coverUrl，否则失败
