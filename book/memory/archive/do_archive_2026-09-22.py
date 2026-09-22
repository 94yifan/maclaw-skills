#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dreaming 2026-09-22 体积自检归档 + 规则2修正 + 9/22缝合写入（单脚本原子执行）。
修正：规则2 作用域由「固定 30 天窗口」改为「体积目标 <145KB + 14 天下限」（守卫十：阈值不可达）。
归档：8/23-8/31（永久保留集：head + 6/23-7/21 方法论簇 + 7/12 教训）。
守卫[写入安全三条件]：①校验输入完整 ②原子写入 ③备份不存在才创建。
守卫[守卫十六]：路径基于 __file__ 推导，不依赖 cwd。
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(BASE, 'MEMORY.md')
ARCH_DIR = os.path.join(BASE, 'memory', 'archive')
BACKUP = os.path.join(ARCH_DIR, 'MEMORY-backup-2026-09-22.md')
ARCHF = os.path.join(ARCH_DIR, 'stitching-archive-through-2026-08-31.md')

# ---------- 9/22 缝合区内容 ----------
STITCH = """## 2026-09-22 Dreaming知识串联（第95天 · 第三个月D34 · 静默D41 · 周二）

### 串联1（记账行为元观察 · 预言 D21 数据点）：记账收敛预言第二十一个验证日——零新增信息连续 23 天，只入账不升格

**观察：** D41 无先例区第 25 天。复盘与 8/31-9/21 二十三天同构：逐日记账连续 23 天零新增信息（8/31-9/22），9/2 收敛预言后第二十一个零新增验证日（含预言日计 D1）。

**连接已有知识：** 9/21（预言 D20 数据点）→ 9/2（记账进入惯性残留阶段，预言自然收敛）→ 8/22（工具功能性消失后被使用只是惯性残留）→ 6/26 脱先原则 → 7/30（不制造关于平淡的发现）。

**新的见解：** 无新增见解。只入账不升格、不重复论证。

### 串联2（弱观察，仅记账）：无先例区第 25 天零事件——普通日零识别第 24 次复现；交界带外非触发第 26 个

D41 无先例区第二十五个数据点，第二十四个普通日零识别复现。今日周二（交界带外），位置外非触发第 26 个（8/18 起计）；位置内维持 10 个（8/23、8/24、8/30、8/31、9/6、9/7、9/13、9/14、9/20、9/21）。8/31 已定格「时间位置不是驱动变量」，门槛达标不产生新结论。8/17 边界声明维持，不行动。

### 串联3（主，机制轨 × 守卫十 × 运行规则2）：守卫十的第三个实例——阈值型规则的「可达性」缺失：作用域压到永久保留集后，阈值永久不可达

**来源：** 今日体积自检（MEMORY.md 152,646B > 150KB）+ 运行规则第 2 条（阈值 150KB + 滚动 30 天窗口）+ 守卫十（2026-09-15 立：校验目标不得互斥）+ 9/19 串联3（规则内阈值与作用域两种时间坐标互斥）。

**串联判断：** 9/19 发现规则 2 的互斥是「阈值滚动（KB）vs 作用域冻结（绝对日期）」，当日把作用域改成滚动窗口。今日发现滚动本身也有边界：作用域底部一旦压到永久保留集（head 12KB + 6/23-7/21 方法论簇 ~55KB），可归档对象就耗尽——窗口每日前移，但窗口外已无可删条目，150KB 阈值从此永久不可达。文件停在 152,646B，规则却再无动作可执行。这是守卫十的第三个实例，射程逐次上移：第一次在 pipeline 校验体系（9/15 黄天鹅），第二次在规则文本自身（9/19），第三次在「规则与其资源底数」的关系。

**新的见解：** **阈值型规则除「阈值—作用域不互斥」外，还需校验「可达性」——触发后，作用域内是否必然存在可执行对象？** 判据：写任何「超过 X 就清理 Y」的规则，先算「永久保留集 + 最小区间内 Y 的下限」是否 < X；若 ≥ X，规则上线即注定在某个日期后假活。修复方向不是改阈值（治标），是把作用域从「固定天数」改为「尺寸目标 + 天数字下限」（保留至 <145KB 的最短窗口，但不短于 14 天）。今日据此修正运行规则第 2 条，并当场归档 8/23-8/31（守卫十八：修复绑在发现它的会话）。

### 串联4（主，时间轨 × 守卫十七）：交付事故「待验证」标记在第二日获得部分证据——同一 cron 连续两日启动延迟，延迟与超时须分列为两个机制

**来源：** 9/21 运行事故记录（22:05 定时、22:39 实际启动，延迟≈34min；随后运行内触达 300s 超时，切开「写入完成」与「投递完成」）+ 今日同 cron（22:05 定时、约 22:23 实际启动，延迟≈18min）。

**串联判断：** 9/21 只有 n=1，按守卫十七只标「待验证/待裁定」。今日出现第二个数据点：延迟再次发生。但必须区分两个不同机制的故障——①调度启动延迟（调度侧，两日均出现，n=2）；②运行内 300s 预算超时（执行侧，9/21 出现、今日尚未触顶）。把两者合并成「超时问题」会掩盖各自的修复方向（前者查调度器/队列，后者削减输入体积或提高预算）。

**新的见解：** 无新增结论，仅记账 + 标记（n=2 < 守卫十五门槛 3，不下结论）。方法上记一条：多个同日出现的异常若机制不同，先分机制再比较数量，否则一致性检查（守卫八）会被假样本污染——「同一现象两次」与「两个现象各一次」的处置完全不同。

### 串联5（弱观察，仅记账）：静默期内系统级事件连续第九次来自跨 agent 提交，无一次来自读书通道

**观察：** 9/8 → 9/15 → 9/16 → 9/17 → 9/18 → 9/19 → 9/20 → 9/21 → 9/22，九次都是他人活动在本 workspace 的投影，或 book 的内部维护。今日实例：brain-mining / strategic-planner / lanshi / social-crawler 各自 09-22 dreaming 或日志出现在本仓库 git status。

**连接已有知识：** 8/10（驱动变量是读书进度非用户在线状态）→ 9/8 串联4 → 8/1 串联4（用户静默≠系统静默）。

**新的见解：** 无增量信息，仅记账。

"""

