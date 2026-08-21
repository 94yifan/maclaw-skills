# Skill 规格说明书：project-ops-orchestrator（项目运营分身通用编排）

## 目标

把蓝氏项目已验证的完整运营协作流程固化为可复用 Skill，未来任何新项目分身（多负责人 + 飞书多维表格 + 定时提醒 + 私信分发 + 晚间客户汇报）直接套用，只改参数。

## Skill 元信息

- name: project-ops-orchestrator
- description（frontmatter，必须含触发关键词）: "项目运营分身通用编排：多负责人待办管理、飞书多维表格打标、定时提醒（D+1/D+2/D+3/D+6）、每日检查、群发+私信双通道分发、晚间客户汇报。触发场景：项目群里的待办记录、进度汇报、状态更新、定时提醒任务、晚间汇报任务。"
- 目录结构：
```
project-ops-orchestrator/
  SKILL.md                     # 主流程编排：触发条件、决策树、步骤、参数
  scripts/
    reminder-schedule.py       # 提醒节点计算（纯函数，无副作用）
    bitable-client.py          # 飞书多维表格封装（完整token校验、重试3次、降级路径）
    render-template.py         # 消息模板渲染（占位符替换）
  assets/
    bitable-schema.json        # 表格字段定义（字段名/类型/选项）
    templates/
      group-reminder.md        # 群提醒模板
      dm-reminder.md           # 私信提醒模板
      evening-report.md        # 晚间客户汇报模板
      daily-check.md           # 每日检查模板
  references/
    rules.md                   # 完整规则库（从蓝氏验证经验提炼，agent 执行时必读）
```

## 参数化设计（config，Skill 开头声明）

每个项目分身使用前需填充：
- project_name：项目名（如 蓝氏奶盾）
- bitable_app_token：飞书多维表格完整 app_token
- bitable_table_id：表 ID
- group_chat_id：项目群 chat_id
- members：负责人列表 [{name, open_id, side(分侧，可选)}]
- reminder_time：主提醒时间（如 10:55）
- evening_report_time：晚间汇报时间（如 19:10）
- side_mapping：分侧映射（如 {"成猫": "陈思安", "幼猫": "花花"}），无分侧可空

## SKILL.md 内容大纲（必须包含的章节）

1. 触发条件：什么消息/任务触发本 Skill（待办记录、状态更新、定时提醒、晚间汇报、每日检查）
2. 配置参数声明
3. 核心流程编排（按顺序）：
   - A. 入群初始化：登记团队成员（name/open_id/分侧），建表格或确认表格字段
   - B. 信息打标：任何群消息/私聊 → 判断是否待办 → 提取字段（日期/分类/次级分类/具体内容/负责人/截止时间/状态/备注/级别/是否日常）→ 写入表格
   - C. 定时提醒：按 D+1/D+2/D+3/D+6 节奏（记录当天为第1天，差值=1/2/3/6 即第2/3/4/7天），群里 @负责人 + 私信各自负责人
   - D. 日常/非日常区分：日常任务每天提醒；非日常已完成不再提醒
   - E. 每日检查：评论区巡查、笔记上线检查等，收到回复记当日 memory，不写表格备注
   - F. 双通道分发：群发整体内容（at 所有人）+ 私信各自相关部分（不交叉）
   - G. 晚间客户汇报：写今日客户汇报（分侧），群里发整体 + at 全员 + 私信分侧内容
4. 决策树（什么情况做什么）：
   - 收到待办 → 打标入表
   - 收到状态更新 → 问清楚再更新状态（铁律）
   - 收到含糊回复 → 不更新，下次继续问
   - 收到"已完成" → 状态改已完成，备注 [日期 姓名确认已完成]，记录保留
   - 被 at 要求回复 / 信息需要反应 → 回复
   - 同事互相 at 的对话 → 不发言，只吸收信息
5. 状态更新铁律
6. API 故障处理（先回人再更新、重试3次、降级记 memory、完整 token）
7. 沟通标准（对同事说话必 at、零 AI 味、结构化表达）
8. 客户汇报用词铁律（具体动作词，禁用抽象包装词）
9. 歧义必问原则
10. 时间标准（北京时间）

## scripts/reminder-schedule.py 需求

纯函数，无副作用，可直接 import 测试：
```python
def compute_reminder_stage(record_date: str, today: str, special_reminder: str | None = None) -> dict
```
- 输入记录日期、今天日期（YYYY-MM-DD）、可选特殊提醒文本
- 若 special_reminder 非空 → 返回 {"mode": "special", "message": special_reminder}（交给 agent 解析频度）
- 否则按差值 day_diff = (today - record_date).days：
  - day_diff == 1 → {"mode": "remind", "stage": 2, "message": "问开始了吗"}
  - day_diff == 2 → {"mode": "remind", "stage": 3, "message": "跟进进展"}
  - day_diff == 3 → {"mode": "remind", "stage": 4, "message": "确认状态"}
  - day_diff == 6 → {"mode": "escalate", "stage": 7, "message": "私聊负责人+群里标记延期+通知逸凡"}
  - 其他 → {"mode": "skip"}
- 注意：记录当天 day_diff=0 不算提醒；差值按自然日计算

## scripts/bitable-client.py 需求

