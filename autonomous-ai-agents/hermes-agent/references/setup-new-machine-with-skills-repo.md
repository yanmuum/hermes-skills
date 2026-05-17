# 在新电脑上部署 Hermes + 私有技能仓库

当用户有一台新电脑（如家里的电脑），需要安装 Hermes 并同步已积累的技能。

## 完整流程

### 1. 安装 Hermes

```bash
# 方式一：官方安装脚本（推荐）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 方式二：pip 安装
pip install hermes-agent

# 首次启动设置
hermes setup
```

### 2. 获取 GitHub Token

用户需要有一个 GitHub Personal Access Token，用于克隆私有仓库。

**Fine-grained token 所需权限：**
- Contents: **Read-only**（只需要读，不需要写）
- Repository access: 选择 **Only selected repositories** → 勾选 `hermes-skills`

或者直接用之前生成过的 old token。

### 3. 克隆私有技能仓库

```bash
# 删除默认技能目录
rm -rf ~/.hermes/skills

# 克隆私有仓库（会提示输入密码，密码填 GitHub Token）
git clone https://github.com/<用户名>/hermes-skills.git ~/.hermes/skills
```

### 4. 配置 Git 凭据持久化（可选，方便以后更新）

```bash
# 把 token 存入环境文件
echo 'GITHUB_TOKEN=你的token粘贴在这里' >> ~/.hermes/.env

# 设置 git 记住凭据
git config --global credential.helper store

# 首次拉取验证（输入一次 token 后就不需要再输了）
cd ~/.hermes/skills
git pull
```

### 5. 启动 Hermes

```bash
hermes
```

### 6. 以后同步技能更新

在公司改了技能后，跟 Hermes 说「更新仓库」，它会在公司电脑上 push 到 GitHub。在家里时：

```bash
cd ~/.hermes/skills
git pull
```

## 额外依赖（按需安装）

如果使用 `qiaomu-anything-to-notebooklm` 技能（内容分析/微信文章处理）：

```bash
cd ~/.hermes/skills/qiaomu-anything-to-notebooklm
pip3 install -r requirements.txt
pip3 install notebooklm-py
```

NotebookLM 首次登录（需要 WSLg 桌面环境）：
```bash
notebooklm doctor --fix
notebooklm login
# 在弹窗的浏览器中登录 Google 账号
# 跳转到 notebooklm.google.com 后，按 Enter 完成
```

## 注意事项

- `hermes-skills` 是私有仓库，没有 token 的人拉不了
- Token 有有效期（fine-grained token 可以设置无过期或自定义天数），过期后需要重新生成
- 新电脑上的 `~/.hermes/.env` 需要重新配置 API Key
- 如果只想拉取部分技能，可以在 `~/.hermes/skills/` 下手动删除不需要的技能目录，但更推荐保留全量
