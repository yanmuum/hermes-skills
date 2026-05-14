#!/usr/bin/env python3
"""
Polymarket Wallet Activity Monitor

Polls the Polymarket Data API for new trades from a target wallet.
Detects unseen trades by tracking transaction hashes.
Silent exit if nothing new; prints notification on discovery.

Usage:
    python3 polymarket-wallet-monitor.py                          # uses default wallet
    python3 polymarket-wallet-monitor.py 0xABC...                 # custom wallet
    python3 polymarket-wallet-monitor.py 0xABC... --state /path   # custom state file
"""

import json, os, sys, urllib.request
from datetime import datetime

DEFAULT_WALLET = "0x492442eab586f242b53bda933fd5de859c8a3782"
STATE_DIR = os.path.expanduser("~/.hermes/polymarket_state")


def resolve_wallet():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        return sys.argv[1]
    return DEFAULT_WALLET


def state_path(wallet):
    for arg in sys.argv:
        if arg.startswith('--state='):
            return arg.split('=', 1)[1]
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, f"{wallet[:8]}.json")


def load_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"seen_tx": []}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(state, f)


def fetch_trades(wallet, limit=20):
    proxy = os.environ.get('http_proxy', os.environ.get('HTTP_PROXY',
                           'http://172.26.240.1:7890'))
    url = f"https://data-api.polymarket.com/trades?user={wallet}&limit={limit}"
    handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with opener.open(req, timeout=15) as resp:
        return json.loads(resp.read())


def fmt_notification(new_trades):
    lines = [f"🔔 Polymarket 钱包新交易！({len(new_trades)} 笔)", "=" * 60]
    for t in sorted(new_trades, key=lambda x: x.get('timestamp', 0), reverse=True)[:10]:
        ts = t.get('timestamp', 0)
        time_str = datetime.fromtimestamp(ts).strftime('%m/%d %H:%M') if ts else 'N/A'
        ttype = t.get('type', 'BUY')
        title = t.get('title', 'Unknown')
        outcome = t.get('outcome', '?')
        size = float(t.get('size', 0))
        price = float(t.get('price', 0))
        tx = (t.get('transactionHash') or '')[:16]

        lines.append(f"  {time_str} | {ttype:6s} | {title}")
        lines.append(f"         → {outcome} | ${size:>10,.2f} @ {price:.1%}  [{tx}]")

    if len(new_trades) > 10:
        lines.append(f"  ... 还有 {len(new_trades)-10} 笔")
    return "\n".join(lines)


def main():
    wallet = resolve_wallet()
    path = state_path(wallet)
    state = load_state(path)
    seen = set(state.get("seen_tx", []))

    trades = fetch_trades(wallet)
    new_tx = []
    for t in trades:
        tx = t.get('transactionHash') or ''
        # Skip obvious test artifacts (e.g. known empty patterns)
        if not tx or tx in seen:
            continue
        new_tx.append(t)
        seen.add(tx)

    if not new_tx:
        sys.exit(0)  # silent exit

    state["seen_tx"] = sorted(seen)
    save_state(path, state)
    print(fmt_notification(new_tx))


if __name__ == "__main__":
    main()
