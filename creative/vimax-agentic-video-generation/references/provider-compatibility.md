# Provider & Model Compatibility (China/GFW Environment)

## OpenRouter 模型在国内的可访问性

从 WSL（中国网络环境）实测结果：

| 模型 ID | 文本 | 多模态 | 国内可用 | 成本 | 备注 |
|---------|------|--------|---------|------|------|
| `google/gemini-2.5-flash-lite-preview-09-2025` | ✅ | ✅ | ❌ 403 | — | ViMax 默认，国内不通 |
| `openai/gpt-4o-mini` | ✅ | ✅ | ❌ 403 | — | |
| `deepseek/deepseek-chat` | ✅ | ❌ | ✅ | ~$0.14/M | 文本任务首选 |
| `~moonshotai/kimi-latest` | ✅ | ✅ | ✅ | 需余额 | 国产多模态，推荐 |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | ✅ | ✅ | ✅ | 免费 | ⚠️ 不稳定，JSON 解析经常失败 |
| `mistralai/mistral-medium-3-5` | ✅ | ✅ | ❓ | — | 未测试 |
| `google/gemini-3.1-flash-lite` | ✅ | ✅ | ❓ | — | 新版 Gemini |

## OpenRouter 余额问题

当 OpenRouter 账户余额不足时，报错:
```
Error code: 402 - This request requires more credits, or fewer max_tokens.
You requested up to 65536 tokens, but can only afford 7973.
```

注意：OpenRouter 的余额以 tokens 为单位显示，不是以美元为单位。实际上不同模型费用不同，
deepseek-chat 很便宜（$0.14/M input），Kimi 较贵。

## 国内 API 直连方案

| Provider | Base URL | 模型推荐 | 多模态 | 备注 |
|----------|---------|---------|--------|------|
| DeepSeek 官方 | `https://api.deepseek.com` | `deepseek-chat` | ❌ | 最便宜的付费文本模型 |
| 月之暗面 Kimi | `https://api.moonshot.cn` | `moonshot-v1-auto` | ✅ | 有免费额度 |
| SiliconFlow | `https://api.siliconflow.cn` | Qwen-VL 系列 | ✅ | 各种开源模型 |
| 云舞 (yunwu.ai) | `https://yunwu.ai` | 代理 Google Veo/Gemini | ✅ | 图像+视频生成 |

## Pipeline 各阶段模型需求速查

| 阶段 | 文件 | 需要能力 | 可用模型 |
|------|------|---------|---------|
| story dev | `screenwriter.py:develop_story()` | 纯文本 | DeepSeek Chat ✅ |
| character extract | `screenwriter.py:extract_characters()` | 纯文本 | DeepSeek Chat ✅ |
| script writing | `screenwriter.py:write_script_based_on_story()` | 纯文本 | DeepSeek Chat ✅ |
| storyboard | `storyboard_designer.py` | 纯文本 | DeepSeek Chat ✅ |
| shot decompose | `shot_decomposer.py` | 纯文本 | DeepSeek Chat ✅ |
| **ref image select** | `reference_image_selector.py` | **图像输入** | **必须多模态模型** |
| image gen | Image Generator | 图像生成 | 云舞 Gemini |
| video gen | Video Generator | 视频生成 | 云舞 Veo |

## 推荐配置顺位

1. **Chat Model: 月之暗面 Kimi 官方 API** → `api.moonshot.cn`（国产，多模态，免费额度）
2. **Chat Model: OpenRouter + Kimi** → 如果已有 OpenRouter 余额
3. **Image Gen: 云舞 Nanobanana** → `yunwu.ai` 代理 Gemini Image
4. **Video Gen: 云舞 Veo** → `yunwu.ai` 代理 Google Veo

## 配置同步规则

`configs/idea2video.yaml` 和 `configs/script2video.yaml` 是两个独立的配置文件，
ViMax 的 Idea2Video pipeline 使用前者，Script2Video pipeline 使用后者。
但 Idea2Video 内部会调用 Script2Video pipeline，因此**两个文件必须同步修改**。
