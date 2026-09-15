#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archive the July '知识缝合' block out of MEMORY.md. Safe: check input, backup once, atomic write."""
import os, sys, shutil, tempfile, datetime

WS = "/Users/yifansmacmini/.openclaw/workspace/ceo"
MEM = os.path.join(WS, "MEMORY.md")
ARCH_DIR = os.path.join(WS, "memory", "archive")
ARCH = os.path.join(ARCH_DIR, "knowledge-stitch-2026-07.md")
BACKUP = os.path.join(ARCH_DIR, "MEMORY-backup-2026-09-15.md")
os.makedirs(ARCH_DIR, exist_ok=True)

with open(MEM, "r", encoding="utf-8") as f:
    text = f.read()

# 1. input integrity check
if os.path.getsize(MEM) < 100000 or "## 知识缝合" not in text:
    sys.exit("ABORT: input MEMORY.md looks incomplete (size/marker).")

lines = text.split("\n")
# find second "## 知识缝合"
idxs = [i for i, l in enumerate(lines) if l.strip() == "## 知识缝合"]
if len(idxs) < 2:
    sys.exit("ABORT: expected 2 '## 知识缝合' headings, found %d" % len(idxs))
cut = idxs[1]
head = lines[:cut]
tail = lines[cut:]

if len(tail) < 100:
    sys.exit("ABORT: July block unexpectedly small (%d lines)" % len(tail))
if not any("2026-07" in l for l in tail):
    sys.exit("ABORT: tail has no 2026-07 content.")

# 2. backup only if not exists (do not clobber)
if not os.path.exists(BACKUP):
    shutil.copy2(MEM, BACKUP)
    print("backup created:", BACKUP)
else:
    print("backup already exists, not overwriting:", BACKUP)

# 3. build archive file
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
arch_text = (
    "# CEO MEMORY 知识缝合归档 — 2026-07\n\n"
    "归档时间：%s\n"
    "归档原因：MEMORY.md 膨胀至 149,876B，超 140KB 阈值（守卫③），归档最老未归档区块（2026-07-12 ~ 2026-07-24 逐日缝合）。\n"
    "来源：原 MEMORY.md 第二「知识缝合」区（July）。原文完整保留，索引结构不变。\n\n"
    "---\n\n"
) % stamp + "\n".join(tail).lstrip("\n")

pointer = (
    "## 知识缝合（2026-07 区块已归档 2026-09-15）\n\n"
    "**2026-07-12 ~ 2026-07-24 期间的逐日知识缝合已归档至 `memory/archive/knowledge-stitch-2026-07.md`。**\n"
    "归档原因：MEMORY.md 达 149,876B 触发 140KB 阈值。需要 7 月缝合（品牌弱三维诊断/CEO 产出可见性/失败归因权限/汇聚点系统等）时读归档文件，索引结构不变。\n"
)

new_text = "\n".join(head) + "\n" + pointer

# 4a. write archive FIRST (so tail is durable before we drop it from MEMORY)
if os.path.exists(ARCH):
    sys.exit("ABORT: archive target already exists: %s" % ARCH)
with open(ARCH, "w", encoding="utf-8") as f:
    f.write(arch_text)
if os.path.getsize(ARCH) < 10000:
    sys.exit("ABORT: archive write looks too small")
print("archive written:", ARCH, os.path.getsize(ARCH), "bytes")

# 4b. atomic replace MEMORY.md
fd, tmp = tempfile.mkstemp(dir=WS, prefix=".MEMORY.tmp")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(new_text)
os.replace(tmp, MEM)

# 5. verify
with open(MEM, "r", encoding="utf-8") as f:
    chk = f.read()
print("new MEMORY.md:", len(chk.encode("utf-8")), "bytes")
print("headings '## 知识缝合' now:", chk.count("## 知识缝合"))
print("contains 2026-07-13 block:", "2026-07-13" in chk)
print("contains 2026-09-15 block:", "2026-09-15" in chk)
