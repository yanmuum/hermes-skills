# E-Commerce Mini Program Project Architecture

> Reference: complete e-commerce Miniapp for Lianping Eagle-Beak Honey Peach (连平鹰嘴蜜桃)
> 68 files, 364KB — C-end retail + Shunfeng cold-chain delivery

## Project Structure Pattern

```
miniapp-root/
├── app.js / app.json / app.wxss       # Global config (brand theme, tabBar, pages)
├── project.config.json / sitemap.json
├── pages/
│   ├── index/          # Home (banner swiper, hot products, brand story, reviews)
│   ├── category/       # Category (LHS nav + RHS grid, search)
│   ├── product/        # Product detail (images, specs, qty, add-to-cart, buy-now)
│   ├── cart/           # Cart (select all, qty +/- , delete, checkout)
│   ├── order/          # Order confirm (address picker, remark, submit + pay)
│   ├── order-list/     # Order list (tab-switch by status)
│   ├── order-detail/   # Order detail (status banner, address, items, tracking)
│   └── user/           # Profile (avatar, stats, order nav, menu items)
├── components/
│   ├── product-card/   # Reusable product card (cover, name, spec, price, tag)
│   └── address-picker/ # Address selection (wx.chooseAddress wrapper)
├── utils/
│   ├── request.js      # Unified HTTP (token inject, 401 refresh, error toast)
│   ├── auth.js         # WeChat login flow (code → token, phone, user profile)
│   ├── payment.js      # WeChat Pay (createOrder → wx.requestPayment)
│   └── util.js         # Formatters (price, date, order status, throttle)
├── services/
│   └── api.js          # All API endpoints centralized
└── subpackages/
    ├── promotion/      # Promotions page (subpackage for size management)
    └── source-trace/   # Source tracing / brand story (subpackage)
```

## Key Patterns

### 1. Mock Data First, API Later

Every page initializes with realistic mock data so the Miniapp is immediately previewable without a backend:

```javascript
// pages/index/index.js
Page({
  data: {
    hotProducts: [
      { id: 1, name: '产品·5斤装', spec: '约15-20个', price: '68.00', cover: '/images/product1.jpg', soldCount: 1256 },
      // ... more mock items
    ],
    reviews: [
      { nickname: '张***', date: '2025-07-15', rating: 5, content: '很好吃！' },
    ]
  },
  onLoad() {
    login()                    // Silent auth
    // this.fetchProducts()    // Uncomment when backend is ready
  },
  async fetchProducts() {
    try {
      const res = await api.getHomeProducts()
      if (res?.products) this.setData({ hotProducts: res.products })
    } catch { /* keep mock */ }
  }
})
```

**Pattern:** `onLoad` calls both login (fires-and-forgets) and data fetch wrapped in try/catch. If API fails, mock data stays. When backend goes live, uncomment the fetch calls.

### 2. API Layer Centralization

All endpoints in one file (`services/api.js`):

```javascript
const api = {
  getHomeProducts: (data) => request({ url: '/products/home', data }),
  getCategories: () => request({ url: '/categories' }),
  getProductDetail: (id) => request({ url: `/products/${id}` }),
  addToCart: (data) => request({ url: '/cart/add', method: 'POST', data }),
  createOrder: (data) => request({ url: '/orders/create', method: 'POST', data }),
  getOrderList: (status, page) => request({ url: '/orders', data: { status, page, page_size: 10 } }),
  // ... all other endpoints
}
```

**Pattern:** Single source of truth for all API routes. Backend developers can see exactly what endpoints are expected.

### 3. Request Wrapper with Auth

```javascript
// utils/request.js
const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('access_token')
    wx.request({
      url: `${BASE_URL}${options.url}`,
      header: { 'Authorization': token ? `Bearer ${token}` : '', ... },
      success: (res) => {
        if (res.statusCode === 401) return refreshTokenAndRetry(options).then(resolve)
        if (res.statusCode === 200 || res.statusCode === 201) resolve(res.data)
        else reject({ code: res.statusCode, message: res.data?.message || '请求失败' })
      },
      fail: () => reject({ code: -1, message: '网络错误' })
    })
  })
}
```

**Pattern:** Token auto-injection, 401 auto-refresh with queue, unified error toast.

### 4. Cart Storage Strategy

Cart data lives in `wx.setStorageSync('cart', ...)` instead of server-side:

```javascript
onAddToCart() {
  const cart = wx.getStorageSync('cart') || []
  const existIdx = cart.findIndex(i => i.productId === id && i.specIndex === selectedSpec)
  if (existIdx > -1) {
    cart[existIdx].quantity += quantity
  } else {
    cart.push({ productId, specIndex, name, specName, price, cover, quantity })
  }
  wx.setStorageSync('cart', cart)
  getApp().setCartCount(cart.reduce((s, i) => s + i.quantity, 0))
}
```

**Pattern:** Local-first cart. On checkout, items are passed to order page via `wx.setStorageSync('checkoutItems', ...)`. After successful payment, purchased items are removed from local cart.

### 5. Brand Color System (CSS Variables)

```css
/* app.wxss */
page {
  --color-primary: #E8553A;     /* Brand red-orange */
  --color-secondary: #F5A623;   /* Brand yellow */
  --color-bg: #FFF5F0;          /* Warm background */
  --color-text: #333333;
  --color-text-light: #999999;
  --radius-lg: 24rpx;
  --shadow-sm: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
```

### 6. Subpackages for Size Management

Heavy pages (promotions with event banners, source tracing with gallery images) go in subpackages:

```json
// app.json
"subpackages": [
  { "root": "subpackages/promotion", "pages": ["index/index"] },
  { "root": "subpackages/source-trace", "pages": ["index/index"] }
]
```

### 7. Order Flow

```
Cart/Product → Order Confirm (address + items) → wx.requestPayment → 
  success → redirect to Order Detail → status: pending_ship
  cancel → stay on page, show toast
```

The order page handles both `from=cart` (bulk checkout) and `from=buy` (buy-now single item) flows:

```javascript
if (options.from === 'buy') {
  items = [wx.getStorageSync('buyNow')]
} else {
  items = wx.getStorageSync('checkoutItems') || []
}
```

## Directories Reference

| Path | Purpose |
|------|---------|
| `~/lianping-peach-mp/` | Complete reference project (68 files) |
| `scripts/generate-assets.py` | Run after `pip install Pillow` to generate placeholder tab icon PNGs |
| `README.md` | Full setup guide including WeChat DevTools import, backend API list, and review tips |
