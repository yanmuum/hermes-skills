# WSL Proxy Poisoning — Diagnosis & Fix

## Symptoms

- Hermes sessions repeatedly disconnect with no clear error
- Gateway fails to connect to Feishu/Telegram/etc. with `connect timed out after 30s`
- DeepSeek API calls fail with timeout/connection errors
- The user says "conversations keep disconnecting"
- Error in gateway log: `HTTPSConnectionPool(host='open.feishu.cn', port=443): Max retries exceeded` or `ConnectTimeout`

## Root Cause

WSL inherits `http_proxy`/`https_proxy` env vars from the Windows host's Clash/V2Ray proxy client (typically at `172.26.240.1:7890` — the WSL default gateway).

The proxy is often set in `~/.bashrc`:
```bash
export http_proxy=http://172.26.240.1:7890
export https_proxy=http://172.26.240.1:7890
export all_proxy=socks5://172.26.240.1:7890
```

When the Windows proxy client is **not running**, port 7890 is closed → ALL API calls fail → sessions crash.

Even when the proxy IS running, it adds latency and instability to API calls that don't need it (DeepSeek, Feishu, Baidu are all directly accessible from mainland China).

## Diagnosis

```bash
# 1. Check if proxy is set
env | grep -i proxy

# 2. Check if proxy port is reachable
timeout 2 bash -c 'echo > /dev/tcp/172.26.240.1/7890' 2>/dev/null && echo "✅ 代理端口可达" || echo "❌ 代理端口不通（VPN未运行）"

# 3. Find the proxy source
grep -r "172.26.240.1" ~/.bashrc ~/.zshrc ~/.profile ~/.bash_profile 2>/dev/null

# 4. Test API provider WITHOUT proxy
unset http_proxy https_proxy all_proxy
curl -s -o /dev/null -w "%{http_code} %{time_total}s" --max-time 5 https://api.deepseek.com
# Expected: 401 (means network path is working, auth just missing)
```

## Fix: Conditional Proxy Aliases

Replace the auto-export lines in `~/.bashrc` with conditional aliases:

```bash
# WSL代理开关 — 默认关，需要上推特/外网时手动开
alias proxy-on='  export http_proxy=http://172.26.240.1:7890; export https_proxy=http://172.26.240.1:7890; export all_proxy=socks5://172.26.240.1:7890; echo "✅ 代理已开 (7890)"'
alias proxy-off=' unset http_proxy https_proxy all_proxy; echo "✅ 代理已关"'
alias proxy-status='echo "http_proxy=${http_proxy:-❌ 未设置}"; echo "https_proxy=${https_proxy:-❌ 未设置}"; echo "all_proxy=${all_proxy:-❌ 未设置}"'
```

Apply it with sed:
```bash
sed -i '/^# WSL_PROXY_FOR_HERMES/,+3c\
# WSL代理开关 — 默认关，需要上推特/外网时手动开\
alias proxy-on='\''  export http_proxy=http://172.26.240.1:7890; export https_proxy=http://172.26.240.1:7890; export all_proxy=socks5://172.26.240.1:7890; echo "✅ 代理已开 (7890)"'\''\
alias proxy-off='\'' unset http_proxy https_proxy all_proxy; echo "✅ 代理已关"'\''\
alias proxy-status='\''echo "http_proxy=${http_proxy:-❌ 未设置}"; echo "https_proxy=${https_proxy:-❌ 未设置}"; echo "all_proxy=${all_proxy:-❌ 未设置}"'\''' ~/.bashrc
```

Or use the patch tool to replace the old proxy block with the alias block (read the full file first).

## Usage

```
# Shell startup: no proxy (Hermes runs fast direct)
proxy-on     # → open Twitter/X/Google
proxy-off    # → back to direct
proxy-status # → check current state
```

## Known Working APIs (China direct, no proxy needed)

- DeepSeek: `https://api.deepseek.com` (~500ms)
- Feishu: `https://open.feishu.cn` 
- Baidu: `https://www.baidu.com`
- Alibaba/DashScope: `https://dashscope.aliyuncs.com`
- Kimi/Moonshot: `https://api.moonshot.cn`
- HuggingFace: `https://huggingface.co` (sometimes, varies)

## Note: bashrc interactive guard

`~/.bashrc` usually has a check at the top that returns early in non-interactive shells:
```bash
case $- in
    *i*) ;;
      *) return;;
esac
```
This means aliases won't be available when `source ~/.bashrc` is called from a non-interactive terminal (like Hermes tool calls). But the proxy env vars are already cleared for the running Hermes session. The aliases work in new interactive terminals.
