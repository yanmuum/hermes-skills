---
name: wechat-mini-program-debugging
description: 微信小程序开发调试 — 模拟器故障排查、WSL路径处理、project.config.json/ app.json常见错误修复
tags: [wechat, miniprogram, debug, 小程序, 模拟器]
related_skills: [wsl-deployment, engineering-wechat-mini-program-developer]
---

# 微信小程序调试技能

针对微信开发者工具（WeChat DevTools）中模拟器启动失败、编译报错等常见问题的系统化排查方案。

## 触发器

当用户反馈以下问题时加载本技能：
- 模拟器启动失败 / 模拟器白屏
- 开发者工具编译报错
- 导入项目后无法预览
- WSL路径无法在开发者工具中找到

## 工作流

### 1. 首轮排查：检查 `project.config.json`

```json
{
  "appid": "wx...",          // 必须是真实AppID或"测试号"
  "compileType": "miniprogram",
  "libVersion": "2.30.0"     // 不要开太高，3.x系列可能不兼容旧版DevTools
}
```

**常见问题：**
- AppID 为 `wx0000000000000000`（占位符）→ 要么改成真实AppID，要么重新导入选"测试号"
- `libVersion` 太高（如3.16.0）→ 降级到 `2.30.0` 或 `3.0.0`

### 2. 第二轮排查：检查 `app.json` tabBar图标路径

模拟器失败最常见的原因是 **tabBar图标文件缺失**，报错格式：

```
["tabBar"]["list"][0]['selectedIconPath']: "images/tab/home-active.png"未找到
```

**排查步骤：**
1. 列出 `images/tab/` 目录下的实际文件
2. 对比 `app.json` 中 tabBar 配置的 `iconPath` 和 `selectedIconPath`
3. 检查是否存在文件扩展名不匹配（如配置写 `.png` 但实际文件是 `.svg`）

**陷阱：SVG 格式不被支持**

即使把配置从 `.png` 改成 `.svg`，依然会报错：

```
文件格式错误，仅支持.png、jpg、jpeg格式
```

微信 tabBar 的 `iconPath` 和 `selectedIconPath` **均不支持 SVG 格式**，只支持点阵图格式。

**修复：**

方案 A（推荐）：用 `cairosvg` 将 SVG 转为 PNG：
```bash
pip3 install --break-system-packages cairosvg
python3 -c "import cairosvg; cairosvg.svg2png(url='input.svg', write_to='output.png', output_width=48, output_height=48)"
```

方案 B（应急）：直接复制现有的非选中态 `.png` 文件作为选中态图标（颜色一样，功能正常）：
```bash
cp images/tab/home.png images/tab/home-active.png
```

**注意：** 转换后的 PNG 尺寸建议 48×48 像素，微信 tabBar 图标推荐此尺寸。

### 3. 第三轮：WXML 模板语法检查

微信 WXML 模板使用的是**受限的表达式语法**，不支持现代 JS 运算符。

**不支持的特性（常见坑）：**
- ❌ 可选链 `?.`（如 `{{item?.name}}`）
- ❌ 展开运算符 `...` 
- ❌ 箭头函数 `=>`
- ❌ 模板字符串 `` `${var}` ``

其中 **可选链 `?.`** 是最常见的错误来源，报错示例：
```
Bad value with ... at files://pages/category/category.wxml#19
```

**修复方法：**
1. 搜索所有 `.wxml` 文件中的 `?.` 模式
```bash
grep -rn '\?\.' pages/ components/ subpackages/
```
2. 将 `{{item?.name}}` 替换为 `{{item.name}}`（WXML 对未定义属性会静默渲染为空）
3. 如果需安全守卫，在 JS 中预处理数据，或在 WXML 中用 `wx:if` 包裹

**实战案例（连平鹰嘴蜜桃小程序）：**
- `pages/category/category.wxml` 第19行：`{{categories[activeIndex]?.name}}` → `{{categories[activeIndex].name}}`
- `pages/order-detail/order-detail.wxml` 第16/17/19行：3处 `order.address?.xxx`
- `pages/order-list/order-list.wxml` 第19/21行：2处 `item.items[0]?.xxx`

共发现 6 处，涉及 3 个文件。

### 4. 第四轮：组件注册但未在模板中使用

模拟器编译通过，但开发者工具报「不应存在无使用的组件」警告（代码依赖分析）：

```
组件不应存在无使用的组件: 3项
components/peach-card/peach-card.json
```

**原因：** 页面 JSON 中 `usingComponents` 注册了组件（如 `"peach-card": "/components/peach-card/peach-card"`），但 WXML 模板中未使用 `<peach-card>` 标签，而是用原生 `<view>` 替代。

