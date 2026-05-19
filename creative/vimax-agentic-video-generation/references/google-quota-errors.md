# Google Gemini Image API 配额错误参考

## 错误信息

```
google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED.
{'error': {
  'code': 429,
  'message': 'You exceeded your current quota, please check your plan and billing details.
    * Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-flash-preview-image
    * Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-flash-preview-image
    * Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-flash-preview-image
  Please retry in 44.134975597s.',
  'status': 'RESOURCE_EXHAUSTED'
  }
}
```

## 原因
- `limit: 0` 表示免费层的限额已经用完或根本不存在
- `gemini-2.5-flash-preview-image` 模型可能已不再提供免费额度
- 需要绑定付费账号或更换模型

## 解决方案

### 方案 1：使用 Google 付费版
1. 在 https://aistudio.google.com/apikey 创建付费 API Key
2. 在 Google Cloud Console 启用 Generative Language API 并配置结算

### 方案 2：通过云舞代理（推荐国内用户）
1. 在 https://yunwu.ai 注册获取 API Key
2. 修改 `configs/idea2video.yaml`：
```yaml
image_generator:
  class_path: tools.ImageGeneratorNanobananaYunwuAPI  # 改用云舞代理
  init_args:
    api_key: <云舞_API_KEY>

video_generator:
  class_path: tools.VideoGeneratorVeoYunwuAPI  # 改用云舞代理
  init_args:
    api_key: <云舞_API_KEY>
```

### 方案 3：使用豆包模型
```yaml
image_generator:
  class_path: tools.ImageGeneratorDoubaoSeedreamYunwuAPI
  init_args:
    api_key: <云舞_API_KEY>

video_generator:
  class_path: tools.VideoGeneratorDoubaoSeedanceYunwuAPI
  init_args:
    api_key: <云舞_API_KEY>
```
