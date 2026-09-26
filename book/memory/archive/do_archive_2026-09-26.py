#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-26 体积自检归档（重试轮，仅体积动作）。
9/26 缝合与 A1 day11 已由首轮写入，本脚本不重复写入，只做规则2「写入后复检」触发的归档。
守卫[写入安全三条件]：①校验输入完整 ②原子写入 ③备份不存在才创建（备份首轮已建，跳过）。
守卫[守卫十六]：路径基于 __file__ 推导，不依赖 cwd。
规则2：阈值 150KB；目标 <145KB；窗口下限 14 天（故只归档 <=2026-09-11 的条目）。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-26.md')
CLUSTER = '### 2026-06-23（第2次Dreaming复盘'

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 140000, 'ABORT size guard %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-26 Dreaming知识串联',
          '## 2026-09-25 Dreaming知识串联', '## 2026-09-06 Dreaming知识串联',
          CLUSTER, '## 2026-07-21 Dreaming知识串联', '当前 A 项状态', 'Day11（9/26）']:
    assert m in data, 'ABORT missing marker %r' % m

THRESH = 150000
TARGET = 145000
# 候选：当前最旧的可归档条目（9/12 及更新属 14 天下限内，不归档）
cands = ['2026-09-%02d' % n for n in range(6, 12)]  # 9/06..9/11 最旧在前
pos = {}
for c in cands:
    h = '## %s Dreaming知识串联' % c
    pos[c] = data.index(h) if h in data else None
assert pos['2026-09-06'] is not None, 'ABORT: 9/06 anchor missing'


def region_bounds(k):
    """最旧 k 个候选（cands[0..k-1]）在文件中的连续区块 [start,end)。
    条目在文件中新→旧排列，故最旧 k 个恰好位于第 k 旧条目标题与 6/23 方法论簇之间。"""
    start = pos[cands[k - 1]]
    end = data.index(CLUSTER)
    return start, end


def built_without(k):
    if k == 0:
        return data
    s, e = region_bounds(k)
    assert s < e, 'ABORT region order %d %d' % (s, e)
    return data[:s] + data[e:]


cur = len(raw)
print('entry=%d threshold_hit=%s' % (cur, cur >= THRESH))
removed = 0
while cur >= TARGET and removed < len(cands):
    removed += 1
    cur = len(built_without(removed).encode('utf-8'))
    print('  remove %d -> %d' % (removed, cur))

new = built_without(removed)
nb = len(new.encode('utf-8'))

if removed:
    last = cands[removed - 1]
    start, end = region_bounds(removed)
    block = data[start:end]
    ARCHF = os.path.join(ARCH_DIR, 'stitching-archive-through-%s.md' % last)
else:
    block, ARCHF = '', None

# ---------- 结构校验 ----------
assert new.count('## 知识缝合区') == 1, 'ABORT: stitch header damaged'
assert '## 2026-09-26 Dreaming知识串联' in new, 'ABORT: 9/26 stitch lost'
assert '## 2026-09-25 Dreaming知识串联' in new, 'ABORT: 9/25 lost'
assert '## 2026-09-12 Dreaming知识串联' in new, 'ABORT: window floor violated'
assert CLUSTER in new and '## 2026-07-21 Dreaming知识串联' in new, 'ABORT: cluster lost'
for idx in range(removed):
    assert ('## %s Dreaming知识串联' % cands[idx]) not in new, 'ABORT: %s not removed' % cands[idx]
assert '## ⚙️ 运行规则' in new and 'Day11（9/26）' in new, 'ABORT: head/status damaged'
print('plan: remove=%d newest_archived=%s final=%d target_ok=%s' % (
    removed, cands[removed - 1] if removed else None, nb, nb < TARGET))

# ③ 备份只在不存在时创建（首轮已建 145,509B 版本，此处应跳过）
if not os.path.exists(BACKUP):
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(data)
    print('backup written')
else:
    print('backup exists, skip (%d)' % os.path.getsize(BACKUP))

# 归档块落地（原子：先写临时再 rename）
if removed and ARCHF:
    archive_block = '# 缝合区归档（截至 %s，2026-09-26 执行）\n\n' % cands[removed - 1] + block
    if os.path.exists(ARCHF):
        old = open(ARCHF, encoding='utf-8').read()
        tmp2 = ARCHF + '.tmp'
        open(tmp2, 'w', encoding='utf-8').write(old + '\n' + archive_block)
        os.replace(tmp2, ARCHF)
    else:
        tmp2 = ARCHF + '.tmp'
        open(tmp2, 'w', encoding='utf-8').write(archive_block)
        os.replace(tmp2, ARCHF)
    print('archived -> %s' % os.path.basename(ARCHF))

# ② 原子写入
tmp = MEM + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new)
os.replace(tmp, MEM)

final = os.path.getsize(MEM)
print('OK removed=%d archived_bytes=%d final=%d <150000=%s <145000=%s' % (
    removed, len(block.encode('utf-8')), final, final < THRESH, final < TARGET))
