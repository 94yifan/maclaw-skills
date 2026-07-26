# 0726 Brand Scan Skill 优化 — 完整分析记录

> 生成时间: 2026-07-26 14:00
> 触发: 逸凡分享 aron厚玉 微信公众号文章《如何用 Codex 在 1 小时内快速了解陌生行业》
> 目标: 将文章方法论 + Codex Pipeline infra 设计模式融入 BREAC Industry Brand Scan Pipeline
> 状态: 待逸凡审阅后执行修改

---

## 一、aron厚玉文章核心方法论

**文章**: 《如何用 Codex 在 1 小时内快速了解陌生行业》
**作者**: aron厚玉
**链接**: https://mp.weixin.qq.com/s/UzikNhV0jbZDiMwnF-EIdg

### 五步法概述

**Step 1: 建立行业数据库**
- 品牌数据库（Top 100品牌，含名称/官网/产品/价格/渠道/规模/卖点/创始人/社媒）
- 产品数据库（按市场规模排序，拆解为成分/评价/优缺点/爆款品牌/市场规模）
- **用户痛点数据库**（从Reddit/社区提取：高频抱怨、需求、问题、目标）← "用户的钱都藏在痛点里"
- 内容数据库+流量渠道（YouTube/TikTok/Instagram/X/Newsletter头部账号+最高互动内容）
- **关键词数据库**（Google/Amazon/Reddit/YouTube/TikTok按意图分类：Commercial/Informational/Comparison/Review/Buying Intent）

**Step 2: 反向拆解行业内怎么赚钱**
- 建立竞品数据库
- 拆导航栏（决定利润产品/流量产品/转化产品）
- 拆Collection（真正的成交路径）
- 拆Product Tag（用户怎么搜索、系统怎么理解产品）
- 拆SEO结构（头部玩家在写什么内容）
- 拆Blog内容（最高流量、更新频率、内链结构）
- 拆社媒内容（按类型：曝光/涨粉/收藏/转化/人设）

**Step 3: 研究行业内容生态**
- 不研究1个号，研究100个号
- 找流量收割机（90天内点赞/评论/转发/播放Top100）
- **内容类型五分类**：曝光型/涨粉型/收藏型/转化型/人设型
- 识别重复爆款规律（什么选题反复爆、什么结构反复爆、什么标题反复爆）
- "一次爆可能是运气，十次爆一定是规律" ← 核心洞察
- 建立内容数据库作为增长系统

**Step 4: 建立行业知识地图**
- 数据库解决存储，地图解决理解
- 建立分层行业地图（Level1→2→3）
- 每个节点建知识卡片（概览/公司/工具/趋势/机会）
- 建立跨行业连接（网状结构，不是树状）
- **机会地图**：竞争最激烈/增长最快/创业机会最好/内容供给缺口

**Step 5: 做成私有知识**
- 从搜索模式切换到订阅模式
- 建立行业信息源（每个平台Top50）
- RSS监控系统
- 竞品监控系统（每周：新品/Collection/LP/Blog/关键词变化）
- 内容监控系统（每日增长跟踪）
- 自动生成周报、自动更新行业地图
- 从知识库升级为情报系统

### 文章中我们Pipeline已有覆盖的部分
- 品牌数据库 → 三档分类（focus/deep/reference/summary）+五维扫描
- 产品数据库 → 四类品分析
- 竞品拆解 → Step 7 竞品五维扫描
- 行业格局 → Porter五力+竞品矩阵+行业趋势
- 趋势分析 → 三趋势模型（行业风向/内容热点/用户情绪）
- 创始人研究 → Step 11
- 创品策略 → Step 10

### 文章中我们Pipeline没有的（5个gap）
1. 用户痛点数据库（从社区讨论系统性挖掘痛点）
2. 内容类型五分类框架（曝光/涨粉/收藏/转化/人设）
3. 重复爆款规律识别（什么选题/结构/标题反复爆）
4. 机会地图四维扫描（竞争激烈度/增长速度/创业机会/内容供给缺口）
5. 关键词意图分类体系（Commercial/Informational/Comparison/Review/Buying Intent）


## 二、Codex 生产级 Workflow 源码分析

逸凡指出文章背后应该是现成的Skill/Pipeline，要求下载分析。实际找到的不是aron厚玉个人skill，而是Codex生态中两个生产级研究工作流，来自 six-ddc/skills 仓库。

### 2.1 deep-research-extracted（Anthropic官方深度研究）

**来源**: six-ddc/skills/workflows/deep-research-extracted.js
**原始出处**: Anthropic Claude Code 内置 deep-research workflow（从 v2.1.162 二进制提取）
**许可证**: (c) Anthropic

**Pipeline: Scope → Search → Fetch+Extract → Verify → Synthesize**

