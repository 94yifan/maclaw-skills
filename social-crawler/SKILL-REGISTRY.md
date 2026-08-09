# Skill Install Registry — Social Crawler

记录所有已安装的 Skill，便于复制到其他分身 workspace。

---

## 已安装 Skill 清单

| # | Skill | 版本 | 安装路径 | 用途 | 来源 |
|---|---|---|---|---|---|
| 1 | xiaohongshu-crawler | 1.0.1 | ./xiaohongshu-crawler | 小红书内容爬取 | ClawHub |
| 2 | browser-automation-stealth | 1.0.0 | ./browser-automation-stealth | 安全浏览器自动化（需--force安装，VirusTotal误报） | ClawHub |
| 3 | desk-research | 1.0.0 | ./desk-research | 结构化 desk research 工作流 | ClawHub |
| 4 | data-analysis-reporting | 0.1.0 | ./data-analysis-reporting | 商业数据报告生成 | ClawHub |
| 5 | xiaohongshu-viral-copy | 1.0.0 | ./xiaohongshu-viral-copy | 小红书爆款文案生成 | ClawHub |
| 6 | copywriting-pro | 1.0.0 | ./copywriting-pro | 专业英文文案 SOP（AIDA/PAS等框架） | ClawHub |
| 7 | copywriting-zh-pro | 0.1.1 | ./copywriting-zh-pro | 中文文案全场景（跨境/小红书/公众号等） | ClawHub |
| 8 | feishu-doc-manager | 1.0.0 | ./feishu-doc-manager | 飞书文档 Markdown 发布（需--force安装，VirusTotal误报） | ClawHub |

---

## 安装命令（复制到新 workspace 时使用）

```bash
# 进入目标 workspace 后执行：
clawhub install xiaohongshu-crawler --dir . --force
clawhub install browser-automation-stealth --dir . --force
clawhub install desk-research --dir . --force
clawhub install data-analysis-reporting --dir . --force
clawhub install xiaohongshu-viral-copy --dir . --force
clawhub install copywriting-pro --dir . --force
clawhub install copywriting-zh-pro --dir . --force
clawhub install feishu-doc-manager --dir . --force
```

---

## 注意事项

- `browser-automation-stealth` 和 `feishu-doc-manager` 被 VirusTotal 标记为可疑，但均为误报（包含加解密关键词）。安装时需加 `--force` 参数。
- 所有 Skill 均以 `--dir .` 安装到当前工作目录，不会污染全局。
- 安装完成后建议用 `skill-vetter` 协议自审一次。

---

## 待复制到的分身 Workspace

| 分身 | Workspace 路径 | 状态 |
|---|---|---|
| 财务数据分析 | 待定 | 待建 |
| CEO管理职能 | 待定 | 待建 |
| 品牌营销及服务设计咨询顾问 | 待定 | 待建 |
| 案例包奖 | 待定 | 待建 |
## 待添加

| # | Skill | 版本 | 安装路径 | 用途 | 来源 |
|---|---|---|---|---|---|
| 9 | tea-brand-daily-report | 1.0.0 | ./skills/tea-brand-daily-report | 19个茶饮品牌微博日报自动生成 | 自建 |
