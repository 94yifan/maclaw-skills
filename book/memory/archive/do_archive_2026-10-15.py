#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, os, sys

BASE = "/Users/yifansmacmini/.openclaw/workspace/book"
P = os.path.join(BASE, "MEMORY.md")
ARCH_DIR = os.path.join(BASE, "memory", "archive")
TODAY = "2026-10-15"
TARGET = 145000
TRIGGER = 150000

orig = open(P, encoding="utf-8").read()
orig_size = len(orig.encode("utf-8"))

if orig_size <= TRIGGER:
    print("SKIP: size %d <= trigger %d, no archiving" % (orig_size, TRIGGER)); sys.exit(0)
for marker in ["# MEMORY.md", "## 2026-10-15 Dreaming知识串联", "当前待裁定项", "## 知识缝合区", "Day30（10/15）"]:
    if marker not in orig:
        print("ABORT: marker missing ->", marker); sys.exit(1)

data = orig
pattern = re.compile(r"^## 2026-\d\d-\d\d Dreaming知识串联", re.M)

def sections(d):
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
    removed_blocks.append(blk)
    m = re.match(r"^## (2026-\d\d-\d\d)", blk)
    removed_dates.append(m.group(1))
    data = data[:s[0]] + data[s[1]:]
    sec = sec[:-1]

if not removed_blocks:
    print("NOTHING ARCHIVED (no sections available)"); sys.exit(0)

new_size = len(data.encode("utf-8"))
backup = os.path.join(BASE, "MEMORY-backup-%s.md" % TODAY)
if not os.path.exists(backup):
    with open(backup, "w", encoding="utf-8") as f:
        f.write(orig)

newest = removed_dates[0] if removed_dates[0] > removed_dates[-1] else removed_dates[-1]
arch_path = os.path.join(ARCH_DIR, "stitching-archive-through-%s.md" % newest)
mode = "a" if os.path.exists(arch_path) else "w"
with open(arch_path, mode, encoding="utf-8") as f:
    f.write("\n\n<!-- archived from MEMORY.md on %s -->\n\n" % TODAY)
    for blk in removed_blocks:
        f.write(blk.rstrip("\n") + "\n")

if "## 2026-10-15 Dreaming知识串联" not in data or "当前待裁定项" not in data:
    print("ABORT: post-slice validation failed"); sys.exit(1)

tmp = P + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(data)
os.replace(tmp, P)

print("orig=%d new=%d archived=%s blocks=%d arch_file=%s backup=%s" % (
    orig_size, new_size, ",".join(removed_dates), len(removed_blocks),
    os.path.basename(arch_path), os.path.basename(backup)))
