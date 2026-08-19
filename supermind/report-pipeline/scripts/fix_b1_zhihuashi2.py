#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-1 修复v2：回退句子拆行（仅保留含渠道词的拆行），恢复段落结构"""
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
        # 非空、非标题、非表格、非列表的散文行：尝试与后续行合并（还原被拆的句子）
        if st and not st.startswith('#') and not st.startswith('|') and not st.startswith('-'):
            merged = st
            j = i + 1
            while j < n:
                nxt = lines[j].strip()
                if not nxt:
                    break
                if nxt.startswith('#') or nxt.startswith('|') or nxt.startswith('-'):
                    break
                # 若当前行含渠道词（B-5拆分结果），不合并
                if any(c in merged for c in CHANNELS):
                    break
                # 若下一行含渠道词且当前行也有渠道词，不合并
                merged = merged + nxt
                j += 1
            out.append(merged)
            i = j
        else:
            out.append(line)
            i += 1
    new_txt = '\n'.join(out)
    if new_txt != txt:
        f.write_text(new_txt, encoding='utf-8')
        print(f"  rejoined: {f.name}")

# 统计
all_lines = []
for f in files:
    if f.name.endswith('_prompt.md'): continue
    all_lines.extend(f.read_text(encoding='utf-8').split('\n'))
paras = [p.strip() for p in all_lines if p.strip() and len(p.strip()) > 20]
numbered = sum(1 for p in paras if re.search(r'\d+', p))
print(f"B-1: {numbered}/{len(paras)} = {numbered/len(paras)*100:.1f}% (need >=60%)")
# B-5 复查
n5 = 0
for p in paras:
    chans = [c for c in CHANNELS if c in p[:200]]
    if len(chans) >= 3: n5 += 1
print("B-5 flagged lines:", n5)
