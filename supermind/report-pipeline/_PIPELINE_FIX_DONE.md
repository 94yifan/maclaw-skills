# Pipeline 固化改动 — 全部完成

完成时间: 2026-07-22 13:25

## 执行清单

| # | 改动 | 文件 | 状态 |
|---|------|------|------|
| P0-1 | Step 0 自动清理 content/charts 目录 | pipeline.py | ✅ |
| P0-2 | 项目输出目录隔离（output_subdir） | config.py + steps/utils.py | ✅ |
| P0-3 | 文件品牌白名单校验 validate_brand_content | steps/utils.py | ✅ |
| P0-4 | charts.py 同时输出 Pillow PNG | steps/charts.py | ✅ |
| P0-5 | docx_builder 全面重写（纯 python-docx） | steps/docx_builder.py | ✅ |
| P0-6 | F层 docx 验证永久纳入（5项检查已存在） | steps/qa_check.py | ✅ |
| P1-7 | Step 3 电商强制采集 + generate_ecommerce_prompt | steps/data_collection.py | ✅ |
| P1-8 | content_gen.py prompt 硬化（5条铁律） | steps/content_gen.py | ✅ |
| P1-9 | B-9 内容质量检测（AI腔/星号/列表体） | steps/qa_check.py | ✅ |
| P1-10 | B-10 人群收入跨度检测 | steps/qa_check.py | ✅ |
| P0-11 | SOUL.md 新增推理守卫九 | SOUL.md | ✅ |
| P0-12 | docx_builder 图片嵌入改用 add_picture | 由 P0-5 覆盖 | ✅ |

## 验证结果

- 所有 8 个模块文件 python3 compile 通过
- `pipeline.py --dry-run` 正常输出 16 步预览
- 关键函数导入验证通过

## 改动要点

### P0-1: 自动清理
main() 中 init_status() 之后、execute steps 之前插入清理逻辑。保留 `_FILL_COMPLETE.md`, `_ECOMMERCE_DONE.md`, `_CONTENT_REWRITE_DONE.md` 三个标记文件。

### P0-2: 目录隔离
ProjectConfig 新增 `output_subdir` 属性 = `project_name.replace(" ", "_") + "_" + datetime.now().strftime("%Y%m%d_%H%M")`。utils.py 中 `content_dir()`, `charts_dir()`, `reports_dir()` 等函数新增 `project_config` 可选参数，带参数时使用隔离子目录。

### P0-3: 品牌白名单校验
`validate_brand_content(filepath, project_config)` 从 project_config 提取 focus/deep/summary 品牌 + 行业通用词 + 通用白名单，检查文件中是否出现指定黑名单品牌（三棵树、立邦、多乐士、卡百利、嘉宝莉、菲玛、亚士漆、榴莲、玉米等）。

### P0-4: charts 同时输出 PNG
`generate_png_from_chart_def(chart_def, brands, data, out_path)` 使用 Pillow ImageDraw 绘制水平条形图（参考 /tmp/gen_charts.py），集成到 `generate_single_chart` 中。

### P0-5: docx_builder 全面重写
- 放弃 zipfile + lxml 方案，纯 python-docx
- `add_md_content_to_docx(doc, md_text)`：strip H1, H2-H4→heading，表格→add_table，**bold**→Run.bold, - 列表→段落, ---→装饰线
- `add_charts_to_docx(doc, chart_files)`：add_picture 嵌入 PNG
- `build_chapter_map(project_config)`：直接文件名加载（不 glob），排除 pre_research.md
- `assemble_docx`：Document → 封面 → TOC → brand_overview → ch1~ch7(硬编码标题+追加图表) → 附录 → save
- `embed_charts_in_docx` → deprecate（功能合并到 add_charts_to_docx）

### P0-6: F层验证
确认 `check_docx_final` 已实现 F-1~F-5 全部 5 项检查，无需新增。

### P1-7: 电商强制采集
`collect_all` 检查 `ecommerce_required` flag，当 true 时打印明确采集要求。`generate_ecommerce_prompt(project_config)` 为每个品牌生成天猫/京东/抖音采集指令。

### P1-8: Prompt 硬化
build_ch2_prompt, build_ch3_prompt, build_ch4_prompt, build_ch5_prompt, build_ch6_prompt 共同追加 5 条写作铁律：首句结论 → 中间数字+事实 → 末句意义 → 禁止**/-列表/填充词 → 收入跨度≤2档位。

### P1-9: B-9 内容质量
检查 `**` 出现次数 < 10、AI填充词（本质上/整体而言等）< 3、破折号列表体 < 5。

### P1-10: B-10 收入跨度
匹配 "月入X-Y" / "收入X-Y" 模式，按 3k/5k/8k/12k/20k/30k/50k+ 档位计算跨度。超过 2 档位则 FAIL。
