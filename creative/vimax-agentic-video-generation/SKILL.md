---
name: vimax-agentic-video-generation
description: ViMax — Agentic Video Generation (导演/编剧/制片/视频生成一体). HKUDS 开源项目，支持 Idea2Video / Script2Video / Novel2Video / AutoCameo 四种模式。多智能体编排，端到端视频生成。
trigger:
  - "vimax"
  - "agentic video"
  - "agentic video generation"
  - "视频生成"
  - "智能视频"
  - "idea2video"
  - "script2video"
  - "novel2video"
  - "云舞"
  - "yunwu"
  - "veo"
  - "seedream"
  - "文档生成视频"
  - "pdf 转视频"
---

# ViMax: Agentic Video Generation 🎬

> 项目地址: https://github.com/HKUDS/ViMax  
> 本地安装: `~/ViMax/`
> 用户配置: 需要 3 组 API Key（chat model + image generator + video generator）

## 安装

```bash
cd ~/ViMax
uv sync
```

**环境要求**: Python >= 3.12, Linux/Windows  
**依赖**: openai, google-genai, langchain, moviepy, opencv-python, faiss-cpu, scenedetect

## 四种工作模式

| 模式 | 入口 | 说明 | 状态 |
|------|------|------|------|
| 🧠 Idea2Video | `main_idea2video.py` | 一句话创意 → 完整视频 | ✅ 可用 |
| ⚙️ Script2Video | `main_script2video.py` | 剧本 → 视频 | ✅ 可用 |
| 🎨 Novel2Video | `pipelines/novel2movie_pipeline.py` | 小说 → 分集视频 | ⏳ `# TODO: NOT IMPLEMENTED YET` |
| 🤳 AutoCameo | — | 照片 → 客串视频 | ⏳ 未实现 |

> Idea2Video 内部实际调用 Script2Video pipeline——`idea2video_pipeline.py` 先写故事/剧本/分镜，然后调用 `script2video_pipeline.py` 完成镜头生成和视频合成。

## 项目结构

```
~/ViMax/
├── agents/                     # 智能体
│   ├── screenwriter.py         # 编剧（故事+剧本）
│   ├── storyboard_designer.py  # 分镜设计
│   ├── shot_decomposer.py      # 镜头分解
│   ├── reference_image_selector.py  # 参考图选择（需要多模态！）
│   ├── character_portraits_generator.py
│   └── video_synthesis_agent.py
├── configs/
│   ├── idea2video.yaml
│   ├── script2video.yaml
│   └── idea2video_minimax.yaml / script2video_minimax.yaml
├── pipelines/
│   ├── idea2video_pipeline.py       # ✅ 主入口
│   ├── script2video_pipeline.py     # ✅ 被 Idea2Video 内部调用
│   └── novel2movie_pipeline.py      # ⏳ 未完成
├── tools/                      # 图像/视频生成器实现
├── main_idea2video.py          # 修改这里的 idea/user_requirement/style
├── main_script2video.py
├── pyproject.toml
└── uv.lock
```

## 配置详解

### 基本 YAML 结构

```yaml
chat_model:
  init_args:
    model: <模型 ID>
    model_provider: openai          # 必须用 openai 兼容模式
    api_key: <YOUR_API_KEY>
    base_url: <API_ENDPOINT_URL>
  max_requests_per_minute: 500      # 可设 null
  max_requests_per_day: 2000

image_generator:
  class_path: tools.ImageGeneratorNanobananaYunwuAPI   # 完整 Python 类路径
  init_args:
    api_key: <YOUR_API_KEY>
  max_requests_per_minute: null     # YunWu 类必须设 null！
  max_requests_per_day: null

video_generator:
  class_path: tools.VideoGeneratorVeoYunwuAPI
  init_args:
    api_key: <YOUR_API_KEY>
  max_requests_per_minute: null
  max_requests_per_day: null

working_dir: .working_dir/idea2video
```

### 可用 Provider 一览

#### Chat Model（AI 对话/规划）

