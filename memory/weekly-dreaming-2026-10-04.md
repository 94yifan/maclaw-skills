# Weekly Dreaming | 2026-10-04（周日）

本周跨度：2026-09-28（一）→ 2026-10-04（日）
范围：仅 main workspace（Omni）。遵守隔离原则，未读取任何 SubAgent 文件内容；系统巡检只取文件名 / 时间戳 / cron 与 task 元数据。

---

## A. 本周执行汇总

### 1. main 本周 3 个执行日，全部事件驱动

| 日期 | 事件 | 结果 |
|------|------|------|
| 09-28 | ① 付款审批提交：非业务付款·咨询费 ¥30000（广州珠玑文化传播，工商银行广州同德支行），附件发票已上传 → instance 56007B41-93C0-4184-9973-2BAC0616BEFA，PENDING ② 蓝氏·口碑通重复追投提醒（cron 一次性）：群 oc_7840e10a86c1814ddcf2c37c2675ba33 + 私聊 user:ou_0b93c01c6406716e01bab2f3e2c09485 双通道送达 | 双通道成功，messageId 留痕；旧单后由逸凡自行撤回 |
| 09-29 | 付款审批两轮重提：08:30 事由从「支付广州珠玑文化传播有限公司咨询费」简化为「咨询费」；08:40 把银行账户写进必填控件（user 要求不能塞备注 / 付款明细）→ 最终单 EE6819B8-8D91-413B-A6C2-29F3C8ABD8D2，serial 202609290024，PENDING | 完成；过程中探字段误建 9 条重复单（4B62BCEB / 8AD29A11 / 2EDA966F / 6749F95F / A830C0B0 / 3A7CA33F / 5485B648 / 6E00E96C / C954E88C）已全部撤回 |
| 10-01 | GitHub 项目 HowToLiveBetter（649 条建议 / 34 章）下载并打包发逸凡 | 完成；github.com 直连不通，走 API tarball 通道；飞书发文件首轮用错参数（见 B-3） |

**空窗**：09-30、10-02、10-03 及今日无 main daily（10/01 起进入国庆假期，main 侧零交互）。假期降频未影响自动化链路（tea-daily / 蓝氏四条链 7/7 全绿）。

**main 本周落账检查**：3 个执行日全部有 memory 记录且已提交（git status 中 memory/ 无未提交项），无漏账。

**遗留**：/tmp 残留 19 个脚本（含 9/29 探字段系列 probe_acct / probe_bank / probe_branch / test_acct_fmt / test_bankname / verify_final 与 3 个 submit_zhuji 版本），未清理归档。

### 2. main 承担的三类工作

- **审批提交**：1 个事由（广州珠玑咨询费）经 3 轮才定稿，全流程走 feishu-approval-submitter
- **群内运营协同**：蓝氏口碑通追投提醒闭环（双通道送达）
- **外部资源获取与交付**：GitHub 仓库下载 + 飞书文件发送

### 3. SubAgent 产出核实（仅文件名 + 时间戳，未读内容）

| 分身 | 本周产出 | 判断 |
|------|:----:|------|
| lanshi | 7/7 天 daily | ✅ 全勤 |
| social-crawler | dreaming 7/7 + weibo_daily 7/7 | ✅ 双线全勤 |
| brain-mining | dying 7/7 | ✅ 全勤 |
| book | dreaming 6/7（缺 09-28） | ⚠️ 缺 1 |
| ceo | dreaming 6/7（缺 09-29） | ⚠️ 缺 1 |
| cfo | dreaming 6/7（缺 09-28） | ⚠️ 缺 1 |
| supermind | dreaming 6/7（缺 10-01） | ⚠️ 缺 1 |
| strategic-planner | daily 4/7（缺 09-29、10-01、10-02）+ dreaming 5/7（缺 10-01、10-02） | ❌ 最弱 |

**结论**：本周没有一个分身出现「不可恢复丢失」（vs 上周 supermind 9/24 复盘内容不可重建），5 个缺日全部是可补的。产出层比上周明显好转。

### 4. run 状态层：失败量首次下降，结构未变

`openclaw tasks list --json` 统计本周 tracked run：**119 次，67 成功 / 50 失败 / 2 running，失败率 43%**（上周 131 次 / 61 失败 / 47%）。

