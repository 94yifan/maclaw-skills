# BREAC 行业品牌扫描 Pipeline v2.0

## 触发词
- "用breac跑XX客户"
- "用燃创咨询的品牌扫描skill跑XX"
- `python3 report-pipeline/pipeline.py --config project_config.json`

## ⚠️ 执行铁律

**读到触发词后，只允许执行以下 3 个命令，不允许任何中间动作（包括搜索、讨论、确认竞品）。**

```bash
# 步骤 1：建 config + 跑全流程（一步到位）
cd ~/.openclaw/workspace/supermind/report-pipeline
python3 pipeline.py --config project_config_客户名.json

# 步骤 2：用 Pro 模型填充 AI-Pro 步骤内容（Steps 5-11）
# 注意：spawn 时用 model="deepseek/deepseek-v4-pro" 指定 Pro 引擎，不是 agentId
# 如果当前 session 本身就是 Pro，直接在当前 session 执行，不需要 spawn
# 步骤 3：生成 docx + QA + 发群
python3 pipeline.py --config project_config_客户名.json --step 13
python3 pipeline.py --config project_config_客户名.json --step 14
# QA 发现问题 → 直接修内容文件 → 重复步骤 3 → 升版本号 → 发群
```

**禁止：**
- 群聊里手工搜数据、讨论框架、确认竞品 — pipeline 自动生成 prompt，填入后由 Pro 模型生成内容
- 用 Flash 模型执行内容生成 — 所有 AI 内容填充步骤必须用 Pro（model="deepseek/deepseek-v4-pro"）
- QA 只标记不改 — 检测到立即修，修完重新生成
- 生成 docx 不发群 — 逸凡不 Access 电脑
- 改完内容不升版本号 — 整数升版=结构改动，小数升版=文字改动

## 位置
`/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/`

## 用途
18步品牌研究报告生产管线——从"不知道赛道和竞品"到"完整报告DOCX交付"。五维模型+创始人研究+创品策略+颗粒度检查。跨行业通用。

**v2.0 新增模块**：
- 🔴 **证据层级系统**：四层（confirmed/reported/mapped/speculation），贯穿全Pipeline。层级只能降不能升。
- 🔴 **对抗式审查**：3票制独立验证。内容生成后、机械QA前，对关键声称做"对不对"检查。
- 🔴 **产业链地图+卡口识别**：第二章新增。产业链价值流向+卡口三问（供给/替代/市场理解）。
- 🔴 **内容类型五分类**：曝光型/涨粉型/收藏型/转化型/人设型。识别品牌内容增长系统。
- 🔴 **用户痛点挖掘**：从天猫评价/小红书/微博/抖音评论区系统性挖掘。注入人群分析。
- 🔴 **量化粗算**：BOM拆解/收入拆分/历史类比/市值错配。上市公司竞品适用。数量级判断。
- 🔴 **机会地图**：四维扫描→2×2矩阵→机会排序。

## 证据层级系统（v2.0核心基础设施）

| 层级 | 标签 | 定义 | 写作措辞 |
|------|------|------|---------|
| **confirmed** | 已确认 | 天猫已售/年报/招股书/官方公告 | 直接陈述 |
| **reported** | 报道层 | 券商/行业研报/第三方平台 | "据XX报道" |
| **mapped** | 生态映射 | 供应链推断/行业相邻推断 | "我映射到" |
| **speculation** | 推测 | 个人推断/未经验证 | "我认为/likely" |

**核心纪律**：层级只能降不能升。pipeline≠orders, qualification≠volume ramp, 生态相邻≠量产订单。

**正文标注**：默认隐藏tier（附录显示），可通过`tier_visible=true`切换为正文显式标注。

## 对抗式审查（v2.0新增QA层）

- **3票制**：每条关键声称→3个独立agent尝试反驳→至少2票有效+否定<2才存活
- **默认怀疑**：不确定时refuted=true
- **审查清单**：来源支撑/反证/来源质量/过期/营销稿
- **与机械QA分工**：对抗审查查「对不对」，机械QA查「全不全」

## 并行取证（v2.0架构增强）

多品牌五维扫描、对抗审查、数据采集支持fan-out并行执行：
- 数据采集：天猫/京东/抖音/财报/社媒同时抓（Python concurrent.futures）
- 多品牌分析：6个deep品牌同时出五维
- 对抗验证：N条声称×3票同时审

## 快速启动
```bash
cd ~/.openclaw/workspace/supermind/report-pipeline

# 预览（不实际执行）
python3 pipeline.py --config project_config.json --dry-run

# 从指定步骤开始
python3 pipeline.py --config project_config.json --from-step 3

# 只跑特定步骤
python3 pipeline.py --config project_config.json --step 14
```

## 配置文件模板
```json
{
  "project_name": "品牌名 报告类型",
  "industry": "所属行业",
  "schema_version": "1.6",
  "brands": {"focus":"本品","deep":["竞品A"],"reference":[],"summary":[]},
  "founder_name": "创始人（如适用）",
  "data_sources": {"ecommerce_platforms":["tmall","jd","douyin"],"ecommerce_required":true},
  "modules_enabled": {
    "pre_research":true,"founder_research":true,"innovation_strategy":true,
    "five_dimension":true,"complete_book":true,
    "industry_chain_map":true,"content_type_classification":true,
    "user_pain_points":true,"quantitative_modeling":false,
    "opportunity_map":true,"adversarial_review":true
  },
  "tier_visible": false,
  "industry_trends": {"dimensions":[]},
  "special_methodology": {},
  "output_dir": "./output/项目名_日期",
  "output_settings": {"docx_filename": "品牌中文名-行业-V数字-日期.docx"}
}
```

## 品牌三档
- **focus**（本品）：五维+规模推算+创始人+内容五分类+用户痛点
- **deep**（竞品≤6）：五维≥30行/品牌+内容五分类
- **reference**（参考，不限）：核心信息+可比性判断
- **summary**（汇总≤15）：一段五要素

## QA硬性底线
- 总行≥800/字符≥60KB
- 深度品牌五维≥30行/品牌
- 创始人研究≥40行（创始人非品牌核心变量时不硬写）
- 创品策略≥10个方向
- 用户痛点≥5条（含quote+opportunity）
- 内容类型分析≥10行/深度品牌
- 产业链地图≥3个segments
- 完本14禁止词命中=0
- 🔴 证据层级一致性：tier_inflation/tier_downgrade/key_discipline/unmarked_claims 全部通过
- 文件命名符合规范
- 图表嵌入正文对应位置
- docx标题大纲自动验证

## docx生成铁律
- 所有docx生成必须走统一模块，禁止项目级独立脚本
- markdown标题映射：`#` → Heading 1, `##` → Heading 2, `###` → Heading 3, `####` → Heading 4
- 必须 `from steps.docx_builder import convert_markdown_to_paragraphs` 复用管线逻辑

## 文档命名规则
**「品牌中文名-行业-V数字-日期」**，全中文（品牌名为英文时保留英文）。

| 示例 | 说明 |
|------|------|
| `榴芒一刻-榴莲食品-V1-20260718.docx` | 品牌报告初版 |
| `XX品牌-XX行业-前置调研-20260718.md` | 前置调研 |

## Pipeline版本号规则
- **重大版本改动**（结构性变化——新增步骤/改报告框架/增删章节/新增基础设施）：升整数 V1→V2→V3
- **其他一切改动**（修数据/调表格/改文字/修bug）：升小数点后一位 V1.4→V1.5

*v2.0 = Schema v1.6 + Playbook v2.0 + 18步Pipeline（2026-07-26）*
