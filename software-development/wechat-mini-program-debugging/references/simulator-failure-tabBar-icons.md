# 模拟器失败：tabBar图标路径不匹配

## 复现场景

连平鹰嘴蜜桃小程序导入微信开发者工具后，模拟器提示启动失败。

## 错误信息

```
模拟器启动失败
Error: app.json: ["tabBar"]["list"][0]['selectedIconPath']: "images/tab/home-active.png"未找到
["tabBar"]["list"][1]["selectedIconPath"]: "images/tab/category-active.png"未找到
[tabBar"]["list"][2]["selectedIconPath"]: "images/tab/cart-active.png"未找到
[tabBar"]["list"][3]["selectedIconPath"]: "images/tab/user-active.png"未找到
File: app.json
```

## 根本原因

`app.json` 中 tabBar 的 `selectedIconPath` 配置为 `.png` 扩展名，但实际文件是 `.svg` 格式：

| 配置中的路径 | 实际文件 |
|---|---|
| `images/tab/home-active.png` | `images/tab/home-active.svg` |
| `images/tab/category-active.png` | `images/tab/category-active.svg` |
| `images/tab/cart-active.png` | `images/tab/cart-active.svg` |
| `images/tab/user-active.png` | `images/tab/user-active.svg` |

注意：普通（未选中）图标 `iconPath` 确实使用 `.png` 文件（如 `images/tab/home.png` 存在），只有选中态图标是 `.svg`。

## 第一次修复尝试（失败）

将 `app.json` 中全部 4 个 `selectedIconPath` 从 `.png` 改为 `.svg`：

```diff
- "selectedIconPath": "images/tab/home-active.png"
+ "selectedIconPath": "images/tab/home-active.svg"
```

**结果：** 仍然报错。微信 tabBar **不支持 SVG 格式**，只支持 png/jpg/jpeg。

```
文件格式错误，仅支持.png、jpg、jpeg格式
```

## 最终修复：SVG → PNG 转换

使用 `cairosvg` 将 SVG 文件转换为 PNG：

```bash
pip3 install --break-system-packages cairosvg
python3 -c "
import cairosvg
cairosvg.svg2png(url='images/tab/home-active.svg', write_to='images/tab/home-active.png', output_width=48, output_height=48)
"
```

对 4 个选中态图标全部执行转换后，将 `app.json` 配置改回 `.png` 引用即可。

## 附加排查步骤（本次对话完整流程）

1. AppID 为 `wx0000000000000000`（占位符）→ 用户提供了真实 AppID `wx3027d377a9eb74c0` 并替换
2. 开发者工具自动将 `libVersion` 从 `3.7.2` 改成 `3.16.0` → 手动降回 `2.30.0`
3. 文件无法从 WSL 路径导入 → 复制到 `C:\Users\Administrator\Desktop\`
4. 最终发现并修复了 tabBar 图标路径问题

## 最终验证

修复后模拟器正常启动，小程序可预览。