```
Phase 0: Scope
  - 输入: 研究问题
  - 动作: 分解为5个互补搜索角度（涵盖不同侧面：broad/primary, academic/technical, recent news, contrarian/skeptical, practitioner/implementation）
  - 输出: JSON (question + angles数组，每个angle有label/query/rationale)

Phase 1: Search（并行）
  - 输入: 5个搜索角度
  - 动作: 5个并行WebSearch agent，每路返回4-6条最相关结果
  - 去重: URL规范化后去重（normURL函数：hostname + pathname lowercase）
  - 预算: MAX_FETCH=15（最多抓取15个来源）
  - 排序: 按relevance(high>medium>low)排序

Phase 2: Fetch+Extract（并行，无barrier）
  - 输入: 去重后的URL列表
  - 动作: 并行WebFetch抓取每个来源
  - 提取: 每条来源提取2-5条可证伪的声称(falsifiable claims)
  - 标记: sourceQuality (primary/secondary/blog/forum/unreliable) + publishDate
  - 每条声称: claim文本 + 支撑quote + importance(central/supporting/tangential)
  - Fail-safe: fetch失败→返回sourceQuality="unreliable" + claims=[]
  - 排序: importance rank × sourceQuality rank → 取Top MAX_VERIFY_CLAIMS(25)

Phase 3: Verify（3票对抗审查）
  - 每条声称派3个独立agent尝试反驳（VERIFY_PROMPT）
  - 审查清单5项: 来源是否支撑声称/有无反证/来源质量是否匹配/是否过期/是否营销稿
  - 默认怀疑: 不确定时refuted=true
  - 法定人数: 至少REFUTATIONS_REQUIRED(2)个有效投票+refuted<REFUTATIONS_REQUIRED才存活
  - 弃权处理: 弃权过多=未裁决，不进入报告
  - 输出: 每条声称带 verdicts数组 + refutedVotes + survives布尔

Phase 4: Synthesize（合并+报告）
  - 输入: 存活的声称(confirmed) + 被否决的声称(killed)
  - 动作: 合并语义重复的声称→合并来源→分组为findings→分配置信度
  - 置信度: high(多一手来源+全票通过)/medium(二手来源或分票)/low(单来源或博客级)
  - 输出: executive summary + findings数组(claim/confidence/sources/evidence/vote) + caveats + openQuestions
  - Fail-safe: 合成失败→返回原始验证声称

**关键设计模式**:
- pipeline()原语: fan-out并行→每个结果立即进入下一阶段（无barrier）
- parallel()原语: 完全并行
- JSON Schema强制结构化输出（SCOPE_SCHEMA/SEARCH_SCHEMA/EXTRACT_SCHEMA/VERDICT_SCHEMA/REPORT_SCHEMA）
- URL去重: normURL规范化（hostname + pathname）
- 预算管理: MAX_FETCH=15, MAX_VERIFY_CLAIMS=25
- 重要性排序: importance × quality × relevance
- Fail-safe: 每步有降级策略
```

### 2.2 serenity-analysis（Serenity投资方法论工作流）

**来源**: six-ddc/skills/workflows/serenity-analysis.js
**方法论**: X投资者 @aleabitoreddit（"Serenity"）的投资分析框架
**配套SKILL**: six-ddc/skills/skills/serenity-investor/SKILL.md（完整人格模拟skill）

**自包含设计**: 方法论常量（PERSONA + VOICE）直接写在workflow内，不依赖外部skill文件

**Pipeline: Scope → Map → Research → Verify → Quant → Verdict → Synthesize → Critique → Finalize**