data = open(MEM, encoding='utf-8').read()
raw = data.encode('utf-8')

# ① 校验输入完整
assert len(raw) > 150000, 'ABORT size guard %d' % len(raw)
for m in ['## ⚙️ 运行规则', '## 知识缝合区', '## 2026-09-21 Dreaming知识串联',
          '## 2026-08-31 Dreaming知识串联', '### 2026-06-23（第2次Dreaming复盘',
          '## 2026-07-21 Dreaming知识串联', '当前 A 项状态']:
    assert m in data, 'ABORT missing marker %r' % m

# ---------- 修正规则2 ----------
R2_OLD = ('超 150KB 即归档旧缝合区（保留近 30 天 + 全部方法论条目）。归档范围（**滚动**，2026-09-19 修正）：'
          '早于「近 30 天窗口」的 Dreaming 串联条目（6/23-7/21 方法论簇、7/12 系统性教训除外）。')
assert data.count(R2_OLD) == 1, 'ABORT rule2 anchor count=%d' % data.count(R2_OLD)
R2_NEW = ('超 150KB 即归档旧缝合区（永久保留全部方法论条目 + 近期串联）。归档范围（**滚动 + 体积目标**，2026-09-22 修正）：'
          '不以固定天数为准，而以体积目标 <145KB 为准——自最旧条目起归档直至 <145KB，保留窗口不短于 14 天；'
          '6/23-7/21 方法论簇、7/12 系统性教训永久保留。**修正依据：** 原「近 30 天」窗口压到永久保留集'
          '（head 12KB + 方法论簇 ~55KB）后，可归档对象耗尽，150KB 阈值永久不可达'
          '（守卫十：阈值与作用域互斥 → 规则假活）；故作用域改为尺寸驱动。')
data = data.replace(R2_OLD, R2_NEW)

# ---------- 更新 A1 状态行（规则10：只改 day 数） ----------
A1_OLD = '首报 9/16，Day6（9/21）已升级、等待归属裁定'
A1_NEW = '首报 9/16，Day7（9/22）已升级、等待归属裁定'
if data.count(A1_OLD) == 1:
    data = data.replace(A1_OLD, A1_NEW)
else:
    print('WARN: A1 status anchor count=%d (skip)' % data.count(A1_OLD))

# ---------- 归档 8/23-8/31（连续块） ----------
H31 = '## 2026-08-31 Dreaming知识串联'
H623 = '### 2026-06-23（第2次Dreaming复盘'
assert data.count(H31) == 1 and data.count(H623) == 1, 'ABORT: August anchors not unique'
i, e = data.index(H31), data.index(H623)
assert i < e, 'ABORT: bad anchors order'
block = data[i:e]
assert '静默D19' in block and '静默D11' in block, 'ABORT: August range incomplete'
assert '位置语义的退役是整体性的' in block, 'ABORT: 8/24 entry missing'
assert len(block.encode('utf-8')) > 15000, 'ABORT: August block too small %d' % len(block.encode('utf-8'))

new = data[:i] + data[e:]

# ---------- 写入 9/22 缝合（插到 9/21 条目之前） ----------
ANCHOR = '## 2026-09-21 Dreaming知识串联'
assert new.count(ANCHOR) == 1, 'ABORT: 9/21 anchor'
j = new.index(ANCHOR)
new = new[:j] + STITCH + new[j:]

# ---------- 结构校验 ----------
assert new.count('## 知识缝合区') == 1, 'ABORT: stitch header damaged'
assert H31 not in new, 'ABORT: August block not removed'
assert '## 2026-09-22 Dreaming知识串联' in new and ANCHOR in new
assert '### 2026-06-23（第2次Dreaming复盘' in new and '## 2026-07-21 Dreaming知识串联' in new
assert '## ⚙️ 运行规则' in new and '滚动 + 体积目标' in new
nb = len(new.encode('utf-8'))
assert nb < len(raw), 'ABORT: no shrink old=%d new=%d' % (len(raw), nb)

# ③ 备份只在不存在时创建（备份的是本次修正前原文）
if not os.path.exists(BACKUP):
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(data)
    print('backup written')

# 归档块落地
archive_block = '# 缝合区归档（截至 2026-08-31，2026-09-22 执行）\n\n' + block
if os.path.exists(ARCHF):
    with open(ARCHF, 'a', encoding='utf-8') as f:
        f.write('\n' + archive_block)
else:
    with open(ARCHF, 'w', encoding='utf-8') as f:
        f.write(archive_block)

# ② 原子写入
tmp = MEM + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new)
os.replace(tmp, MEM)

# 写入后复检（规则2）
final = os.path.getsize(MEM)
print('OK old=%d new=%d (archived=%d, stitch=+%d) final=%d threshold_ok=%s' % (
    len(raw), nb, len(block.encode('utf-8')), len(STITCH.encode('utf-8')),
    final, final < 150000))