| Provider | 国内可用 | 多模态 | 成本 | 备注 |
|----------|---------|--------|------|------|
| DeepSeek 官方 (`api.deepseek.com`) | ✅ | ❌ 纯文本 | ~$0.14/M tok | 文本任务首选，便宜稳定 |
| OpenRouter + Moonshot/Kimi | ✅ | ✅ 图像 | 需充值 | 多模态方案，参考图选择必备 |
| OpenRouter + DeepSeek Chat | ✅ | ❌ | 需充值 | 文本任务可用 |
| OpenRouter + Gemini/GPT-4o | ❌ 403 | ✅ | — | 国内被墙 |
| SiliconFlow | ✅ | ✅ | 免费/付费 | 托管 Qwen-VL 等国产多模态 |
| **Kimi (Moonshot) 官方 API** | ✅ | ✅ | 有免费额度 | `api.moonshot.cn` |

> ⚠️ **必须理解**: `reference_image_selector` agent 会把生成的 PNG 首帧图发给 chat model。这意味着 **chat model 必须支持图像输入 (multimodal)**。纯文本模型（如 DeepSeek Chat）会报 404。详见 `references/provider-compatibility.md`。\n> **但 SiliconFlow 多模态调用极不稳定**——如果卡死在此步，可用 `scripts/patch-skip-multimodal.sh` 跳过多模态阶段，纯文本选择参考图。详见 `references/siliconflow-timeout-patterns.md`。

#### Image Generator（图像生成）

| 实现类 | 所需 Key | 模型 | 国内可用 | 备注 |
|--------|---------|------|---------|------|
| `ImageGeneratorNanobananaGoogleAPI` | Google AI API | Gemini 2.5 Flash Image | ❌ GFW | 免费配额极低易 429 |
| `ImageGeneratorNanobananaYunwuAPI` | 云舞 Key | Gemini 2.5 Flash Image (代理) | ✅ | 推荐，不支持 rate_limiter |
| `ImageGeneratorDoubaoSeedreamYunwuAPI` | 云舞 Key | 豆包 Seedream 4.0 | ✅ | 国产模型，通过云舞 API |

#### Video Generator（视频生成）

| 实现类 | 所需 Key | 模型 | 国内可用 | 备注 |
|--------|---------|------|---------|------|
| `VideoGeneratorVeoGoogleAPI` | Google AI API | Google Veo | ❌ GFW | |
| `VideoGeneratorVeoYunwuAPI` | 云舞 Key | Veo 系列 (代理) | ✅ | 推荐，不支 rate_limiter |
| `VideoGeneratorDoubaoSeedanceYunwuAPI` | 云舞 Key | 豆包 Seedance/即梦 | ✅ | 国产无审核，支持 1080p 推荐 |

**云舞 Veo 模型列表:**
```
veo2, veo2-fast, veo2-fast-frames (首尾帧), veo2-pro
veo3, veo3-fast, veo3-pro, veo3-frames
```
veo3 不支持首尾帧，需用 veo2-fast-frames 或 veo3-frames。

### 推荐的国内用户配置（✅ 推荐 — Kimi + 即梦/Seedance）

```yaml
# configs/idea2video.yaml
chat_model:
  init_args:
    model: kimi-latest                        # 国产多模态，看图稳，不超时
    model_provider: openai
    api_key: <KIMI_API_KEY>
    base_url: https://api.moonshot.cn/v1
  max_requests_per_minute: 500
  max_requests_per_day: null

image_generator:
  class_path: tools.ImageGeneratorNanobananaYunwuAPI
  init_args:
    api_key: <YUNWU_API_KEY>
  max_requests_per_minute: null
  max_requests_per_day: null

video_generator:
  class_path: tools.VideoGeneratorDoubaoSeedanceYunwuAPI   # 即梦/Seedance，无审核
  init_args:
    api_key: <YUNWU_API_KEY>
  max_requests_per_minute: null
  max_requests_per_day: null
```

> Kimi (`kimi-latest`) 是国产多模态模型中最稳定的选择，参考图选择环节不再卡死。月之暗面官方 API `api.moonshot.cn` 国内直连无墙。

## 运行流程（Idea2Video Pipeline）

Pipeline 各阶段及模型需求：

