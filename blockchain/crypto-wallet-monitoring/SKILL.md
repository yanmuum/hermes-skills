---
name: crypto-wallet-monitoring
description: "Monitor cryptocurrency wallets for new transactions using on-chain data — fallback strategies when primary APIs are unavailable, state file management, and multi-chain support."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [blockchain, wallet, monitoring, polygon, polymarket, on-chain, cron]
    related_skills: [wsl-deployment]

---

# Crypto Wallet Monitoring

Monitor cryptocurrency wallets for new transactions. Covers primary API approaches, on-chain RPC fallbacks when APIs are blocked, state file management for tracking seen transactions, and strategies for specific blockchains (Polygon/Polygon, Ethereum, etc.).

## When to use

- User asks to check a wallet for new activity (deposits, trades, transfers)
- Running a cron job to periodically check wallet activity
- The primary API (e.g. Polymarket data API, Etherscan API) is unreachable, blocked, or rate-limited
- Need to verify wallet balances or recent transfers on-chain

## Principles

### 1. Try the primary API first, fall back to on-chain RPC

Many wallet monitoring scripts rely on project-specific APIs (Polymarket data API, Binance API, etc.). When these are unreachable:

| Failure Mode | Cause | Fallback |
|---|---|---|
| `Errno 101 Network is unreachable` | IP/subnet blocked | Use public RPC endpoint |
| `timed out` | Proxy unavailable or API slow | Use alternative RPC |
| `HTTP 403` | Rate limited / geo-blocked | Switch to on-chain analysis |
| `HTTP 429` | Too many requests | Enable request throttling |

### 2. On-chain analysis via RPC

When APIs fail, query the blockchain directly via RPC:

```
Chain: Polygon (MATIC)
Public RPCs:
  - https://rpc-mainnet.matic.quiknode.pro   (works from most networks)
  - https://polygon-rpc.com                   (may require API key)
  - https://rpc.ankr.com/polygon             (requires API key)

Chain: Ethereum
Public RPCs:
  - https://eth.llamarpc.com
  - https://rpc.ankr.com/eth
  - https://ethereum-rpc.publicnode.com
```

### 3. State file management

Track seen transactions with a JSON state file to avoid re-notifying:

```json
{
  "seen_tx_hashes": [
    "0xabc...",
    "0xdef..."
  ]
}
```

- Store at `~/.hermes/<project>_wallet_state.json`
- Insert new txs at the front (newest first)
- Keep a bounded list (e.g. last 50-100 hashes)

### 4. Determine relevant tokens

Research which tokens the wallet might transact in:

| Platform | Token | Contract (Polygon) | Decimals |
|---|---|---|---|
| Polymarket | pUSD (Polymarket USD) | `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` | 6 |
| USDC (Circle) | USDC | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` | 6 |
| USDC.e (Bridged) | USDC.e | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` | 6 |

## Workflow: Check wallet for new transactions

### Step 1: Try the primary API

For cron jobs, wrap the primary API call with a try/except so network failures produce a clean silent exit (no traceback, no false notifications):

```python
import urllib.request, json

WALLET = "0x..."
url = f"https://data-api.polymarket.com/trades?user={WALLET}&limit=20"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        trades = json.loads(resp.read())
except Exception:
    # Network failure — silent exit (cron-friendly)
    # Do NOT print the error; that might trigger a false notification
    sys.exit(0)

# If here, trades were fetched — proceed with Step 3
```

If the API is expected to fail transiently (proxy issues, IP blocks), add the on-chain fallback from Step 2 before the silent exit instead.

### Step 2: On-chain fallback via RPC

