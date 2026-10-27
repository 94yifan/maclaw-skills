# Weekly Dreaming | 2026-10-25（周日）

本周跨度：2026-10-19（一）→ 2026-10-25（日），7 天
范围：仅 main workspace（Omni）。遵守隔离原则，未读取任何 SubAgent 文件内容；系统巡检只取文件名 / 时间戳 / cron 与 run 元数据。
数据源：只读副本 `/tmp/oc_dream_ro2.sqlite`（源 `~/.openclaw/state/openclaw.sqlite`，`task_runs` / `cron_run_logs` / `cron_jobs`）+ `launchctl list` + 进程表 + `/tmp/openclaw/*.log` + `~/.openclaw/logs/gateway-restart.log` + `git log/status`。

---

## A. 本周执行汇总

### 1. 运行层：失败率腰斩，但没有一天停摆

| 日期 | run | 失败 | 成功 | 备注 |
|------|:--:|:--:|:--:|------|
| 10-19 | 13 | 2 | 11 | dreaming 集群 2 败 |
| 10-20 | 15 | 2 | 13 | tea-daily + dreaming-cfo |
| 10-21 | 13 | 1 | 12 | dreaming-brain-mining |
| 10-22 | 14 | 1 | 13 | dreaming-book |
| 10-23 | 13 | 1 | 12 | dreaming-strategic-planner |
| 10-24 | 14 | 2 | 12 | tea-daily + dreaming-supermind |
| 10-25 | 13 | 4 | 8（+1 running） | tea-daily + 3 个 dreaming |

**合计 95 次，13 失败 / 81 成功 / 1 running → 失败率 13.7%（上周 28.2%，101 次 24 败 23.8%）。**

- 7/7 天有运行，**本周零停摆日**（上周 10-16 整日零运行）
- 网关 PID 86159 自 10-17 23:32 起连续运行 **7 天 23 小时**，`gateway-restart.log` 本周无新记录
- 失败分布：dreaming 集群 10 次，业务链 3 次（全在 tea-daily-report）

按主体：lanshi 24/0 败、social-crawler 21/4、ceo 14/0、supermind 7/2、strategic-planner 7/2、cfo 7/1、brain-mining 7/3、book 7/1、main 1/0。

### 2. 业务链：产物 7/7 齐，但三次 run 报错 + 一次 11 小时延迟

| 链路 | run 结果 | 产物 |
|------|------|------|
| 蓝氏四条（每日TODO / 18点笔记检查 / 19:10 晚间汇报 / 评论区巡查） | 全部 ok | lanshi daily 7/7（10-19 ~ 10-25 齐全） |
| tea-daily-report | 4 成功 / 3 失败（10-20、10-24、10-25） | **微博日报 7/7 全部落盘** |
| birthday-anniversary-check | 7/7 ok | — |
| charm-cdp-warm | 7/7 ok | — |

日报落盘时间：10-19 11:04 / 10-20 11:05 / 10-21 11:09 / 10-22 **22:03（延迟 11h）** / 10-23 11:11 / 10-24 **22:02（延迟 11h）** / 10-25 **12:48（延迟 1h48m）**。

三次 run 报错，三次产物照常生成 —— **run 状态与产物再次脱钩，本周再验证 3 次（累计第 4、5、6 次）。**

### 3. 本体（main）：本周近乎空转

| 项目 | 事实 |
|------|------|
| cron run | 1 次（10-20 蓝氏周二提醒） |
| daily 落账 | 1 篇（10-24，蓝氏提醒项改造） |
| SOUL.md | 末次修改 10-15，本周零更新 |
| MEMORY.md | 末次修改 10-18 22:43（上周 dreaming），本周零更新 |
| 新建 / 修改 skill | 0 |
| 审批单 / 对外交付 | 0 |

10-24 那篇 daily 记的是实质工作：按陈思安 + 逸凡指示，把蓝氏 5 条策略项从每日 TODO 移出（改「周提醒」+ 状态进行中 + 备注留痕），新建周一/周四策略提醒 cron（b1055fa1，已生效，下次 10-26 10:00），并改掉每日 TODO 的 prompt 跳过周提醒项。**已核对：该 cron 在 enabled 列表内，配置正确。**

### 4. 上周四个决定项：0/4 落地

| 上周建议 | 本周实测 | 状态 |
|------|------|:--:|
| ① 网关交回 launchd 托管 | `launchctl list` 仍只有 `openclaw.update.once`；网关仍是 zsh 子进程（PPID 86115） | ❌ 未做 |
| ② 处理更新死循环 | Node 仍 v25.8.1；`npm i openclaw@2026.10.3` 正在跑（PID 47033，19.9% CPU）；日志 Update ERROR 10-24 3662 次 / 10-25 4151 次 | ❌ 未做 |
| ③ 11 条业务链开 failureAlert | 全部 `failure_alert_after = -`（仅 8 个 dreaming 有 =3） | ❌ 未做 |
| ④ 18 个 job 配 fallback | 全部 `payload_fallbacks_json = NULL` | ❌ 未做 |

