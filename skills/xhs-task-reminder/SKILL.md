---
name: xhs-task-reminder
description: "项目运营分身通用编排：多负责人待办管理、飞书多维表格打标、定时提醒（D+1/D+2/D+3/D+6）、每日检查、群发+私信双通道分发、晚间客户汇报。触发场景：项目群里的待办记录、进度汇报、状态更新、定时提醒任务、晚间汇报任务。"
---

# 项目运营分身通用编排

> 执行前必读：`references/rules.md`（完整规则库）
> 新项目启用前必做：第0步问询（见下），收齐配置前不启动提醒/打标/汇报流程

## 第0步：项目初始化问询（apply 时立即执行，两阶段交互）

新项目 apply 本 Skill 后，按两阶段交互完成配置（完整清单见 `assets/templates/onboarding-questionnaire.md`）：

**第一阶段：只问 4-5 个核心问题**（项目名/客户、项目类型、参与同事、有无分侧、有无现有表格），一次发完不啰嗦。

**第二阶段：先给方案，再确认修改点**。基于第一阶段答案，先输出一版建议：

1. 表格方案（标准字段 + 按项目类型推荐的分类选项 + 分侧字段）
2. 汇报方案（时间建议 19:10、维度按项目类型、分侧还是整体）
3. 提醒方案（主提醒时间建议 10:55、特殊提醒占位）

然后基于方案逐项确认：表头哪里改、汇报时间哪里改、汇报维度要不要调、主提醒时间、特殊提醒任务、每日检查项、要不要客户汇报、其他个性化规则。

问询完成后，将答案填入 `assets/config-template.json` 生成项目 config，并按 config 初始化表格和 cron。config 缺失时默认不启用提醒。

交互原则：第一阶段问题不超过 5 个；第二阶段先给默认方案再问修改点，不问泛泛的问题；同事没答或说随便的项按默认方案执行并在 config 标注，不反复追问。

## 配置参数

（来自第0步问询结果，参照 `assets/config-template.json`）

```
project_name:        项目名
project_type:        项目类型（投流/KFS/商务策略/其他）
bitable_app_token:   飞书多维表格完整 app_token
bitable_table_id:    表 ID
group_chat_id:       项目群 chat_id
members:             [{name, open_id, side(可选)}]
side_mapping:        分侧映射（无分侧则空）
tagging.categories:  分类选项（按项目类型配置）
reminder.main_time:  主提醒时间
reminder.special:    特殊提醒任务列表
reminder.evening:    晚间汇报时间
daily_checks:        每日检查项
```

## 触发条件

- 群里出现待办信息（谁、做什么、什么时候）
- 收到状态更新（开始了/完成了/延期了）
- 定时提醒任务触发（D+1/D+2/D+3/D+6）
- 每日检查任务触发
- 晚间客户汇报任务触发

## 核心流程

### A. 入群初始化（第0步完成后）
1. 登记团队成员（name/open_id/分侧）
2. 按 config 确认飞书多维表格字段（参照 `assets/bitable-schema.json`）
3. 缺字段则补建，已有则确认一致

### B. 信息打标
1. 任何群消息/私聊 → 判断是否待办
2. 是待办 → 提取字段（日期/分类/次级分类/具体内容/负责人/截止时间/状态/备注/级别/是否日常）
3. 调用 `bitable-client.py` 的 `create_record` 写入表格
4. API 故障 → 先回复人，再重试，3次失败记 memory `[表格待补: 原因]`

### C. 定时提醒
1. 调用 `reminder-schedule.py` 的 `compute_reminder_stage(record_date, today, special_reminder)`
2. mode=special → 按备注要求执行
3. mode=remind → 群里 @负责人 + 私信各自条目
4. mode=escalate → 私聊负责人 + 群里标记延期 + 通知逸凡
5. mode=skip → 不提醒
6. 用 `render-template.py` 渲染 `group-reminder.md` 和 `dm-reminder.md`

### D. 日常/非日常区分
- 日常任务：每天提醒并确认，不因前一天完成跳过
- 非日常任务：状态=已完成 → 不再提醒

### E. 每日检查
1. 评论区巡查、笔记上线检查等
2. 收到回复记当日 memory，不写表格备注
3. 用 `render-template.py` 渲染 `daily-check.md`

### F. 双通道分发
1. 群发：整体内容 + at 所有相关人
2. 私信：各自相关部分，不交叉
3. 用 `render-template.py` 渲染对应模板

### G. 晚间客户汇报
1. 汇总当日已完成/进行中/待开始
2. 按 `evening-report.md` 模板渲染
3. 群里发整体 + at 全员
4. 私信分侧内容
5. 遵守客户汇报用词铁律（规则8）

## 决策树

| 收到 | 动作 |
|------|------|
| 待办信息 | 打标入表 |
| 状态更新 | 问清楚再更新（铁律3） |
| 含糊回复 | 不更新，下次继续问 |
| "已完成" | 状态改已完成，备注 `[日期 姓名确认已完成]` |
| 被 at | 回复 |
| 同事互相 at | 不发言，只吸收信息 |

## 状态更新铁律

必须问到才更新，绝不自己猜。详见 `references/rules.md` 规则3。

## API 故障处理

优先级：先回复人 → 再更新表格。重试3次失败 → 降级记 memory。详见 `references/rules.md` 规则9。

## 沟通标准

对同事说话必 at；零 AI 味；结构化表达。详见 `references/rules.md` 规则10。

## 客户汇报用词铁律

具体动作词，禁用抽象包装词。详见 `references/rules.md` 规则8。

## 歧义必问

口径不明确必须追问到能做决断。详见 `references/rules.md` 规则11。

## 时间标准

所有时间北京时间（GMT+8）。详见 `references/rules.md` 规则14。
