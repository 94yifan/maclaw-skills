#!/usr/bin/env python3
import re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCDIR = os.path.join(BASE, 'memory', 'archive')
ARC = os.path.join(ARCDIR, 'stitching-archive-through-2026-09-22.md')
BAK = os.path.join(ARCDIR, 'MEMORY-backup-2026-10-06.md')

# --- 条件①：校验输入完整 ---
if not os.path.exists(MEM):
    sys.exit('abort: MEMORY.md missing')
raw = open(MEM, 'rb').read()
if len(raw) < 100000:
    sys.exit(f'abort: MEMORY.md too small ({len(raw)}B) - refusing to operate')
s = raw.decode('utf-8')
for marker in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-10-06 Dreaming知识串联', '19. **决策请求的送达不得只挂交付链路末段']:
    if marker not in s:
        sys.exit(f'abort: marker missing -> {marker}')

# --- 条件③：备份只在不存在时创建 ---
if not os.path.exists(BAK):
    open(BAK, 'wb').write(raw)
    print(f'backup created: {BAK} ({len(raw)}B)')
else:
    print(f'backup exists, not overwritten: {BAK}')

# --- 定位并摘除 9/21、9/22 两块 ---
heads = [(m.start(), m.group(1)) for m in re.finditer(r'^## (2026-\d\d-\d\d) Dreaming知识串联.*$', s, re.M)]
idx = {day: i for i, (_, day) in enumerate(heads)}
targets = ['2026-09-21', '2026-09-22']
for t in targets:
    if t not in idx:
        sys.exit(f'abort: target block {t} not found')

removed_chunks = []
for t in targets:
    i = idx[t]
    start = heads[i][0]
    end = heads[i+1][0] if i+1 < len(heads) else len(s)
    removed_chunks.append(s[start:end])

removed = ''.join(removed_chunks)
new_s = s
for t in sorted(targets, key=lambda x: idx[x], reverse=True):
    i = idx[t]
    start = heads[i][0]
    end = heads[i+1][0] if i+1 < len(heads) else len(s)
    new_s = new_s[:start] + new_s[end:]

new_b = new_s.encode('utf-8')

# --- 归档文件追加（不覆盖既有内容）---
header = '\n\n<!-- ==== archive batch 2026-10-06: 9/21-9/22 ==== -->\n\n'
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
if '## 2026-10-06 Dreaming知识串联' not in chk.decode('utf-8'):
    sys.exit('abort: new block lost after write')
if '2026-09-21 Dreaming知识串联' in chk.decode('utf-8'):
    sys.exit('abort: 9/21 still present')
print('OK')
