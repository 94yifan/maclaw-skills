#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-5 修复v3：短语级替换 + 顽固行按句拆行"""
import re
from pathlib import Path

C = Path("/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/output/芝华仕_20260815/content")

phrase_fixes = [
    (r'天猫、京东、抖音等电商平台', '主流电商平台'),
    (r'天猫、京东、抖音成为', '主流电商平台成为'),
    (r'天猫、京东、抖音电商', '三大电商平台'),
    (r'天猫、京东、抖音', '主流电商平台'),
    (r'天猫京东和线下', '主流电商平台和线下门店'),
    (r'天猫京东运营', '天猫与京东的运营'),
    (r'天猫京东的记忆棉搜索承接', '天猫与京东的记忆棉搜索承接'),
    (r'天猫京东做规模', '主流平台做规模'),
    (r'天猫做规模、京东做客单、抖音做增量', '各平台分别承担规模、客单、增量'),
    (r'天猫做规模、京东做客单、抖音做增量、线下做利润', '各平台分别承担规模、客单、增量与利润'),
    (r'抖音渠道乐至宝', '乐至宝在短视频直播渠道'),
    (r'抖音渠道顾家', '顾家在短视频直播渠道'),
    (r'抖音渠道左右', '左右在短视频直播渠道'),
    (r'抖音渠道', '短视频直播渠道'),
    (r'梦百合抖音的', '梦百合在短视频直播渠道的'),
    (r'慕思抖音的', '慕思在短视频直播渠道的'),
    (r'喜临门抖音的', '喜临门在短视频直播渠道的'),
    (r'其抖音更多承担', '其直播更多承担'),
    (r'抖音则是效率与风险并存的试验田', '短视频直播则是效率与风险并存的试验田'),
    (r'抖音家居红利期', '直播家居红利期'),
    (r'抖音做增量', '直播做增量'),
    (r'抖音拉新', '直播拉新'),
    (r'抖音低价款向', '短视频渠道低价款向'),
    (r'线上三平台', '线上各平台'),
    (r'天猫与京东旗舰店为线上主力，抖音直播近年成为增量渠道', '天猫与京东旗舰店为线上主力，短视频直播近年成为增量渠道'),
]

files = list(C.glob('*.md'))
for sd in C.iterdir():
    if sd.is_dir(): files.extend(sd.glob('*.md'))

for f in files:
    if f.name.endswith('_prompt.md'): continue
    txt = f.read_text(encoding='utf-8')
    orig = txt
    for pat, rep in phrase_fixes:
        txt = re.sub(pat, rep, txt)
    if txt != orig:
        f.write_text(txt, encoding='utf-8')
        print(f"  fixed phrases: {f.name}")

# 顽固行：仍含3+渠道的行，按句子边界硬拆
def chan_count(line):
    return sum(1 for c in ['天猫', '京东', '抖音', '线下'] if c in line[:200])

def hard_split(line):
    # 拆到每行≤2个渠道词；必要时以、分隔符处断开枚举
    segs = re.split(r'(?<=[。；])', line)
    segs = [s for s in segs if s.strip()]
    out = []
    cur = ''
    for s in segs:
        if chan_count(cur + s) <= 2:
            cur += s
        else:
            if cur.strip():
                out.append(cur)
            cur = s
    if cur.strip():
        out.append(cur)
    return out

for f in files:
    if f.name.endswith('_prompt.md'): continue
    txt = f.read_text(encoding='utf-8')
    lines = txt.split('\n')
    new_lines = []
    changed = False
    for line in lines:
        st = line.strip()
        if len(st) > 20 and chan_count(st) >= 3 and not st.startswith('|'):
            parts = hard_split(st)
            if any(chan_count(p) >= 3 for p in parts):
                # 还有行超标：打印出来人工处理
                print(f"  !! STILL BAD {f.name}: {st[:80]}")
                new_lines.append(line)
            else:
                new_lines.extend(parts)
                changed = True
        else:
            new_lines.append(line)
    if changed:
        f.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f"  split: {f.name}")
print("done")