**非 dreaming 任务 100% 绿：**
- tea-daily-report 7/7、charm-cdp-warm 7/7、birthday-anniversary-check 7/7
- 蓝氏四条链全绿：每日 TODO 7/7、笔记上线检查 7/7、晚间客户汇报 7/7、评论区巡查 4/4
- monthly-birthday-anniversary-preview 1/1、玄武阁借款节前提醒 1/1、蓝氏口碑通追投提醒 1/1、蓝氏人群测试方向双周提醒 1/1

**dreaming 集群 50 次失败 / 16 成功：**

| job | 成功 | 失败 | 备注 |
|-----|:---:|:---:|------|
| dreaming-supermind | 0 | 7 | 连续两周 0 成功 |
| dreaming-cfo | 1 | 9 | |
| dreaming-ceo | 3 | 11 | |
| dreaming-brain-mining | 3 | 8 | |
| dreaming-book | 1 | 6 | |
| dreaming-strategic-planner | 2 | 7 | |
| dreaming-social-crawler | 7 | 2 | 唯一过半 |
| dreaming-omni（main 自身） | — | — | 今晚本轮 running；上周为 300s 超时后重试 |

**失败类型（耗时中位数 300.18s / max 300.31s，全部精确卡在 300s 墙）：**
- 300s 超时，last phase = `model-call-started`：**37 次**
- 300s 超时，last phase = `tool-execution-started`：**3 次**
- 工具步失败（sqlite3 查 seq / 命令失败）：**10 次**（与上周同型）

### 5. 系统层状态

- **crontab 保持为空** ✅（无污染项）
- **GitHub 备份同步** ✅（`git rev-list --left-right --count github/main...HEAD` = 0/0）
- **failureAlert**：8 个 dreaming job 全部为 None → 50 次失败零通知（连续第三周）
- **dreaming 排期**：22:00 social-crawler → 22:01 cfo → 22:02 strategic-planner → 22:03 supermind → 22:04 brain-mining → 22:05 book → 22:06 ceo，**8 个挤在 7 分钟内**（上周为 22:00-22:18 共 18 分钟，本周更紧）
- **timeout 仍全部 300s**：上周建议的 300→600 未落地
- **SOUL.md / AGENTS.md / TOOLS.md / USER.md**：本周无改动 commit
- 工作区仍有 `wx_login_qr.png` / `wx_qr_zoom.png`（含登录码，不入库、不解读）

---

## B. 本周学到的关键洞察

**1. 上周三条配置级建议连续第二周零落地，卡点已从「效率」变成「授权」**
timeout 300→600、错峰拆窗、打开 failureAlert——三项都是配置级、一次改动即可验证，均为按 SOP 需逸凡确认后执行。上周写进"下周建议"，本周诊断结论完全相同，说明这不是认知缺口而是授权缺口：agent 不能自改 cron，于是每周把同一件事重新诊断一遍。ceo、cfo 各自的复盘里都已把它记为"唯一决定项"。**这条建议从本周起不再叫"建议"，叫"待决项"——不定就是默认不做。**

**2. 失败量首次下降（61→50），但这是噪声不是改善**
非 dreaming 链路的 daily 类任务本周无失败，dreaming 集群的 300s 墙一次没被绕过：40/50 失败仍是硬超时（37 卡在模型调用起点）。含义：任务单轮体量依然超预算，且卡点在任务头部而非尾部。修复方向没变，没有任何证据表明故障被修。

**3. 交付层的坑升级了：从「发不出去」变成「发出去改不了」**
10/01 发 GitHub 压缩包时用了 inline `MEDIA:` / `attachments` 路径，飞书侧收到的是 post 纯文本——MEDIA 行被当正文渲染、末尾追加 `📎 路径`，**文件实际没送出去**；改用 `message(media=...)` 后 receipt 里 `parts[].kind` 才变成 `media`。同时确认当前飞书插件（@openclaw/feishu 2026.5.27）不支持 edit/delete → **消息一旦发出无法收回**。操作含义：飞书发送必须"发前自检"，因为不存在"发后修正"这个选项。

**4. 能力边界判断必须实测，已沉淀的 skill 结论会过期**
9/29 推翻了 feishu-approval-submitter 里「account 控件 API 不支持，需用 textarea 替代」的结论——实测可写，且通过"故意漏字段触发校验错误"逐个探明了子控件结构（widgetAccountName / widgetAccountNumber / widgetAccountBankName 需带 bankCode+bankNameZh / widgetAccountBankBranch 只认飞书自有银行编码字典）。直接用推理守卫六验证：先跑工具、再下结论。