```
Phase 0: Scope
  - 解析目标，判定 stock/industry 模式
  - 规范化标的名称（TICKER / 公司名（市场））
  - 定位架构语境（属于哪个下一代架构切换语境）
  - 抽取关键问题

Phase 1: Map（仅industry模式）
  - 画产业链地图：segments（每个环节的角色+瓶颈风险）
  - 初筛chokepoint候选：name/ticker/segment/whyChokepoint
  - chokepoint初判：supplyTight/substitutionHard/marketUnderstands
  - 按priority排序

Phase 2: Research（六路并行取证）
  每路独立agent + 专门研究brief:

  Lane 1: 财务与filings
    - 最新财报+guidance、产能预订/客户预付款/volume orders
    - ATM/shelf/可转债/float结构、SBC、现金跑道、毛利目标
    - 必须明确回答：有没有toxic融资结构（硬否决项）
    - A股标的: 走ashare-data-kit skill取一手财务数据

  Lane 2: 供应链与产业报道
    - 券商supplier note（MS/GS类）
    - UDN/Digitimes/TrendForce类产业媒体
    - 客户/订单线索、qualification与量产进展
    - 注意区分development contract与volume order

  Lane 3: 股权与资金结构
    - 机构持仓变化（13F/大额持股披露）
    - 空头比例与变化（空头结构=squeeze燃料）
    - 托管行流向（float被谁拿走）
    - 指数纳入/剔除（带回指数权重与流通盘数据）
    - NASDAQ/ADR/双重上市通道、sell-side覆盖变化、内部人买卖
    - 回答"机构路径走到哪一步"

  Lane 4: 技术与竞争格局
    - 在架构扩散链的位置
    - 替代方案与多供方风险
    - sole-source可能性
    - 市场是否错误分类（integrator vs core IP等）
    - design-out风险

  Lane 5: 社区与传播
    - X/Reddit/媒体关注度与叙事
    - 大V讨论情况（含@aleabitoreddit本人）
    - 媒体唱多/唱空
    - retail拥挤度与反身性风险

  Lane 6: 政策与地缘一手文件
    - CHIPS Act/EU Chips Act申请与项目文件
    - NIST/白宫fact sheet
    - 出口管制清单与技术封锁
    - 盟友供应链战争中的位置
    - 中国暴露与司法/政策折价

  每路输出: facts数组（每条含fact/tier/source/asOf/direction/loadBearing）+ laneSummary

Phase 3: Verify（多票对抗审查）
  - 每条事实送审（VERIFY_PROMPT）
  - 审查清单: 来源是否支撑/有无反证/层级审计/是否过期/是否营销内容
  - 层级审计（核心纪律）: tierAfterAudit只许持平或降级，不许升级
  - pipeline≠orders、qualification≠volume ramp、生态相邻≠量产订单
  - 法定人数: QUORUM + 否决阈值REFUTES
  - A股事实优先用ashare-data-kit复核

Phase 4: Quant（量化粗算）
  四件套（挑适用的）:
  - bom-build: 单机价值量×出货量×市占haircut→收入→forward P/E情景
  - revenue-build: 按产品线逐项加总（参照公司guidance/产能口径）
  - historical-analog: 找已验证赢家的重估路径做锚（"the next $LITE"式）
  - mcap-mismatch: 上游卡口市值vs整条下游对它的依赖度

  每条假设标注建立在哪层证据上；建立在unverified或mapped/speculation级事实上的假设必须在modelNote自首

Phase 5: Verdict（决策算法裁决）
  按顺序跑:
  1. 架构定位
  2. chokepoint三问（基于存活事实回答，不许臆测）
  3. 分类纠错（市场放对类别了吗）
  4. 机构路径走到哪一步
  5. 反面筛选（触发硬否决→vetoed=true，action只能avoid/short）
  6. 信念分级（high-conviction/research-thesis/watchlist/info-only/avoid）
     - 核心纪律: 证据多为mapped/speculation时最高只能research-thesis或watchlist
  7. 时间桶（~6mo/~2y/5y+/too-early）
  8. 仓位计划（生命周期式: 试错仓条件→验证信号→trim触发）
  9. bull/bear case
  10. whatWouldChangeMyMind

Phase 6: Synthesize（跨标的汇总排序）
  - 写中文初稿（用Serenity口吻）
  - 行业模式: 先产业链地图+价值流向→按优先级逐标的
  - 标的模式: 架构定位→chokepoint论证→催化剂→量化→风险

Phase 7: Critique（对抗审稿）
  专门找:
  - tierInflation: 把低层证据写成高层确定性的地方
  - missingNegativeScreens: 没查或没写的反面筛选项
  - vetoConsistency: vetoed=true的标的是否仍给了buy/add
  - bullBias: 只组装多头证据、bear case缺席或敷衍
  - unstatedAssumptions: 没标明的假设
  - staleOrUnverifiedData: 过期/未经核实却当事实用的数据
  - missingThemes: 遗漏的主题
  - coverageVerdict: ok/needs-revision

Phase 8: Finalize
  - 按审稿修订
  - 产出双层报告: 长帖（公开，high-level）+ 底稿（完整证据链）

**证据四层系统（serenity-analysis核心纪律）**:
| 层级 | 含义 | 措辞 |
|------|------|------|
| confirmed | 公开订单/公司一手披露 | 直说 |
| reported | 券商/产业媒体报道（MS/GS/UDN/Digitimes/TrendForce） | "据MS/UDN报道" |
| mapped | 生态相邻/供应链表推断 | "我把它映射到" |
| speculation | 推断猜测 | "我认为/我推断/likely" |

关键纪律:
- 层级只能降不能升（tierAfterAudit ≤ 原tier）
- pipeline≠orders, qualification≠volume ramp, 生态相邻≠量产订单
- 绝不把低层证据写成confirmed

**Serenity方法论核心常量（PERSONA）**:
- 架构先行: 先判断下一代系统怎么变，再问目标卡在扩散链哪一环；不从当前EPS出发
- chokepoint三问: 供给紧不紧？替代难不难？市场理解了没有？三者同时成立才是高信念卡口
- 分类纠错: 检查市场是否放错类别（integrator vs core IP等）→错分类=错multiple
- 选择性财报: 低配trailing EPS，高配能证明放量路径的指标
- 机构路径: retail先发现→机构后进入→指数/流动性/coverage兑现（frontrunning the institutions）
- 地缘供应链战争: AI硬件重估大背景是allied chokepoint weaponization
- 反面筛选（硬否决）: toxic ATM/大额dilution/NAV溢价/closed-end包装/logo partnership/只讲power capacity没真实合同/retail exit liquidity
- 时间桶: ~6mo/~2y/5y+/too-early（"原型期进场就是去当稀释对象"）
- 仓位生命周期: 小仓试错→验证后向上加仓（不是补跌）→trim只因假设被证伪（不因价格回撤）→让赢家复利少卖

**Serenity口吻（VOICE）**:
- 第一人称、叙事式长帖
- 先说为什么这个环节重要→供应链细节（谁买谁的什么）→历史类比→结论
- 中文自然口语（说人话不翻译腔），ticker/术语保留英文
- return%当记分牌
- 强观点+免责并存（DYOR/NFA/personal thoughts）
- 证据分层措辞: confirmed直说/reported写"据XX报道"/mapped写"我映射到"/speculation写"likely"


## 三、两套Infra对比

### 我们的Pipeline Infra（BREAC Industry Brand Scan v1.6）

**架构**: Python脚本驱动，16步顺序执行
**核心文件**:
- pipeline.py（主控脚本，argparse CLI, 逐_step_execute）
- config.py（ReportSchema + ProjectConfig 配置管理器）
- report_schema.json（v1.5，机器可读的完整报告schema）
- report_playbook.md（v1.5，人类可读的操作手册）
- steps/content_gen.py（prompt构建+LLM调用生成各章内容）
- steps/qa_check.py（5层机械QA: 结构/内容/图表/颗粒度/交付）
- steps/data_collection.py（电商+财报+行业研报采集）
- steps/data_dispatch.py（按schema.mapping自动分发）
- steps/charts.py（ECharts图表生成）
- steps/docx_builder.py（python-docx文档组装）

**执行模式**:
- 纯串行（Step 1→2→3→...→16）
- 每个Step是独立的Python函数调用
- 通过project_config.json配置项目参数
- 通过report_schema.json定义报告结构和规则
- QA是事后机械检查（regex/行数/文件存在性）
- 内容生成：构建prompt模板→保存为prompt文件→人工或LLM填充→保存md

**特点**:
- 配置驱动，跨行业可复用
- Schema定义了完整的报告结构和方法论
- 五维分析模型（市场渠道/品牌力/产品/趋势/人群）是核心框架
- 有多行业适配映射（消费品/SaaS/服务/制造）
- 有严格的写作规范（完本检查/禁止AI腔/结论先行）
- 有颗粒度硬性标准（≥800行/≥60KB/深度品牌≥30行/创始人≥40行/创品≥10个方向）

### Codex Workflow Infra

**架构**: JavaScript workflow runner（内置于Codex CLI）
**核心设计模式**:

1. **Phase系统**
   - 每个Phase: name + description + phases数组（title/detail）
   - meta.whenToUse: 触发条件描述
   - 每个Phase有JSON Schema约束输出格式

2. **三种执行原语**
   - pipeline(items, mapFn, thenFn): fan-out并行→每个结果立即进入下一阶段（无barrier）
   - parallel(tasks[]): 完全并行，等所有完成
   - agent(prompt, {label, phase, schema}): 单个agent调用

3. **结构化输出强制**
   - 每个agent调用必须指定schema
   - 输出即时验证（不符合schema=无效）
   - 不是事后检查，是执行时强制

4. **去重与预算管理**
   - URL规范化去重（normURL）
   - MAX_FETCH/MAX_VERIFY_CLAIMS常量
   - 按relevance×importance×quality排序取Top N

5. **证据层级内嵌**
   - 每条数据从采集起就带tier标签
   - 贯穿全Pipeline，最终输出可选标注/隐藏

6. **对抗式验证**
   - 独立验证阶段，不同于机械QA
   - 多票制（默认怀疑，不确定时refuted=true）
   - 法定人数+否决阈值

7. **Fail-safe**
   - 每步有降级策略（fetch失败→空claims+标unreliable）
   - synthesis失败→返回原始验证声称
   - all claims被否决→返回inconclusive报告

8. **自包含设计**
   - serenity-analysis把完整方法论（PERSONA+VOICE）写在workflow内
   - 不依赖外部skill文件

9. **双层输出**
   - 长帖（公开，high-level）+底稿（完整证据）
   - 量化过程藏在底稿，公开帖只给结论

### 核心差异总结

| 维度 | 我们的Pipeline | Codex Workflow |
|------|---------------|----------------|
| 执行模式 | 纯串行 | fan-out并行（pipeline/parallel原语） |
| 输出约束 | 事后QA检查 | 执行时JSON Schema强制 |
| 验证方式 | 机械检查（regex/行数/关键词） | 对抗式多票审查 |
| 证据管理 | 附录后验标注 | 数据流内嵌tier标签 |
| 错误处理 | step_fail→sys.exit(1) | fail-safe降级 |
| 方法论存放 | 分离（report_schema.json + playbook + SOUL） | 自包含（workflow内含PERSONA常量） |
| 输出格式 | 单层（一份docx） | 双层（公开帖+底稿） |
| 量化建模 | 仅非上市规模推算 | 四件套粗算（BOM/revenue/analog/mcap） |
| 批判审稿 | 无 | 独立Critique阶段 |


## 四、融合方案

### A. 融入现有模块（4项）

**1. 五维扫描引入六路并行取证架构**
- serenity-analysis的6路（财务/供应链/股权/技术/传播/政策）和我们五维不完全重叠
- 但并行取证的设计模式直接套用：品牌力、产品、市场渠道、趋势、人群五个维度各自作为独立lane
- 每lane有专门research brief + 独立agent并行跑，不再串行逐维生成
- fan-out→fan-in汇总到竞争模式归纳

**2. QA检查前增加对抗式审查阶段**
- deep-research的3票制验证逻辑：每条声称→3个独立agent尝试反驳→2票否决即剔除
- 被剔除的声称不能进入最终报告但保留在QA日志
- 和现有机械QA分工：对抗审查查"对不对"，机械QA查"全不全"
- 建议放在content生成后、docx组装前

**3. 第二章行业分析增加产业链地图和卡口识别**
- serenity-analysis的Map + chokepoint三问融入行业格局分析
- 不只是Porter五力+竞品矩阵，还有：
  - 产业链价值流向图（segments + bottleneck risk评估）
  - 关键卡口识别（供给紧不紧/替代难不难/市场理解了没有）
  - 卡口候选按priority排序

**4. 第六章策略建议融入机会地图和量化粗算层**
- 机会地图四维扫描：竞争激烈度×增长速度×创业机会×内容供给缺口
- 量化粗算（用于上市公司竞品）：BOM拆解/收入build/历史类比/市值错配
- 每条假设标注证据层级

### B. 新增模块（3项）

**5. 用户痛点挖掘模块（来自aron厚玉文章）**
- 放置位置：数据采集阶段，新增子模块
- 方法：抓取社区/社媒讨论→提取高频抱怨/需求/问题/目标→结构化痛点库
- 注入人群维度分析
- 核心价值："用户的钱都藏在痛点里"→从"25-35岁白领女性"升级为有洞察力的判断

**6. 内容类型五分类框架（来自aron厚玉文章）**
- 融入品牌力维度的社媒分析
- 不只是看发了什么内容、多少互动
- 分类为：曝光型（观点强争议大易传播）/涨粉型（资源型推荐型）/收藏型（步骤SOP模板工作流，生命周期长）/转化型（展示结果案例收益，最容易赚钱）/人设型（故事经历踩坑复盘，记住的是你）
- 判断竞品的内容增长系统长什么样

**7. 证据层级系统（来自serenity-analysis）**
- 贯穿整个Pipeline的基础设施级改动
- 四层定义：confirmed（公开可查证）→reported（券商/媒体报道）→mapped（生态推断）→speculation（猜测）
- 层级只能降不能升（tierAfterAudit ≤ 原tier）
- 从数据采集层开始标记：
  - 天猫已售数据 = confirmed
  - 行业研报引用 = reported
  - 推断/映射 = speculation
- content_gen时保留tier标签
- docx生成时可选标注（默认：正文隐藏tier，附录数据核验表显示）
- QA检查tier consistency

### C. 新代码架构设计

**保持Python为主控语言**（不迁到JS），引入Codex三个核心设计模式：

**P0: Phase系统重写**
- 每个Phase有明确的: name/description/input_schema/output_schema/fallback策略
- 替代现在pipeline.py里散落的if num==N分支
- 使用Python dataclass定义Phase结构

**P1: 并行执行原语**
- 增加parallel()函数：接受任务列表，fan-out到独立agent/进程跑，fan-in汇总
- 受益场景：
  - 数据采集（天猫/京东/抖音/财报/社媒同时抓）
  - 多品牌分析（6个deep品牌同时出五维）
  - 对抗验证（N条声称×3票同时审）
  - 图表生成（4张mandatory同时生成）
- 实现方式：Python concurrent.futures/asyncio 或 sessions_spawn subagent

**P2: 证据层标签**
- 在数据流中增加tier字段（confirmed/reported/mapped/speculation）
- 数据结构改变：所有数据采集输出增加tier标记
- content_gen的prompt模板增加"请标注每条关键声称的证据层级"
- QA增加tier consistency检查

**P3: Fail-safe机制**
- 每个Phase出错不崩全流程
- 数据源不可达→返回空结果+标记unreliable
- content生成失败→保留prompt文件待手动重跑
- 验证阶段剔除的声称→不进入报告但保留在QA日志
- 所有声称被否决→生成inconclusive报告而非空报告

### D. 7项改动优先级排序

**P0（基础架构，必须先做）**:
- Phase系统重写
- 并行执行原语
- 证据层标签系统

**P1（核心能力提升）**:
- 对抗式审查阶段
- 用户痛点挖掘模块

**P2（增强模块）**:
- 内容类型五分类
- 第二章产业链地图+卡口识别
- 第六章机会地图+量化粗算


## 五、我们的Pipeline反思与经验（来自历史复盘）

这些是在之前项目中积累的、和本次优化相关的关键教训：

### 执行鸿沟元模式（2026-05-02教训4 + 2026-07-21缝合点1）
识别≠修复。问题不会被"记住"解决，只会被"执行"解决。Pipeline的Phase系统+结构化输出可以建立执行契约——缺陷发现后自动触发修复，而不是进入"识别循环"。

### 推理守卫八: Pipeline任务强制执行（2026-07-21三棵树复盘）
当逸凡说"用燃创咨询的skill跑XX"时，必须直接走代码路径，禁止手工绕圈。Schema+Pipeline的价值是让orchestration稳定——建config就跑代码。这次融入Codex的Phase系统后，会进一步加强这个纪律。

### 推理守卫九: 临时修复必须合并回源文件（2026-07-22康尔馨复盘）
任何在/tmp/或临时脚本中的修复代码，修复完成后必须立即合并回pipeline源文件。Codex workflow的fail-safe机制可以借鉴——每个Phase的修复应该直接修改对应模块，不留孤儿脚本。

### 推理守卫十: 局部修改不得触发全局重建（2026-07-22蓝氏复盘）
修改报告某一处只能修改docx对应部分，不能重新生成整个文档。Codex的Pipeline架构天然支持这个——每个Phase独立运行，修改一个Phase不影响其他Phase的输出。

### 产出周期四阶段模型（2026-07-25缝合点1）
触发期→爆发期→枯竭静默期→休息期。Pipeline的执行模式决定了产出高峰依赖的是任务积压量+管线成熟度，而非逸凡触发时间。

### 跨行业模板复用验证（2026-07-22缝合点4）
从食品（榴芒一刻/北纬47度）→家居/床品（康尔馨）→宠物食品（蓝氏）的跨行业跳跃在4天内完成，验证了通用playbook决策降低了迁移成本。Codex workflow的自包含设计（方法论写在workflow内）进一步强化了这个方向。

### Bug收敛率曲线（2026-07-22缝合点1+2）
三棵树10项→康尔馨4项→蓝氏0项。引入Phase系统+JSON Schema强制输出后，bug发现将从"运行时暴露"前置到"执行时阻断"——不符合schema的输出根本不会进入下一Phase。

### 静态QA vs 对抗审查的差异
我们现有的QA（14个禁止短语命中=0、行数≥800、每段至少一个数据锚点）是机械检查。对抗审查是定性判断——"这个声称的证据真的能支撑吗？"两者互补，前者确保规范达标，后者确保事实正确。这是一个之前没有认识到的关键设计缺陷。


## 六、待逸凡确认的事项

1. 融合方案7项改动的优先级和范围是否ok？
2. 新Phase架构的具体Phase定义（多少步？哪些Phase并行？）
3. 证据层级系统是在正文中显示还是只在附录显示？
4. 对抗式审查的票数设置（3票制还是2票制？否决阈值？）
5. 用户痛点挖掘的社区范围（仅天猫评价还是扩展小红书/抖音？）
6. 量化粗算层是否对所有报告生效还是仅上市公司竞品？
7. 是否需要维护两套输出（公开摘要+完整底稿）还是维持单层docx？


## 七、关键源码引用

### 我们的Pipeline核心文件
- `/report-pipeline/pipeline.py` — 主控脚本（16步顺序执行）
- `/report-pipeline/config.py` — 配置管理器（ReportSchema + ProjectConfig）
- `/report-pipeline/report_schema.json` — v1.5完整报告schema
- `/report-pipeline/report_playbook.md` — v1.5操作手册
- `/report-pipeline/steps/content_gen.py` — 内容生成（prompt构建+LLM调用）
- `/report-pipeline/steps/qa_check.py` — 5层机械QA
- `/report-pipeline/steps/data_collection.py` — 数据采集
- `/report-pipeline/steps/data_dispatch.py` — 数据分发
- `/report-pipeline/steps/charts.py` — 图表生成
- `/report-pipeline/steps/docx_builder.py` — docx组装

### Codex Workflow源码（已拉取完整内容）
- six-ddc/skills/workflows/deep-research-extracted.js — Anthropic深度研究（完整源码）
- six-ddc/skills/workflows/serenity-analysis.js — Serenity分析工作流（完整源码）
- six-ddc/skills/skills/serenity-investor/SKILL.md — Serenity投资人格skill（完整源码）

### 参考文章
- aron厚玉《如何用 Codex 在 1 小时内快速了解陌生行业》https://mp.weixin.qq.com/s/UzikNhV0jbZDiMwnF-EIdg
- aron厚玉《巨牛X的 Codex skill 合集》https://aronhouyu.com/archives/500
- awesome-codex-skills: https://github.com/ComposioHQ/awesome-codex-skills
- six-ddc/skills: https://github.com/six-ddc/skills


---

## 八、社媒数据采集方案：搜索 vs 爬虫 vs 混合

### 8.1 我们当前的实际模式

**搜索驱动（已在使用）**：
- 财报、行业研报、公开信息 → 搜狗搜索 site:xxx → web_fetch 抓页面内容
- 这套逻辑和 Codex workflow 完全一致

**爬虫驱动（已在使用）**：
- 天猫/京东爆款数据 → CDP + browser-automation 直接打开商品页爬DOM
- 微博企业号timeline → CDP + browser-automation 爬主页动态
- 不经过搜索层，直接访问目标URL

**为什么有这两层**：
- 搜索层的问题：web_search（DuckDuckGo）被墙，实际用搜狗网页搜索代偿；但搜狗对天猫/京东商品页的索引覆盖度低，且商品详情页搜狗不一定能索引到
- 爬虫层的问题：CDP依赖Chrome 9333端口可用性（历史上多次因端口不可用导致cron失败），且直接爬DOM面临反爬风险

### 8.2 Codex Workflow的社媒采集方式

两套workflow都是纯搜索驱动，零爬虫逻辑：

**deep-research-extracted**:
- 5路WebSearch agent搜不同角度关键词
- 搜索结果URL → WebFetch抓取页面内容 → 提取可证伪声称
- 没有任何CDP、browser-automation、DOM解析代码
- 数据源完全依赖搜索引擎的索引

**serenity-analysis**:
- Lane 5（社区与传播）: agent用WebSearch搜X/Reddit/媒体讨论 → WebFetch抓内容
- 关键约束: "不许凭记忆编数字，必须实际检索"
- A股标的: 优先走ashare-data-kit skill（一个A股全栈数据工具包，uv可执行脚本，取交易所/公司一手数据），不是爬虫
- 对社媒内容不要求实时/完整，只要求搜索能索引到的部分

**核心差异**：
- Codex面对的是Google/Bing对X/Reddit的高覆盖度索引 → 搜索基本能拿到主要社媒讨论
- 我们面对的中国平台（微博/小红书/抖音）Google/搜狗索引覆盖度远不如 → 纯搜索可能漏掉大量内容

### 8.3 搜索+爬虫混合策略设计

**三层漏斗模型**：

```
第一层：搜索发现
  ├── 搜"品牌名 site:weibo.com" / "品牌名 site:xiaohongshu.com" / "品牌名 site:douyin.com"
  ├── 搜"品牌名 天猫旗舰店" / "品牌名 京东自营"
  ├── 搜"品牌名 财报" / "品牌名 招股书" / "品牌名 行业研报"
  └── 搜"品牌名 联名" / "品牌名 代言" / "品牌名 新品"
      ↓
