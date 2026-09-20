#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-20 体积自检归档（当日写入后触发）。
规则2：保留「近30天」的 Dreaming 串联条目，其前的归档；方法论簇（6/23-7/21）与 7/12 教训除外。
今日窗口 = 2026-08-22 .. 2026-09-20 → 归档 8/21、8/20 两条。
守卫：[写入安全三条件] ①校验输入完整 ②原子写入 ③备份不存在才创建。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-20.md')
ARCH = os.path.join(ARCH_DIR, 'stitching-archive-through-2026-08-21.md')

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 150000, 'ABORT: size guard, file too small %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-20 Dreaming知识串联',
          '## 2026-08-22 Dreaming知识串联', '## 2026-07-12 系统性教训',
          '## E. 协议状态', '## F. 节律模式验证进度']:
    assert m in data, 'ABORT: missing marker %r' % m

H21 = '## 2026-08-21 Dreaming知识串联'
H22 = '## 2026-08-22 Dreaming知识串联'
H20 = '## 2026-08-20 Dreaming知识串联'
H623 = '### 2026-06-23（第2次Dreaming复盘'
for h in (H21, H22, H20, H623):
    assert data.count(h) == 1, 'ABORT: anchor %r count != 1' % h

i1, e1 = data.index(H21), data.index(H22)
i2, e2 = data.index(H20), data.index(H623)
assert i1 < e1, 'ABORT: bad anchors 8/21'
assert i2 < e2, 'ABORT: bad anchors 8/20'
assert i1 < i2, 'ABORT: unexpected order'
block1 = data[i1:e1]   # 8/21
block2 = data[i2:e2]   # 8/20
assert '第三个月首日' in block1, 'ABORT: 8/21 content missing'
assert '第二个月收官日' in block2, 'ABORT: 8/20 content missing'
assert len(block1.encode('utf-8')) > 1500 and len(block2.encode('utf-8')) > 2500, 'ABORT: block too small'

# 先删靠后的 block2，再删 block1
new = data[:i2] + data[e2:]
assert new.count(H20) == 0
i1, e1 = new.index(H21), new.index(H22)
new = new[:i1] + new[e1:]

# 结构校验
assert new.count('## 知识缝合区') == 1, 'ABORT: stitching header damaged'
assert new.count(H20) == 0 and new.count(H21) == 0, 'ABORT: blocks not removed'
assert H22 in new and H623 in new and '## E. 协议状态' in new and '## F. 节律模式验证进度' in new
assert '## 2026-09-19 Dreaming知识串联' in new and '## 2026-09-20 Dreaming知识串联' in new
assert len(new.encode('utf-8')) < len(raw), 'ABORT: no shrink'

archive_block = (
    '# 缝合区归档（截至 2026-08-21，2026-09-20 执行）\n\n'
    + '## 2026-08-20 Dreaming知识串联（第62天 · 第二个月收官日 · 静默D8 · 收官清单分支②命中）\n'
    + block2.split('\n', 1)[1]
    + '\n' + block1
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
