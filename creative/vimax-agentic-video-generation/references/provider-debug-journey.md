# ViMax Provider Debugging Journey

This document records the provider compatibility testing done during one session.
Use this as a diagnostic reference when setting up ViMax from scratch in China.

## Environment

- WSL2 (Ubuntu), behind GFW
- Python 3.12, uv package manager
- Target: Run `main_idea2video.py` for a Chinese DeFi startup story

## Provider Attempts (in order)

### Attempt 1: Google AI API (Direct)
- **Image Gen**: `ImageGeneratorNanobananaGoogleAPI` 
- **Video Gen**: `VideoGeneratorVeoGoogleAPI`
- **Result**: ❌ Google free tier exhausted (429), GFW blocks direct API
- **Error**: `429 RESOURCE_EXHAUSTED - Quota exceeded for free tier`

### Attempt 2: OpenRouter + Google Gemini (via OpenRouter)
- **Model**: `google/gemini-2.5-flash-lite-preview-09-2025`
- **Result**: ❌ Region blocked
- **Error**: `403 - This model is not available in your region`

### Attempt 3: OpenRouter + GPT-4o-mini
- **Model**: `openai/gpt-4o-mini`
- **Result**: ❌ Region blocked
- **Error**: `403 - This model is not available in your region`

### Attempt 4: OpenRouter + DeepSeek Chat
- **Model**: `deepseek/deepseek-chat`
- **Result**: ❌ No multimodal support
- **What worked**: Story, characters, script, storyboard, shot descriptions all passed (text-only)
- **What failed**: `reference_image_selector` needs image input
- **Error**: `404 - No endpoints found that support image input`

### Attempt 5: OpenRouter + Kimi (Moonshot)
- **Model**: `~moonshotai/kimi-latest`
- **Result**: ❌ Insufficient credits
- **Error**: `402 - You requested up to 65536 tokens, but can only afford 7973`

### Attempt 6: OpenRouter + NVIDIA Nemotron (Free)
- **Model**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
- **Result**: ❌ Unreliable JSON output
- **Error**: `JSONDecodeError: Expecting value` - free model rate-limited, returns garbled responses

### Attempt 7: SiliconFlow + Qwen3-VL-32B-Instruct
- **Provider**: `https://api.siliconflow.cn/v1`
- **Model**: `Qwen/Qwen3-VL-32B-Instruct`
- **Result**: ✅ ALL TEXT + MULTIMODAL tasks passed
- **Note**: Chinese provider, no GFW issues, no credit problems with valid API key

### Attempt 8 (video): YunWu Veo
- **Video Gen**: `VideoGeneratorVeoYunwuAPI`
- **Result**: ⚠️ Partial - shots 0, 1 succeeded, shots 2, 3 failed
- **Error**: `PUBLIC_ERROR_AUDIO_FILTERED` - content moderation flags DeFi/business prompts

### Attempt 9 (video): YunWu Seedance/即梦
- **Video Gen**: `VideoGeneratorDoubaoSeedanceYunwuAPI`
- **Model**: `doubao-seedance-1-0-lite-t2v-250428`
- **Result**: ✅ No content moderation, Chinese domestic model
- **Note**: Use `yunwu.ai` as proxy for ByteDance's 火山引擎 API

## Working Configuration

```yaml
# configs/idea2video.yaml
chat_model:
  init_args:
    model: Qwen/Qwen3-VL-32B-Instruct
    model_provider: openai
    api_key: <SILICONFLOW_API_KEY>
    base_url: https://api.siliconflow.cn/v1
  max_requests_per_minute: 500
  max_requests_per_day: 2000

image_generator:
  class_path: tools.ImageGeneratorNanobananaYunwuAPI
  init_args:
    api_key: <YUNWU_API_KEY>
  max_requests_per_minute: null
  max_requests_per_day: null

video_generator:
  class_path: tools.VideoGeneratorDoubaoSeedanceYunwuAPI
  init_args:
    api_key: <YUNWU_API_KEY>
  max_requests_per_minute: null
  max_requests_per_day: null

working_dir: .working_dir/idea2video
```

## Key Lessons

1. **Domestic providers are essential** in China - OpenRouter blocks many models, Google is GFW'd
2. **SiliconFlow** has excellent multi-modal models (Qwen3-VL series) that handle both text and image tasks
3. **YunWu AI** is a proxy service that can relay Google (Veo/Gemini) or ByteDance (Seedance) APIs
4. **Veo vs Seedance**: Veo has better quality but strict content moderation; Seedance/即梦 has no Chinese content restrictions
5. **The `reference_image_selector` agent requires multimodal** - cannot use text-only models like DeepSeek Chat
6. **rate_limiter parameter**: YunWu classes don't accept `rate_limiter`, must set `max_requests_per_minute: null`
