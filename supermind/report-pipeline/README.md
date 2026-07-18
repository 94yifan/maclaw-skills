# 品牌研究报告生产 Pipeline

基于 `report_schema.json` + `report_playbook.md` 的品牌研究报告自动化生产流水线。
覆盖商业分析全流程：数据采集 → 分发 → 内容生成 → 图表 → DOCX → QA。

## 架构概览

```
pipeline.py              # 主控入口（CLI）
config.py                # Schema + 项目配置管理
steps/
├── data_collection.py   # Step 3: 数据采集指令生成
├── data_dispatch.py     # Step 4: 数据自动分发
├── content_gen.py       # Step 5-9: Prompt + 内容框架
├── charts.py            # Step 10: ECharts 图表生成
├── docx_builder.py      # Step 11: docx 6步法生成
├── qa_check.py          # Step 12: QA 自动检查
└── utils.py             # 通用工具函数
```

## 安装依赖

```bash
pip install python-docx lxml
# ECharts HTML 渲染需要浏览器：
pip install playwright
playwright install chromium
```

## 使用方法

### 1. 准备项目配置

拷贝模板并编辑：

```bash
cp templates/project_config_template.json my_project.json
```

编辑 `my_project.json`，填写：
- `project_name` — 项目名
- `industry` — 行业名称
- `industry_type` — 行业类型（consumables / tech / service / manufacturing）
- `brands.focus` — 本品品牌名
- `brands.deep` — 深度品牌列表（≤6个）
- `brands.summary` — 汇总品牌列表（≤15个）
- `data_sources` — 数据平台和财务来源配置
- `output_settings` — 输出文件名等

### 2. 全流程执行

```bash
python pipeline.py --config my_project.json
```

### 3. 指定步骤执行

```bash
# 从 Step 3 开始
python pipeline.py --config my_project.json --from-step 3

# 只执行指定步骤
python pipeline.py --config my_project.json --step 10 --step 11 --step 12

# 跳过手动步骤
python pipeline.py --config my_project.json --skip-steps 1,2

# 预览（不实际执行）
python pipeline.py --config my_project.json --dry-run
```

## Pipeline 14 步流程

| 步骤 | 名称 | 类型 | 自动化 | 说明 |
|------|------|------|--------|------|
| 1 | Init | 手动 | ❌ | 确认行业/品牌范围/深度/框架版本 |
| 2 | 框架搭建 | 手动 | ❌ | 读 schema 搭建分析框架 |
| 3 | 数据采集 | 半自动 | ❌ | 调用 browser/web_search/web_fetch 采集数据 |
| 4 | 数据分发 | 自动 | ✅ | 按 mapping 自动路由到各章节维度 |
| 5 | 行业分析 | AI-Pro | ❌ | Ch2 Porter五力+行业趋势+竞品矩阵 |
| 6 | 竞品扫描 | AI-Pro | ❌ | Ch3 深度品牌5维+汇总+竞争模式 |
| 7 | 本品分析 | AI-Pro | ❌ | Ch4 五维深度诊断+趋势预判 |
| 8 | 差距对比 | AI-Pro | ❌ | Ch5 集团层+品牌层+差距定位 |
| 9 | 策略建议 | AI-Pro | ❌ | Ch6 品牌策略+集团议题+项目范围 |
| 10 | 图表生成 | 自动 | ✅ | 4张mandatory + 按需optional |
| 11 | docx生成 | 自动 | ✅ | 6步法（python-docx + lxml + zipfile） |
| 12 | QA检查 | 自动 | ✅ | 结构/内容/图表/交付四层 |
| 13 | 截图审查 | AI-5V | ❌ | GLM 5V Turbo 截图验证 |
| 14 | 最终交付 | 手动 | ❌ | docx + QA报告 + 核验表 |

## 模型分工

| 模型 | 职责 | 不可做的 |
|------|------|---------|
| **DeepSeek V4 Pro** | 全部分析内容写作（ch1-ch6） | 不写脚本、不作图表、不作数据采集 |
| **GLM 5.2** | 所有脚本代码（Coding Hook） | 不写分析内容 |
| **GLM 5V Turbo** | 截图审查验证 | 不作判断、不写作 |
| **Flash** | 数据采集、浏览店铺 | 不作分析判断 |

## 输出目录结构

```
output/
├── data/
│   ├── raw/                    # 原始采集数据（JSON）
│   │   ├── ecommerce_tmall.json
│   │   ├── ecommerce_jd.json
│   │   ├── financial_report.json
│   │   └── ...
│   └── dispatched/             # 已分发数据（JSON）
│       ├── ch3_deep_brands_market_channel_品牌A.json
│       └── ...
├── content/
│   ├── ch2_industry.md         # 行业分析
│   ├── ch3_competitive/        # 竞品扫描
│   ├── ch4_deep/               # 本品分析
│   ├── ch5_gap.md              # 差距对比
│   ├── ch6_recommendations.md  # 策略建议
│   └── *_prompt.md             # DeepSeek Pro 调用 prompt
├── charts/
│   ├── *.html                  # ECharts 页面
│   ├── *.png                   # 截图（如有 playwright）
│   └── *_data.json             # 图表数据
└── reports/
    ├── *.docx                  # 最终报告
    └── qa_report.md            # QA 检查报告
```

## 配置驱动

所有规则从 `report_schema.json` 读取，不硬编码：

- 📐 **分析维度**：深度品牌五维定义、每维必含要素
- 📝 **写作规范**：结论先行、数据锚点、段落结构
- 📊 **图表规范**：4张 mandatory、标签、顺序、位置
- ✅ **QA 规则**：四层检查、每项规则/fail处理
- 🔄 **Pipeline 流程**：每步的输入输出、自动化标志
- 🌐 **跨行业适配**：消费品/科技/SaaS/服务/制造行业映射

## 与 DeepSeek V4 Pro 协作

内容生成步骤（5-9）生成 Prompt 文件而非直接调用 LLM：

1. `content/gen_*_prompt.md` — 包含 schema 中的必含要素清单 + 写作规范 + 数据
2. 在**主 session** 中，将 prompt 传给 DeepSeek V4 Pro 生成分析内容
3. 将生成的 markdown 保存回对应 `content/ch*_*.md`

Prompt 模板包含：
- 写入规范（结论先行、数据锚点、禁止AI腔、自然段落）
- 必含要素清单（每题需要覆盖的分析子维度）
- 表达约束（完整句子、不可省略关键信息）

## 错误处理

- 任何步骤失败 → 写入 `pipeline_status.json` → **自动停止** → 输出错误日志
- 不静默跳过失败步骤
- QA 检查失败项 → 在报告中列出需修复项 → 回退到对应步骤
- 输入输出契约验证：每一步检查必要输入是否存在、输出是否生成

## 状态监控

`pipeline_status.json` 记录每一步的执行状态、用时和产出物清单：

```json
{
  "project": "XX行业品牌研究报告",
  "steps": {
    "step_3": {
      "status": "success",
      "started_at": "2026-07-15T17:00:00",
      "outputs": ["..."]
    }
  },
  "overall": "running"
}
```

---

*基于 report_schema.json v1.2 / report_playbook.md v4 | 五维分析模型由逸凡定义 | 所有方法论框架归属燃创咨询 BreaC Lab体系*
