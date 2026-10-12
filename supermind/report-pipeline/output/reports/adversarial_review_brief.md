# 对抗式审查任务（CoT增强版）

**项目**: 王小卤 品牌与赛道分析报告（休闲卤味零食）
**提取声称**: 35 条
**总任务数**: 105 个（每声称3票）
**否决阈值**: ≥2/3票否决则剔除
**审查方法**: CoT 5步推理链
**生成时间**: 2026-10-12 16:17

## 执行说明

审查任务已保存至 `/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/output/reports/adversarial_tasks.json`。

由 openclaw orchestrator 执行：
1. 读取 `adversarial_tasks.json`
2. 为每条声称 spawn 3个并行审查 session（每个使用对应task的prompt）
3. 收集各票 verdict JSON → 运行投票 → 汇总为审查报告
4. 被否决的声称记录在QA日志中，不进入最终报告

## CoT审查清单（每票强制走完）
- **Step 1: 来源核对** — 这个声称的原始来源是什么？我是否实际检索了来源来核对原文？来源真的支持这个声称吗，还是过度引申？
- **Step 2: 反证搜索** — 有没有可信来源反驳或大幅限定这个声称？搜索相反立场的证据。
- **Step 3: 层级审计** — 这个声称申报的evidence_tier配得上它的证据吗？是confirmed/reported/mapped/speculation哪一层？
- **Step 4: 时效检查** — 这个信息还新鲜吗？快速变化的领域里，旧数据要打折。
- **Step 5: 意图判断** — 这是营销稿？PR软文？品牌官方宣传？独立第三方？论坛猜测？

## 声称预览（前10条）
- [CLAIM-001] 这条心智路径分两步走：第一步用可生食这一全新安全标准开创品类，第二步跨越到高品质鸡蛋的代名词（据冯斌公开演讲，evidence_tier：reported）。... (tier:speculation, ch:unknown)
- [CLAIM-002] 在可生食鸡蛋这个细分品类内，黄天鹅销量占比79.6%、渗透率78.2%（2022年4月至2023年3月，evidence_tier：reported），基本等同于品类开创者级别的独占占位。... (tier:speculation, ch:unknown)
- [CLAIM-003] 在更宽的2元以上高价带，黄天鹅市占率约90%（evidence_tier：reported），冯斌本人对外口径则是一块八以上价格区间占比80%多（据冯斌公开演讲，evidence_tier：repor... (tier:mapped, ch:unknown)
- [CLAIM-004] 2023年3月，evidence_tier：reported），基本等同于品类开创者级别的独占占位。... (tier:speculation, ch:unknown)
- [CLAIM-005] 80%多（据冯斌公开演讲，evidence_tier：reported）。... (tier:speculation, ch:unknown)
- [CLAIM-006] 品牌定价锚定约2.65元一枚（evidence_tier：reported），是普通散装鸡蛋约0.5元一枚的5倍左右（价格倍数为推测，evidence_tier：speculation）。... (tier:mapped, ch:unknown)
- [CLAIM-007] 5元一枚的5倍左右（价格倍数为推测，evidence_tier：speculation）。... (tier:mapped, ch:unknown)
- [CLAIM-008] 3元一枚）、德青源（约1到1.5元一枚）等品牌蛋拉开，也把可生食心智和日本标准绑定在一起卖溢价。... (tier:mapped, ch:unknown)
- [CLAIM-009] 连续4年高品质鸡蛋销量全国第一（evidence_tier：reported），京东与盒马可生食鸡蛋品类TOP1（evidence_tier：reported），2026年618天猫、京东、抖音三平台... (tier:speculation, ch:unknown)
- [CLAIM-010] 这些背书共同把黄天鹅钉在高端鸡蛋第一品牌的位置上，也说明它的渠道统治力已经从单一平台扩散到全平台。... (tier:speculation, ch:unknown)