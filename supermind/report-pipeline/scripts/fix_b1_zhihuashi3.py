#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-1 修复v3：完全还原段落结构（所有连续散文行合并回一行），再评估B-5"""
import re
from pathlib import Path

C = Path("/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/output/芝华仕_20260815/content")
CHANNELS = ['天猫', '京东', '抖音', '线下']

files = list(C.glob('*.md'))
for sd in C.iterdir():
    if sd.is_dir(): files.extend(sd.glob('*.md'))

for f in files:
    if f.name.endswith('_prompt.md'): continue
    txt = f.read_text(encoding='utf-8')
    lines = txt.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        st = line.strip()
        if st and not st.startswith('#') and not st.startswith('|') and not st.startswith('-'):
            merged = st
            j = i + 1
            while j < n:
                nxt = lines[j].strip()
                if not nxt or nxt.startswith('#') or nxt.startswith('|') or nxt.startswith('-'):
                    break
                merged = merged + nxt
                j += 1
            out.append(merged)
            i = j
        else:
            out.append(line)
            i += 1
    f.write_text('\n'.join(out), encoding='utf-8')

# 统计
all_lines = []
for f in files:
    if f.name.endswith('_prompt.md'): continue
    all_lines.extend(f.read_text(encoding='utf-8').split('\n'))
paras = [p.strip() for p in all_lines if p.strip() and len(p.strip()) > 20]
numbered = sum(1 for p in paras if re.search(r'\d+', p))
print(f"B-1: {numbered}/{len(paras)} = {numbered/len(paras)*100:.1f}% (need >=60%)")
n5 = 0
for p in paras:
    chans = [c for c in CHANNELS if c in p[:200]]
    if len(chans) >= 3:
        n5 += 1
        if n5 <= 8:
            print(f"  B5: {p[:70]}")
print("B-5 flagged lines:", n5)
