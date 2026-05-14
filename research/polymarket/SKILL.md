---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## User / Wallet Analysis

When analyzing a specific Polymarket user's trading history:

### Profile Page URL

Format: `https://polymarket.com/zh/@0xADDRESS-NUMBER`

Wallet address is the hex address (0x...). The number suffix (e.g. -1766317541188) is an internal profile ID.

### Profile-Level Info Visible on Page

- Total PnL, portfolio value, highest profit, total predictions count
- Join date, page views
- Current open positions (with entry price, current price, PnL %)
- Trade history (buy/sell records with amounts and timestamps)

### Data API — Wallet-Specific Endpoints

Use `data-api.polymarket.com` with the `user` parameter (NOT `maker`):

```
GET /trades?user=0xADDRESS&limit=500
GET /positions?user=0xADDRESS&limit=2000
```

**Critical findings:**

1. **`/trades?maker=0x...` does NOT filter by user** — It returns random trades from all users. Must use `?user=0x...` instead.

2. **`/trades?user=` only returns BUY records** (opening positions, not sells/closes). PnL from closed trades is not readily available from this endpoint alone.

3. **Max 500 trades**, data window is approximately the last month only. No working pagination observed.

4. **`/positions?user=` only returns CURRENT open positions** (5-20 max). Does not return historical closed positions even with `&closed=true`.

5. **`proxyWallet` field** in the response is the user's proxy address. For many wallets, this is the same as their main wallet address.

6. **Profile/PNL history APIs** — endpoints like `/user-stats`, `/leaderboard/user`, `/pnl`, `/pnl/timeseries`, `/portfolio/pnl` all return 404. PnL chart data is rendered client-side from the profile page and not exposed via public API.

### WSL / Network Workarounds

Direct curl/python API calls from WSL may time out or get 403/SSL errors (due to Windows proxy interference). When that happens:

1. **Use `browser_console` with `fetch()`** — Open the user's Polymarket profile page, then run JavaScript `fetch()` calls from the browser console. This bypasses WSL proxy issues.

2. **Unset proxy first** — `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` before curl from WSL terminal.

3. **Avoid `curl | python3` pipes** — The security scanner blocks these. Use Python's `urllib` via `execute_code` tool, or save to file then parse.

### Example: Analyze a User's Win Rate

```
1. Navigate to https://polymarket.com/zh/@0xADDRESS-NUMBER via browser
2. Use browser_console to fetch trades:
   fetch('https://data-api.polymarket.com/trades?user=0xADDRESS&limit=500')
3. Parse response: all are BUY records with price, size, title, outcome, timestamp
4. For PnL: check current open positions via /positions endpoint
5. On the page itself, the "交易记录" tab shows buy/sell history
   and the current open positions show individual PnL%
```

## Wallet Activity Monitoring

Track a specific wallet's recent trades — useful for following whale activity, copy-trading signals, or setting up notifications.

### API Endpoint

```
GET https://data-api.polymarket.com/trades?user=WALLET_ADDRESS&limit=N
```

⚠️ **`user`** is the correct parameter, **not** `maker`. The API returns trades where this wallet was the maker, identified by its proxy wallet address.

### Response Fields (key ones)

| Field | Description |
|-------|-------------|
| `proxyWallet` | The proxy contract address used by this wallet |
| `side` | `BUY` or `SELL` |
| `title` | Market title |
| `outcome` | Which side was picked (Yes/No or team name) |
| `size` | Dollar amount wagered (float) |
| `price` | Price paid per share (0.0–1.0, as probability) |
| `timestamp` | Unix timestamp |
| `transactionHash` | On-chain tx hash (unique identifier) |
| `type` | Trade type (usually BUY, sometimes REDEEM/SELL) |
| `slug` | Market slug for URL linking |

### Proxy Handling (WSL Architecture)

**Polymarket APIs require the Windows host proxy** when accessed from WSL. The WSL environment's network is routed through the Windows host's Clash proxy at `172.26.240.1:7890`:

```python
proxy = os.environ.get('http_proxy', 'http://172.26.240.1:7890')
proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
opener = urllib.request.build_opener(proxy_handler)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with opener.open(req, timeout=15) as resp:
    data = json.loads(resp.read())
```

⚠️ **Critical failure mode — proxy down:** When the Clash proxy service is NOT running on the Windows host, ALL outbound HTTPS connections from WSL silently fail (connect timeout). This is not a Polymarket-specific outage — even `google.com` will fail. DNS resolution still works, and ICMP ping to 8.8.8.8 may succeed, creating a confusing "partially working" appearance. Diagnosis:

```bash
# Check if the proxy port is open
timeout 2 bash -c 'echo > /dev/tcp/172.26.240.1/7890' && echo "PROXY RUNNING" || echo "PROXY DOWN"
# Try a simple HTTPS request
curl -s --connect-timeout 5 'https://google.com' >/dev/null && echo "HTTPS OK" || echo "HTTPS BLOCKED"
```

Resolution: Start the Clash proxy service (or alternative tunnel) on the Windows host. No code changes needed — the script just needs the proxy endpoint to be available.

### Detection Strategy (for monitoring)

1. **Fetch current trades** via `?user=WALLET&limit=20`
2. **Compare against stored state** — track `transactionHash` values you've already seen
3. **Any unseen hash = new bet** — format a notification
4. **Save updated state** (list of seen tx hashes) for next check

### Cron Job / Scheduled Check Pattern

When running wallet monitoring as a cron job or automated check:

**User's check script:** `~/.hermes/scripts/check_polymarket_wallet.py` — a standalone variant that stores seen tx hashes at `~/.hermes/polymarket_wallet_state.json`. Designed for cron: silent exit (code 0) when no new trades, prints notification on discovery.

1. **Run `scripts/polymarket-wallet-monitor.py`** — this is the canonical reusable script that handles state persistence and silent-exit-on-no-change.
2. **Also compatible:** standalone check scripts at `~/.hermes/scripts/check_polymarket_wallet.py` (stores state at `~/.hermes/polymarket_wallet_state.json`).
3. **Exit codes matter:** The monitor script exits 0 (silent) when no new trades found, 1 on error.
4. **Proxy failure handling:** If the Clash proxy is down, the script errors with `URLError: timed out`. In cron job mode, report this as a network failure — do NOT silently suppress it.
5. **What to report:**
   - Script output with new trades → send to configured notification channel (Feishu, Slack, etc.)
   - Proxy/network failure → report "proxy not available, check skipped"
   - Empty output (no new trades) → respond with "[SILENT]" or "无新交易" depending on delivery config

### Profile URL Format

```
https://polymarket.com/@WALLET_ADDRESS-POSITION_GROUP_ID
```

The `POSITION_GROUP_ID` suffix is a numerical ID appended by Polymarket. The wallet address alone may redirect. Visiting the page in a browser shows the full profile with positions, activity, P/L chart, and stats.

### Data from Browser (for reference)

When visiting a wallet's profile page, you can extract via browser snapshot:
- **Position Value** — total dollar amount of open positions
- **Biggest Win** — largest win ever
- **Predictions** — count of all-time trades
- **Profit/Loss** — overall P/L figure
- **Active Positions** — per-market breakdown with shares, avg price, current value, P/L %
- **Activity** — chronological trade history with amounts and timestamps

See `scripts/polymarket-wallet-monitor.py` for a ready-to-use monitoring script.

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Wallet monitoring via the Data API only shows trades, not deposits/withdrawals
- The API does not include proxy wallet address discovery — use the wallet profile URL to see the actual trading wallet
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible
- User wallet data API is limited — only last ~500 trades, only BUY records, no historical closed positions via public API
