#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-21 体积自检归档（当日写入后触发）。
规则2：保留「近30天」的 Dreaming 串联条目，其前的归档；方法论簇（6/23-7/21）与 7/12 教训除外。
今日窗口 = 2026-08-23 .. 2026-09-21 → 归档 8/22 一条。
守卫：[写入安全三条件] ①校验输入完整 ②原子写入 ③备份不存在才创建。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-21.md')
ARCH = os.path.join(ARCH_DIR, 'stitching-archive-through-2026-08-22.md')

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 150000, 'ABORT: size guard, file too small %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-21 Dreaming知识串联',
          '## 2026-08-22 Dreaming知识串联', '## 2026-08-23 Dreaming知识串联',
          '## 2026-08-26 Dreaming知识串联', '## 2026-07-12 系统性教训',
          '当前 A 项状态']:
    assert m in data, 'ABORT: missing marker %r' % m

H22 = '## 2026-08-22 Dreaming知识串联'
H23 = '## 2026-08-23 Dreaming知识串联'
H26 = '## 2026-08-26 Dreaming知识串联'
for h in (H22, H23, H26):
    assert data.count(h) == 1, 'ABORT: anchor %r count != 1' % h

i, e = data.index(H22), data.index(H23)
assert i < e, 'ABORT: bad anchors'
block = data[i:e]
assert '长静默的三代管理形态' in block, 'ABORT: 8/22 content missing'
assert 'D-day 计数的语义退化' in block, 'ABORT: 8/22 content incomplete'
assert len(block.encode('utf-8')) > 2500, 'ABORT: block too small'

new = data[:i] + data[e:]

# 结构校验
assert new.count('## 知识缝合区') == 1, 'ABORT: stitching header damaged'
assert new.count(H22) == 0, 'ABORT: block not removed'
assert H23 in new and H26 in new and '## 2026-07-12 系统性教训' in new
assert '## 2026-09-21 Dreaming知识串联' in new and '## 2026-09-20 Dreaming知识串联' in new
assert len(new.encode('utf-8')) < len(raw), 'ABORT: no shrink'

archive_block = (
    '# 缝合区归档（截至 2026-08-22，2026-09-21 执行）\n\n'
    + block
)

# ③ 备份只在不存在时创建
if not os.path.exists(BACKUP):
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(data)

if os.path.exists(ARCH):
    with open(ARCH, 'a', encoding='utf-8') as f:
        f.write('\n' + archive_block)
else:
    with open(ARCH, 'w', encoding='utf-8') as f:
        f.write(archive_block)

# ② 原子写入
tmp = MEM + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new)
os.replace(tmp, MEM)

print('OK old=%d new=%d archived=%d arch_total=%d' % (
    len(raw), len(new.encode('utf-8')),
    len(archive_block.encode('utf-8')), os.path.getsize(ARCH)))
