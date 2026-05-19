# 外部文档 → ViMax 视频工作流

将 PDF/文本内容转化为 ViMax 视频的完整流程。

## 1. 提取文本

```bash
# PDF 提取（使用系统 Python 的 pymupdf，不要用 uv venv 里的）
python3 -c "
import pymupdf
doc = pymupdf.open('/path/to/document.pdf')
text = ''
for page in doc:
    text += page.get_text()
print(text)
" > /tmp/extracted_text.txt
```

系统 Python 通常已安装 pymupdf。如果 uv 同步卡住，直接用系统 python3。

## 2. 将文本转化为视频 idea

短文本（<5000 字）→ 直接作为 Idea2Video 的 `idea` 输入
长文本 → 提炼核心概念作为 idea，或转为剧本格式走 Script2Video

## 3. 修改 main_idea2video.py

```python
idea = \"\"\"
[从文档中提取的核心故事梗概，200-500 字]
\"\"\"
user_requirement = \"\"\"
[风格要求、场景数、镜头数限制]
\"\"\"
style = "Realistic, cinematic warm tones, Chinese street atmosphere"
```

## 4. 运行

```bash
cd ~/ViMax
rm -rf .working_dir  # 清缓存
uv run python main_idea2video.py
```

## 注意事项

- ViMax 的 Novel2Video 标记为 `# TODO: NOT IMPLEMENTED YET`，长篇小说无法直接使用
- 替代方案：提炼核心故事为 Idea2Video 输入，或写剧本格式用 Script2Video
- 故事生成质量取决于 LLM（默认 OpenRouter gemini-2.5-flash-lite），可换更强模型
