# 组件注册未使用 + 事件处理格式切换

## 复现场景

连平鹰嘴蜜桃小程序修复 tabBar 图标和 WXML 可选链后，开发者工具代码依赖分析报：

```
组件不应存在无使用的组件: 3项
components/peach-card/peach-card.json
```

## 根本原因

`pages/index/index.json` 中注册了 `peach-card` 组件：

```json
{
  "usingComponents": {
    "peach-card": "/components/peach-card/peach-card"
  }
}
```

但 `index.wxml` 未使用 `<peach-card>` 标签——商品卡片用原生 `<view>` + 内联代码渲染。

## 修复过程

### 步骤 1：替换 WXML 模板

原代码（手动渲染）：
```html
<view class="product-card" wx:for="{{hotProducts}}" wx:key="id" bind:tap="onProductTap" data-id="{{item.id}}">
  <image class="product-img" src="{{item.cover}}" mode="aspectFill" />
  <view class="product-info">
    <text class="product-name text-ellipsis">{{item.name}}</text>
    <text class="product-spec">{{item.spec}}</text>
    <view class="product-bottom">
      <text class="product-price">¥<text class="price-num">{{item.price}}</text></text>
      <text class="product-sold">已售 {{item.soldCount}}</text>
    </view>
  </view>
</view>
```

改为组件调用：
```html
<peach-card wx:for="{{hotProducts}}" wx:key="id"
  cover="{{item.cover}}"
  name="{{item.name}}"
  spec="{{item.spec}}"
  price="{{item.price}}"
  productId="{{item.id}}"
  bind:tap="onProductTap" />
```

### 步骤 2：调整事件处理函数

**关键陷阱：** 组件内部用 `triggerEvent` 发射事件，数据在 `e.detail` 而非 `e.currentTarget.dataset`。

peach-card 组件的 JS：
```javascript
Component({
  properties: { productId: { type: String, value: '' } },
  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.properties.productId })
    }
  }
})
```

原事件处理（与 `<view>` 配合）：
```javascript
onProductTap(e) {
  const id = e.currentTarget.dataset.id  // ❌ 组件不适用
  wx.navigateTo({ url: `/pages/product/product?id=${id}` })
}
```

修正后（与组件配合）：
```javascript
onProductTap(e) {
  const id = e.detail.id  // ✅ triggerEvent 的数据在 detail 中
  wx.navigateTo({ url: `/pages/product/product?id=${id}` })
}
```

### 数据流向对比

| 场景 | 数据来源 | 示例 |
|------|---------|------|
| `<view data-id="{{id}}" bind:tap="handler">` | `e.currentTarget.dataset.id` | 原生组件 |
| `<custom bind:tap="handler">` 组件内 `triggerEvent('tap', { id })` | `e.detail.id` | 自定义组件 |

## 验证

修改后 DevTools 代码依赖分析不再警告，模拟器正常运行。
