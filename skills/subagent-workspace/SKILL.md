# subagent-workspace

**功能：** 标准化部署一个新的 subagent workspace，包含完整的 SOUL、IDENTITY、AGENTS、MEMORY、skills 软链、dreaming cron。

**适用场景：** 创建新的 subagent 分身时，执行本 skill，确保不遗漏任何关键配置。

---

## 部署清单

### 第一步：创建目录结构

```bash
WORKSPACE="/Users/yifansmacmini/.openclaw/workspace/{subagent-id}"
mkdir -p $WORKSPACE/{skills,memory/.dreams}
```

### 第二步：创建核心文件

每个 workspace 需要 4 个核心文件：

| 文件 | 来源 | 自定义内容 |
|------|------|-----------|
| `SOUL.md` | 从主 SOUL 复制，修改原则第3条 + 使命段 | identity name、核心职责、沟通偏好 |
| `IDENTITY.md` | 从模板创建 | name、creature、vibe、emoji |
| `AGENTS.md` | 从主 AGENTS 复制 | 无需修改 |
| `MEMORY.md` | 从主 MEMORY 复制，精简 | 添加 subagent 专属背景 |

**SOUL 第3条原则（必须）：**
```
3. **24/7 永动机** — 我是24小时永远不停歇的永动机，不存在"休息"的概念。
收到消息立即响应，没有"稍后"、"等一下"、"明天再说"。
每个重要进展或决策必须实时更新到 MEMORY.md，不依赖事后回忆。
```

**SOUL 自定义规则：** 只修改 1-2 处，不要大规模改写。参考：
- 使命段：写清楚这个 subagent 负责什么
- 身份段：写清楚这个 subagent 的角色定位
- 其他段落：尽量保持和主 SOUL 一致

### 第三步：软链 skills

```bash
ln -s /Users/yifansmacmini/.openclaw/workspace/skills/* $WORKSPACE/skills/
```

### 第四步：注册 agents.list

```bash
openclaw config set agents.list --json '[...]' --replace
# 在现有列表中添加：
{
  "id": "{subagent-id}",
  "workspace": "$WORKSPACE",
  "model": {"primary": "minimax/MiniMax-M2.7"},
  "identity": {"name": "{Subagent Name}"}
}
```

然后重启 gateway。

### 第五步：注册 bindings

```bash
openclaw config set bindings --json '[...]' --replace
# 添加新绑定：
{
  "agentId": "{subagent-id}",
  "match": {
    "chatId": "{group-chat-id}"
  }
}
```

然后重启 gateway。

### 第六步：配置 dreaming cron（两次/天）

**12:00 午后沉思：**
```json
{
  "name": "{Subagent} Dreaming Noon",
  "agentId": "{subagent-id}",
  "schedule": {"kind": "cron", "expr": "0 12 * * *", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 {Subagent} 分身。今天是工作日，进行午后沉思。\n\n1. 阅读你的 MEMORY.md 和 recent memory/\n2. 回顾今天的工作，思考有没有值得记录的重要经验或风险教训\n3. 将值得长期记住的内容以追加方式写入 `{workspace}/memory/YYYY-MM-DD.md`（格式：\\n## [{时间}] Dreaming\\n- 要点），文件不存在就先创建\n4. 完成后静默结束，不需要向任何人报告。"
  },
  "delivery": {"mode": "none"}
}
```

**22:00 夜间复盘：**
```json
{
  "name": "{Subagent} Dreaming Night",
  "agentId": "{subagent-id}",
  "schedule": {"kind": "cron", "expr": "0 22 * * *", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 {Subagent} 分身。今天结束，进行夜间复盘。\n\n1. 回顾今天完成的所有工作，将今日进展以追加方式写入 `{workspace}/memory/YYYY-MM-DD.md`（今天日期，格式：\\n## [{时间}] Dreaming\\n- 要点），如果文件不存在就先创建\n2. 提炼今天的重大洞察或方法更新到 MEMORY.md\n3. 思考明天最重要的一件事是什么\n4. 完成后静默结束，不需要向任何人报告。"
  },
  "delivery": {"mode": "none"}
}
```

**关键要求（必须写入 prompt）：**
- 使用**绝对路径**，不是相对路径
- 使用**追加写入**（append），不是覆盖
- 文件路径：`{workspace}/memory/YYYY-MM-DD.md`
- 格式：追加 `## [{时间}] Dreaming` 条目块
- 每个 subagent 的 memory 存放在自己独立的 workspace 里

### 第七步：创建 .dreams 目录

```bash
mkdir -p {workspace}/memory/.dreams
```

这是 OpenClaw 的 memory recall 目录，必须存在。

---

## 模板文件内容

### SOUL.md 自定义段示例

```markdown
## 使命

负责 {具体职责}。

**沟通标准：** 简洁、清晰、不废话。结论先行，有判断，有边界。

## 身份

- 我是逸凡的 {subagent-role} 分身
- 负责：{具体业务范围}
- 风格：{风格描述}
```

### MEMORY.md 必含段

```markdown
# MEMORY.md - {Subagent Name} 长期记忆

## 身份
- **Name:** {Subagent Name}
- **职责：** {具体职责}
- ** workspace：** {绝对路径}

## 技术环境
- OpenClaw Chrome DevTools 端口：18800
- 其他 subagent 特定配置...

## 已安装 Skills
（软链自 /Users/yifansmacmini/.openclaw/workspace/skills/）

## 重大教训
- （持续积累）
```

---

## 验证清单

部署完成后，逐一验证：

- [ ] SOUL.md 第3条原则是"24/7 永动机"
- [ ] skills 目录是软链（`ls -la` 检查）
- [ ] `openclaw config get agents.list` 包含新 subagent
- [ ] `openclaw config get bindings` 包含新群绑定
- [ ] `curl -s http://localhost:18789/api/cron/list | jq` 包含两条 dreaming cron，agentId 正确
- [ ] workspace/memory/.dreams 目录存在
- [ ] 在对应群发消息，subagent 能在 60 秒内响应
