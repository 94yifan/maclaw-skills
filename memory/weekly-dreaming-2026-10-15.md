# Weekly Dreaming | 2026-10-15（周四·非排期触发）

本周跨度：2026-10-12（一）→ 2026-10-15（四），4 天（部分周：本轮 dreaming-omni 在周四 22:44 触发，排期本为周日 22:42）
范围：仅 main workspace（Omni）。遵守隔离原则，未读取任何 SubAgent 文件内容；系统巡检只取文件名 / 时间戳 / cron 与 run 元数据。
数据源：`openclaw tasks list` + 只读查询 `~/.openclaw/state/openclaw.sqlite` 的 `task_runs` / `cron_jobs`（`-readonly`，无写操作）。

---

## A. 本周执行汇总

### 1. main 本周执行

| 日期 | 事件 | 结果 |
|------|------|------|
| 10-13 | 曼拾 logo 资产导出（SVG→PNG，白底/透明底/深色底共 8 个文件） | 已交付 |
| 10-13 | 蓝氏每周二提醒 + 人群测试双周提醒（cron，main） | ok / ok |
| 10-14 | 曼拾名片效果图 + PPT 背景 6 版 + 品牌文化一页 + 品牌释义 v3/v4 + 五心与凤凰叙事 | 已交付（v4 待逸凡确认可读性） |
| 10-14 | 固化 skill `manshi-visual-layout`（逸凡授权，CLI apply 成功） | 已装 `skills/manshi-visual-layout/` |
| 10-15 | 模型切换到 DeepSeek V4.1 Flash（`deepseek/deepseek-flash`），全局默认 + SOUL/MEMORY 同步 | 已生效 |
| 10-15 | 本轮 dreaming-omni（非排期触发，原因待确认） | running |

main 本周落账 3 个 daily（10-13 / 10-14 / 10-15）；10-12 无 daily（零交互日，仅有 cron 提醒，非故障）。

### 2. 全量 run 统计（10-12 00:00 → 10-15 22:45，北京时间）

**65 次，42 成功 / 22 失败 / 1 running → 失败率 33.8%**（上周 101 次 / 24 失败 / 23.8%）

| 日期 | run | 失败 | 成功 |
|------|:--:|:--:|:--:|
| 10-12 | 16 | 4 | 12 |
| 10-13 | 15 | 3 | 12 |
| 10-14 | 14 | 2 | 12 |
| 10-15 | 20 | **13** | 6 |

按主体：ceo 11/7、social-crawler 15/5、supermind 6/3、book 4/3、lanshi 14/1、cfo 4/1、brain-mining 4/1、strategic-planner 4/1、main 3/0。

**结构判断：本周失败高度集中在 10-15 一天（13/20，65%）。10-12/13/14 三天 9 次失败全在 dreaming 集群，非 dreaming 业务链 9/9 全绿。**

### 3. 失败形态：一周内三次迁移

| 形态 | 时间 | 样本 |
|------|------|------|
| 工具步自证（sqlite3 读 state DB / 文件量测） | 10-12 / 10-13 | sp、bm、ceo、book（`print text → run sqlite3 → failed`） |
| Process 异步（`Process: <slug> failed`） | 10-14 / 10-15 | cfo cool-trail 489.8s、ceo nova-rook 204.6s、book quick-river 226.9s、supermind fresh-slug 264.5s / plaid-rook 218.2s |
| provider 层 | 10-15 | lanshi 与 social-crawler 各 1 次 `LLM request failed`（389s）；`model-call-started` 超时 120s×4（charm-cdp-warm）、300s×3（birthday-anniversary-check） |

**10-15 早间业务链受损情况（关键）：**
- 08:00 birthday-anniversary-check 连失败 3 次（300s model-call 超时）→ 08:21 第 4 次成功（自动重试救回）
- 10:45 charm-cdp-warm 连失败 4 次（120s 超时）
- 10:55 蓝氏每日TODO提醒 失败（`LLM request failed`，389s）→ **无后续重试**
- 11:03 tea-daily-report 失败（`LLM request failed`，389s）→ **无后续重试**

### 4. 上周三项配置级建议：本周全部落地（首次破零）

