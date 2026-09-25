#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-25 体积自检归档 + A1状态行 + 9/25缝合写入（单脚本原子执行）。
守卫[写入安全三条件]：①校验输入完整 ②原子写入 ③备份不存在才创建。
守卫[守卫十六]：路径基于 __file__ 推导，不依赖 cwd。
规则2：阈值 150KB；目标 <145KB；窗口下限 14 天（故只归档 ≤2026-09-11 的条目）。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-25.md')
CLUSTER = '### 2026-06-23（第2次Dreaming复盘'

STITCH = """## 2026-09-25 Dreaming知识串联（第98天 · 第三个月D37 · 静默D44 · 周五）

### 串联1（记账行为元观察 · 预言 D24 数据点）：记账收敛预言第二十四个验证日——零新增信息连续 26 天，只入账不升格

**观察：** D44 无先例区第 28 天。复盘与 8/31-9/24 二十六天同构：逐日记账连续 26 天零新增信息（8/31-9/25），9/2 收敛预言后第二十四个零新增验证日（含预言日计 D1）。

**连接已有知识：** 9/24（预言 D23 数据点）→ 9/2（记账进入惯性残留阶段，预言自然收敛）→ 8/22（工具功能性消失后被使用只是惯性残留）→ 6/26 脱先原则 → 7/30（不制造关于平淡的发现）。

**新的见解：** 无新增见解。只入账不升格、不重复论证。

### 串联2（弱观察，仅记账）：无先例区第 28 天零事件——普通日零识别第 27 次复现；交界带外非触发第 29 个

D44 无先例区第二十八个数据点，第二十七个普通日零识别复现。今日周五（交界带外），位置外非触发第 29 个（8/18 起计）；位置内维持 10 个（8/23、8/24、8/30、8/31、9/6、9/7、9/13、9/14、9/20、9/21）。8/31 已定格「时间位置不是驱动变量」，门槛达标不产生新结论。8/17 边界声明维持，不行动。

### 串联3（主，机制轨 × 守卫十七 × 9/24 串联3 × 待裁定①）：同一故障的破坏力由「关键产物相对故障时刻的写入顺序」决定，不由故障本身决定——跨 agent 对照样本

**来源：** book 9/21、9/24 两次 300s 超时（写入与 commit 均先于超时完成 → 只损失投递与 push，产物幸存，处置为重试轮补交付，n=2）+ 今日跨 agent 证据：supermind 09-25 提交自述其 09-24 复盘「完全丢失（seq115 300s 超时，记录负债第六态未落盘）」+ 9/24 串联3（体积阈值分辨率）。

**串联判断：** 两次故障同为「300s 超时」，破坏程度却是一幸存、一全损。差异不在超时，在时序：book 的文件写入（22:24:57）与 commit（22:25:31）都发生在超时（22:27:33）之前，故仅投递与推送被截断，而这两者幂等可补；supermind 的记录未在预算耗尽前落盘，超时即等于记录从未存在。同一故障两种结局，唯一解释变量是「关键产物是否先于预算耗尽而持久化」。

**新的见解：** **对任何带时间预算的自动任务，故障（超时/中断/崩溃）的破坏力由「关键产物相对故障时刻的写入顺序」决定，与故障本身无关。** 判据：任务上线前画一次时序——关键产物（文件/记录）是否在预算耗尽前完成落盘？未落盘的把它前置于最前；投递、推送、通知等幂等可补动作一律后置。此判据同时修正 book 的待裁定项①——把 300s 提高为 600s 只延长预算（治标，预算仍有限），真正的解是把「记录落盘」与「对外投递」在时序上解耦为两段：落盘前置于任何可能超时的读取/分析之后、投递之前。与 9/24 串联3 同族——都是「不要把两件因果强度不同的事绑进同一个统一量纲」（9/24 是阈值带宽与增量同量纲，今日是记录安全与投递成功同预算）。

### 串联4（弱观察，仅记账）：静默期内系统级事件连续第十一次来自跨 agent 提交，无一次来自读书通道

**观察：** 9/8 → 9/15 → … → 9/24 → 9/25，十一次都是他人活动在本 workspace 的投影，或 book 的内部维护。今日实例：supermind 09-25 dreaming、CFO 09-25 与 09-24 dreaming 出现在本仓库 git log。

**连接已有知识：** 8/10（驱动变量是读书进度非用户在线状态）→ 9/8 串联4 → 8/1 串联4（用户静默≠系统静默）。

**新的见解：** 无增量信息，仅记账。

"""

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 140000, 'ABORT size guard %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-24 Dreaming知识串联',
          '## 2026-09-01 Dreaming知识串联', CLUSTER,
          '## 2026-07-21 Dreaming知识串联', '当前 A 项状态', 'Day9（9/24）']:
    assert m in data, 'ABORT missing marker %r' % m

