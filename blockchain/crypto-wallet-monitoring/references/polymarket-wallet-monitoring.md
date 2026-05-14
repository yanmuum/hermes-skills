# Polymarket Wallet Monitoring — Session Notes

## Wallet

`0x492442eab586f242b53bda933fd5de859c8a3782`

## State File

`~/.hermes/polymarket_wallet_state.json`

Format:
```json
{
  "seen_tx_hashes": ["0x...", "0x..."]
}
```

## Known Issues

### Issue 1: Polymarket Data API Unreachable

The primary endpoint `https://data-api.polymarket.com/trades?user={WALLET}` returns `Errno 101: Network is unreachable` from this WSL environment. The proxy `http://172.26.240.1:7890` (hardcoded in the script) also times out.

Meta IP range: `31.13.90.33`, `173.252.88.133` (both timeout from this network).

Its sibling `https://clob.polymarket.com/` has the same issue.

### Issue 2: Windows proxy not running

The proxy on the Windows host (`172.26.240.1:7890`) was found closed:

```
Port 7890 CLOSED (err: 11)
```

No proxy env vars are set (`http_proxy`, `https_proxy`, etc. are all unset). The hardcoded value in the script is the only reference to this proxy, but it isn't running.

## Working Fallback: QuickNode Polygon RPC

`https://rpc-mainnet.matic.quiknode.pro` works without authentication.

## pUSD Token (Polymarket USD)

- **Contract**: `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`
- **Name**: Polymarket USD
- **Symbol**: pUSD
- **Decimals**: 6
- **Chain**: Polygon (MATIC)

All Polymarket wallet trades/payouts use pUSD.

## Transactions Discovered (Historical)

### 2026-05-09: 1.00 pUSD Incoming

- Tx: `0x4878b3edd1ee362789b41080ee9e1d6e6c6ab067c262502c6c355a569ccbb91f`
- Block: 86,591,269
- Timestamp: 2026-05-09 05:07:09 UTC
- From: `0x8b8f19c699c4cb7d37e5de59db80febfed7dc01d`
- Amount: 1.00 pUSD

### 2026-05-11: 0.50 pUSD Incoming

- Tx: `0x621a0c7ec4721824d962ccc4449a6564d674e1b48a99b4988c556f0d1d009730`
- Block: 86,687,665
- From: `0x8b8f19c699c4cb7d37e5de59db80febfed7dc01d`
- Amount: 0.50 pUSD

## Wallet Status (Current)

As of block 86,716,177 (2026-05-11):

| Metric | Value |
|--------|-------|
| Nonce | 1 (only 1 outgoing tx ever) |
| MATIC balance | 0 |
| pUSD balance | $0.00 |
| USDC (Circle) | 0.00 |
| USDC.e (Bridged) | 0.00 |
| Last activity | 2026-05-09 |
| Recent transfers (5000 blocks) | 0 incoming, 0 outgoing |
| Recent CTF orders | 0 |

The wallet is effectively dormant — no recent Polymarket activity, no token balances.

## Script Patches Applied (2026-05-11)

### Patch 1: Force IPv4

Added `socket.getaddrinfo` monkey-patch to force IPv4 resolution, avoiding IPv6 "Network is unreachable" timeouts.

### Patch 2: Increased timeout

Changed from 15s to 20s to account for slower proxy/proxy-less paths.

### Patch 3: Graceful network error handling

Wrapped `fetch_trades()` in try/except — on network failure, `sys.exit(0)` instead of printing a traceback. Prevents cron from producing a false-positive notification.

```python
def main():
    ...
    try:
        trades = fetch_trades()
    except Exception:
        # Network unavailable — exit silently, no delivery
        sys.exit(0)
    ...
```

## Future Improvements

1. Add fallback to `eth_getLogs` via QuickNode RPC scanning `Transfer` events from pUSD contract
2. Add block number tracking to state file to know where to start scanning next time
3. Make proxy configurable via env vars (already done via `os.environ.get('http_proxy', 'default')` pattern)
4. Remove hardcoded IPv6-only DNS resolution assumption
