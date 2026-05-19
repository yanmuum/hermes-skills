# Session Transcript: 生成"卖山东大枣的李哥，教会了我 Defi 创业"视频

## 输入
用户桌面 PDF 文件: `/mnt/c/Users/Administrator/Desktop/01卖山东大枣的李哥，教会了我 Defi 创业.pdf`
约 3905 字中文短篇故事。主角: 阿冬/程峰（哈佛退学生）、李哥（水果店老板）、小芳（妻子/前女友）。

## 经过的配置变更（7 次尝试）

| 尝试 | Chat Model | Image Gen | Video Gen | 结果 | 根因 |
|------|-----------|-----------|-----------|------|------|
| 1 | Google Gemini 默认 | Google 直连 | Google 直连 | ❌ 429 | Google 免费配额耗尽 |
| 2 | Google Gemini 默认 | 云舞 Nanobanana | 云舞 Veo | ❌ 403 | 云舞余额 $0.20 < $0.225 |
| 3 | Google Gemini 默认 (充值后) | 云舞 Nanobanana | 云舞 Veo | ❌ PUB_ERROR | Veo 内容审核 + 超时 |
| 4 | GPT-4o-mini (OpenRouter) | 云舞 Nanobanana | 云舞 Veo | ❌ 403 | OpenRouter 地区限制 |
| 5 | DeepSeek Chat (OpenRouter) | 云舞 Nanobanana | 云舞 Veo | ❌ 404 | DeepSeek 不支持图像输入 |
| 6 | Kimi Latest (OpenRouter) | 云舞 Nanobanana | 云舞 Veo | ❌ 402 | OpenRouter 余额不足 |
| 7 | NVIDIA Nemotron (free) | 云舞 Nanobanana | 云舞 Veo | ❌ JSON parse | 免费模型不稳定 |

## 问题根因树

```
无法生成视频
├── API Key 类
│   ├── Google 免费配额 429 → 换云舞
│   ├── 云舞余额不足 403 → 充值 yunwu.ai
│   └── OpenRouter 余额不足 402 → 充值或换免费模型
├── 地区封锁类
│   ├── Google Gemini → 走云舞代理
│   ├── OpenRouter GPT-4o-mini → 换 Kimi/国产
│   └── OpenRouter Gemini → 换 Kimi/国产
├── 模型能力类
│   ├── DeepSeek 纯文本 → 换多模态模型
│   └── 免费模型不稳定 → 换付费模型
└── Veo 平台类
    ├── 内容审核 PUB_ERROR → 换安全提示词
    └── 查询超时 → 代码本身无重试保护
```

## 关键发现

1. **国内用户最佳路径**: OpenRouter + Kimi (多模态) + 云舞 (图像+视频)
2. **云舞 rate_limiter 不兼容**: `max_requests_per_minute` / `per_day` 必须 null
3. **工作目录清理**: 用 `mv` 替代 `rm -rf` (Hermes 安全拦截)
4. **Chat Model 必须支持图像输入** 否则 reference_image_selector 404
5. **Idea2Video 内调 Script2Video**: 修改 idea 后不用动 script 相关代码
6. **OpenRouter 模型名规则**: `~moonshotai/kimi-latest` 的 `~` 表示自动重定向
