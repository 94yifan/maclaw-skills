# GLM Skill 生成报告：project-ops-orchestrator

生成时间：2026-08-14 11:07 GMT+8

## 文件清单

| 文件路径 | 行数 | 说明 |
|---------|------|------|
| `SKILL.md` | 106 | 主流程编排，含 frontmatter（name + description） |
| `scripts/reminder-schedule.py` | 96 | 提醒节点计算纯函数，含 __main__ 自测 |
| `scripts/bitable-client.py` | 316 | 飞书多维表格封装，token校验/重试3次/降级/限流识别 |
| `scripts/render-template.py` | 271 | 模板渲染引擎，{{placeholder}}替换 + at标签渲染 |
| `assets/bitable-schema.json` | 114 | 表格字段定义（10个字段，含选项） |
| `assets/templates/group-reminder.md` | 10 | 群提醒模板 |
| `assets/templates/dm-reminder.md` | 12 | 私信提醒模板 |
| `assets/templates/evening-report.md` | 20 | 晚间客户汇报模板 |
| `assets/templates/daily-check.md` | 12 | 每日检查模板 |
| `references/rules.md` | 105 | 完整16条规则库（中文） |

总文件数：10 个
总行数：1062 行

## 自测结果

### 1. 语法检查（py_compile）
- ✅ `reminder-schedule.py` — 无语法错误
- ✅ `bitable-client.py` — 无语法错误
- ✅ `render-template.py` — 无语法错误

### 2. reminder-schedule.py 自测
- ✅ day_diff=0（当天）→ skip
- ✅ day_diff=1 → stage 2，"问开始了吗"
- ✅ day_diff=2 → stage 3，"跟进进展"
- ✅ day_diff=3 → stage 4，"确认状态"
- ✅ day_diff=6 → escalate，stage 7
- ✅ day_diff=4/5（非提醒节点）→ skip
- ✅ 特殊提醒文本 → mode=special
- ✅ 空白特殊提醒 → 走默认节奏
- ✅ None 特殊提醒 → 走默认节奏

### 3. render-template.py 自测
- ✅ 单个 at 标签渲染
- ✅ 多人 at 标签串渲染
- ✅ 空成员列表处理
- ✅ items 按负责人分组渲染
- ✅ 空待办列表占位文本
- ✅ 模板字符串占位符替换
- ✅ 未提供变量替换为空字符串
- ✅ 从文件读取模板并渲染

### 4. bitable-client.py 自测
- ✅ 空 token 被拒绝（degraded=True）
- ✅ 缩写 token（长度<20）被拒绝
- ✅ 有效格式 token 请求失败正确降级
- ✅ update_record token 校验拦截
- ✅ validate_app_token 直接调用校验
- ✅ 限流检测逻辑（429/含"限流"字样）

## 规格符合性检查

| 规格要求 | 状态 | 说明 |
|---------|------|------|
| SKILL.md ≤120行 | ✅ | 106行 |
| frontmatter name + description | ✅ | 含触发关键词 |
| description 引号包裹 | ✅ | 双引号包裹 |
| reminder-schedule.py 纯函数 | ✅ | 无副作用 |
| reminder-schedule.py 含 __main__ 自测 | ✅ | 10个测试用例 |
| bitable-client.py token校验 | ✅ | 长度<20拒绝 |
| bitable-client.py 重试3次 | ✅ | MAX_RETRIES=3 |
| bitable-client.py 降级返回 | ✅ | {"ok":False,"degraded":True} |
| bitable-client.py 限流识别 | ✅ | 429+30秒等待+1次额外重试 |
| bitable-client.py 含 __main__ 自测 | ✅ | 6个测试用例 |
| render-template.py {{placeholder}}替换 | ✅ | 正则替换 |
| render-template.py at标签渲染 | ✅ | `<at user_id="ou_xxx">名字</at>` |
| render-template.py 含 __main__ 自测 | ✅ | 8个测试用例 |
| bitable-schema.json 10个字段 | ✅ | 日期/具体内容/分类/次级分类/负责人/截止时间/状态/备注/级别/是否日常 |
| 分类9个选项 | ✅ | 调户-新增人群/新增关键词/成本控制/放量/内容产出/汇报沟通/数据监控/策略规划/调户-新增笔记 |
| 状态3个选项 | ✅ | 待开始/进行中/已完成 |
| 级别3个选项 | ✅ | S级/A级/B级 |
| 是否日常2个选项 | ✅ | 日常/非日常 |
| 4个模板文件 | ✅ | group-reminder/dm-reminder/evening-report/daily-check |
| rules.md 16条规则 | ✅ | 全部包含，中文 |
| 代码只用标准库 | ✅ | 无第三方依赖 |
| 代码注释用中文 | ✅ | 全部中文注释 |
| 无规格外额外文件 | ✅ | 已清理 __pycache__ |

## 偏差说明

无偏差。所有文件均严格按照规格说明书生成，未遗漏任何需求，未添加规格外文件。