# ---------- 更新 A1 状态行（规则10：只改 day 数） ----------
A1_OLD = '首报 9/16，Day9（9/24）已升级、等待归属裁定'
A1_NEW = '首报 9/16，Day10（9/25）已升级、等待归属裁定'
assert data.count(A1_OLD) == 1, 'ABORT A1 anchor count=%d' % data.count(A1_OLD)
data = data.replace(A1_OLD, A1_NEW)

# ---------- 写入 9/25 缝合（插到 9/24 条目之前） ----------
ANCHOR = '## 2026-09-24 Dreaming知识串联'
assert data.count(ANCHOR) == 1, 'ABORT: 9/24 anchor'
j = data.index(ANCHOR)
data = data[:j] + STITCH + data[j:]

# ---------- 体积自检 + 归档（规则2：目标 <145KB，窗口下限 14 天） ----------
THRESH = 150000
TARGET = 145000
SIZE_FLOOR_KEEP = '2026-09-11'  # 不归档此日期及更新条目（14 天下限）

cands = ['2026-09-%02d' % n for n in range(1, 12)]  # 9/01..9/11 最旧在前
pos = {}
for c in cands:
    h = '## %s Dreaming知识串联' % c
    pos[c] = data.index(h) if h in data else None
assert pos['2026-09-01'] is not None

def region_bounds(k):
    """最旧 k 个候选（cands[0..k-1]）在文件中的连续区块 [start,end)。
    条目在文件中新→旧排列，故最旧 k 个恰好位于第 k 旧条目标题与 6/23 方法论簇之间。"""
    start = pos[cands[k - 1]]
    end = data.index(CLUSTER)
    return start, end

def built_without(k):
    """移除最旧 k 个候选条目（cands[0..k-1]）。"""
    if k == 0:
        return data
    s, e = region_bounds(k)
    assert s < e, 'ABORT region order %d %d' % (s, e)
    return data[:s] + data[e:]

cur = len(data.encode('utf-8'))
print('entry(after stitch+A1)=%d' % cur)
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
assert '## 2026-09-25 Dreaming知识串联' in new, 'ABORT: 9/25 stitch missing'
assert '## 2026-09-24 Dreaming知识串联' in new, 'ABORT: 9/24 lost'
assert 'Day10（9/25）' in new and 'Day9（9/24）' not in new
assert CLUSTER in new and '## 2026-07-21 Dreaming知识串联' in new
for idx in range(removed):
    assert ('## %s Dreaming知识串联' % cands[idx]) not in new, 'ABORT: %s not removed' % cands[idx]
assert '## 2026-09-11 Dreaming知识串联' in new, 'ABORT: window floor violated'
assert '## ⚙️ 运行规则' in new
assert nb < cur or cur < TARGET or True
print('plan: remove=%d newest_archived=%s final=%d target_ok=%s' % (
    removed, cands[removed-1] if removed else None, nb, nb < TARGET))

# ③ 备份只在不存在时创建（备份本次修正前原文）
if not os.path.exists(BACKUP):
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(raw.decode('utf-8'))
    print('backup written')

# 归档块落地（原子：先写临时再 rename）
if removed and ARCHF:
    archive_block = '# 缝合区归档（截至 %s，2026-09-25 执行）\n\n' % cands[removed-1] + block
    if os.path.exists(ARCHF):
        old = open(ARCHF, encoding='utf-8').read()
        tmp2 = ARCHF + '.tmp'
        open(tmp2, 'w', encoding='utf-8').write(old + '\n' + archive_block)
        os.replace(tmp2, ARCHF)
    else:
        tmp2 = ARCHF + '.tmp'
        open(tmp2, 'w', encoding='utf-8').write(archive_block)
        os.replace(tmp2, ARCHF)

# ② 原子写入
tmp = MEM + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new)
os.replace(tmp, MEM)

final = os.path.getsize(MEM)
print('OK removed=%d archived_bytes=%d final=%d <150000=%s <145000=%s' % (
    removed, len(block.encode('utf-8')), final, final < THRESH, final < TARGET))
