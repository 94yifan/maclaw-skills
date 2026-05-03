---
name: create-subagent
description: 部署新 subagent 分身的标准化 skill。每次创建分身时执行，确保不遗漏任何关键配置。
---

# create-subagent

## 一、这个 skill 用来做什么？

**功能：** 将任意一个新的 subagent 分身标准化接入系统，包含独立 workspace、skills 软链、飞书 bindings、dreaming cron × 2。

**解决的问题：** 每次创建新分身容易遗漏步骤（尤其是 dreaming cron 和 bindings），导致分身能创建但无法正常接收消息或运行。

**适用范围：** 任何新的 subagent 部署，无论是 Social Crawler、CEO、品牌顾问还是未来的小红书研究分身。

---

## 二、具体工作 SOP

### 第一步：确定群绑定

在执行本 skill 之前，必须确认：
- 新 subagent 的飞书群 ID（chatId）
- 新 subagent 的职责定位（一句话描述）

---

### 第二步：创建目录结构

在终端执行：

```bash
SUBAGENT_ID="新分身ID"   # 例：xiaohongshu / brand-consultant
WORKSPACE="/Users/yifansmacmini/.openclaw/workspace/$SUBAGENT_ID"
mkdir -p $WORKSPACE/{skills,memory/.dreams}
```

---

### 第三步：捕获完整人设描述（最关键步骤，必须先执行）

**在写任何文件之前，必须先完成这一步，禁止跳过。**

用户会给出 subagent 的人设描述（身份定位、核心使命、能力范围、行为规范），格式可能是一段文字或多个要点。

收到人设描述后：
1. **用自己的语言复述**用户描述的核心定位，例如："我理解你想要的 {subagent-name} 是这样的：..."
2. **等用户确认**后才继续写文件
3. 用户确认后，将人设内容**完整写入 SOUL.md**，不遗漏任何细节，不用自己的理解去填充空白

**禁止：** 拿到人设描述就开始写文件，用自己之前的理解去补充空白。
**正确流程：** 用户给描述 → 我复述确认 → 用户确认 → 才写入文件

---

### 第四步：创建核心文件（4个）

#### 4.1 SOUL.md — 人设描述已确认后写入，以下为基础结构框架

**必须严格按以下顺序和内容写入，不得修改或简化：**

第1段（身份）：根据已确认的人设描述写入
第2段（当前绑定业务）：根据已确认的人设描述写入
第3段（使命）：根据已确认的人设描述写入
**第4段（原则）：必须原样复制主 SOUL 的第4段（原则），包括所有编号原则和 spawn subagent 行为描述，一条都不许删改**
**第5段（Skill原则）：必须原样复制主 SOUL 的第5段（Skill原则），包含 Step 1-6 的完整内容**
**第6段（方法）：必须原样复制主 SOUL 的第6段（方法）**
**第7段（标准）：必须原样复制主 SOUL 的第7段（标准），包含第一到第八的全部内容**
**第8段（边界）：必须原样复制主 SOUL 的第8段（边界）**
**第9段（协作）：必须原样复制主 SOUL 的第9段（协作）**
**第10段（复盘框架）：必须原样复制主 SOUL 的第10段（复盘框架），包含 Step 1-6 和默认复盘输出格式**
**第11段（Skill分析输出格式）：必须原样复制主 SOUL 的第11段（Skill分析输出格式）**
第12段（自定义能力范围）：根据 subagent 角色写入
第13段（自定义行为规范）：根据 subagent 角色写入

**禁止：** 重新编写、简化、合并、或用自己的理解重写任何第4-11段的内容。这些段落的内容是所有 subagent 与主 agent 保持一致的底层逻辑，必须原样复制。

#### 4.2 IDENTITY.md — 从主 IDENTITY.md 复制，修改以下内容

```markdown
# IDENTITY.md - Who Am I?

- **Name:** {Subagent Name}
- **Creature:** AI 助手
- **Vibe:** 直接、务实，不废话
- **Emoji:** ⚡
```

#### 4.3 AGENTS.md — 直接复制主 AGENTS.md，不修改

路径：`/Users/yifansmacmini/.openclaw/workspace/AGENTS.md`

#### 4.4 MEMORY.md — 从主 MEMORY.md 复制，追加以下内容

在文件末尾追加：

```markdown
## {Subagent Name} 专属背景

- **workspace：** `/Users/yifansmacmini/.openclaw/workspace/{subagent-id}/`
- **职责：** {具体职责描述}
- **飞书群绑定：** {群ID}
- **创建日期：** {日期}
```

---

### 第五步：软链 skills

在终端执行：

```bash
WORKSPACE="/Users/yifansmacmini/.openclaw/workspace/$SUBAGENT_ID"
for skill_dir in /Users/yifansmacmini/.openclaw/workspace/skills/*/; do
  skill_name=$(basename "$skill_dir")
  ln -sf "$skill_dir" "$WORKSPACE/skills/$skill_name"
done
```

软链完成后，用 `ls -la $WORKSPACE/skills/` 确认所有 skills 都是软链（箭头指向主 skills 目录）。

---

### 第六步：注册 agents.list + 重启

在终端执行：

