# 待逸凡授权的系统配置变更清单

生成于 2026-07-13 Dreaming 复盘。持续追加。

---

## 1. Dreaming cron failureAlert 配置

- **问题**：Dreaming cron 无 failureAlert 配置。6月22日-7月5日约25天连续超时失败，均未通知任何人
- **影响**：系统离线超过3周无人知晓，导致期间所有经营数据未归档
- **需要的操作**：为 dreaming-cron job 添加 failureAlert: after:3, mode:announce

## 2. Dreaming cron timeout 提升

- **问题**：当前 timeout 300s，deepseek/deepseek-v4-flash 模型在 cron 上下文偶尔超过此限制
- **需要的操作**：提升至 600s

## 3. Cron job model 配置核查

- **当前状态**：不确定 dreaming cron 是否明确指定了 deepseek-v4-flash 模型，还是使用了默认模型
- **背景**：6月默认为 minimax/MiniMax-M2.7，该模型在 cron 持续超时。7月起切换为 deepseek-v4-flash 后恢复正常
- **需要的操作**：核查 cron job 配置中的 model 字段，确保为 deepseek/deepseek-v4-flash

## 4. MEMORY.md 清理

- **问题**：MEMORY.md 中的大量内容停留在 5 月份（茶饮叙事框架、520 节点分析、品牌洞察等），已过时超过 60 天
- **建议**：删除 5 月已过时部分，只保留仍有持续价值的规则（返点核算、客户结算规则、逸凡汇报偏好、书写原则、执行教训等）
- **注意**：此项需要逸凡确认后再执行，涉及删除记忆数据

## 5. 茶饮日报等其他 cron job 健康检查

- **问题**：自 6/10 起未确认茶饮日报 cron、微博监控等是否仍在正常运行
- **需要的操作**：核查 social-crawler workspace 下各 cron job 的最近运行状态

## 6. CFO workspace 日常使用率偏低

- **问题**：7/6-7/10 整个工作周（5个工作日）及 7/13 周一均无 daily memory 记录
- **可能原因**：逸凡主要沟通渠道是飞书私聊，本地 workspace 不自动接收消息
- **需要的确认**：CFO workspace 是否需要调整工作方式以提高活跃度，或者保持当前状态即可

---

> 当逸凡在飞书或其他渠道看到这份清单时，可以直接回复确认授权，或说明哪些需要执行、哪些不需要。