第二层：web_fetch 轻量抓取
  ├── 搜索结果中能直接fetch的（财报/研报/新闻）→ 直接抓
  ├── 需要登录/JS渲染的（微博/小红书/天猫详情页）→ 标记，进入第三层
  └── 搜狗中转链接（/link?url=...）拼成完整URL再fetch
      ↓
第三层：CDP定点精准采集
  ├── 仅对 web_fetch 失败的URL启动CDP
  ├── 使用真实Chrome profile（已登录、有cookie）
  ├── 单品牌/单次任务的总采集量控制在合理范围内
  └── 采集间隔随机化（2-5秒），模拟人类浏览节奏
```

**三层分工逻辑**：
- 第一层：发现（找到有什么可以采的），成本最低，覆盖面最广
- 第二层：轻量获取（能fetch的先fetch），不消耗CDP资源
- 第三层：精准突破（只对必须CDP的URL启动浏览器），最小化CDP暴露面

### 8.4 反封策略

**CDP层面的保护**：
1. 真实Chrome profile（已登录、有正常浏览历史），不是headless/隐身模式
2. 请求间隔随机化（2-5秒随机，不是固定间隔）
3. 单品牌单次任务采集量上限（天猫≤20个SKU，京东≤15个SKU，微博≤30条）
4. 不连续采集同一平台（天猫→京东→微博→研究→回来，不是天猫天猫天猫）
5. 浏览器保持在用户使用状态（不专门开一个空的CDP端口），随用户Chrome的生命周期

**搜索层面的保护**：
1. 搜狗搜索本质上是网页搜索，不会触发平台的反爬
2. 搜索结果URL的web_fetch是普通HTTP GET，不携带cookie，不会被识别为爬虫
3. 搜索间隔自然（不同品牌的搜索之间有分析/写入/格式化等步骤，天然间隔）

**为什么混合比纯爬虫更安全**：
- 纯爬虫：所有数据都靠CDP，CDP的请求密度高，触发反爬概率高
- 纯搜索：中国平台索引覆盖不够，拿不到足够的电商/社媒数据
- 混合：大部分数据走搜索+web_fetch（零反爬风险），只有少量必须的精细化数据用CDP（低频、有cookie、间隔随机），整体风险可控

### 8.5 值得从Codex借鉴的具体做法

**1. 搜索角度的多样性**
Codex的Scope Phase拆解为5个互补角度（broad/academic/news/contrarian/practitioner），每个角度一个独立搜索query。我们在搜索品牌数据时也可以拆角度：品牌基本面query / 竞品对比query / 最新动态query / 负面舆情query / 社媒口碑query，5路并行搜，结果合并去重。

**2. URL去重机制**
deep-research的normURL函数（hostname+pathname lowercase）可以复用。采集跨平台、跨搜索引擎的数据时，同一个页面可能被多次命中，需要去重。

**3. 来源质量标记**
每条采集到的数据标sourceQuality（primary/secondary/blog/forum/unreliable），对应我们的证据层级。天猫已售数据=primary，行业研报=secondary，微博博文=forum，未知来源=unreliable。

**4. Fail-safe采集**
deep-research的fetch失败→返回unreliable+空claims模式值得用在我们的CDP采集上。天猫/京东页面打不开时不崩全流程，标记unavailable继续跑下一个品牌。

### 8.6 和中国平台的适配建议

**微博**：
- 搜索层：web_fetch搜索"品牌名 site:weibo.com" → 能拿到部分公开微博
- 爬虫层：需要登录看的内容/CDP点对点抓（频控：每条品牌≤30条）
- 注意：微博企业号UID比handle更稳定，用数字UID

**小红书**：
- 搜索层：搜狗对小红书索引极差，基本搜不到
- 爬虫层：小红书反爬极强，CDP也需要手机端UA
- 建议：品牌力分析中社媒部分降低小红书权重，更多依赖第三方数据（蝉妈妈/飞瓜）或已有的social-crawler skill

**抖音**：
- 搜索层：搜狗对抖音有一定索引但主要是视频标题
- 爬虫层：抖音页面重JS渲染，CDP需要等待
- 建议：优先用飞瓜/蝉妈妈数据，搜索补品牌号粉丝数和内容方向

**天猫/京东**：
- 搜索层：搜"品牌名 天猫旗舰店"可以找到店铺URL
- 爬虫层：商品详情页必须CDP（需要已登录cookie）
- 建议：搜索发现→CDP定点采集，单品牌单次≤20个SKU

## 九、补充：Codex Workflow中我们没有的社媒采集设计模式

### 9.1 内容类型分类在采集阶段就标记
serenity-analysis的每路取证要求direction标记（bullish/bearish/neutral）。对应到我们的内容分析：采集时就可以标注"这条内容是品牌正面宣传/用户负面反馈/中性信息"，不用等到分析阶段再判断。

### 9.2 证据时点标记
每条采集数据带asOf字段（YYYY-MM或具体日期）。我们的Pipeline目前只在数据核验表里标"采集日快照"，没有逐条标记信息时点。这对应我们之前发现的"过期数据当事实用"的问题。

### 9.3 多源交叉验证在采集阶段启动
serenity-analysis要求每路取证至少2条bearish方向的事实，实在找不到要在laneSummary里说明原因。这避免了"只搜多头信息"的偏差。我们采集时也应该强制"每条搜索query至少包含一个负面/批评视角的搜索"。

### 9.4 自包含方法论
serenity-analysis把完整的PERSONA+VOICE常量直接写在workflow.js里，不依赖外部SKILL.md文件。这意味着workflow可以独立运行、独立迁移。我们的pipeline.py目前依赖report_schema.json+config.py+多个steps模块，迁移时需要带整个目录。可以考虑把核心方法论常量也内嵌到pipeline.py或一个独立的methodology.py里。


---

*本文档包含了从aron厚玉文章分析、Codex workflow源码逆向、我们Pipeline结构审查、历史教训回顾、社媒采集方案分析的全部内容。等待逸凡审阅后确定具体修改方案和执行顺序。*
