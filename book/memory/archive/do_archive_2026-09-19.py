#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-19 体积自检归档。
规则：MEMORY.md 超 150KB 即归档「保留近30天」之前的 Dreaming 串联条目（方法论簇除外）。
守卫：[写入安全三条件] ①校验输入完整 ②原子写入 ③备份不存在才创建。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-19.md')
ARCH = os.path.join(ARCH_DIR, 'stitching-archive-through-2026-08-19.md')

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 150000, 'ABORT: size guard, file too small %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-18 Dreaming知识串联',
          '## 2026-09-13 Dreaming知识串联', '## 2026-07-12 系统性教训']:
    assert m in data, 'ABORT: missing marker %r' % m

start_anchor = '## 2026-08-16 Dreaming知识串联'
end_anchor = '## E. 协议状态'
si = data.index(start_anchor)
ei = data.index(end_anchor)
assert si < ei, 'ABORT: bad anchors'
block = data[si:ei]
assert '## 2026-08-19 Dreaming' in block, 'ABORT: 8/19 missing from block'
assert '## 2026-08-20' not in block, 'ABORT: 8/20 leaked into block'
assert len(block.encode('utf-8')) > 5000, 'ABORT: block too small'

new = data[:si] + data[ei:]
assert new.count('## 知识缝合区') == 1, 'ABORT: stitching header damaged'
assert '## E. 协议状态' in new, 'ABORT: tail lost'

# ③ 备份只在不存在时创建
if not os.path.exists(BACKUP):
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(data)

# 归档（不存在则创建）
if os.path.exists(ARCH):
    with open(ARCH, 'a', encoding='utf-8') as f:
        f.write('\n' + block)
else:
    with open(ARCH, 'w', encoding='utf-8') as f:
        f.write('# 缝合区归档（截至 2026-08-19，2026-09-19 执行）\n\n' + block)

# ② 原子写入
tmp = MEM + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new)
os.replace(tmp, MEM)

print('OK old=%d new=%d archived_block=%d archived_total=%d' % (
    len(raw), len(new.encode('utf-8')), len(block.encode('utf-8')),
    os.path.getsize(ARCH)))
