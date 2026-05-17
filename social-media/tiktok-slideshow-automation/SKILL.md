---
name: tiktok-slideshow-automation
description: TikTok 幻灯片内容自动化 — 从找钩子、找图、生成幻灯片到排期发布的全流程
---

# TikTok 幻灯片内容自动化工作流

基于 Alex Nguyen (@alexcooldev) 分享的 TikTok Slideshow 自动化工作流。

## ⚠️ 重要：这个技能做什么

这是一个**内容创作工作流技能**，不是"发一个 TikTok 链接就自动生成视频"。

**它能做：**
- 分析 TikTok 爆款视频/幻灯片的钩子（Hook）和视觉风格
- 根据分析结果生成类似的 Hook 变体
- 生成 Pinterest 搜索词来配图
- 提供 Node.js Canvas 脚本 + slides-config.json 来批量生成幻灯片 PNG
- 提供 Postiz Agent CLI 排期发布流程

**它不能做（需要用户配合）：**
- ✅ 爬取 TikTok 视频内容 ✓ （tikwm API 可获取元数据）
- ❌ 自动生成视频（需要你提供 Pinterest 图片和自己的 Niche）
- ❌ 自动发布到 TikTok（需要你装 Postiz CLI + 关联 TikTok 账号）

**典型用法：**
1. 你发一个爆款 TikTok slideshow 链接
2. 我分析钩子和视觉风格
3. 你告诉我你的 Niche（健身 / 理财 / 美妆 / 书单...）
4. 你从 Pinterest 找图放在本地文件夹
5. 我生成 slides-config.json + Canvas 脚本
6. 你跑 `node generate-slides.js` 生成幻灯片
7. 你用 Postiz CLI 排期发布

## 流程概览

❌ **不是"发一个 TikTok 链接就自动生成视频"**  
用户发一个 TikTok URL 过来，Hermes **不能直接生成视频**。需要走完 6 步流程。

❌ **不是自动剪辑/搬运他人视频的工具**  
这是**创作你自己 niche 的幻灯片内容**的工作流，不是下载编辑别人的视频。

✅ **是内容创作辅助**：分析爆款 → 提取钩子 → Pinterest 找图 → 脚本生成幻灯片 → 排期发布

## 用户预期管理

当用户说"根据这个 TikTok 帮我生成视频"时，应该回复：
1. 先分析这个视频的 Hook 和视觉风格（能做的事）
2. 问用户的 Niche/领域（健身/理财/美妆/书单...）
3. 说明需要用户提供 Pinterest 图片才能走完流程
4. 不能直接产出最终视频

## 流程概览

```
TikTok Scroll → SnapTik 下载 → Claude 提取 Hook
     ↓
Pinterest 找图 → Node.js Canvas 生成 PNG 幻灯片
     ↓
Postiz Agent CLI → 排期 Draft
     ↓
TikTok App → Drafts → 手动发布
```

## 前置安装

```bash
# 1. 安装 Postiz CLI
npm install -g postiz

# 2. 注册 Postiz → Settings → API Keys → 复制 API Key
export POSTIZ_API_KEY=your_api_key_here
# 添加进 ~/.zshrc 持久化

# 3. 创建项目并安装 Canvas
mkdir tiktok-slide-gen && cd tiktok-slide-gen
npm init -y
npm install @napi-rs/canvas

# 4. （可选）字体下载
# 下载 Montserrat-Black.ttf 或其他粗体字体放到 ./fonts/
```

## Step 1: 找钩子

从 TikTok 找正在爆的 slideshow 视频：
- 搜索 niche 关键词（StudyTok / GymTok / BookTok / 理财）
- 按 Most Liked 或 Most Recent 排序
- 用 SnapTik.app 或 SSSTik.io 下载无水印视频
- 记录：前 3 秒文字覆盖、开头语、重复出现的格式

## Step 2: 用 Claude 提取 Hook

将下载的幻灯片上传给 Claude（Opus 4.7），使用以下 prompt：

```
Analyze this TikTok slideshow and:

1. Identify the main hook used in the first slide
   (focus on text overlay, headline, and visual framing)

2. Explain why this hook works
   (curiosity / pain point / surprise / relatability)

3. Break down the hook structure
   (e.g., number + outcome, negative framing, identity targeting)

4. Write 5 similar hook variations for the niche [YOUR NICHE HERE]
   - Each hook under 10 words
   - Format: a question OR a strong statement
   - Avoid generic openers like "Did you know"

Output as a numbered list, one hook per line.
```

**同时生成 Pinterest 搜索词：**

```
Based on this slideshow, suggest 10 Pinterest search queries
that match the visual style and content theme.

Focus on:
- Aesthetic keywords
- Composition (minimal, bold text, dark mode, etc.)
- Niche-specific visuals

Output as a list of short search phrases.
```

保存 Hook 到 Obsidian / Notion / Google Sheets 建立 Hook 数据库。

## Step 3: 从 Pinterest 找图

