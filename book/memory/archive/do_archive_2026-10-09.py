#!/usr/bin/env python3
import re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCDIR = os.path.join(BASE, 'memory', 'archive')
ARC = os.path.join(ARCDIR, 'stitching-archive-through-2026-09-28.md')
BAK = os.path.join(ARCDIR, 'MEMORY-backup-2026-10-09.md')

TARGET = 145000
TRIGGER = 150000
TARGETS = ['2026-09-26', '2026-09-27', '2026-09-28']

# --- 条件①：校验输入完整 ---
if not os.path.exists(MEM):
    sys.exit('abort: MEMORY.md missing')
raw = open(MEM, 'rb').read()
if len(raw) < 100000:
    sys.exit(f'abort: MEMORY.md too small ({len(raw)}B) - refusing to operate')
if len(raw) <= TRIGGER:
    sys.exit(f'abort: {len(raw)}B <= trigger, nothing to do')
s = raw.decode('utf-8')
for marker in ['## ⚙️ 运行规则', '## 知识缝合区',
               '## 2026-10-09 Dreaming知识串联', '## 2026-10-08 Dreaming知识串联',
               '## 2026-07-21 Dreaming知识串联']:
    if marker not in s:
        sys.exit(f'abort: marker missing -> {marker}')

# --- 条件③：备份只在不存在时创建 ---
if not os.path.exists(BAK):
    open(BAK, 'wb').write(raw)
    print(f'backup created: {BAK} ({len(raw)}B)')
else:
    print(f'backup exists, not overwritten: {BAK}')

heads = [(m.start(), m.group(1)) for m in
         re.finditer(r'^## (2026-\d\d-\d\d) Dreaming知识串联.*$', s, re.M)]
idx = {day: i for i, (_, day) in enumerate(heads)}
for t in TARGETS:
    if t not in idx:
        sys.exit(f'abort: target block {t} not found')

def block_bounds(i):
    start = heads[i][0]
    end = heads[i+1][0] if i+1 < len(heads) else len(s)
    return start, end

removed = ''
for t in sorted(TARGETS, key=lambda x: idx[x], reverse=True):
    i = idx[t]
    start, end = block_bounds(i)
    removed = s[start:end] + removed

new_s = s
# 从后往前删，避免位移影响（用原始坐标逐块进行，按索引降序）
for t in sorted(TARGETS, key=lambda x: idx[x], reverse=True):
    i = idx[t]
    start, end = block_bounds(i)
    new_s = new_s[:start] + new_s[end:]

new_b = new_s.encode('utf-8')
if len(new_b) >= len(raw):
    sys.exit('abort: size did not shrink')

header = '\n\n<!-- ==== archive batch 2026-10-09: 9/26-9/28 ==== -->\n\n'
with open(ARC, 'ab') as f:
    f.write(header.encode('utf-8'))
    f.write(removed.encode('utf-8'))
print(f'archived {len(removed.encode("utf-8"))}B -> {ARC}')

# --- 条件②：原子写入 ---
tmp = MEM + '.tmp'
with open(tmp, 'wb') as f:
    f.write(new_b)
os.replace(tmp, MEM)
print(f'MEMORY.md: {len(raw)}B -> {len(new_b)}B')

# --- 校验输出 ---
chk = open(MEM, 'rb').read()
if len(chk) != len(new_b):
    sys.exit('abort: post-write size mismatch')
cs = chk.decode('utf-8')
for keep in ['## 2026-10-09 Dreaming知识串联', '## 2026-10-08 Dreaming知识串联', '## 2026-07-21 Dreaming知识串联']:
    if keep not in cs:
        sys.exit(f'abort: block lost after write -> {keep}')
for d in TARGETS:
    if f'## {d} Dreaming知识串联' in cs:
        sys.exit(f'abort: {d} still present')
print(f'final size: {len(chk)}B (<150000: {len(chk) < TRIGGER}, <145000: {len(chk) < TARGET})')
print('OK')