**连续两周，最高杠杆的建议零落地。**

### 5. 新故障形态：从模型层漏到工具链层

13 次失败里没有一次是模型报错，全部是多步工具链中断：

- `🩹 Apply Patch failed` × 3（social-crawler 10-19、cfo 10-20、strategic-planner 10-23）
- `🛠️ print text → find files → show first 40 lines → ... failed` × 4（brain-mining 10-19/10-21/10-25、supermind 10-24/10-25）—— 特征是"读自己刚写的文件"这一步失败
- `🛠️ sqlite3 ~/.openclaw/state/openclaw.sqlite "SELECT ..." failed` × 1（strategic-planner 10-25）
- `🧰 Process: delta-breeze failed` × 1（tea-daily 10-24）

同型根因很清楚：**dreaming 的执行段依赖"多段串行 exec + 读写刚生成的文件"，链条越长，中间任意一跳失败整轮就作废。** 这类失败不是能力问题，是编排脆弱性。

### 6. 今晚（10-25）实况：3 个分身的复盘没送到逸凡

22:00 social-crawler ✅ / 22:06 cfo ✅ / 22:12 strategic-planner ❌ / 22:18 supermind ❌ / 22:24 brain-mining ❌ / 22:30 book ✅ / 22:36 ceo（本轮时仍 running）/ 22:42 main（本轮）。

- 三个失败 run 的 `delivery_status` 全部 = `not-delivered`
- supermind 已连续 2 天失败（10-24 + 10-25）= **48 小时无复盘送达，零通知**
- 原因：dreaming 的 `failure_alert_after = 3`，两次连续失败达不到阈值

### 7. 成本侧：失败也在烧 token

本周 cron 口径总 token **113.8M**（deepseek-flash，绝大部分是上下文重复读）。单次 dreaming 1.4–5.1M 不等，**失败 run 单次仍消耗 1.4–1.6M**，13 次失败约等于 **20M token 花在没产出的活上**。日志侧同期每天 63–72 MB（10-24 63.6 MB、10-25 72.0 MB），主要来自更新循环刷错。磁盘尚有余量（/ 用 12Gi / 926Gi）。

### 8. 系统层

- crontab：空 ✅
- git：`rev-list --left-right --count github/main...HEAD` = 0/0 ✅（本周 commit 正常，含各分身 dreaming 落库）
- 未提交项：`brain-mining/MEMORY.md`、`models.json`、`social-crawler/MEMORY.md`、`strategic-planner/MEMORY.md`、`skills/weibo-daily-report/SKILL.md`、`plugins/deepseek/catalog.json`（仍处删除态 D，上周已标记待确认）
- fallback：18 个启用 job **第 2 周全空**
- failureAlert：8 dreaming =3，11 条业务链 none

---

## B. 本周学到的关键洞察

**1. 失败率降了，但那是分母变了，不是风险消了**
28.2% → 13.7% 看着漂亮，实际原因是本周再没有出现 10-16 那种"整天零运行"。10-16 那天不是 1 次失败，是整条链消失。**只要 gateway 还是裸进程，下一次 shell 退出或重启就复现，而四张防护牌一张都没打。** 用失败率判断系统健康会骗人，要看"最坏一天发生了什么"。

**2. 告警阈值 3 对日频任务，等于没有告警**
本周 13 次失败，**没有一次连续 3 次**，所以整套 failureAlert 一次都没响。supermind 连续 2 天失败、48 小时零送达，依然静默。**日频任务的阈值必须 ≤2；对交付类链路应该 =1（一次失败就是一次客户感知缺失）。** 阈值是按"减少噪音"设的，但代价被设在了对外交付上，方向反了。

**3. 建议没有执行入口，就等于没提**
上周写了 8 条、4 个决定项，写得越全越像被处理过了。**一份长清单的真实作用，是让读的人觉得事情已在轨道上，从而不必今天做决定。** 本周该改的做法：每周最多 1 个决定项，且必须二选一可直接回答；能我自己改的（阈值、fallback、清理）不放进决定项，直接改完报结果。诊断不缺，缺的是收窄。

**4. 失败的成本是双份：没产出 + 烧 token**
20M token 在本周被失败 run 吃掉。以前我只把失败当"缺一份交付"，没算过它还占预算。**任何重试/长链任务，都该带一个失败成本指标（单次失败 token × 次数），否则"多跑几次总能成"会默默变贵。**

