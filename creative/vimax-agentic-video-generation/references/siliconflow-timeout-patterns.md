# SiliconFlow Timeout Issues in ViMax Pipeline

## 现象

使用 `Qwen/Qwen3-VL-32B-Instruct` (via `api.siliconflow.cn/v1`) 作为 chat model 时，
pipeline 在以下环节频繁出现 `TimeoutError()`，每次重试后可能成功也可能继续超时。

## 实测数据（2026-05-19）

- **Story dev**: ✅ 偶有重试，最终成功（~30s）
- **Character portraits**: ✅ 通过云舞 API 生成，成功
- **Script writing**: ✅ 偶有重试，成功
- **Storyboard**: 1 次重试后成功
- **Shot decomposition (14 shots)**: 约 50% 的 shot 需要重试 1-2 次，最终全部成功（~10 分钟）
- **Construct camera tree / Reference image selector**: ❌ 卡死——连续超时，不再写出新文件

## 判断卡死的方法

```bash
# 在 pipeline 运行中定期检查
find .working_dir -name "*.json" -o -name "*.png" | while read f; do
    age=$(($(date +%s) - $(stat -c %Y "$f")))
    echo "$f: ${age}s ago"
done | sort -t: -k2 -rn | head -20
```

如果所有文件的最后修改时间都超过 5 分钟，而进程仍在运行（`ps aux | grep python` 显示 0.4-1% CPU），
说明 pipeline 卡死在某次 API 调用上，应当杀掉重试。

## 根本原因

SiliconFlow 的 Qwen3-VL-32B-Instruct 在长上下文（camera tree 需要处理 14 个 shot 的完整描述）
和多模态（reference image selector 需要带图调用）场景下表现不稳定。

## 推荐替代

| 替代方案 | 配置 | 说明 |
|---------|------|------|
| 月之暗面 Kimi 官方 | `base_url: https://api.moonshot.cn`, `model: moonshot-v1-auto` | 国产多模态，免费额度，稳定性好 |
| 跳过多模态（Patch） | `scripts/patch-skip-multimodal.sh` | 修改源代码，避坑永久解法 |
| 换轻量模型 | `Qwen/Qwen3-VL-8B-Instruct` | 纯文本更快但多模态照卡 |

## Patch 方案：跳过多模态参考图选择

**原理**：`agents/reference_image_selector.py` 的第二步将 PNG 图片 base64 编码发给 chat model 做多模态分析，
在 SiliconFlow 上这一步极不稳定（Qwen3-VL-32B/8B 皆如此）。patch 后直接使用第一步（纯文本）
的筛选结果，跳过图片传输环节。

**效果**：参考图选择精度略有下降（不再看实际画面），但 pipeline 不再卡死在 Step 7。

**应用方法**：
```bash
bash ~/.hermes/skills/creative/vimax-agentic-video-generation/scripts/patch-skip-multimodal.sh
```

**恢复方法**：
```bash
cd ~/ViMax && git checkout agents/reference_image_selector.py
```

## Session 实测日志 (2026-05-19)

### Run 1: Qwen3-VL-32B-Instruct (SiliconFlow)
- ✅ Story → Characters → Portraits → Script → Storyboard → Shot Decomp (14 shots)
- ❌ 卡死在 camera tree / reference image selector（连续 TimeoutError, 10min+ 无文件输出）
- 2000s uptime, 0.4% CPU, 进程存活但不产生新文件

### Run 2: Qwen3-VL-8B-Instruct (SiliconFlow)
- ✅ 5 shots (更少的镜头数, 不同seed的故事: 林浩/李哥/小芳)
- ✅ Camera tree 生成成功
- ❌ 卡死在 reference image selector 多模态阶段（同 Run 1）

### Run 3: Qwen3-VL-8B-Instruct + 多模态 Patch
- 🏗️ 正在运行中...

## 模型降级经验

| Model | 文本任务 | 多模态 | 备注 |
|-------|---------|--------|------|
| Qwen3-VL-32B-Instruct | 慢但稳 | ❌ 频繁超时 | 默认配置 |
| Qwen3-VL-8B-Instruct | 较快 | ❌ 同样超时 | 推荐降级 |
| Qwen3-VL-30B-A3B-Instruct | 未测试 | 未测试 | MoE 3B 活跃参数 |

## 配置示例（Kimi）

```yaml
chat_model:
  init_args:
    model: moonshot-v1-auto
    model_provider: openai
    api_key: <MOONSHOT_API_KEY>
    base_url: https://api.moonshot.cn/v1
  max_requests_per_minute: 500
  max_requests_per_day: 2000
```
