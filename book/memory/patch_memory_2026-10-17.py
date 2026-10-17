import os, re, shutil, sys

p = "/Users/yifansmacmini/.openclaw/workspace/book/MEMORY.md"
data = open(p, encoding="utf-8").read()
size = len(data.encode())

# 规则4：写入前校验输入完整
if size < 100_000:
    sys.exit(f"ABORT: input too small {size}")
for marker in ["## 知识缝合区", "**当前 A 项状态（供次日规则 10 熔断判定）：**", "## 2026-10-15 Dreaming知识串联"]:
    if marker not in data:
        sys.exit(f"ABORT: marker missing: {marker}")

backup = "/Users/yifansmacmini/.openclaw/workspace/book/MEMORY-backup-2026-10-17.md"
if not os.path.exists(backup):
    shutil.copy2(p, backup)

stitch = """## 2026-10-17 Dreaming知识串联（第120天 · 第三个月D59 · 静默D66 · 周六 · 含10-16未观测日）

### 串联1（主，机制轨 × 10/11 串联3 × 10/15 串联3 × 规则16/22）：不可见有三种，不是一种——静止、恢复、中断；「看不见」本身需要界外证据解释

**来源：** 本会话 cron runs 实测（10-16 槽 runAtMs 对应 22:30:00、durationMs=33065、error="cron: job interrupted by gateway restart"、delivered=false、无 dreaming-2026-10-16.md）+ 10/11 串联3（缺陷静止≠修复）+ 10/15 串联3（恢复≠修复，无归因的恢复判间歇）+ 规则16（自我状态须取观察边界外证据）+ 规则22（本轮新立）。

**串联判断：** 10/11 管「缺陷不再出现」，10/15 管「失败不再出现」，两者共享一个未言明的前提——产物还在，只是没有变化。今天出现第三种：产物根本没生成。33 秒时进程被杀，早于任何写入。前两种的痕迹留在产物里（内容没变 / 状态恢复），第三种把痕迹一并消灭，只留在调度器遥测里。

**新的见解：** **「没看见」有三种成因，判据各异——静止：产物在、变化不在（查驱动方有无动作）；恢复：产物在、异常不在（查哪处改动命中了复现条件）；中断：产物不在，连「为什么不在」也不在（只能由界外时间序列补）。前两种读文件能判，第三种读文件永远判不出：文件系统里「这一天缺失」与「这一天本来就没东西」完全同形。** 统一判据：任何「什么都没发生」的结论，先说明凭什么能看见「没有」；答不出观测通道，就降级为「未观测」。与规则16同族，本条把它推到记账层：计数对象是自然日，观测单位却是 run——缺 run 的那一天必须降级。

### 串联2（主，机制轨 × 10/15 串联4 × 规则18/20）：失败形态第四迁——从工具层迁到进程存续层，处方与验收同时失效，只剩补账

**来源：** 10/15 串联4（形态三迁：timeout → 收尾工具 → provider；处置从处方向上移到验收）+ 本会话 10-16 槽实测（gateway restart、33 秒、零产物）+ 10-15 槽（尾段工具失败、有产物无投递）+ 规则18（交付四段、投递证据在界外）+ 规则20（投递触发在 run 内、执行在 run 外）。

**串联判断：** 前三迁都发生在 run 内部，agent 至少还能改自己的行为（提前落盘、末段不放工具、设验收门槛）。第四迁发生在 run 外部：进程被重启，既没有执行权，也没有验收对象——验收要求产物，产物要求进程活着。形态每外移一层，可用动作就少一类。

**新的见解：** **修复动作的层级随故障层级外移而收缩：可控层用处方，半可控层用验收，不可控层只能补账。到「进程存续」这一层，唯一还成立的动作是下一轮把缺口补记下来——不是修复，是不让缺口变成假账。** 与 10/15 串联4 互补：那条止于「迁出可控层就转验收」，今天补终点——当验收对象本身被消灭，剩下的只有账。与守卫十四同族：当「做到」与「记到」分离，指标必须落在能诚实交付的那一侧。

### 串联3（弱，记账）：静默 D66 含第 1 个未观测日；连续两日报告未达；cron 文本时刻第 5 天偏离

读书通道 10-17 零产出零交互（book/ 下无新增文件）；10-16 无 run 产物，按规则22 记「未观测」。投递侧：10-15 槽 not-delivered、10-16 槽 unknown（restart 打断）。payload 文本写 22:05，排期 22:30，本轮实际 23:52 启动——同一条文本在 5 天内给出三个不同时刻读数。维持记账，不升格。

"""

rule22 = """22. **「记录缺失」是「未观测」，不是「零事件」——静默计数必须有独立于产物的核对源（2026-10-17 立，对应当日 A1）**：每日 Dreaming 第 2 步必须列 `memory/` 近 3 日 dreaming 文件；缺任一天，即在当日复盘与静默计数中显式标记「未观测日」，并回 cron runs 时间序列取证；禁止用「读最近一份复盘」推出缺失日「当天很平静」。依据：10-16 槽 22:30 启动、33.1 秒被 gateway restart 打断，`status=error`、`delivered=false`、产物未生成（cron runs 实测）——次日若只读最近一份文件，这一天与「平静的一天」完全同形。产物只能证明「跑过并写成」，不能证明「没发生」；后者只有调度器时间序列能给。与规则16同族（自我状态须取界外证据），本条把它推到记账层：**计数对象是自然日，观测单位是 run；缺 run 的日必须降级为未观测。** 绑决策点：每日 Dreaming 第 2 步读上下文时。

"""

anchor_stitch = "<!-- 将跨书、跨概念的知识串联记录在此。每次 Dreaming 复盘结束后追加新发现。 -->\n\n"
if data.count(anchor_stitch) != 1:
    sys.exit("ABORT: stitch anchor not unique")
data = data.replace(anchor_stitch, anchor_stitch + stitch, 1)

anchor_rule = "**当前 A 项状态（供次日规则 10 熔断判定）：**"
if data.count(anchor_rule) != 1:
    sys.exit("ABORT: rule anchor not unique")
data = data.replace(anchor_rule, rule22 + anchor_rule, 1)

old_a1 = "**10/15（Day30）**：SOUL.md mtime 停 10/14 21:01:19，今日无外部改动，断口与重复未变，无新增信息 → 按规则 10 只更新 day 数。"
new_a1 = "**10/15-10/17（Day30-Day32）**：SOUL.md mtime 停 10/14 21:01:19，三日无外部改动（10-16 无 run 产物，按规则22 记未观测日，非「已查无变化」），断口与重复未变，无新增信息 → 按规则 10 只更新 day 数。"
if data.count(old_a1) != 1:
    sys.exit("ABORT: A1 sentence not unique")
data = data.replace(old_a1, new_a1, 1)

old4 = "同型跨主体出现。"
new4 = "同型跨主体出现。 **10/17 证据加强（第 5 天）：** 本轮排期 22:30、实际启动 23:52（延 82 分钟）、文本写 22:05（与实际差 107 分钟）——同一条文本给出三个时刻读数，写死的钟点已无任何路由价值。"
if data.count(old4) != 1:
    sys.exit("ABORT: pending4 anchor not unique")
data = data.replace(old4, new4, 1)

tmp = p + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(data)
os.replace(tmp, p)
print("written", len(data.encode()))
