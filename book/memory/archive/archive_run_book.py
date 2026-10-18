#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEMORY.md 归档脚本：自最旧「近期缝合块」起归档，直到 < TARGET。

用法：python3 archive_run_book.py YYYY-MM-DD [keep_marker]
- TODAY 由参数传入（2026-10-18 修正：原硬编码 10-12，跨日运行会用错备份名与归档标签）
- keep_marker 默认 = "## <TODAY> Dreaming知识串联"，用于写入前校验与写入后复检
"""
import re, os, sys

BASE = "/Users/yifansmacmini/.openclaw/workspace/book"
P = os.path.join(BASE, "MEMORY.md")
ARCH_DIR = os.path.join(BASE, "memory", "archive")
TODAY = sys.argv[1] if len(sys.argv) > 1 else None
if not TODAY or not re.fullmatch(r"\d{4}-\d\d-\d\d", TODAY):
    print("ABORT: usage: archive_run_book.py YYYY-MM-DD [keep_marker]"); sys.exit(2)
KEEP = sys.argv[2] if len(sys.argv) > 2 else "## %s Dreaming知识串联" % TODAY
TARGET = 145000
TRIGGER = 150000

orig = open(P, encoding="utf-8").read()
orig_size = len(orig.encode("utf-8"))

# 条件①：校验输入完整（大小 + 关键标记在位），不满足即中止
if orig_size <= TRIGGER:
    print("SKIP: size %d <= trigger %d, no archiving" % (orig_size, TRIGGER)); sys.exit(0)
for marker in ["# MEMORY.md", KEEP, "当前待裁定项", "## 知识缝合区", "## ⚙️ 运行规则"]:
    if marker not in orig:
        print("ABORT: marker missing ->", marker); sys.exit(1)

data = orig
pattern = re.compile(r"^## 2026-\d\d-\d\d Dreaming知识串联", re.M)

def sections(d):
    # 仅取「近期缝合块」内的日节（截止在永久保留的 7 月方法论簇之前）
    cut = d.find("## 2026-07-13 Dreaming知识串联")
    if cut < 0:
        cut = len(d)
    ms = [m for m in pattern.finditer(d) if m.start() < cut]
    out = []
    for k, m in enumerate(ms):
        s = m.start()
        e = ms[k+1].start() if k+1 < len(ms) else cut
        out.append([s, e, d[s:s+45]])
    return out

sec = sections(data)
removed_blocks = []
removed_dates = []
while len(data.encode("utf-8")) >= TARGET and sec:
    s = sec[-1]
    blk = data[s[0]:s[1]]
    if KEEP in blk[:200]:
        print("ABORT: would archive the keep-marker section ->", blk[:60]); sys.exit(1)
    removed_blocks.append(blk)
    m = re.match(r"^## (2026-\d\d-\d\d)", blk)
    removed_dates.append(m.group(1))
    data = data[:s[0]] + data[s[1]:]
    sec = sec[:-1]

if not removed_blocks:
    print("NOTHING ARCHIVED (no sections available)"); sys.exit(0)

new_size = len(data.encode("utf-8"))
# 条件②：备份只在不存在时创建（禁止覆盖）
backup = os.path.join(BASE, "MEMORY-backup-%s.md" % TODAY)
if not os.path.exists(backup):
    with open(backup, "w", encoding="utf-8") as f:
        f.write(orig)

# 归档文件：追加（旧→新）
newest = max(removed_dates)
arch_path = os.path.join(ARCH_DIR, "stitching-archive-through-%s.md" % newest)
mode = "a" if os.path.exists(arch_path) else "w"
with open(arch_path, mode, encoding="utf-8") as f:
    f.write("\n\n<!-- archived from MEMORY.md on %s -->\n\n" % TODAY)
    for blk in removed_blocks:
        f.write(blk.rstrip("\n") + "\n")

# 校验：写入前复检新内容完整
if KEEP not in data or "当前待裁定项" not in data or "# MEMORY.md" not in data:
    print("ABORT: post-slice validation failed"); sys.exit(1)
if len(data.encode("utf-8")) >= orig_size:
    print("ABORT: size did not decrease"); sys.exit(1)

# 条件③：原子写入（temp + rename）
tmp = P + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(data)
os.replace(tmp, P)

print("orig=%d new=%d archived=%s blocks=%d arch_file=%s backup=%s" % (
    orig_size, new_size, ",".join(removed_dates), len(removed_blocks),
    os.path.basename(arch_path), os.path.basename(backup)))
