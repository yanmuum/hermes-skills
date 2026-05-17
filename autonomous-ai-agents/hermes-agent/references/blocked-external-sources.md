# Blocked External Sources — Handling Strategy

## Context

This Hermes instance runs in mainland China where the Great Firewall (GFW) blocks:
- Twitter/X (x.com, twitter.com) — direct and all mirrors (nitter, vxtwitter, fxtwitter)
- raw.githubusercontent.com (times out)
- Google, YouTube, and most Western social media

Additionally, the proxy (172.26.240.1:7890) is often not running on the Windows host.

## Strategy: User Requests Skill Install from Blocked Source

When a user sends a Twitter/X link saying "install this skill" or similar:

1. **Diagnose quickly** — don't loop through 10 dead-end approaches. Try at most 2-3 methods, then ask:
   - browser_navigate (one try)
   - curl with proxy (one try)
   - GitHub API / search for related content (one try)

2. **Explain clearly, once** — state the limitation, ask for the content directly:
   > "Twitter is inaccessible from this network. Can you paste the tweet content so I can proceed?"

3. **Never send the user's own text back to them** — this creates confusion and frustration.

## Currently Accessible Resources

| Resource | Accessible? | Notes |
|----------|-------------|-------|
| Baidu (www.baidu.com) | ✅ Yes | Direct, no proxy needed |
| GitHub API (api.github.com) | ✅ Yes | Search, read repos, user data |
| GitHub raw content | ❌ No | raw.githubusercontent.com times out |
| GitHub git clone | ❌ No | All git operations time out |
| npm registry | ❌ No | Even npmmirror times out |
| DeepSeek API | ✅ Yes | Direct connection works |
| Feishu API | ✅ Yes | Direct connection works |
| baidu.com links | ✅ Yes | Works direct |
| Stack Overflow | ❌ Blocked | GFW blocks |

## Related Projects (Accessible via GitHub API)

- **OpenClaw** (372k★) — Personal AI assistant, similar to Hermes. Has 13k+ skills on ClawHub. The xurl skill in Hermes lists OpenClaw as its upstream source. Good inspiration for Hermes skills.
- **Claude Code** — Anthropic's coding agent
- **Codex** — OpenAI's coding agent