把 Claude 生成的搜索词粘贴到 Pinterest 搜索。
选图标准：
- **比例**: 9:16 portrait 优先，landscape 也行脚本会切
- **颜色**: 高对比度、粗体，避免柔和色调
- **内容**: 图片上文字尽量少（后续要叠加 hook 文字）
- **氛围**: 匹配 hook 的情感（理财=生活方式图，健身=动作图）

下载方式：PinDown Chrome 插件 / 右键保存 / Python 批量下载

## Step 4: 生成幻灯片 (Node.js Canvas)

### 项目结构
```
tiktok-slide-gen/
├── generate-slides.js      # 幻灯片生成脚本
├── slides-config.json      # 幻灯片配置
├── pinterest_images/        # 图片源文件夹
│   └── finance/
├── output/                 # 输出文件夹
└── fonts/
    └── Montserrat-Black.ttf
```

### generate-slides.js

```javascript
import { createCanvas, loadImage, GlobalFonts } from '@napi-rs/canvas'
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const OUTPUT_DIR = './output'
const CANVAS_W = 1080
const CANVAS_H = 1920
const OVERLAY_OPACITY = 0.52
const OVERLAY_COLOR = '0,0,0'

function wrapText(ctx, text, maxWidth) {
  const words = text.split(' ')
  const lines = []
  let current = ''
  for (const word of words) {
    const test = current ? `${current} ${word}` : word
    if (ctx.measureText(test).width > maxWidth && current) {
      lines.push(current)
      current = word
    } else {
      current = test
    }
  }
  if (current) lines.push(current)
  return lines
}

async function generateSlide(slide, index) {
  const canvas = createCanvas(CANVAS_W, CANVAS_H)
  const ctx = canvas.getContext('2d')

  const img = await loadImage(slide.imagePath)
  const scale = Math.max(CANVAS_W / img.width, CANVAS_H / img.height)
  const drawW = img.width * scale
  const drawH = img.height * scale
  const offsetX = (CANVAS_W - drawW) / 2
  const offsetY = (CANVAS_H - drawH) / 2
  ctx.drawImage(img, offsetX, offsetY, drawW, drawH)

  ctx.fillStyle = `rgba(${OVERLAY_COLOR},${OVERLAY_OPACITY})`
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

  const PADDING = 80
  const MAX_TEXT_W = CANVAS_W - PADDING * 2

  for (const line of slide.lines) {
    ctx.font = `${line.weight} ${line.size}px sans-serif`
    ctx.fillStyle = '#ffffff'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.shadowColor = 'rgba(0,0,0,0.75)'
    ctx.shadowBlur = 12
    ctx.shadowOffsetY = 4

    const wrapped = wrapText(ctx, line.text, MAX_TEXT_W)
    const lineHeight = line.size * 1.2
    wrapped.forEach((l, i) => {
      ctx.fillText(l, CANVAS_W / 2, line.y + i * lineHeight)
    })
  }

  mkdirSync(OUTPUT_DIR, { recursive: true })
  const outPath = join(OUTPUT_DIR, `slide_${String(index + 1).padStart(2, '0')}.png`)
  const buffer = canvas.toBuffer('image/png')
  writeFileSync(outPath, buffer)
  console.log(`✓ ${outPath}`)
}

async function main() {
  const slides = JSON.parse(readFileSync('./slides-config.json', 'utf-8'))
  console.log(`Generating ${slides.length} slides...`)
  for (let i = 0; i < slides.length; i++) {
    await generateSlide(slides[i], i)
  }
  console.log(`\nDone → ${OUTPUT_DIR}/`)
}

main().catch(console.error)
```

### slides-config.json

```json
[
  {
    "imagePath": "./pinterest_images/finance/image_001.jpg",
    "lines": [
      { "text": "I saved $5k in 6 months", "size": 88, "weight": "bold", "y": 860 },
      { "text": "doing this one thing", "size": 72, "weight": "normal", "y": 970 }
    ]
  },
  {
    "imagePath": "./pinterest_images/finance/image_002.jpg",
    "lines": [
      { "text": "Most people spend", "size": 64, "weight": "normal", "y": 820 },
      { "text": "before they save.", "size": 64, "weight": "bold", "y": 910 },
      { "text": "Here's why that's a trap.", "size": 56, "weight": "normal", "y": 990 }
    ]
  },
  {
    "imagePath": "./pinterest_images/finance/image_003.jpg",
    "lines": [
      { "text": "01. Pay yourself first", "size": 72, "weight": "bold", "y": 900 },
      { "text": "Move 20% to savings on payday.", "size": 52, "weight": "normal", "y": 990 },
      { "text": "Before any expense hits.", "size": 52, "weight": "normal", "y": 1060 }
    ]
  },
  {
    "imagePath": "./pinterest_images/finance/image_006.jpg",
    "lines": [
      { "text": "Save this post 🔖", "size": 80, "weight": "bold", "y": 860 },
      { "text": "Follow for more money tips", "size": 56, "weight": "normal", "y": 970 },
      { "text": "every week →", "size": 56, "weight": "normal", "y": 1050 }
    ]
  }
]
```

