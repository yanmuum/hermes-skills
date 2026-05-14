# Agricultural & Seasonal Produce Miniapp Patterns

> Domain knowledge for building WeChat Mini Programs that sell agricultural products (农产品/生鲜).
> Based on the 连平鹰嘴蜜桃 project — a real 68-file production Miniapp.

## 1. Seasonal Availability Pattern

Agricultural products are seasonal. The Miniapp must handle:

```javascript
// Check if product is in season
const isInSeason = (seasonStart, seasonEnd) => {
  const now = new Date()
  const start = new Date(seasonStart)
  const end = new Date(seasonEnd)
  return now >= start && now <= end
}
```

**Pre-sale (预售) flow:**
- Before season opens: show countdown + deposit button
- During season: show "现摘现发" (freshly picked) + real-time stock
- After season: show "已售罄，明年见" + subscribe button for next year notification

**Page pattern:** Product detail page should show a seasonal banner:
```
┌─────────────────────────────┐
│  📅  7月新鲜上市 · 预售中   │
│      距上市还有 15天        │
│   [ 预付订金 ¥10 ]          │
└─────────────────────────────┘
```

## 2. Cold-Chain Shipping Display

Shipping information must be prominent at every stage:

| Stage | Where to display |
|-------|------------------|
| Product detail | Below price: "🚚 顺丰冷链 · 满88包邮" |
| Cart | Before checkout: "冷链配送，保持新鲜" |
| Order | Shipping method shown in order summary |
| Tracking | Express company name + tracking number |

## 3. Geographical Indication (地理标志)

Certification display pattern:

```wxml
<view class="cert-badges">
  <view wx:for="{{product.certifications}}" wx:key="name" class="cert-item">
    <text class="cert-icon">{{item.icon}}</text>
    <text class="cert-name">{{item.name}}</text>
  </view>
</view>
```

Common Chinese agricultural certifications:
- 国家地理标志保护产品 (National Geographical Indication)
- 绿色食品认证 (Green Food Certification)
- 有机产品认证 (Organic Certification)
- 无公害农产品 (Pollution-free Agricultural Product)
- SC食品生产许可证 (Food Production License)

## 4. Source Tracing Page (产地溯源)

Dedicated subpackage page showing:

```
┌─ 产地溯源 ──────────────────┐
│  🌄 [hero image of orchard] │
│                             │
│  连平 · 中国鹰嘴蜜桃之乡     │
│  广东省河源市连平县上坪镇     │
│                             │
│  🌱 种植过程                  │
│  ✓ 三月开花 — 自然授粉       │
│  ✓ 五月套袋 — 无农药残留     │
│  ✓ 七月采摘 — 清晨手工采摘   │
│  ✓ 冷链直达 — 48小时送达     │
│                             │
│  🏆 资质认证                  │
│  国家地理标志 · 绿色食品认证  │
│  食用农产品合格证             │
└──────────────────────────────┘
```

## 5. Multi-Spec Pricing

Agricultural products typically have 3-4 spec lines:

| Spec | Price | Target |
|------|-------|--------|
| 5斤家庭装 | ¥68 | Individual consumers |
| 10斤实惠装 | ¥118 | Families / bulk buyers |
| 12枚精品礼盒 | ¥168 | Gift buyers |

Each spec needs separate stock tracking. The product detail page should show specs as selectable option cards:

```wxml
<view class="spec-option {{selectedSpec === index ? 'active' : ''}}"
      wx:for="{{product.specs}}" wx:for-index="index">
  <text>{{item.name}}</text>
  <text class="spec-price">¥{{item.price}}</text>
</view>
```

## 6. Food Compliance for WeChat Review

When submitting an agricultural product Miniapp for WeChat review:

| Requirement | Details |
|-------------|---------|
| 《食品经营许可证》 | Must be uploaded to WeChat backend before submission |
| Privacy policy | Must cover food safety claims, quality guarantees, and return policies |
| Product descriptions | Cannot make unsubstantiated health claims |
| Pre-sale deposits | Must clearly state delivery timeline on product page |
| Price claims | "原价" requires 7-day historical transaction records |
| Image materials | All product images must be original or properly licensed |

## 7. Common Agricultural Miniapp Pages

Minimal set for an agricultural product Miniapp (8 pages + 2 subpackages):

| Page | Purpose | Mock data |
|------|---------|-----------|
| index | Banner + hot products + brand story + reviews | 3 banners, 4 products, 3 reviews |
| category | Category nav + product grid | 5 categories |
| product | Images + specs + qty + cart/pay | 3 spec lines, 5 images |
| cart | Select + qty + checkout | Empty state + populated |
| order | Address + items + remark + pay | wx.chooseAddress |
| order-list | Status tabs + order cards | 5 status tabs |
| order-detail | Status banner + items + tracking | Timeline |
| user | Avatar + stats + order nav | Login + menu |
| promotion (subpackage) | Discount events | 3 promo cards |
| source-trace (subpackage) | Orchard story + process + certs | 4 steps, 4 gallery images |

## 8. API Layer for Agricultural Products

Key endpoints beyond standard e-commerce:

```javascript
// Seasonal
getSeasonStatus: (productId) => request({ url: `/products/${productId}/season` }),
getPreSaleInfo: (productId) => request({ url: `/products/${productId}/presale` }),

// Source tracing
getSourceTrace: (productId) => request({ url: `/source-trace/${productId}` }),
getCertifications: (productId) => request({ url: `/products/${productId}/certs` }),

// Shipping
getShippingEstimate: (addressId, productIds) => request({ url: '/shipping/estimate', method: 'POST' }),
getExpressTracking: (orderId) => request({ url: `/orders/${orderId}/tracking` }),

// Quality assurance
submitQualityClaim: (orderId, data) => request({ url: `/orders/${orderId}/claim`, method: 'POST', data }),
```

## Reference Project

The complete reference implementation lives at:
```
~/lianping-peach-mp/
```
68 files, 364KB. See `references/e-commerce-project-architecture.md` for the full project structure and patterns.