| 建议 | 状态 | 证据 |
|------|:----:|------|
| dreaming 拆窗 | ✅ | 由 22:00–22:06 挤窗改为 22:00 / 06 / 12 / 18 / 24 / 30 / 36 / 42，每 6 分钟一个 |
| timeout 300→600 | ✅ | 8 个 dreaming job 全部 `payload_timeout_seconds=600` |
| 打开 failureAlert | ✅ | 8 个 dreaming job `failure_alert_after=3`；10-15 22:38 dreaming-ceo 首次触发（连续四周零通知的静默被打破） |

这是连续三周「配置级建议落地率 0/3」后的第一次全部执行。

### 5. 输出层（仅文件名 + 时间戳）

- 8 个分身 dreaming：10-12 至 10-15 **32/32 齐全** ✅
- social-crawler 微博日报 **4/4**，其中 10-15 那份 13:20 落盘（常态 11:04，延迟约 2h16m，且体积最大 10436B）——对应上面那次 run 失败
- lanshi daily 4/4，10-15 那份 19:11 落盘（与常态一致，晚间 19:10 链正常）
- strategic-planner 本周 dream 4/4 + daily 1 份（10-15），不再是上周的最弱环

### 6. 系统层

- crontab 保持为空 ✅；/tmp 无残留脚本（0 个）✅
- GitHub 同步 ✅：`git log -1 github/main` == HEAD（cc2b121），推送已恢复正常（上周还在超时）
- 未提交项：MEMORY.md / SOUL.md / plugins/deepseek/catalog.json（V4.1 模型行）+ 新增 memory/2026-10-15.md → 本轮已提交
- **缺口 1：19 个启用 job 中，`payload_fallbacks_json` 全为空**——没有一条 cron 配了兜底模型，provider 层失败时无自动降级
- **缺口 2：告警只配在 dreaming 上**——8 个 dreaming 有 failureAlert，11 个业务链（tea-daily-report、charm-cdp-warm、birthday-anniversary-check、蓝氏四条链、蓝氏周二提醒等）全部 `none`，10-15 早间四条链失败零通知

---

## B. 本周学到的关键洞察

**1. 配置级建议落地 ≠ 故障修复，本周给出了完整反证**
三项处方（拆窗 / 加 timeout / 开告警）全部落地，同一周却出现本季最差失败日（10-15，13/20）。原因不是处方无效——10-14 之前那两天工具步失败确实消失了；是失败面迁移到了处方管不到的层。**判断修复是否有效，必须同时看失败总量、失败构成、以及失败面有没有迁移**，只看第一项会被骗（上周结论的第二次验证）。

**2. 失败形态三次迁移 = 水往更底层漏**
一周内走完 工具步自证 → Process 异步 → provider 层三步。每一次上游被治住，漏点就往下走一层。走到 provider 层时，agent 已经没有可调的旋钮了——可控层处方到头，修复目标必须从「防失败」转成「让失败可被及时发现和验收」。这条与分身侧独立记录一致（ceo / supermind / book 10-15 均记「失败形态第三次迁移」），跨主体收敛说明是结构规律而非个案。

**3. 告警保护对象配反了**
告警配在 8 个 dreaming 上（内部复盘，失败影响最小），没配在影响客户交付的 11 条业务链上（失败当天就可能漏发提醒）。10-15 就是这个配置的实盘结果：早上四条业务链失败，零通知，直到本轮复盘才被发现。**保护应优先配在对外交付链上，而不是配在做复盘的地方。**

**4. 生成 ≠ 送达，本周再次实盘验证**
tea-daily-report 的 run 报错，但日报文件 13:20 仍然生成了（延迟 2h16m）。run 层的红绿不能直接推断交付层结果。**业务链的验收标准必须是「产物 + 送达」双确认，run 状态只是其中一半。** 查 run 失败时，第一件事是查产物是否已经生成。

**5. 同一系统里重试策略不一致**
同样报错，三条链三种命运：birthday-anniversary-check 自动重试 3 次后成功、charm-cdp-warm 自动重试 4 次、蓝氏每日TODO提醒与 tea-daily-report 一次即止无重试。**如果一个系统里「会不会重试」取决于 job 而不是取决于错误类型，那么可靠性就不是设计出来的，是碰出来的。**

**6. 补跑制造窗口错位（与分身同日收敛）**
本轮 dreaming-omni 在周四 22:44 触发，而它的排期是周日 22:42，`last_run_at_ms` 仍停在 10-11 22:30 —— 从数据看更像一次手动/强制触发。补跑能补回内容，但会把排期节点打乱、让「这一周的边界」变得含糊；分身侧同日也记到同类现象。