封装飞书多维表格操作，防止 API 故障卡死：
- 必须校验 app_token 完整（拒绝缩写 token，长度 < 20 直接报错提示用完整 token）
- 每次操作最多重试 3 次，连续失败 3 次返回 {"ok": false, "error": ..., "degraded": true}，由 agent 走降级路径（记 memory 标注 [表格待补: 原因]）
- 提供函数：list_records、create_record、update_record（备注追加）、list_fields
- 限流识别：同一参数间歇性失败 = 限流，等 30 秒后最多再试 1 次

## scripts/render-template.py 需求

- 读 assets/templates/ 下的模板文件，做 {{placeholder}} 替换
- 输入模板名 + 变量 dict，输出渲染后的文本
- 模板中支持 {{date}} {{members_at}} {{items}} {{side}} {{project_name}} 等占位符
- members_at：把成员列表渲染成飞书 at 标签串 `<at user_id="ou_xxx">名字</at>`

## assets/bitable-schema.json 需求

字段定义（蓝氏验证过的最终版）：
- 日期（DateTime）
- 具体内容（Text）
- 分类（SingleSelect）：调户-新增人群/新增关键词/成本控制/放量、内容产出、汇报沟通、数据监控、策略规划、调户-新增笔记
- 次级分类（SingleSelect）：同选项，可空
- 负责人（MultiSelect 或 Text，存姓名）
- 截止时间（DateTime 或 Text）
- 状态（SingleSelect）：待开始/进行中/已完成
- 备注（Text）
- 级别（SingleSelect）：S级/A级/B级
- 是否日常（SingleSelect）：日常/非日常

## assets/templates/ 需求

1. group-reminder.md：群提醒模板，含 at 负责人、待办清单（按负责人分组）、截止时间
2. dm-reminder.md：私信模板，只含本人相关条目，语气自然
3. evening-report.md：晚间客户汇报模板：
   - 开头：今日汇报日期 + 项目名
   - 正文按维度分块（搜索/人群/内容/日常），每条 = 具体动作 + 目的
   - 结尾：未完成/待确认项单独列明
4. daily-check.md：每日检查模板（笔记上线检查等）

## references/rules.md 需求（完整规则库，agent 执行时必读）

必须包含以下全部规则（从蓝氏验证经验提炼，一条不落）：

1. 提醒节奏规则：以记录当天为第1天，提醒节点 = 记录后第2天(差值1)、第3天(差值2)、第4天(差值3)、第7天(差值6)；D+7 升级 = 私聊负责人 + 群里标记延期 + 通知逸凡
2. 特殊提醒规则：备注含「特殊提醒：」的记录不走默认节奏，按备注要求执行
3. 状态更新铁律：必须问到才更新，绝不自己猜；已完成记录永不删除/隐藏；删除/隐藏/批量状态变更必须先确认；默认状态=待开始；回复"开始了/在做了/进行中"→进行中（备注 [日期 姓名确认已开始]）；回复"完成了/做好了"→已完成（备注 [日期 姓名确认已完成]）；含糊回复→不更新继续问；进行中也要持续跟进直到已完成
4. 日常/非日常规则：日常任务每天提醒并确认，不因前一天完成跳过；非日常任务状态=已完成就不再提醒
5. 私聊/群发双通道：群发后额外私信每位负责人，只发各自相关，不交叉
6. 分侧规则（如有分侧）：各负责人报各侧；一侧完成≠全部完成；必须追问另一侧
7. 每日检查规则：笔记上线等每日循环确认只记当日 memory，不写表格备注（备注保持干净）
8. 客户汇报用词铁律：具体动作词（增加预算/暂停投放/新增人群），禁用抽象包装词（加码/赋能/深耕/抓手/卡位等营销腔）；汇报是动作清单要可验证，不是创意文案
9. API 故障处理：第一优先级先回复人再更新表格；最大重试3次；3次失败记 memory 标注 [表格待补: 原因] 继续下一条；feishu_bitable 必须传完整 app_token（缩写会 400）；限流等30秒最多再试1次
10. 沟通标准：对同事说话必须 at（无 at 等于没发）；零 AI 味（禁引号装饰、禁星号井号破折号列表体、禁填充词）；结构化表达（结论先行、重点加粗、分块、不超过5要点）
11. 歧义必问：口径不明确必须追问到能做决断，绝不妄断执行
12. 数据有出处：每个数字可追溯，无来源不写，推断标注[推断]
13. 日期不能错：写完再过一遍日期（今天几号/明天几号/截止日周几）
14. 时间标准：所有时间北京时间（GMT+8）
15. 群内响应：同事互相 at 的对话默认不回复只吸收信息；被明确 at 或信息需要反应才回复
16. 级别判定标准：影响程度+紧急程度+任务性质；重要调户/大促/策略规划/未完成关键词打包→S级；日常循环和数据机制→A级；已完成低影响→B级

## 编写要求

- SKILL.md 保持精简（≤120行），详细规则放 references/rules.md，由 SKILL.md 指引必读
- scripts 必须是可运行的 Python 3，无第三方依赖（只用标准库），含 if __name__ == "__main__" 自测
- 所有模板用飞书友好的纯文本格式，不依赖 markdown 渲染
- 代码注释用中文
- 生成后运行 scripts 自测确认无语法错误