运行：
```bash
node generate-slides.js
```

## Step 5: Postiz CLI 排期发布

### 配置 Postiz

```bash
# 设置 API Key
export POSTIZ_API_KEY=your_api_key_here

# 连接 TikTok 账号 — 先在 app.postiz.com → Integrations → Add Channel → TikTok 授权
postiz integrations:list
# 记下 TikTok integration ID
```

### 上传幻灯片并排期

```bash
# 上传每张幻灯片，获取 CDN URL
SLIDE1=$(postiz upload ./output/slide_01.png | jq -r '.path')
SLIDE2=$(postiz upload ./output/slide_02.png | jq -r '.path')
SLIDE3=$(postiz upload ./output/slide_03.png | jq -r '.path')

# 创建排期帖子（多图 slideshow）
postiz posts:create \
  -c "I saved \$5k in 6 months doing this 💰 #personalfinance #moneytips" \
  -m "$SLIDE1" -m "$SLIDE2" -m "$SLIDE3" \
  -s "2026-04-21T09:00:00Z" \
  -i "clx9abc123"   # ← 你的 TikTok integration ID
```

### 批量排期一周

创建 `schedule.json` 和 `batch-schedule.js`，一次性上传整个星期的内容。

### Safe Publishing — Draft 模式

避免直接 API 发布被 TikTok 标记为机器人：

1. **Draft 模式**: 用 `-t draft` 让帖子留在 Postiz 草稿
2. **TikTok Inbox 推送**: 设置 `content_posting_method: "UPLOAD"`，推送至 TikTok App 的 Inbox，在手机上手动发布
3. **Postiz Notify 模式**: 设置推送通知提醒 → 手机打开 TikTok → Drafts → 手动点发布

关键：从 Postiz 录入日历，从手机手动发布 — TikTok 看到的是真人行为。

## 幻灯片结构模板

| 幻灯片 | 内容 | 示例 |
|--------|------|------|
| Slide 1 | HOOK（最强图片+钩子文字） | "I saved $5k in 6 months doing this" |
| Slide 2 | 问题/设定 | "Most people spend before they save" |
| Slide 3 | 要点 1 | "01. Pay yourself first" |
| Slide 4 | 要点 2 | "02. Kill subscriptions" |
| Slide 5 | 要点 3 | "03. Use cash envelopes" |
| Slide 6 | CTA | "Save this post 🔖 Follow →" |

## 预期管理

**⚠️ 这个技能是一个工作流，不是一键生成器。** 发一个 TikTok 链接不会自动生成视频。

正确的使用方式：
1. 你提供一个爆款的 TikTok 视频/幻灯片链接
2. 我分析它的钩子（Hook）和视觉风格
3. 你告诉我你的 **Niche/领域**（健身、理财、美妆、书单...）
4. 你去 Pinterest 找对应风格的图片，或告诉我关键词我帮你生成搜索词
5. 我帮你写 `slides-config.json` + `generate-slides.js`
6. 你在本地 `node generate-slides.js` 生成 PNG 幻灯片
7. 你用 Postiz CLI 排期发布

> 如果给的是普通视频（非幻灯片），分析的是它的标题、文案结构、视觉风格 → 生成可复用的 Hook 模板，仍然是同一条工作流。

## 与 AiToEarn 的关系

AiToEarn（`aitoearn-mcp` 技能）是一个全平台内容营销 SaaS，支持一键发布到 10+ 平台（含 TikTok）。两者互补：

- **本技能**：负责内容创作（Hook 分析、Pinterest 找图、Node.js Canvas 生成幻灯片 PNG）
- **AiToEarn**：负责内容发布与排期（替代 Postiz CLI，支持更多平台、日历排期、MCP 集成）

如果你已经配置了 AiToEarn MCP，生成幻灯片后可以直接通过 AiToEarn 发布，无需单独安装 Postiz CLI。

## 坑／注意事项

- `POSTIZ_API_KEY` 环境变量必须在当前 shell 生效，建议写入 `~/.zshrc`
- `postiz integrations:list` 返回空数组 → 还没在 app.postiz.com 上关联 TikTok 账号
- 大 PNG 文件可用 `pngquant` 压缩后再上传
- 排期失败 → 检查 TikTok OAuth 是否过期，去 app.postiz.com 重新授权
- 新账号/高频率发帖 → 务必用 Draft 模式避免被限流

## 用户预期管理

用户初次使用时，通常会以为"发一个 TikTok URL = 自动生成视频"，需要明确说明这个技能是**工作流**而非**一键生成**：

1. **明确告诉用户需要什么**：Niche + Pinterest 图片（Hermes 没有自动找图的能力）
2. **明确区分 slideshow vs 普通视频**：72 秒的真人视频不是 slideshow，只能分析钩子写法，无法直接生成幻灯片
3. **明确分步流程**：不要一次性要求所有信息，引导用户一步步走（先分析 → 再问 Niche → 再引导找图 → 再生成配置）
