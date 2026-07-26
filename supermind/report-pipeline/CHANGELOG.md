# BREAC Brand Scan Pipeline — CHANGELOG

## v2.0 (2026-07-26) — Codex Fusion

### 核心基础设施

**证据层级系统（Evidence Tier System）**
- 四层定义：confirmed（已确认）/ reported（报道层）/ mapped（生态映射）/ speculation（推测）
- 贯穿全Pipeline：从数据采集即带tier标签，对抗审查后层级只能降不能升
- 正文默认隐藏tier，附录显示完整tier链
- 三条关键纪律：pipeline≠orders, qualification≠volume ramp, 生态相邻≠量产订单

**对抗式审查（Adversarial Review）**
- 3票制独立验证：每条关键声称→3个agent并行反驳→≥2有效票+否定<2才存活
- 审查清单5项：来源支撑/反证/来源质量/过期/营销稿
- 默认怀疑：不确定时refuted=true
- 与机械QA分工：对抗审查查"对不对"，机械QA查"全不全"

### 新增分析模块

**ch2 产业链地图+卡口识别**
- 产业链价值流向图：segments数组（角色/瓶颈风险/主要玩家/议价力）
- 关键卡口识别：三问（供给紧不紧/替代难不难/市场理解了没有）→自动定priority(P0/P1/P2)

**ch3 内容类型五分类**
- 五类型：曝光型/涨粉型/收藏型/转化型/人设型
- 对深度品牌执行
- 判断品牌内容增长系统，识别重复爆款规律

**ch4 用户痛点挖掘**
- 数据来源：天猫评价/小红书吐槽帖/微博评论/抖音评论区/天猫问大家
- 输出pain_points数组（theme/keywords/frequency/quote/opportunity/evidence_tier）

**ch5 量化粗算**
- 四件套：BOM拆解/收入拆分/历史类比/市值错配（上市公司竞品适用）
- 每条假设标注evidence_tier
- 目标：数量级判断，非精确估值

**ch6 机会地图**
- 四维扫描：竞争激烈度×赛道增速×创业机会×内容供给缺口
- 2×2矩阵（金矿/红海/鸡肋/陷阱）+机会排序

**附录扩展**
- 附录B：用户痛点数据库
- 附录C：竞品内容类型分析

### Pipeline 结构变化
- 从16步扩展至18步（新增对抗式审查 + 附录生成）
- 新增子步骤：5.1产业链地图、7.1内容类型、8.1量化粗算、9.1机会地图
- all_steps支持浮点数步骤编号（5.1, 7.1等），保持向后兼容

### 改动文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| report_schema.json | 重构 v1.5→v1.6 | 新增11个section/子节，所有新字段optional |
| report_playbook.md | 重写 v2.0 | 18步Pipeline+新增4章规范（证据/内容/对抗/七章） |
| SKILL.md | 更新 v2.0 | 新增模块列表+证据层级简介+并行取证+对抗式审查说明 |
| pipeline.py | 增强 | 新增4个step handler(5.1/7.1/8.1/9.1/11.1/12.1)，all_steps扩展至18步 |

### 向后兼容
- 所有新增schema字段均为optional
- pipeline.py维持现有_step_execute结构不变
- project_config新增modules_enabled开关，不启用不影响旧项目

### Bug修复（2026-07-26）

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | pipeline.py | P0 | 修正 Step 6/7 标签互换（Step 6=竞品五维扫描，Step 7=本品五维扫描）|
| 2 | adversarial_verify.py | P0 | extract_key_claims() 添加 source_url 字段，CoT prompt 展示来源URL |
| 3 | adversarial_verify.py | P0 | content/为空时 step_fail→step_skip，pipeline 不崩溃 |
| 4 | content_gen.py | P0 | content_dir() 统一使用 project_config 参数，确保读写路径一致 |
| 5 | qa_check.py | P1 | 新增 check_evidence_tier_consistency()：tier_inflation/tier_downgrade_only/key_discipline/unmarked_claims |
| 6 | content_gen.py | P1 | writing_hard_rules 抽取为模块级常量 WRITING_HARD_RULES，消除6处重复 |
| 7 | charts.py | P1 | 新增 _get_cjk_font() 跨平台字体检测（macOS/Linux/Windows 自动适配）|

---

## v1.6 (2026-07-22) — 康尔馨复盘

12项固化修复（详见康尔馨项目复盘记录）

## v1.5 (2026-07-18) — 榴芒一刻复盘

- 颗粒度检查 + 图表嵌入验证 + 命名规则 + 创始人研究弹性触发
- 跨行业适配器（消费品/SaaS/服务/制造）