**排查：**
```bash
# 查出哪些页面/WXML 引用了该组件标签
grep -rn '<peach-card' pages/ components/ subpackages/ --include='*.wxml'

# 对比 page.json 中注册的组件 vs WXML 中实际使用的组件标签
```

**修复：** 在 WXML 中用组件标签替换手写代码：
```xml
<!-- ❌ 手写代码（不使用组件） -->
<view class="product-card" wx:for="{{hotProducts}}" wx:key="id" bind:tap="onProductTap" data-id="{{item.id}}">
  ...
</view>

<!-- ✅ 使用组件（修正后） -->
<peach-card wx:for="{{hotProducts}}" wx:key="id"
  cover="{{item.cover}}"
  name="{{item.name}}"
  ...
  bind:tap="onProductTap" />
```

**⚠️ 事件处理格式陷阱：** 从手动 `<view>` 切换到自定义组件后，事件参数的获取方式发生变化：

| 原来（view） | 改用组件后 |
|---|---|
| `e.currentTarget.dataset.id` | `e.detail.id`（因为组件通过 `triggerEvent('tap', { id })` 发射事件） |

**原因：** 自定义组件内部用 `triggerEvent` 发射自定义事件，数据在 `e.detail` 中，而不是 `e.currentTarget.dataset`。

### 5. 第五轮：缺失本地图片资源

图片缺失不会直接导致模拟器启动失败，但会在控制台报错：
```
[渲染层网络层错误] Failed to load local image resource /images/default-avatar.png 
the server responded with a status of 500
```

**常见缺失图片：**
- 默认头像 `default-avatar.png`（用户页面 Fallback）
- 轮播图 `banner1.jpg`、`banner2.jpg` 等
- 商品图 `peach1.jpg` 等
- 快速入口图标 `icon-all.png` 等

**修复：** 用 Pillow 批量生成占位图：
```python
from PIL import Image
import os

placeholders = {
    "banner1.jpg": (750, 300, (232, 85, 58)),
    "default-avatar.png": (48, 48, (200, 200, 200)),
}

base = "images"
for name, (w, h, color) in placeholders.items():
    img = Image.new('RGB', (w, h), color)
    path = os.path.join(base, name)
    if name.endswith('.png'):
        img.save(path, 'PNG')
    else:
        img.save(path, 'JPEG', quality=85)
```

> 注：图片缺失不影响模拟器基本功能，但会影响视觉预览和用户体验。

### 6. 第六轮：其他可能原因

- **缓存问题**：在开发者工具中「设置」→「清除缓存」→「全部清除」
- **网络问题**：基础库需要联网下载，检查网络代理
- **AppID未注册**：确认已到 mp.weixin.qq.com 注册小程序
- **项目路径问题**：从 WSL（`\\wsl$`）路径导入的，需先复制到 Windows 桌面再导入

### 7. WSL路径处理

微信开发者工具的原生文件选择弹窗不支持 `\\wsl$` 网络路径。

**必须操作：**
```
cp -r ~/project-name /mnt/c/Users/<用户名>/Desktop/
```

然后从桌面 `C:\Users\<用户名>\Desktop\project-name` 导入。

> **提示：** 关于 WSL ↔ Windows 文件桥接的更多场景（symbolic link junction、防火墙端口转发、WSL 网络代理管理），请参考 `wsl-deployment` 技能，其中包含完整的 WSL 网络和文件访问模式。

### 8. 验证步骤

修复后：
1. 菜单 → 「项目」→「关闭当前项目」
2. 重新打开项目
3. 或直接 Ctrl+R 刷新模拟器

## 注意事项

- 修改 `project.config.json` 或 `app.json` 后不需要重启工具，保存后刷新即可
- 开发者工具会自动修改 `project.config.json`（如 libVersion、editorSetting 等），这是正常行为
- 用测试号（测试号）导入可绕过 AppID 相关的问题
- 部分组件引用缺失也会导致模拟器初始化失败（检查页面 JSON 中的 usingComponents 路径）

## 关联参考文件

- `references/simulator-failure-tabBar-icons.md` — tabBar 图标 SVG/PNG 格式问题的完整排查记录
- `references/wxml-optional-chaining.md` — WXML 模板不支持可选链 `?.` 的排查与修复
- `references/component-unused-and-event-handler.md` — 组件注册但未在 WXML 中使用 + 事件处理 `dataset`→`detail` 切换
- `references/placeholder-images.md` — 用 Pillow 批量生成缺失的本地图片占位