| # | 阶段 | Agent/File | 调用模型 | 需要能力 | 典型耗时 |
|---|------|-----------|---------|---------|---------|
| 1 | 故事生成 | `screenwriter.develop_story()` | Chat Model | 纯文本 | ~10s |
| 2 | 角色提取 | `screenwriter.extract_characters()` | Chat Model | 纯文本 | ~5s |
| 3 | 角色肖像 | `character_portraits_generator` | **Image Generator** | 图像生成 | ~30s/角色 |
| 4 | 剧本编写 | `screenwriter.write_script_based_on_story()` | Chat Model | 纯文本 | ~20s |
| 5 | 分镜设计 | `storyboard_designer` | Chat Model | 纯文本 | ~10s |
| 6 | 镜头分解 | `shot_decomposer` | Chat Model | 纯文本 | ~10s/镜头 |
| 7 | 参考图选择 | `reference_image_selector` | **Chat Model 多模态** | 图像输入！ | 见 Patch |
| 8 | 首帧生成 | Image Generator | 图像生成 | ~15s/镜头 |
| 9 | 过渡视频 | Video Generator | 视频生成 | ~60s/镜头 |
| 10 | 最终合成 | 视频拼接 | — | ~10s |

> 第 7 步是唯一需要 chat model 支持图像输入的环节。其余文本步骤可用纯文本模型（如 DeepSeek Chat）。

## 使用方式

### Idea2Video

```bash
cd ~/ViMax
uv run python main_idea2video.py
```

修改 `main_idea2video.py`:
```python
idea = """你的创意描述"""
user_requirement = """约束条件（场景数、镜头数、受众等）"""
style = "视觉风格（如 Cartoon, Realistic, Anime）"
```

### Script2Video

```bash
cd ~/ViMax
uv run python main_script2video.py
```

### 文档转视频（PDF/DOC → Idea2Video）

1. 从 PDF 提取文本（pymupdf / pypdf）
2. 把文本梗概/中心思想放入 `main_idea2video.py` 的 `idea` 变量
3. 修改 `user_requirement` 约束风格和长度
4. 运行

**PDF 提取示例:**
```python
import pymupdf
doc = pymupdf.open('/tmp/your_file.pdf')
text = ''.join(page.get_text() for page in doc)
```

### 清理工作目录（重要）

ViMax 会缓存结果到 `working_dir`，修改配置后必须清理：
```bash
# 用 mv 替代 rm（Hermes 安全策略拦截 rm -rf）
mv ~/ViMax/.working_dir ~/ViMax/.working_dir_old
```

## 踩坑大全

### 1. API 收费/配额

| 错误 | 原因 | 解决 |
|------|------|------|
| `429 RESOURCE_EXHAUSTED` | Google 免费配额用完 | 换云舞代理或充值，降`max_requests_per_minute` |
| `insufficient_quota: user quota: $0.20, need: $0.225` | 云舞余额不足 | 去 yunwu.ai 充值 |
| `402: can only afford 7973 tokens` | OpenRouter 余额不足 | 充值或换免费模型 |
| `403: This model is not available in your region` | 国内无法访问该模型 | 换 Kimi/DeepSeek 等国内可用的模型 |

### 2. 代码 Bug

- `tools/image_generator_nanobanana_google_api.py` 第 67 行: `e.status_code` → `e.code`
  （`google.genai.errors.ClientError` 用 `.code` 不是 `.status_code`）

### 3. 云舞 (yunwu.ai) 特有坑

**rate_limiter 参数不兼容** — YunWu 系列类不接受 `rate_limiter` 参数。配置中 `max_requests_per_minute` 和 `max_requests_per_day` 必须设为 `null`。

**Veo 内容审核** — Google Veo 审核音轨，以下内容可能触发 `PUBLIC_ERROR_AUDIO_FILTERED`：
- 健身/人体特写（如臀部训练）
- **商业/金融关键词**（如 DeFi、交易、聚合器、加密货币）
- 品牌名、产品名
遇到此错误换 即梦/Seedance（国产，无审核限制）。

**错误** | `Connection timeout to host https://yunwu.ai` | 云舞偶发超时 | 代码会重试但如果返回 None 会崩。重启即可 |

### 4. SiliconFlow API 超时/稳定性问题

SiliconFlow 的 Qwen3-VL-32B-Instruct 在国内可用，但**频繁超时**，尤其在以下环节：

