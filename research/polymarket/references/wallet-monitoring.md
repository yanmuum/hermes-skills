# Polymarket Wallet Monitoring — API Reference

## Data API — Wallet Trades

```
GET https://data-api.polymarket.com/trades?user=WALLET_ADDRESS&limit=N
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user` | hex address | yes | Wallet address (not proxy wallet) |
| `limit` | int | no | Max results (default ~100) |

⚠️ Use **`user`**, not `maker`. Despite the response field being `proxyWallet`, the filter parameter is `user`.

## Quick Examples

```bash
# Latest 5 trades from a wallet (with proxy)
curl -s --proxy http://172.26.240.1:7890 \
  "https://data-api.polymarket.com/trades?user=0x492442...&limit=5"

# Extract just trade summaries
curl -s --proxy http://172.26.240.1:7890 \
  "https://data-api.polymarket.com/trades?user=0x492442...&limit=5" \
  | python3 -c "
import json,sys
for t in json.load(sys.stdin):
    print(f\"{t.get('title','?')} | {t.get('outcome','?')} | \${float(t.get('size',0)):>8,.2f}\")
  "
```

## Response Schema

Array of trade objects:

```json
[
  {
    "proxyWallet": "0x4c29a0d9c4759f7e4a3a816db61f994e97f3bb8e",
    "side": "BUY",
    "asset": "89948458598034204604526438302904057960032648640538202800811767246988018853399",
    "conditionId": "0xd343b2f246e33cfc1acfe4812958e4f19486dcb74e82889ba585408d06470ff1",
    "size": 27.027026,
    "price": 0.36999997705999915,
    "timestamp": 1778324504,
    "title": "Spurs vs. Timberwolves",
    "slug": "nba-sas-min-2026-05-10",
    "outcome": "Timberwolves",
    "outcomeIndex": 1,
    "transactionHash": "0xac3787e86986c70839537af9145fa9114a7aeba1972a45a01be66567b36737d1",
    "type": "BUY"
  }
]
```

## Wallet Profile (Browser Only)

The full wallet profile page at `https://polymarket.com/@WALLET_ADDRESS-POSITION_GROUP_ID`
contains additional data not available through the public API:
- Open position value, biggest win, total predictions
- P/L chart data
- Full position list with average price, current value, unrealized P/L
- Redeem/settlement history

## Monitoring State File Format

The companion script `scripts/polymarket-wallet-monitor.py` stores state as JSON:

```json
{
  "seen_tx": [
    "0xac3787e86986c70839537af9145fa9114a7aeba1972a45a01be66567b36737d1",
    "0x0d6923a1073a94535ba35239c6c8876b32e2cecad58d67b2c99265609e0c7926"
  ]
}
```

Stored in `~/.hermes/polymarket_state/<first8chars>.json` by default.
