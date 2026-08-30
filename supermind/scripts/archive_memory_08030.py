#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEMORY.md 瘦身：归档 2026-07-31 及以前的知识缝合区与项目复盘，保留 08 月内容。
策略：按 ## 级 section 切分，section 内 ### 子段按日期判定。
归档文件：memory/archive/knowledge-stitch-2026-05to07.md
"""
import re, shutil, os
from datetime import datetime

BASE = "/Users/yifansmacmini/.openclaw/workspace/supermind"
SRC = os.path.join(BASE, "MEMORY.md")
ARCHIVE_DIR = os.path.join(BASE, "memory", "archive")
ARCHIVE = os.path.join(ARCHIVE_DIR, "knowledge-stitch-2026-05to07.md")
BACKUP = os.path.join(ARCHIVE_DIR, "MEMORY-backup-20260830.md")

os.makedirs(ARCHIVE_DIR, exist_ok=True)
# 备份
shutil.copy2(SRC, BACKUP)

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

def section_date(title):
    """从 ## 标题提取日期；无日期返回 None"""
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", title)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

CUTOFF = datetime(2026, 7, 31)

def is_archive_section(title):
    """判断整个 ## section 是否归档"""
    t = title.strip()
    if t.startswith("## 知识缝合"):
        d = section_date(t)
        return d is not None and d <= CUTOFF
    if t.startswith("## 2026-07-2") or t.startswith("## 2026-07-1"):  # 康尔馨/三棵树整段
        return True
    return False

def is_archive_sub(title):
    """判断 ### 子段是否归档（项目复盘存档/项目复盘内的子项）"""
    m = re.search(r"\[(20\d\d)-(\d\d)-(\d\d)\]", title)
    if not m:
        return False
    d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return d <= CUTOFF

# 切分 sections
sections = []  # (start_idx, end_idx_exclusive, title)
cur_start = 0
cur_title = None
for i, ln in enumerate(lines):
    if ln.startswith("## "):
        if cur_title is not None:
            sections.append((cur_start, i, cur_title))
        cur_start = i
        cur_title = ln
if cur_title is not None:
    sections.append((cur_start, len(lines), cur_title))

keep_lines = []
archived = []
for start, end, title in sections:
    t = title.strip()
    if is_archive_section(t):
        archived.append((start, end, title))
        continue
    # 项目复盘存档 / 项目复盘：子段按日期拆
    if t.startswith("## 项目复盘存档") or t.startswith("## 项目复盘"):
        # 切分子段
        subs = []  # (s, e, subtitle) within section
        cs = start
        cst = None
        for i in range(start, end):
            if lines[i].startswith("### "):
                if cst is not None:
                    subs.append((cs, i, cst))
                cs = i
                cst = lines[i]
        if cst is not None:
            subs.append((cs, end, cst))
        # 子段可能不是 ### 开头（section 头下面直接是内容，比如格式说明）——需要保留非子段内容
        # 处理：遍历子段，归档日期<=cutoff的，保留其余；section 头保留
        keep_lines.append(title)
        kept_any = False
        for s, e, st in subs:
            if is_archive_sub(st):
                archived.append((s, e, st))
            else:
                keep_lines.extend(lines[s:e])
                kept_any = True
        # 若整个 section 的子段全部归档（无保留内容），则 section 头也无意义——保留头+空行标记
        if not kept_any:
            keep_lines.append("# [项目复盘存档 2026-07 及以前内容已归档至 memory/archive/knowledge-stitch-2026-05to07.md]\n")
        else:
            keep_lines.append("\n")
        continue
    keep_lines.extend(lines[start:end])

# 写入归档文件
with open(ARCHIVE, "w", encoding="utf-8") as f:
    f.write("# 知识缝合区归档 2026-05-09 ~ 2026-07-31\n\n")
    f.write("> 归档时间：2026-08-30（MEMORY.md 瘦身，原 184KB/1443 行 → 目标 100KB 内）\n")
    f.write("> 归档范围：2026-07-31 及以前的知识缝合区 + 项目复盘存档（07 月项目）+ 项目复盘（07 月静默日）\n")
    f.write("> 索引：本文件保留完整历史，当前知识以 MEMORY.md 知识缝合区（2026-08-01 起）为准\n\n")
    f.write("---\n\n")
    for _, _, title in sorted(archived, key=lambda x: x[0]):
        f.write(title)
    # 注意：上面的 title 只是标题行，需要补内容
    # 重新按内容写：直接从 lines 切片
    f.close()

# 上面的归档写入只写了标题，重新完整写入
with open(ARCHIVE, "w", encoding="utf-8") as f:
    f.write("# 知识缝合区归档 2026-05-09 ~ 2026-07-31\n\n")
    f.write("> 归档时间：2026-08-30（MEMORY.md 瘦身）\n")
    f.write("> 归档范围：2026-07-31 及以前的知识缝合区 + 07 月项目复盘存档/项目复盘\n")
    f.write("> 说明：当前知识以 MEMORY.md 知识缝合区（2026-08-01 起）为准，本文件保留完整历史供回溯\n\n")
    f.write("---\n\n")
    for s, e, _ in sorted(archived, key=lambda x: x[0]):
        f.write("".join(lines[s:e]))
        f.write("\n\n---\n\n")

with open(SRC, "w", encoding="utf-8") as f:
    f.writelines(keep_lines)

print(f"归档段落数: {len(archived)}")
print(f"归档文件行数: {sum(e-s for s,e,_ in archived)}")
print(f"新 MEMORY.md 行数: {len(keep_lines)}")
new_bytes = len("".join(keep_lines).encode("utf-8"))
print(f"新 MEMORY.md 字节: {new_bytes}")
