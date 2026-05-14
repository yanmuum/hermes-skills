# 缺失本地图片资源的批量占位

## 场景

微信小程序项目从代码仓库检出后，经常缺少图片资源（默认头像、banner图、商品图、品牌故事图等）。

虽然图片缺失不会导致编译失败、模拟器崩溃，但会在控制台报错：
```
[渲染层网络层错误] Failed to load local image resource /images/default-avatar.png
the server responded with a status of 500 (HTTP/1.1 500 Internal Server Error)
```

## 常见缺失图片清单

| 路径 | 用途 |
|------|------|
| `/images/default-avatar.png` | 用户页默认头像（`user.wxml` 中的 fallback） |
| `/images/banner1.jpg` ~ `/images/banner3.jpg` | 首页轮播图 |
| `/images/peach1.jpg` ~ `/images/peach4.jpg` | 商品缩略图 |
| `/images/icon-all.png`, `icon-gift.png` 等 | 快捷导航图标 |
| `/images/promo1.jpg` | 促销活动图 |
| `/images/share-card.jpg` | 分享卡片 |
| `/images/brand-story-placeholder.jpg` | 品牌故事配图 |

## 批量生成方案

使用 Python Pillow 快速生成占位色块图：

```python
from PIL import Image
import os

BASE = "images"

PLACEHOLDERS = {
    # name: (width, height, (R, G, B))
    "banner1.jpg": (750, 300, (232, 85, 58)),     # 深橙色
    "banner2.jpg": (750, 300, (53, 163, 91)),      # 绿色
    "banner3.jpg": (750, 300, (98, 114, 194)),     # 紫色
    "icon-all.png": (80, 80, (232, 85, 58)),
    "icon-gift.png": (80, 80, (232, 85, 58)),
    "icon-source.png": (80, 80, (232, 85, 58)),
    "icon-order.png": (80, 80, (232, 85, 58)),
    "peach1.jpg": (300, 300, (255, 200, 180)),
    "promo1.jpg": (700, 200, (255, 100, 80)),
    "share-card.jpg": (500, 400, (232, 85, 58)),
    "brand-story-placeholder.jpg": (700, 300, (240, 240, 240)),
    "default-avatar.png": (48, 48, (200, 200, 200)),
}

for name, (w, h, color) in PLACEHOLDERS.items():
    img = Image.new('RGB', (w, h), color)
    path = os.path.join(BASE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if name.endswith('.png'):
        img.save(path, 'PNG')
    else:
        img.save(path, 'JPEG', quality=85)
```

## 注意点

1. **扩展名必须与格式一致** — `.jpg` 文件必须是 JPEG 格式，`.png` 文件必须是 PNG 格式。微信 DevTools 不信任扩展名，会检查实际文件头。
2. **默认头像建议 48×48** — 与微信头像展示尺寸一致，缩小内存占用。
3. **轮播图建议 750×300** — 与微信小程序页面宽度 750rpx 匹配。