```python
import json, urllib.request, ssl

WALLET = "0x..."
RPC = "https://rpc-mainnet.matic.quiknode.pro"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def rpc(method, params, timeout=10):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(RPC, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read())

# 1. Check nonce for outgoing transactions
resp = rpc("eth_getTransactionCount", [WALLET, "latest"])
nonce = int(resp["result"], 16)
print(f"Outgoing txs: {nonce}")

# 2. Check balance of specific tokens
# pUSD token contract
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
balance_of_data = "0x70a08231" + "000000000000000000000000" + WALLET[2:].lower()
resp = rpc("eth_call", [{"to": PUSD, "data": balance_of_data}, "latest"])
pusd_balance = int(resp["result"], 16) / 1e6
print(f"pUSD balance: ${pusd_balance:,.2f}")

# 3. Check recent Transfer events
# Transfer event: Transfer(address indexed from, address indexed to, uint256 value)
transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Incoming transfers (to wallet)
params = {
    "fromBlock": hex(latest_block - 500),
    "toBlock": "latest",
    "topics": [
        transfer_sig,
        None,
        "0x000000000000000000000000" + WALLET[2:].lower(),
    ]
}
resp = rpc("eth_getLogs", [params], timeout=20)
logs = resp.get("result", [])

# Filter for new transactions not in state file
state_file = os.path.expanduser("~/.hermes/polymarket_wallet_state.json")
with open(state_file) as f:
    state = json.load(f)
seen = set(state["seen_tx_hashes"])

new_txs = []
for log in logs:
    tx = log['transactionHash']
    if tx not in seen:
        from_addr = "0x" + log['topics'][1][26:]
        amount = int(log['data'], 16) / 1e6  # 6 decimals for USDC/pUSD
        new_txs.append({
            'tx': tx,
            'from': from_addr,
            'amount': amount,
            'block': int(log['blockNumber'], 16),
            'contract': log['address']
        })
```

### Step 3: Update state and report

```python
# Add new transactions to state
all_tx = seen | {t['tx'] for t in new_txs}
state["seen_tx_hashes"] = list(all_tx)[:50]  # Keep last 50
with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)
```

## RPC Endpoint Notes

### QuickNode (free tier)
- Endpoint: `https://rpc-mainnet.matic.quiknode.pro`
- Rate limits: ~100 req/s on free tier
- Queries that work: `eth_blockNumber`, `eth_getTransactionCount`, `eth_getBalance`, `eth_call`, `eth_getLogs` (small ranges)
- Queries that may timeout: `eth_getLogs` with large ranges (>10000 blocks), `eth_getBlockByNumber` with full transaction objects on large blocks

### Avoiding timeouts
- Scan blocks in small chunks (500-5000 blocks at a time)
- Use short timeouts and retry with smaller ranges
- For `eth_getLogs`: filter by contract address AND topics to reduce data volume
- Prefer `eth_call` for single-address balance queries over `eth_getLogs`

## Token Identification

When you find a new transaction but don't know the token:

```python
contract = "0x..."
name_data = "0x06fdde03"       # name() selector
symbol_data = "0x95d89b41"     # symbol() selector
decimals_data = "0x313ce567"   # decimals() selector

resp = rpc("eth_call", [{"to": contract, "data": name_data}, "latest"])
resp = rpc("eth_call", [{"to": contract, "data": symbol_data}, "latest"])
resp = rpc("eth_call", [{"to": contract, "data": decimals_data}, "latest"])
```

## Pitfalls

### ❌ WSL proxy / networking issues

When running from WSL, proxy env vars (`http_proxy`, `all_proxy`) block direct RPC connections, and IPv6 routes may be unreachable. See the **`wsl-deployment`** skill for comprehensive WSL proxy management, including:
- Unsetting proxy vars before RPC calls
- IPv4-only socket workaround for cron jobs
- Proxy liveness checking
- Conditional proxy aliases (`proxy-on`/`proxy-off`)

### ❌ eth_getLogs with wildcard addresses is slow
Scanning ALL contracts for a wallet address is extremely heavy. Always specify the relevant token contract address when possible.

### ❌ Block range too large causes timeout
Querying `eth_getLogs` across 100K+ blocks will timeout. Use ranges of 500-5000 blocks and iterate.

### ❌ Token decimals vary
Not all tokens use 6 decimals. Always check `decimals()` — USDC/pUSD use 6, standard ERC20 uses 18.

### ❌ Nonce only tracks outgoing transactions
If the wallet only received funds, nonce stays 0 or low. Check `eth_getLogs` for incoming transfers.

### ❌ Some RPCs require API keys
`polygon-rpc.com` requires auth, `rpc.ankr.com/polygon` requires API key, `rpc-mainnet.matic.quiknode.pro` works without auth.

## Verification checklist

- [ ] Wallet address is valid and checksummed
- [ ] RPC endpoint is reachable (test with `eth_blockNumber`)
- [ ] Correct token contract(s) targeted
- [ ] Block range is within timeout budget (<5000 blocks per query)
- [ ] State file updated with new transaction hashes
- [ ] Timestamps checked to avoid reporting old transactions as new