**5. 探字段不能打正式接口——本周最贵的操作教训**
探 account 结构时每次"成功创建"都会真建单并通知审批人，代价是 9 条重复单 + 一轮撤回。正确姿势是先制造校验错误（用无效值触发 `控件值不合法或者为空`）来暴露字段结构，而不是用真实数据试。这条应写进审批 skill 的操作约束。

**6. 假期降频是常态，不是故障信号**
10/02-10/04 main 零 daily，但 tea-daily 与蓝氏四条链 7/7 全绿。判断系统健康要看"该跑的有没有跑"，而不是看 main 有没有产出。这条也顺带解释了为什么"main 无产出 ≠ 系统停摆"。

**7. 重试机制在持续代偿，但代偿本身开始制造工作量**
ceo / cfo / book 本周各自出现多轮重试（ceo 有 run3 / run4 核验轮，cfo 反复撞 300s 后自记连败，book 连续补提交上一轮遗留产物）。机制有效——产出缺口被补上了，但每轮都是全量重跑，且产生"上一轮产物未提交"的二次遗留（book 因此立了规则 17/18）。

---

## C. 系统健康度评估

### 评分：7/10（上周 6.5/10）

| 维度 | 状态 | 变化 |
|------|:----:|:----:|
| 非 dreaming 业务链 | ✅ 7/7 全绿 | → |
| SubAgent 产出层 | ✅ 无不可恢复丢失，5 个可补缺日 | ↑ |
| dreaming 集群 run | ⚠️ 50 次失败 / 43% | ↑（略好，实为噪声） |
| 无告警 | ⚠️ 50 次失败零通知 | → |
| crontab 污染 | ✅ 保持清零 | → |
| GitHub 备份 | ✅ 0 ahead / 0 behind | → |
| main 执行与落账 | ✅ 3 执行日全部留痕，无漏账 | → |
| 配置级建议落地率 | ❌ 0/3（连续两周） | ↓↓ |

### 需要关注的三个信号

**1. 授权卡点（最高优先级）** —— timeout 300→600 + failureAlert + 拆窗 三项连续两周未落地，是 dreaming 集群全部失败（40/50 硬超时）的共同根因。本轮需要的是一个明确答复："同意改" 或 "先不改"，而不是第四周再诊断一次。

**2. 排期压缩加剧** —— 8 个 dreaming 挤在 7 分钟窗口内（上周 18 分钟），同时读写同一 git 仓库、同时调模型，与 50 次失败量同向。拆窗的收益比单纯加 timeout 更确定。

**3. supermind 是唯一"从来没成功过"的 job** —— 上周 0/9、本周 0/7，连续 14 天零成功。它不是"偶发超时"，是排期 / 体量结构不匹配，需要单独处理（降任务量或换窗口）。

---

## 下周建议（按杠杆排序）

1. **dreaming 舰队 timeout 300 → 600**（需逸凡确认）——40 次失败直接卡在模型调用，扩预算单点最高杠杆。
2. **8 个 dreaming 拆窗**（每 10 分钟一个，或分 22:00 / 23:00 两批）——减少同仓库写争用，收益确定性最高。
3. **打开 failureAlert**——连续三周 50+ 次失败零通知，不能再静默。
4. **supermind 单独排查**——连续 14 天 0 成功，考虑拆任务或改排期。
5. **strategic-planner 补齐 09-29 / 10-01 / 10-02 daily 与 10-01 / 10-02 dreaming**；book / ceo / cfo / supermind 各补 1 个缺日。
6. **归档 /tmp 19 个脚本**（9/29 探字段系列已失效，保留 submit_zhuji_final.py 一个入口即可）。
7. **main 侧操作固化**：飞书发送统一走 `media` 参数 + 发前自检（无 edit/delete 兜底）；审批 skill 补两条约束（account 控件实测可写、探字段禁用正式接口）→ 写入 TOOLS.md 与 skill。

---

## 送达留痕

- 送达方式：`message` 工具显式投递至逸凡飞书私聊（ou_c4249d713be906d36ef8607efab6506f）
- messageId `om_x100b63120fbe04a0c27ad588d89f3e1`，sentAt 2026-10-04 22:35（ok:true，receipt parts[].kind = text）
- 本轮为 dreaming-omni 周度任务（cron e239ae49-a3bf-48eb-a948-70865190c64f），2026-10-04 22:31 启动。
- 说明：第 1、2、3 项属 scheduler 配置变更，按 SOP 需逸凡确认后执行，本轮只做诊断与建议，未改动任何配置。
