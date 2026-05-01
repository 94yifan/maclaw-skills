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

### 第四步：汇报新功能

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
