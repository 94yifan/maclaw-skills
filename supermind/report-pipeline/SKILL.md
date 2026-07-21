# BREAC 行业品牌扫描 Pipeline v1.5

## 触发词
- "用breac跑XX客户"
- "用燃创咨询的品牌扫描skill跑XX"
- `python3 report-pipeline/pipeline.py --config project_config.json`

## ⚠️ 执行铁律（2026-07-21 三棵树项目复盘）

**读到触发词后，只允许执行以下 3 个命令，不允许任何中间动作（包括搜索、讨论、确认竞品）。**

```bash
# 步骤 1：建 config + 跑全流程（一步到位）
cd ~/.openclaw/workspace/supermind/report-pipeline
python3 pipeline.py --config project_config_客户名.json

# 步骤 2：spawn DeepSeek Pro 填充 AI-Pro 步骤内容（Steps 5-11）
# 步骤 3：生成 docx + QA + 发群
python3 pipeline.py --config project_config_客户名.json --step 13
python3 pipeline.py --config project_config_客户名.json --step 14
# QA 发现问题 → 直接修内容文件 → 重复步骤 3 → 升版本号 → 发群
```

**禁止：**
- 群聊里手工搜数据、讨论框架、确认竞品 — pipeline 自动生成 prompt 让 Pro 搜索填充
- QA 只标记不改 — 检测到立即修，修完重新生成
- 生成 docx 不发群 — 逸凡不 Access 电脑
- 改完内容不升版本号 — 整数升版=结构改动，小数升版=文字改动

## 位置
`/Users/yifansmacmini/.openclaw/workspace/supermind/report-pipeline/`

## 用途
16步品牌研究报告生产管线——从"不知道赛道和竞品"到"完整报告DOCX交付"。五维模型+创始人研究+创品策略+颗粒度检查。跨行业通用。

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
  "brands": {"focus":"本品","deep":["竞品A"],"reference":[],"summary":[]},
  "founder_name": "创始人（如适用）",
  "data_sources": {"ecommerce_platforms":["tmall","jd","douyin"],"ecommerce_required":true},
  "modules_enabled": {"pre_research":true,"founder_research":true,"innovation_strategy":true,"five_dimension":true,"complete_book":true},
  "industry_trends": {"dimensions":[]},
  "special_methodology": {},
  "output_dir": "./output/项目名_日期",
  "output_settings": {"docx_filename": "品牌中文名-行业-V数字-日期.docx"}
}
```

## 品牌三档
- **focus**（本品）：五维+规模推算+创始人
- **deep**（竞品≤6）：五维≥30行/品牌
- **reference**（参考，不限）：核心信息+可比性判断
- **summary**（汇总≤15）：一段五要素

## QA硬性底线
- 总行≥800/字符≥60KB
- 深度品牌五维≥30行/品牌
- 创始人研究≥40行（创始人非品牌核心变量时不硬写）
- 创品策略≥10个方向
- 完本14禁止词命中=0
- 文件命名「品牌中文名-行业-V数字.数字-日期.docx」符合规范，整数升版=结构改动（增删章节/补全模块），小数升版=文字改动（修bug/改措辞/调数据）
- 图表嵌入正文对应位置（不堆末尾，不独立成章）：天猫爆款→竞品扫描章、价格带→产品矩阵后、店铺评分→渠道章、品类覆盖→品牌概览后
- 电商数据不独立成章，归入五维模型市场/渠道维度和渠道供应链章节
- 电商数据必采不可跳过
- **docx 标题大纲自动验证**：Heading1≥2, Heading2≥3, Heading3≥5。防止 markdown #→Heading 映射错误导致导航大纲空白

## docx 生成铁律
- **所有 docx 生成必须走统一模块**，禁止项目级独立脚本各自实现 markdown→docx 转换
- markdown 标题映射：`#` → Heading 1, `##` → Heading 2, `###` → Heading 3, `####` → Heading 4
- 如有项目需要独立生成脚本（如 `generate_*.py`），必须 `from steps.docx_builder import convert_markdown_to_paragraphs` 复用管线逻辑，不做重复实现
- 2026-07-20 教训：北纬47度独立脚本把 `#` 映射成 level=0，导致整个标题大纲消失。此条铁律防止同样问题再次出现

## 文档命名规则
**「品牌中文名-行业-V数字-日期」**，全中文（品牌名为英文时保留英文）。版本号统一用V1/V2/V3格式，同一套逻辑同时适用于Pipeline文件和品牌研究文档。

| 示例 | 说明 |
|------|------|
| `榴芒一刻-榴莲食品-V1-20260718.docx` | 品牌报告初版 |
| `榴芒一刻-榴莲食品-V2-20260718.docx` | 修订版 |
| `北纬47度-鲜食玉米-V1-20260718.docx` | 品牌报告初版 |
| `XX品牌-XX行业-前置调研-20260718.md` | 前置调研（调研阶段可用类型名） |

日期格式：YYYYMMDD。行业用产品赛道（不是泛类，而是"榴莲食品""鲜食玉米""人体工学椅"）。

## Pipeline 版本号规则
- **重大版本改动**（结构性变化——新增步骤、改报告框架、增删章节）：升整数 V1→V2→V3
- **其他一切改动**（修数据、调表格、改文字、修bug）：升小数点后一位 V1.4→V1.5→...→V1.9

例：v1.3→v1.4 = 新增颗粒度检查（重大，升整数）。V1.4→V1.5 = 修正某个正则bug（其他改动，升小数）。