```bash
openclaw config set agents.list --replace
# 在弹出的编辑器中，将以下 JSON 条目添加到 agents.list 数组末尾：
{
  "id": "新subagent-id",
  "workspace": "/Users/yifansmacmini/.openclaw/workspace/新subagent-id",
  "model": {"primary": "minimax/MiniMax-M2.7"},
  "identity": {"name": "新分身名称"}
}
```

保存后重启 gateway：

```bash
openclaw gateway restart
```

验证：`openclaw config get agents.list` 确认新 subagent 出现在列表中。

---

### 第七步：注册 bindings + 重启

在终端执行：

```bash
openclaw config set bindings --replace
# 在弹出的编辑器中，将以下 JSON 条目添加到 bindings 数组末尾：
{
  "agentId": "新subagent-id",
  "match": {"chatId": "群ID"}
}
```

保存后重启 gateway：

```bash
openclaw gateway restart
```

验证：`openclaw config get bindings` 确认新绑定存在。

---

### 第八步：配置 dreaming cron × 2

**7.1 12:00 午后沉思**

使用 cron 工具添加 job：

```json
{
  "name": "{Subagent} Dreaming Noon",
  "agentId": "新subagent-id",
  "schedule": {"kind": "cron", "expr": "0 12 * * *", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 {Subagent} 分身。今天是工作日，进行午后沉思。\n\n1. 阅读你的 MEMORY.md 和 recent memory/\n2. 回顾今天的工作，思考有没有值得记录的重要经验或风险教训\n3. 将值得长期记住的内容以追加方式写入 `/Users/yifansmacmini/.openclaw/workspace/{subagent-id}/memory/YYYY-MM-DD.md`（格式：\\n## [{时间}] Dreaming\\n- 要点），文件不存在就先创建\n4. 完成后静默结束，不需要向任何人报告。"
  },
  "delivery": {"mode": "none"}
}
```

**7.2 22:00 夜间复盘**

使用 cron 工具添加 job：

```json
{
  "name": "{Subagent} Dreaming Night",
  "agentId": "新subagent-id",
  "schedule": {"kind": "cron", "expr": "0 22 * * *", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 {Subagent} 分身。今天结束，进行夜间复盘。\n\n1. 回顾今天完成的所有工作，将今日进展以追加方式写入 `/Users/yifansmacmini/.openclaw/workspace/{subagent-id}/memory/YYYY-MM-DD.md`（今天日期，格式：\\n## [{时间}] Dreaming\\n- 要点），如果文件不存在就先创建\n2. 提炼今天的重大洞察或方法更新到 MEMORY.md\n3. 思考明天最重要的一件事是什么\n4. 完成后静默结束，不需要向任何人报告。"
  },
  "delivery": {"mode": "none"}
}
```

---

### 第九步：验证

部署完成后，按以下清单逐项验证：

| 验证项 | 方法 | 预期结果 |
|--------|------|---------|
| SOUL.md 第3条原则 | `grep "24/7 永动机" $WORKSPACE/SOUL.md` | 有输出 |
| skills 是软链 | `ls -la $WORKSPACE/skills/` | 所有条目箭头指向主目录 |
| agents.list 包含新 subagent | `openclaw config get agents.list` | 新 id 出现在列表中 |
| bindings 包含新群绑定 | `openclaw config get bindings` | 新 chatId 出现在列表中 |
| dreaming cron 存在 × 2 | `openclaw cron list` | 两条，agentId 正确 |
| .dreams 目录存在 | `ls $WORKSPACE/memory/.dreams/` | 目录存在 |
| 分身响应测试 | 在对应群发一条消息 | 60秒内有响应 |

---

### 第十步：分身在群内自我介绍并与用户校验

使用 message 工具，在对应群内发送分身自我介绍：

```
我是逸凡的 {Subagent Name}，负责 {职责描述}。

我的核心能力：
- {能力1}
- {能力2}
- {能力3}

如有需要请随时 @ 我或直接发消息，我会立即响应。
```

发送后，在群内等待用户回复确认。如用户有补充或纠正，将其记录到 MEMORY.md。

---

## 三、未来可复用价值

**这个 skill 解决的是重复性配置问题，不是一次性问题。**

每次创建新 subagent 都需要执行完整9步，这些步骤结构完全固定，只有具体 ID、群绑定、职责定位是变量。未来逸凡会持续创建新的 subagent，每个新分身都能用这个 skill 一次性完成全部配置。

**复用时只需提供：**
- 群 ID（chatId）
- 职责定位（一句话）
- subagent ID

其余全部自动执行，不需要每次手动梳理步骤。

---

## 五、常见错误警告

1. **跳过人设确认步骤**：不先复述确认就开始写文件 → 禁止，必须先确认
2. **修改第4-11段内容**：觉得自己可以"优化"主 SOUL 的原则 → 禁止，原样复制
3. **忘记配置 dreaming cron**：只配了 workspace 就结束 → 必须配 2 个 cron
4. **忘记备份知识图谱**：不配置每日 GitHub 备份 → 禁止，知识图谱必须每日备份
5. **CEO 独立汇报**：所有晚间汇报统一由主 agent 向逸凡汇报，CEO 不独立汇报