**7. main 本周本体失误：品牌事实误读**
把 logo 中心的五叶草读成蒲公英，围绕蒲公英写了一整版文案（种子随风飞、落在人心里长复利）并出了一版成品，全部作废重做。根因不是眼力，是顺序——先做图后对齐文字。逸凡当天明确纠正两点：中间是五叶草不是蒲公英；「不要急吼吼的做图，文字和我确认好再做图」。**对外文案与品牌资产类任务，文字先对齐、确认后出图，这条已写进 SOUL。**

---

## C. 系统健康度评估

### 评分：6.5/10（上周 7.5/10）

| 维度 | 状态 | 变化 |
|------|:----:|:----:|
| 非 dreaming 业务链 | ⚠️ 10-12～10-14 全绿 9/9，10-15 早间 4 条失败（2 条对外链） | ↓ |
| SubAgent 产出层 | ✅ 32/32 dreaming + 日报 4/4 | → 稳 |
| dreaming 集群 run | ⚠️ 22 失败 / 33.8%，但集中在 10-15 一天 | ↓ |
| 配置级落地率 | ✅ 3/3，首次破零 | ↑↑ |
| 告警覆盖 | ⚠️ dreaming 已覆盖并首次触发；业务链 11 条全静默 | ↓ |
| 兜底模型 | ❌ 19 个 job 全无 fallback | → |
| 备份 / 环境 | ✅ crontab 空、/tmp 清、GitHub 同步 | → |
| main 本体交付 | ✅ 品牌资产一批交付 + skill 固化 + 模型升级；1 次品牌事实误读 | ⚠️ |

### 需要关注的四个信号

1. **对外交付链的静默失败面（最高）**——10-15 早间四条业务链失败零通知，其中两条直接面向客户节奏。当前靠「下一轮复盘发现」兜底，等于没有兜底。
2. **provider 层失败进入常规化**——本周已有 2 次 `LLM request failed` + 7 次 model-call 超时。这一层不可控，但可以做到失败后自动降级（fallback 模型）与自动重试。
3. **重试与告警的策略不统一**——同一系统三种重试命运，说明这两项不是统一设计，而是逐个 job 手工长出来的。
4. **非排期触发的补跑**——本轮 omni 的触发原因未确认，需向逸凡核实；若为习惯性手动补跑，排期与周界会持续漂移。

---

## 下周建议（按杠杆排序，前三条需逸凡确认）

1. **【决定项·最高】给业务链开 failureAlert**——tea-daily-report、charm-cdp-warm、birthday-anniversary-check、蓝氏四条链等，开关与 dreaming 完全同构（`failure_alert_after` + `announce` 到飞书）。一次配置，收益是把今天这种静默失败变成可见。审计与配置动作由 main 侧统一执行（不由子任务自证）。
2. **【决定项】给关键 job 配 fallback 模型**——`payload_fallbacks_json` 目前全空。provider 层失败时自动切备用模型（如 deepseek-v4-pro 或 minimax），把「不可控层的失败」转成「可恢复的失败」。
3. **【决定项】统一重试策略**——先查清蓝氏每日TODO提醒与 tea-daily-report 为什么不重试，再决定是统一重试次数，还是把不重试的改成重试。
4. **业务链验收改为双确认**——run 状态 + 产物 + 送达三者对齐；run 报错时先查产物是否已生成（10-15 日报即为产物已生成的实例）。
5. **main 本体：对外文案先对齐再出图**——已于 10-14 立规并写入 SOUL，后续品牌类任务按此执行，不再先出成品。
6. **确认 dreaming-omni 本轮非排期触发原因**（是否逸凡手动触发）。

---

## 送达留痕

- 本轮为 dreaming-omni（cron e239ae49-a3bf-48eb-a948-70865190c64f）周度任务，2026-10-15 22:44 启动（非排期触发）
- 复盘落盘：`memory/weekly-dreaming-2026-10-15.md`；MEMORY.md 追加本周关键条目；SOUL.md 加一条对外文案执行顺序
- 交付方式：本轮按系统约定不做显式 message 调用，复盘输出由系统自动转发至逸凡飞书私聊
- 第 1 / 2 / 3 项属 scheduler 与模型配置变更，按 SOP 需逸凡确认后执行，本轮只做诊断与建议，未改动任何 cron 配置
