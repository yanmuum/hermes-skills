# WXML 可选链（`?.`）不支持问题

## 复现场景

连平鹰嘴蜜桃小程序在修复 tabBar 图标后，再次遇到模拟器编译失败。错误信息指向 `pages/category/category.wxml` 第 19 行。

## 错误信息

```
File:/pagBad value with
...
<view class="category-title">>19{(categories[activeIndex]?. namel}</view>
编译.wxml文件错误
```

## 根本原因

**微信 WXML 模板不支持可选链 `?.` 运算符。** WXML 使用受限表达式引擎，仅支持：

- 属性访问：`item.name`
- 索引访问：`arr[0]`
- 比较运算：`===`、`!==`、`>`、`<` 等
- 逻辑运算：`&&`、`||`、`!`
- 三元表达式：`a ? b : c`
- 算术运算：`+`、`-`、`*`、`/`

**不支持：** `?.`、`??`、`...`、`=>`、模板字符串、`?.()`、`[]` 等现代 JS 语法。

## 影响范围

本次对话中在 3 个文件发现共 6 处：

| 文件 | 行号 | 原代码 | 修复后 |
|------|------|--------|--------|
| `pages/category/category.wxml` | 19 | `{{categories[activeIndex]?.name}}` | `{{categories[activeIndex].name}}` |
| `pages/order-detail/order-detail.wxml` | 16 | `{{order.address?.name \|\| '收货人'}}` | `{{order.address.name \|\| '收货人'}}` |
| `pages/order-detail/order-detail.wxml` | 17 | `{{order.address?.phone}}` | `{{order.address.phone}}` |
| `pages/order-detail/order-detail.wxml` | 19 | `{{order.address?.fullAddress}}` | `{{order.address.fullAddress}}` |
| `pages/order-list/order-list.wxml` | 19 | `{{item.items[0]?.cover \|\| ''}}` | `{{item.items[0].cover \|\| ''}}` |
| `pages/order-list/order-list.wxml` | 21 | `{{item.items[0]?.name}}` | `{{item.items[0].name}}` |

## 修复方案

### 方案 A：直接去掉 `?.`（推荐）

```diff
- {{item?.name}}
+ {{item.name}}
```

**为什么安全：** WXML 对 `undefined` 属性访问会静默渲染为空字符串，不会崩溃。如果担心显示异常，配合 `||` 兜底：

```
{{item.name || '默认值'}}
```

### 方案 B：在 JS 中预处理

```javascript
// Page JS
data: {
  safeItem: item?.name || '默认名'
}
```

然后在 WXML 中使用已处理好的值。

### 方案 C：使用 wx:if 守卫

```xml
<view wx:if="{{item}}">{{item.name}}</view>
```

## 预防措施

- 新建小程序项目后，用 `grep -rn '\?\.' pages/ components/ subpackages/ --include="*.wxml"` 全局搜索
- 对从现代 JS 项目迁移来的代码尤其需要检查
- 使用 VS Code 的 wechat-pages 插件可在保存时提示语法错误
