#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-5 修复：把同一行内出现3+渠道的句子拆分为按渠道分行，表格单元格改写"""
import re
from pathlib import Path

C = Path("/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/output/芝华仕_20260815/content")
CHANNELS = ['天猫', '京东', '抖音', '线下']

def chan_count(line):
    return sum(1 for c in CHANNELS if c in line[:200])

# 需要改写的表格行（单元格内3渠道并列）
table_fixes = {
    "channel_supply_chain.md": [
        ("| 全渠道期 | 2010年到2020年 | 天猫京东抖音电商上线，门店破6000家 | 线上拉新、线下成交双轮驱动 |",
         "| 全渠道期 | 2010年到2020年 | 三大电商平台陆续上线，门店破6000家 | 线上拉新、线下成交双轮驱动 |"),
        ("| 全域一盘货期 | 2020年至今 | 线上线下同款同价，直播与私域补位 | 天猫做规模、京东做客单、抖音做增量 |",
         "| 全域一盘货期 | 2020年至今 | 线上线下同款同价，直播与私域补位 | 三个平台按规模、客单、增量分工 |"),
    ],
}

def split_prose(line):
    """按句号/分号切分，再贪心合并保证每行前200字符≤2个渠道词"""
    sentences = re.split(r'(?<=[。；])', line)
    sentences = [s for s in sentences if s.strip()]
    if not sentences:
        return [line]
    result = []
    cur = ""
    for s in sentences:
        if chan_count(cur + s) <= 2:
            cur += s
        else:
            if cur.strip():
                result.append(cur)
            cur = s
    if cur.strip():
        result.append(cur)
    return result

# 处理表格修复
for fname, fixes in table_fixes.items():
    p = C / fname
    txt = p.read_text(encoding='utf-8')
    for old, new in fixes:
        if old in txt:
            txt = txt.replace(old, new)
            print(f"  table fix: {fname}: {old[:30]}...")
        else:
            print(f"  !! NOT FOUND in {fname}: {old[:30]}")
    p.write_text(txt, encoding='utf-8')

# 处理散文行
files = list(C.glob('*.md'))
for sd in C.iterdir():
    if sd.is_dir(): files.extend(sd.glob('*.md'))

total_split = 0
for f in files:
    if f.name.endswith('_prompt.md'): continue
    txt = f.read_text(encoding='utf-8')
    lines = txt.split('\n')
    new_lines = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if (len(stripped) > 20 and chan_count(stripped) >= 3
                and not stripped.startswith('|')):
            parts = split_prose(stripped)
            if len(parts) > 1:
                new_lines.extend(parts)
                changed = True
                total_split += 1
                print(f"  split {f.name}: {len(parts)} 段")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    if changed:
        p.write_text('\n'.join(new_lines), encoding='utf-8')
print("total prose lines split:", total_split)