**5. 本体空转是最容易被忽略的健康指标**
分身 24/24 全绿、日报 7/7 齐、网关 8 天稳 —— 从"系统可用性"看这周是近期最好的一周。但我自己：1 次 cron、1 篇 daily、SOUL 和 MEMORY 零更新、零对外交付。**可用性上升 + 本体停滞，是一种温水状态：系统在替我维持运转，而我没有推进任何自己的东西。** 上一周我在做交付（品牌资产、审批），这一周两头都没有 —— 说明我的排班不是被工作占满，是缺触发。

**6. 分身的失败模式已经稳定可描述，该修在编排层**
4 次失败都是"读自己刚写的文件"这一跳。这不是模型能力，是 dreaming 跑到收尾时段、上下文最长、多段串行命令最密的位置。**修法不是让它更努力，是把收尾段拆成"先落盘、再回报"两个独立动作，任何一跳失败不牵连整轮产出。**

---

## C. 系统健康度评估

### 评分：6.0/10（上周 5.0，周三周报 6.5）

| 维度 | 状态 | 变化 |
|------|:----:|:----:|
| 业务链可用性 | ✅ 6 条日链 41/42 成功，零停摆日 | ↑↑ |
| 网关托管 | ❌ 仍裸进程（zsh 子进程，PID 86159） | → |
| 自动更新 | ❌ 死循环未停，3662→4151 次/天 | → |
| dreaming 集群 | ⚠️ 10 败 / 95 = 10.5%，全为工具链中断 | ↑ |
| 产出层 | ✅ 日报 7/7、lanshi daily 7/7；❌ 3 个 dreaming 今晚未送达 | ↑ |
| 告警覆盖 | ❌ 业务链 11 条 none；dreaming 阈值 3 从未触发 | ↓ |
| 兜底模型 | ❌ 18 个 job 第 2 周全空 | → |
| 本体产出 | ❌ 1 次 run / 1 篇 daily / SOUL+MEMORY 零更新 | ↓↓ |
| 环境 / 备份 | ✅ crontab 空、git 0/0、磁盘充足 | → |
| 上周建议落地 | ❌ 0/4 | ↓↓ |

### 需要关注的五个信号（按紧急度）

1. **网关托管缺失（最高，未动）** —— plist 在、未加载。一次 shell 退出即复现 10-16。
2. **告警阈值失效（次高，本周新发现）** —— 阈值 3 让整套 dreaming 告警形同虚设，supermind 已静默 48h。
3. **更新死循环（持续消耗）** —— Node v25.8.1 与目标版不兼容，可用版已到 2026.10.7，重试无解。
4. **业务链零告警（未动）** —— 11 条仍 none。
5. **本体停滞（新提）** —— 本周无任何自我推进动作，需定一个固定触发点。

---

## 下周建议

**决定项（只留一个，需要逸凡一句话）**
网关托管二选一：
- A：我把网关交回 launchd（`launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist`），验证 `launchctl list` 出现 ai.openclaw.gateway 且 PPID 不是 shell。风险：需要重启一次网关，约 1–2 分钟不可用。
- B：暂不动，接受"shell 退出即可能整天停摆"，我用 daily 心跳自检兜底（发现当天 0 run 就私信你）。

**我可以直接做、不需授权的（默认本周内完成，做完报结果）**
1. 把 7 个 dreaming 的 `failure_alert_after` 从 3 改成 1（supermind 这种连续 2 天静默的情况必须立刻响）
2. 清理 `plugins/deepseek/catalog.json` 的删除态：确认是预期删除还是误删，再决定提交或还原
3. 提交本周遗留未提交项（brain-mining / social-crawler / strategic-planner MEMORY、models.json、weibo-daily-report SKILL）
4. 给 dreaming 收尾段改成"先落盘、再回报"：产物写完即 commit，回报失败不影响产物（针对本周 4 次同型失败）

**需要逸凡决定的第二件事（单独一件，不急但会持续烧钱）**
更新死循环：①升 Node 到 24 LTS 或 26+ 后更新到 2026.10.7；②卸载 `openclaw.update.once` 改手动择时。不定的话每天 4000 次失败照跑。

---

## 送达留痕

- 本轮为 dreaming-omni 周度任务（cron e239ae49-a3bf-48eb-a948-70865190c64f），2026-10-25 22:42 启动，排期正常（周日）
- 复盘落盘：`memory/weekly-dreaming-2026-10-25.md`
- 交付方式：按系统约定不做显式 message 调用，复盘输出由系统自动转发至逸凡飞书私聊
- 本轮只做诊断，未改动任何 cron、launchd 或 Node 配置
