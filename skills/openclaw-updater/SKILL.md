---
name: openclaw-updater
description: 每天 22:30 自动检查 OpenClaw 更新，发现更新后执行升级并汇报新功能。
---

# openclaw-updater

## 一、这个 skill 用来做什么？

**功能：** 每天 22:30 自动检查 OpenClaw 是否有新版本，如有则在后台静默升级，升级完成后向逸凡汇报本次更新内容。

**解决的问题：** OpenClaw 更新后，我往往不会主动告知有什么新功能，逸凡也不知道系统发生了什么变化。这个 skill 把"检查→升级→汇报"变成自动化流程。

**适用范围：** 主 agent 和所有 subagent 的 OpenClaw 运行环境。

---

## 二、具体工作 SOP

### 第一步：检查更新

```bash
openclaw update check
```

检查是否有可用更新。

---

### 第二步：如有更新，执行升级

```bash
openclaw update run
```

等待升级完成。OpenClaw 升级后会自动重启 gateway（SIGUSR1）。

**关键：** update.run 完成后不等于 gateway 已经用新版本跑起来——需要等 gateway 重启生效（约2-3秒）。用 `openclaw gateway status` 确认新版本已经在跑，再进行第三步。

如果 gateway 状态异常（如卡在旧的进程上），手动重启：
```bash
openclaw gateway restart
```

### 第三步：验证新版本

```bash
openclaw gateway status
openclaw version
```

确认版本号已更新、gateway 进程已刷新。

---

### 第四步：重建所有 subagent cron job（关键防呆）

OpenClaw 升级后，所有带 `agentId` 的 cron job 的模块路径哈希会过期（如 `delivery-subagent-registry.runtime-旧哈希.js` → `delivery-subagent-registry.runtime-新哈希.js`），直接触发 `ERR_MODULE_NOT_FOUND`。

**必须重建所有 `agentId!=main` 的 cron job。**

查询并重建步骤：

```bash
# 1. 列出所有 cron job，找到 agentId 不是 main 的
openclaw cron list --json | python3 -c "
import sys,json
data=json.load(sys.stdin)
for j in data.get('jobs',[]):
    if j.get('agentId') not in (None,'main',''):
        print(f\"REBUILD: {j['id']} agentId={j['agentId']} name={j['name']}\")
"

# 2. 对每个需要重建的 job：
#    a. 记录它的 schedule/payload/delivery/name
#    b. openclaw cron rm <id>
#    c. openclaw cron add <同配置>
```

**重建原则：**
- `agentId=main` 的不需要重建（走 main agent 路径，不触发 subagent delivery）
- `agentId=social-crawler`、`agentId=ceo` 等需要重建
- 重建后新 job 的模块路径哈希是当前版本的，不会再报错

**防呆自动化（推荐）：** 在 `openclaw update run` 之后立即执行重建，而不是等下次 cron 触发。避免定时任务先跑一次报错。

---

### 第五步：汇报新功能

升级完成后，用自然语言向逸凡汇报：

- **本次更新内容：** 这次升级解决了什么问题，有什么新功能
- **对系统的影响：** 是否需要调整配置或重置任何设置
- **是否需要人工介入：** 如有需要重启服务或修改配置，明确告知

汇报格式与 skill 汇报一致——描述性段落，不用清单体。

---

## 三、未来可复用价值

每次 OpenClaw 升级后，逸凡需要知道：
- 升级了什么
- 是否有新的配置选项需要调整
- 是否有新的 tool 或 capability 可以使用

这个 skill 把这个信息差消除，变成日常自动化的一部分。

**复用前提：** 只需要确保机器可以访问网络，其余全部自动执行。