| 环节 | 表现 | 影响 |
|------|------|------|
| `construct_camera_tree` | `TimeoutError()` 重试循环 | pipeline 卡死 |
| `reference_image_selector` | 需要多模态看图，超时重试 | pipeline 卡死 |
| `shot_decomposer` | 每 shot 都可能超时重试 | 极慢但能推进 |

经验：
- SiliconFlow 做纯文本任务（story/script/storyboard）通常能跑完，只是慢
- 进入 `construct_camera_tree` 和 `reference_image_selector` 阶段（需要长上下文/多模态推理）时最容易卡死
- 卡死后进程仍存活（0.4-1% CPU），但不再写文件——**判断方法：检查最后修改时间，超过5分钟无新文件=卡死**
- **推荐替代方案**：月之暗面 Kimi 官方 API (`api.moonshot.cn`, model `moonshot-v1-auto`)，国产多模态，稳定性远好于 SiliconFlow

### 5. Chat Model 选型陷阱

| 陷阱 | 表现 | 原因 |
|------|------|------|
| 纯文本模型 | 首帧阶段报 404 `No endpoints found that support image input` | reference_image_selector 需要多模态 |
| 地区限制模型 | 开局直接 403 | 国内无法访问 Google/GPT 模型 |
| 免费模型 | 不稳定 JSON，中途崩 | 换付费模型 |

### 6. SiliconFlow 多模态卡死 — 跳过多模态参考图选择

根因：`agents/reference_image_selector.py` 的第二步会把角色肖像/首帧图片 base64 编码后发给 chat model 做多模态选图，SiliconFlow 在这一步频繁超时卡死。

**方案 A：跳过多模态（推荐）** — 修改 `reference_image_selector.py`，注释掉多模态阶段，直接用纯文本筛选结果：

```python
# Patch applied — replaces multimodal stage with text-only fallback
# See scripts/patch-skip-multimodal.sh for auto-apply
reference_image_path_and_text_pairs = filtered_image_path_and_text_pairs[:8]
prompt_parts = []
for idx, (_, text) in enumerate(reference_image_path_and_text_pairs):
    prompt_parts.append(f"Image {idx}: {text}")
prompt_parts.append(f"Create an image based on: {frame_description}")
text_prompt = "\n".join(prompt_parts)
return {
    "reference_image_path_and_text_pairs": reference_image_path_and_text_pairs,
    "text_prompt": text_prompt,
}
```

运行 `scripts/patch-skip-multimodal.sh` 自动应用此 patch。

**方案 B：换 Kimi（彻底解决）** — 配置 Kimi 官方 API：
```yaml
chat_model:
  init_args:
    model: moonshot-v1-auto
    model_provider: openai
    api_key: <KIMI_API_KEY>
    base_url: https://api.moonshot.cn/v1
```

### 7. 进程管理 — 判断卡死

ViMax pipeline 跑起来后（`background=true`），用以下方法判断是否卡死：

```bash
# 检查最后修改时间
find .working_dir -name "*.json" -o -name "*.png" -o -name "*.mp4" | \
  while read f; do echo "$f: $(( $(date +%s) - $(stat -c %Y "$f") ))s ago"; done | \
  sort -t: -k2 -rn | head -10
```

如果所有文件超过 5 分钟未更新，且进程仍存活（`ps aux | grep python` 显示 0.4-1% CPU），说明卡死了，杀掉重试。

### 8. 模型降级策略

当 SiliconFlow 32B 模型频繁超时时：

| 操作 | 效果 |
|------|------|
| 32B → 8B (`Qwen/Qwen3-VL-8B-Instruct`) | 响应更快，但多模态照旧卡 |
| 32B → 轻量 MoE (`Qwen2.5-VL-7B-Instruct`) | 未测 |
| 加 patch 跳过多模态 | ✅ 解决卡死，但参考图纯文本选择精度略降 |

- 修改配置后 **必须清理工作目录**（用 `mv` 不是 `rm`）
- 首次跑通建议用简单的卡通/动物题材（避免 Veo 内容审核）
- 长视频用 `terminal(timeout=600, background=true)` 后台跑
- `configs/` 下两个文件（idea2video + script2video）要同步改
