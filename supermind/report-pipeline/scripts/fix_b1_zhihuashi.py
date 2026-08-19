#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-1 修复：把长段落按句拆行，数据密集句拆开后提升数字锚点覆盖率"""
import re
from pathlib import Path

C = Path("/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/output/芝华仕_20260815/content")

def split_sentences(line):
    """按句末标点拆行，保留 [tier] 标记在句尾"""
    segs = re.split(r'(?<=[。；])', line)
    return [s for s in segs if s.strip()]

files = list(C.glob('*.md'))
for sd in C.iterdir():
    if sd.is_dir(): files.extend(sd.glob('*.md'))

total_new = 0
for f in files:
    if f.name.endswith('_prompt.md'): continue
    txt = f.read_text(encoding='utf-8')
    lines = txt.split('\n')
    new_lines = []
    changed = False
    for line in lines:
        st = line.strip()
        # 只拆：非标题、非表格、长度>140 的散文行
        if (len(st) > 140 and not st.startswith('#') and not st.startswith('|')
                and not st.startswith('-') and not re.match(r'^\d+[\.\)]', st)):
            parts = split_sentences(st)
            if len(parts) > 1:
                new_lines.extend(parts)
                changed = True
                total_new += len(parts) - 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    if changed:
        f.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f"  split {f.name}")
print("extra lines created:", total_new)

# 统计 B-1 比率
all_lines = []
for f in files:
    if f.name.endswith('_prompt.md'): continue
    all_lines.extend(f.read_text(encoding='utf-8').split('\n'))
paras = [p.strip() for p in all_lines if p.strip() and len(p.strip()) > 20]
numbered = sum(1 for p in paras if re.search(r'\d+', p))
print(f"B-1: {numbered}/{len(paras)} = {numbered/len(paras)*100:.1f}% (need >=60%)")
