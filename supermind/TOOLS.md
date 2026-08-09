# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## 联网搜索（2026-07-18 确认）

- web_search 工具不可用：provider 是 DuckDuckGo，在本机网络被墙；Brave/Perplexity API 同样被墙，重试无意义
- **默认用网页搜**：web_fetch 抓搜狗 `https://www.sogou.com/web?query=URL编码关键词`，约1.3秒返回，稳定
- 搜狗结果里的 /link?url= 中转链接拼成 `https://www.sogou.com/link?url=...` 再 fetch；mp.weixin.qq.com 链接一般可直接 fetch
- 逸凡已确认：后面搜索先都走网页搜，不急着修 web_search

## Related

- [Agent workspace](/concepts/agent-workspace)
