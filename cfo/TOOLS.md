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

## Related

- [Agent workspace](/concepts/agent-workspace)

## docx 生成与预览（2026-10-18，三个坑已踩过）

- **段落字体**：`python-docx` 的 `Paragraph` 没有 `.font`。设字号/字体必须落到 `run`（`p.add_run()` 后设 `run.font.size`），或改 `style.font`。直接写 `cell.paragraphs[0].font.size` 必定 `AttributeError`。
- **rPr 判空**：`run._element.rPr` 在新建 run 上可能是 `None`。写字号/中文字体前先 `run.font.size = Pt(10)` 触发 rPr 创建，再 `rPr.rFonts.set(qn("w:eastAsia"), "黑体")`；直接 `.set()` 会 `AttributeError: 'NoneType'`。
- **渲染预览**：本机没有 LibreOffice（`soffice` / `libreoffice` 均不存在）。看排版用 `qlmanage -t -s 1600 -o <outdir> <file.docx>`，输出 `<文件名>.docx.png`，再用 image 工具读图。`/tmp/qlout/` 这类目录要先 `mkdir -p`。
- **Word 修订标记**：直接写 `w:ins` / `w:del` 节点（不是涂色）。`w:del` 内必须是 `w:delText`，不能留 `w:t`；`w:ins`/`w:del` 必须带 `w:id`、`w:author`、`w:date`；`pPr/rPr` 必须排在段属性最后。验收做双向：接受全部修订后与定稿逐段比对、拒绝全部修订后与原稿逐段比对，并检查非法节点计数为 0。
- **可复用脚本**：`cfo/tmp/legal/gen_partner_agreement.py`（条款文档生成 + 表格）、`gen_redline.py`（按段配对生成修订标记稿）。
