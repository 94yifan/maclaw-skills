# BREAC 行业品牌扫描 Pipeline v1.4

## 触发词
- "用breac跑XX客户"
- "用燃创咨询的品牌扫描skill跑XX"
- `python3 report-pipeline/pipeline.py --config project_config.json`

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
  "special_methodology": {}
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
- 图表嵌入正文对应位置（不堆末尾）
- 电商数据必采不可跳过

## 文档命名规则
**「品牌中文名-行业-版本-日期」**，全中文（品牌名为英文时保留英文）。

示例：
- `榴芒一刻-榴莲食品-完整报告-20260718.docx`
- `北纬47度-鲜食玉米-前置调研-20260718.md`

版本可选值：前置调研 / 完整报告 / 竞品扫描 / 创始人研究。日期格式：YYYYMMDD。

## Pipeline 版本号规则
- **重大版本改动**（结构性变化——新增步骤、改报告框架、增删章节）：升整数 V1→V2→V3
- **其他一切改动**（修数据、调表格、改文字、修bug）：升小数点后一位 V1.4→V1.5→...→V1.9

例：v1.3→v1.4 = 新增颗粒度检查（重大，升整数）。V1.4→V1.5 = 修正某个正则bug（其他改动，升小数）。
