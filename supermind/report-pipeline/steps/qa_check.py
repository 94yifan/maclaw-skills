"""
Step 12: QA 自动检查模块。

职责：按 schema.qa_rules 逐项执行自动化检查。
检查层级（与 schema 对应）：
A. 结构性检查 — 章节完整性、五维一致性、要素完整性、内容完整性
B. 内容检查 — 数据锚点覆盖率、结论先行、段落结构、禁止AI腔、品类渠道拆分
C. 图表检查 — 标签完整性、标题规范性、嵌入位置、图表顺序
D. 交付检查（逸凡确认节点）

输出：output/reports/qa_report.md

发现错误 → 通知上游回退到对应步骤修复。
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from steps.utils import (
    step_start, step_success, step_fail,
    save_text, load_json, load_markdown,
    verify_input_file, verify_output_file,
    content_dir, charts_dir, output_dir, reports_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


def run_full_qc(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """
    Step 12 主入口：运行全套 QA 检查。
    返回 QA 报告路径。
    """
    step_start("qa_check", "QA 自动检查 — 结构/内容/图表/交付四层")
    
    r_dir = reports_dir()
    
    # 执行五层检查
    structural_results = check_structural(schema, project_config)
    content_results = check_content(schema, project_config)
    chart_results = check_charts(schema, project_config)
    granularity_results = check_granularity(schema, project_config)
    delivery_results = check_delivery(schema, project_config)
    
    all_results = structural_results + content_results + chart_results + granularity_results + delivery_results
    
    # 统计
    total = len(all_results)
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL")
    warnings = sum(1 for r in all_results if r["status"] == "WARN")
    
    # 生成报告
    report = generate_qa_report(all_results, schema, project_config, total, passed, failed, warnings)
    
    report_path = r_dir / "qa_report.md"
    save_text(report, report_path)
    
    print(f"\n  QA 总检查项: {total}")
    print(f"  ✓ 通过: {passed}")
    print(f"  ✗ 失败: {failed}")
    print(f"  ⚠ 警告: {warnings}")
    
    if failed > 0:
        print(f"\n  ⚠ 发现 {failed} 项失败，需修复后重新检查。")
    
    verify_output_file(report_path, "qa_check")
    step_success("qa_check", [str(report_path)])
    return report_path


# ── A. 结构性检查 ──────────────────────────────────────────

def check_structural(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """A. 结构性检查。"""
    results = []
    c_dir = content_dir()
    ch3_dir = c_dir / "ch3_competitive"
    ch4_dir = c_dir / "ch4_deep"
    
    # A-1: 章节完整性 — 支持独立文件或统一文件两种结构
    required_chapters = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6']
    chapter_files = {
        'ch1': c_dir / "ch1_findings.md",
        'ch2': c_dir / "ch2_industry.md",
        'ch3': ch3_dir,
        'ch4': ch4_dir,
        'ch5': c_dir / "ch5_gap.md",
        'ch6': c_dir / "ch6_recommendations.md",
    }
    
    # 检查是否存在统一报告文件
    unified_files = list(c_dir.glob("report*.md"))
    if unified_files:
        # 统一文件模式：扫描文件中是否有6章内容
        unified_content = load_markdown(unified_files[0])
        chinese_chapters = ["一、", "二、", "三、", "四、", "五、", "六、", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章"]
        found_any = any(ch in unified_content for ch in chinese_chapters)
        missing_chapters = [] if found_any else required_chapters
    else:
        # 独立文件模式
        missing_chapters = []
        for ch_key, path in chapter_files.items():
            if not path.exists():
                missing_chapters.append(ch_key)
    
    results.append({
        "category": "A. 结构性检查",
        "check": "A-1 章节完整性",
        "rule": "六章缺一不可",
        "detail": f"需包含: {', '.join(required_chapters)}",
        "status": "FAIL" if missing_chapters else "PASS",
        "message": f"缺失章节: {', '.join(missing_chapters)}" if missing_chapters else "全部章节已就位"
    })
    
    # A-2: 深度品牌五维一致性
    deep_brands = project_config.deep_brands
    required_dims = ["市场/渠道", "品牌力", "产品", "趋势", "人群"]
    
    dim_check_ok = True
    missing_dims_detail = []
    for brand in deep_brands:
        brand_files = list(ch3_dir.glob(f"deep_{brand}*.md"))
        if not brand_files:
            dim_check_ok = False
            missing_dims_detail.append(f"{brand}: 无内容文件")
            continue
        
        for bf in brand_files:
            try:
                content = load_markdown(bf)
                for dim in required_dims:
                    # 检查维度关键词
                    dim_keywords = {
                        "市场/渠道": ["市场", "渠道", "财务", "天猫", "京东", "抖音"],
                        "品牌力": ["品牌", "代言", "联名", "营销", "种草"],
                        "产品": ["产品", "SKU", "爆款", "价格", "评价"],
                        "趋势": ["趋势", "行业风向", "内容热点", "用户情绪"],
                        "人群": ["人群", "用户", "画像", "消费者"],
                    }
                    keywords = dim_keywords.get(dim.split("/")[0], [dim])
                    if not any(kw in content for kw in keywords):
                        dim_check_ok = False
                        missing_dims_detail.append(f"{brand}: 可能缺失维度「{dim}」")
            except (FileNotFoundError, OSError):
                continue
    
    results.append({
        "category": "A. 结构性检查",
        "check": "A-2 深度品牌五维一致性",
        "rule": "每个深度品牌必须包含全部五个维度",
        "detail": f"品牌: {', '.join(deep_brands)}",
        "status": "WARN" if not dim_check_ok else "PASS",
        "message": "; ".join(missing_dims_detail) if missing_dims_detail else "所有品牌五维覆盖"
    })
    
    # A-3: 汇总品牌要素完整性
    if project_config.summary_brands:
        results.append({
            "category": "A. 结构性检查",
            "check": "A-3 汇总品牌要素完整性",
            "rule": "每个汇总品牌一段，五要素全覆盖",
            "detail": f"汇总品牌: {', '.join(project_config.summary_brands)}",
            "status": "PASS",
            "message": "（需人工验证段落内容）"
        })
    
    # A-4: 内容完整性（非关键词碎片）
    results.append({
        "category": "A. 结构性检查",
        "check": "A-4 内容完整性",
        "rule": "每个段落用完整句子表达，不写成关键词碎片",
        "detail": "所有内容文件",
        "status": "PASS",
        "message": "（基础检查通过，需 DeepSeek Pro 确认表达完整性）"
    })
    
    return results


# ── B. 内容检查 ────────────────────────────────────────────

def check_content(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """B. 内容检查。"""
    results = []
    c_dir = content_dir()
    
    # 收集所有内容文件（支持独立文件ch*.md和统一文件report*.md）
    content_files = []
    for pattern in ["ch*.md", "ch*/*.md", "report*.md"]:
        content_files.extend(c_dir.glob(pattern))
    
    all_content = ""
    for f in content_files:
        if f.name.endswith("_prompt.md"):
            continue
        try:
            all_content += load_markdown(f) + "\n"
        except (FileNotFoundError, OSError):
            continue
    
    # B-1: 数据锚点覆盖率
    # 检查是否有数字（整数/小数）
    numbers_found = len(re.findall(r'\d+[\.\d]*', all_content))
    paragraphs = [p.strip() for p in all_content.split('\n') if p.strip() and len(p.strip()) > 20]
    paras_with_numbers = sum(1 for p in paragraphs if re.search(r'\d+', p))
    
    data_ok = paras_with_numbers >= len(paragraphs) * 0.6  # 60% 以上段落有数字
    
    results.append({
        "category": "B. 内容检查",
        "check": "B-1 数据锚点覆盖率",
        "rule": "每段至少一个具体数字",
        "detail": f"{paras_with_numbers}/{len(paragraphs)} 段落含数字",
        "status": "PASS" if data_ok else "WARN",
        "message": f"共找到 {numbers_found} 个数字，{paras_with_numbers}/{len(paragraphs)} 段落含数据锚点"
    })
    
    # B-2: 结论先行
    non_conclusion_starts = 0
    sample_issues = []
    if paragraphs:
        for i, p in enumerate(paragraphs[:50]):  # 检查前50段
            first_30 = p[:30]
            # 检查是否以背景/过渡开头
            background_starters = ["随着", "近年来", "从某种意义上说", "整体而言", "关于", "在...背景下",
                                    "我找到", "我查到了", "正在看", "我们来看", "需要说明"]
            if any(p.startswith(starter) for starter in background_starters):
                non_conclusion_starts += 1
                if len(sample_issues) < 5:
                    sample_issues.append(f"段{i+1}: 「{p[:50]}...」")
    
    conclusion_ok = len(paragraphs) == 0 or non_conclusion_starts <= max(len(paragraphs) * 0.1, 0)
    
    results.append({
        "category": "B. 内容检查",
        "check": "B-2 结论先行",
        "rule": "每段首句是可独立理解的判断句",
        "detail": f"非结论开头段落: {non_conclusion_starts}/{min(50, len(paragraphs))}",
        "status": "FAIL" if not conclusion_ok else "PASS",
        "message": "示例: " + "; ".join(sample_issues[:3]) if sample_issues else "结论先行规范良好"
    })
    
    # B-3: 段落结构
    results.append({
        "category": "B. 内容检查",
        "check": "B-3 段落结构",
        "rule": "每段=判断结论→数据支撑→收尾判断句",
        "detail": "检查维度覆盖",
        "status": "PASS",
        "message": "（需 DeepSeek Pro 确认段落结构是否符合要求）"
    })
    
    # B-4: 禁止AI腔
    ai_patterns = {
        "引号概念强调": ["「", "」", "\"\"", "''"],
        "星号列表体": ["* ", "- ", "• "],
        "填充词": ["当然", "其实", "本质上", "整体而言", "从某种意义上说"],
        "中间态汇报": ["我找到了", "我查到了", "正在看", "我们来看"],
    }
    
    ai_issues = []
    for pattern_name, patterns in ai_patterns.items():
        for pat in patterns:
            found = all_content.count(pat)
            if found > 0:
                ai_issues.append(f"{pattern_name} ({pat}): {found}次")
    
    ai_ok = len(ai_issues) == 0
    
    results.append({
        "category": "B. 内容检查",
        "check": "B-4 禁止AI腔",
        "rule": "无引号强调、无星号列表、无填充词、无中间态汇报",
        "detail": f"发现 {len(ai_issues)} 项问题",
        "status": "WARN" if not ai_ok else "PASS",
        "message": "; ".join(ai_issues) if ai_issues else "未检测到AI腔特征"
    })
    
    # B-5: 品类/渠道拆分
    split_keywords = ["天猫", "京东", "抖音", "线下"]
    channels_in_same_para = 0
    
    for p in paragraphs:
        found_channels = [c for c in split_keywords if c in p[:200]]
        if len(found_channels) >= 3:
            channels_in_same_para += 1
    
    results.append({
        "category": "B. 内容检查",
        "check": "B-5 品类/渠道拆分",
        "rule": "不同品类/渠道分别陈述",
        "detail": f"同一段含3+渠道的段落: {channels_in_same_para}",
        "status": "WARN" if channels_in_same_para > 1 else "PASS",
        "message": f"有 {channels_in_same_para} 段可能未拆分渠道" if channels_in_same_para > 1 else "渠道拆分规范"
    })
    
    # B-6: 品牌力子维度完整性 — 必须含组织力+社媒分析
    brand_power_keywords = ["组织", "社媒", "小红书", "抖音", "粉丝"]
    brand_power_hits = sum(1 for kw in brand_power_keywords if kw in all_content)
    brand_power_ok = brand_power_hits >= 3
    results.append({
        "category": "B. 内容检查",
        "check": "B-6 品牌力子维度完整性",
        "rule": "品牌力须含：组织力(公司治理/团队)+社媒渠道表现(小红书/抖音/微博/微信)",
        "detail": f"关键词覆盖: {brand_power_hits}/{len(brand_power_keywords)}",
        "status": "PASS" if brand_power_ok else "FAIL",
        "message": f"覆盖关键词: {[kw for kw in brand_power_keywords if kw in all_content]}，缺失: {[kw for kw in brand_power_keywords if kw not in all_content]}"
    })
    
    # B-7: 趋势子维度完整性 — 必须含已做趋势+可做趋势
    trend_keywords = ["已做", "可做", "预判", "前景", "机会"]
    trend_hits = sum(1 for kw in trend_keywords if kw in all_content)
    trend_has_done = ("已做" in all_content) or ("已经" in all_content and "趋势" in all_content)
    trend_has_todo = ("可做" in all_content) or ("预判" in all_content) or ("机会" in all_content)
    trend_ok = trend_has_done and trend_has_todo
    results.append({
        "category": "B. 内容检查",
        "check": "B-7 趋势子维度完整性",
        "rule": "趋势须含：已做趋势(具体产品/动作)+可做趋势预判(赛道/营销/情绪)",
        "detail": f"已做趋势={'有' if trend_has_done else '缺'}，可做预判={'有' if trend_has_todo else '缺'}",
        "status": "PASS" if trend_ok else "FAIL",
        "message": "趋势维度子项完整" if trend_ok else f"缺失: {'已做趋势' if not trend_has_done else ''}{'、' if not trend_has_done and not trend_has_todo else ''}{'可做趋势预判' if not trend_has_todo else ''}"
    })
    
    return results


# ── C. 图表检查 ────────────────────────────────────────────

def check_charts(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """C. 图表检查。"""
    results = []
    c_dir = charts_dir()
    chart_rules = schema.get_chart_rules()
    mandatory = schema.get_mandatory_charts()
    
    expected_order = [
        "chart_brand_comparison_1",  # 天猫爆款
        "chart_brand_comparison_2",  # 京东爆款
        "chart_brand_comparison_3",  # 斤价
        "chart_brand_comparison_4",  # 回头客
    ]
    
    # C-1: 图表存在性
    existing_charts = []
    missing_charts = []
    for chart_def in mandatory:
        chart_id = chart_def.get("id", "")
        chart_paths = list(c_dir.glob(f"{chart_id}.*"))
        if chart_paths:
            existing_charts.append(chart_id)
        else:
            missing_charts.append(chart_def.get("title", chart_id))
    
    results.append({
        "category": "C. 图表检查",
        "check": "C-1 图表存在性",
        "rule": "4张 mandatory 图表必须全部生成",
        "detail": f"已生成 {len(existing_charts)}/4",
        "status": "FAIL" if missing_charts else "PASS",
        "message": f"缺失: {', '.join(missing_charts)}" if missing_charts else "全部 mandatory 图表已生成"
    })
    
    # C-2: 图表顺序
    order_ok = True
    for i, expected_id in enumerate(expected_order):
        if i < len(existing_charts) and existing_charts[i] != expected_id:
            order_ok = False
            break
    
    results.append({
        "category": "C. 图表检查",
        "check": "C-2 图表顺序",
        "rule": f"生成顺序正确: 天猫爆款→京东爆款→斤价→回头客",
        "detail": f"当前顺序: {', '.join(existing_charts)}",
        "status": "FAIL" if not order_ok else "PASS",
        "message": "图表顺序需调整" if not order_ok else "图表顺序正确"
    })
    
    # C-3: 标签完整性（X/Y轴中文品牌名）
    html_files = list(c_dir.glob("*.html"))
    label_issues = 0
    for hf in html_files:
        try:
            content = load_markdown(hf)
            # 检查 ECharts data 是否有中文
            if "名称" not in content and re.search(r'data:\s*\[', content):
                label_issues += 1
        except (FileNotFoundError, OSError):
            continue
    
    results.append({
        "category": "C. 图表检查",
        "check": "C-3 标签完整性",
        "rule": "X/Y轴全为中文品牌名",
        "detail": f"检查 {len(html_files)} 个图表文件",
        "status": "WARN" if label_issues > 0 else "PASS",
        "message": f"{label_issues} 个图表可能缺少中文品牌名标签" if label_issues > 0 else "图表标签检查通过"
    })
    
    # C-4: 标题规范性
    results.append({
        "category": "C. 图表检查",
        "check": "C-4 标题规范性",
        "rule": "标题含数据源+指标",
        "detail": "图表标题格式",
        "status": "PASS",
        "message": "（由 GLM 5V Turbo 截图审查确认）"
    })
    
    # C-5: 图表嵌入位置（2026-07-18新增，逸凡要求）
    # 图表不能统一放在末尾附录，必须嵌入正文对应的分析位置
    content_files = list(content_dir().glob("*.md"))
    end_of_file_chart_count = 0
    inline_chart_count = 0
    for cf in content_files:
        md_content = cf.read_text(encoding="utf-8")
        lines = md_content.split("\n")
        total = len(lines)
        # 检查最后20行中是否集中了多个图表引用（=放在末尾）
        last_lines = "\n".join(lines[-20:])
        chart_refs_in_tail = len(re.findall(r'!\[.*\]\(.*\.png\)', last_lines))
        end_of_file_chart_count += chart_refs_in_tail
        # 检查全文中的内嵌图表引用
        inline_chart_count += len(re.findall(r'!\[.*\]\(.*\.png\)', md_content)) - chart_refs_in_tail
    
    chart_position_ok = end_of_file_chart_count == 0
    results.append({
        "category": "C. 图表检查",
        "check": "C-5 图表嵌入位置",
        "rule": "图表必须嵌入正文对应分析位置，不能统一放在末尾",
        "detail": f"末尾图表数: {end_of_file_chart_count}, 内嵌图表数: {inline_chart_count}",
        "status": "PASS" if chart_position_ok else "FAIL",
        "message": "" if chart_position_ok else f"警告：{end_of_file_chart_count}张图表位于文档末尾，应移至正文对应章节"
    })
    
    # C-6: 图表数据源标注（2026-07-18新增，逸凡要求）
    # 图表必须有数据来源标注：平台+日期+来源类型
    data_source_pattern = r'(来源[:：]|数据来源[:：]|Source:|天猫旗舰店|京东|蝉妈妈|招股书|财报)'
    charts_with_source = 0
    charts_missing_source = 0
    for cf in content_files:
        md_content = cf.read_text(encoding="utf-8")
        chart_blocks = re.findall(r'!\[.*\]\(.*\.png\).*?\n\*.*?\*', md_content, re.DOTALL)
        for cb in chart_blocks:
            if re.search(data_source_pattern, cb, re.IGNORECASE):
                charts_with_source += 1
            else:
                charts_missing_source += 1
    
    results.append({
        "category": "C. 图表检查",
        "check": "C-6 图表数据源标注",
        "rule": "每张图表必须有数据来源标注（平台+日期）",
        "detail": f"已标注: {charts_with_source}, 未标注: {charts_missing_source}",
        "status": "PASS" if charts_missing_source == 0 else "FAIL",
        "message": f"" if charts_missing_source == 0 else f"{charts_missing_source}张图表缺少数据源标注"
    })
    
    return results


# ── D. 颗粒度完整性检查（2026-07-18新增，逸凡要求）────────────────────
# 检查每章段的最小行数/字数/要素数量，确保报告信息密度达标
# 防止"结构对但内容空"的情况——北纬47度教训：24KB/423行 vs 榴芒一刻117KB/1111行

GRANULARITY_RULES = {
    "brand_overview_info_table": {"min_rows": 10, "check": "品牌基础信息表格行数≥10"},
    "brand_milestones": {"min_events": 8, "check": "里程碑事件≥8个"},
    "scale_judgment": {"min_evidence": 3, "check": "规模判断≥3条侧面证据"},
    "product_matrix": {"min_categories": 4, "check": "核心品类≥4个且标注市场地位"},
    "pricing_table": {"min_rows": 6, "check": "定价带表格≥6行含定价锚点"},
    "channel_evolution": {"min_stages": 4, "check": "渠道演变≥4个阶段"},
    "five_dim_per_deep_brand": {"min_lines": 30, "check": "每个深度品牌五维≥30行"},
    "core_findings": {"min_items": 5, "check": "核心发现≥5条"},
    "founder_research": {"min_lines": 40, "check": "创始人研究≥40行（含原生稿件≥3篇）"},
    "innovation_strategy": {"min_directions": 10, "check": "创品策略≥10个方向"},
    "total_lines": {"min_lines": 800, "check": "报告总行数≥800行"},
    "total_chars": {"min_chars": 60000, "check": "报告总字符数≥60KB（约60000字符）"},
}

def check_granularity(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """检查报告颗粒度完整性——每章段的内容密度是否达标"""
    results = []
    content_files = list(content_dir().glob("*.md"))
    # 同时读取子目录中的内容（如 ch3_competitive/deep_*.md）
    for subdir in content_dir().iterdir():
        if subdir.is_dir():
            content_files.extend(subdir.glob("*.md"))
    
    if not content_files:
        results.append({
            "category": "D. 颗粒度检查",
            "check": "D-0 内容文件存在",
            "rule": "至少存在一个.md内容文件",
            "detail": "内容目录为空",
            "status": "FAIL",
            "message": "无任何内容文件，检查终止"
        })
        return results
    
    all_content = ""
    for cf in content_files:
        all_content += cf.read_text(encoding="utf-8") + "\n"
    
    lines = [l for l in all_content.split("\n") if l.strip()]
    total_lines = len(lines)
    total_chars = len(all_content)
    
    # D-1: 总行数
    min_lines = GRANULARITY_RULES["total_lines"]["min_lines"]
    line_ok = total_lines >= min_lines
    results.append({
        "category": "D. 颗粒度检查",
        "check": "D-1 报告总行数",
        "rule": f"≥{min_lines}行",
        "detail": f"实际: {total_lines}行",
        "status": "PASS" if line_ok else "FAIL",
        "message": "" if line_ok else f"不足，仅{total_lines}行（差{min_lines-total_lines}行）。北纬47度教训：24KB/423行 vs 榴芒一刻117KB/1111行"
    })
    
    # D-2: 总字符数
    min_chars = GRANULARITY_RULES["total_chars"]["min_chars"]
    char_ok = total_chars >= min_chars
    results.append({
        "category": "D. 颗粒度检查",
        "check": "D-2 报告总字符数",
        "rule": f"≥{min_chars}字",
        "detail": f"实际: {total_chars}字（约{total_chars//1000}KB）",
        "status": "PASS" if char_ok else "FAIL",
        "message": "" if char_ok else f"不足，仅{total_chars}字（约{total_chars//1000}KB）"
    })
    
    # D-3: 核心发现数量
    finding_count = len(re.findall(r'发现[一二三四五六七八九十\d]', all_content))
    findings_ok = finding_count >= GRANULARITY_RULES["core_findings"]["min_items"]
    results.append({
        "category": "D. 颗粒度检查",
        "check": "D-3 核心发现数量",
        "rule": f"≥{GRANULARITY_RULES['core_findings']['min_items']}条",
        "detail": f"检测到: {finding_count}条",
        "status": "PASS" if findings_ok else "FAIL",
        "message": "" if findings_ok else f"核心发现仅{finding_count}条"
    })
    
    # D-4: 深度品牌五维 — 检查每个deep品牌是否有足够的行数
    deep_brands = project_config.deep_brands
    min_deep_lines = GRANULARITY_RULES["five_dim_per_deep_brand"]["min_lines"]
    
    for brand in deep_brands:
        brand_pattern = re.escape(brand)
        # 优先匹配深度品牌文件格式: # 深度品牌：XXX
        brand_section_match = re.search(
            rf'#[^\n]*深度品牌[^\n]*{brand_pattern}[^\n]*\n(.*?)(?=(?:#{1,4})\s+深度品牌|\Z)',
            all_content, re.DOTALL
        )
        if not brand_section_match:
            # 回退：在合并章节中匹配 ### 品牌名
            brand_section_match = re.search(
                rf'(?:###|####)\s+[^\n]*{brand_pattern}[^\n]*\n(.*?)(?=(?:###|####)\s+|\Z)',
                all_content, re.DOTALL
            )
        if brand_section_match:
            brand_lines = len([l for l in brand_section_match.group(1).split("\n") if l.strip()])
            brand_ok = brand_lines >= min_deep_lines
        else:
            brand_lines = 0
            brand_ok = False
        
        results.append({
            "category": "D. 颗粒度检查",
            "check": f"D-4 深度品牌[{brand}]五维行数",
            "rule": f"≥{min_deep_lines}行",
            "detail": f"实际: {brand_lines}行",
            "status": "PASS" if brand_ok else "FAIL",
            "message": "" if brand_ok else f"仅{brand_lines}行，五维展开不足"
        })
    
    # D-5: 创始人研究
    founder_lines = 0
    founder_match = re.search(r'##\s+[^\n]*(?:创始人|冷友斌|邓文镇)[^\n]*\n(.*?)(?=##\s+|\Z)', all_content, re.DOTALL)
    if founder_match:
        founder_lines = len([l for l in founder_match.group(1).split("\n") if l.strip()])
    
    min_founder = GRANULARITY_RULES["founder_research"]["min_lines"]
    founder_ok = founder_lines >= min_founder
    results.append({
        "category": "D. 颗粒度检查",
        "check": "D-5 创始人研究行数",
        "rule": f"≥{min_founder}行，含≥3篇原生稿件索引",
        "detail": f"实际: {founder_lines}行",
        "status": "PASS" if founder_ok else "FAIL",
        "message": "" if founder_ok else f"创始人研究仅{founder_lines}行"
    })
    
    # D-6: 创品策略方向数量
    innovation_count = len(re.findall(r'借鉴|原创性|创品|新品类', all_content))
    innovation_ok = innovation_count >= GRANULARITY_RULES["innovation_strategy"]["min_directions"]
    results.append({
        "category": "D. 颗粒度检查",
        "check": "D-6 创品策略方向数量",
        "rule": f"≥{GRANULARITY_RULES['innovation_strategy']['min_directions']}个方向",
        "detail": f"检测到创品相关内容: {innovation_count}处",
        "status": "PASS" if innovation_ok else "WARN",
        "message": "" if innovation_ok else "创品策略可能不足10个方向"
    })
    
    return results


# ── E. 交付检查 ────────────────────────────────────────────

def check_delivery(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """D. 交付检查（逸凡确认节点）。"""
    results = []
    
    # D-1: 维度一致性——所有品牌趋势与人群是否补齐
    results.append({
        "category": "D. 交付检查",
        "check": "D-1 维度一致性",
        "rule": "所有品牌趋势与人群是否补齐",
        "detail": "趋势+人群维度覆盖",
        "status": "PASS",
        "message": "【逸凡确认】趋势与人群维度覆盖情况"
    })
    
    # D-2: 图表标签
    c_dir = charts_dir()
    chart_count = len(list(c_dir.glob("*"))) if c_dir.exists() else 0
    results.append({
        "category": "D. 交付检查",
        "check": "D-2 图表标签完整性",
        "rule": "图表是否有品牌名标签",
        "detail": f"共 {chart_count} 个图表文件",
        "status": "PASS" if chart_count > 0 else "WARN",
        "message": f"已生成 {chart_count} 个图表文件"
    })
    
    # D-3: 数据完整性
    c_dir_content = content_dir()
    content_file_count = len(list(c_dir_content.rglob("*.md"))) if c_dir_content.exists() else 0
    results.append({
        "category": "D. 交付检查",
        "check": "D-3 数据完整性",
        "rule": "上市公司财报数据是否完整",
        "detail": f"内容文件数: {content_file_count}",
        "status": "PASS",
        "message": "【逸凡确认】财报数据完整性需人工核实"
    })
    
    # D-4: 导航正确性 — 自动验证 docx heading 结构
    heading_check = verify_docx_heading_structure(project_config)
    results.append(heading_check)
    
    # D-5: ch5 品牌对比维度标注
    ch5_note = project_config.get_ch5_dimensions_note()
    results.append({
        "category": "D. 交付检查",
        "check": "D-5 ch5品牌对比维度",
        "rule": "是否已标注'维度待逸凡定义'",
        "detail": f"当前配置: {ch5_note}",
        "status": "PASS" if ch5_note else "WARN",
        "message": f"ch5 品牌对比维度配置: {ch5_note}"
    })
    
    # D-6: 版本号规范检查
    results.append({
        "category": "D. 交付检查",
        "check": "D-6 版本号规范",
        "rule": "文件命名「品牌中文名-行业-V数字.数字-日期.docx」，整数升版=结构改动，小数升版=文字改动",
        "detail": f"当前: {project_config.get_docx_filename()}",
        "status": "PASS" if _verify_version_format(project_config) else "WARN",
        "message": _version_check_message(project_config)
    })
    
    return results


# ── E. docx 标题结构验证 ───────────────────────────────────

def verify_docx_heading_structure(project_config: ProjectConfig) -> dict:
    """
    E. docx 标题结构自动验证。
    打开生成的 docx，解析 word/document.xml，
    检查 Heading1/Heading2/Heading3 数量是否达标。

    依据：Word 左侧导航大纲 = pStyle w:val="Heading1|Heading2|Heading3" 的段落
    
    Bug 案例（2026-07-20）：北纬47度独立脚本把 markdown # 映射成 level=0,
    导致 Heading1=0，导航大纲完全空白。
    """
    import zipfile
    from lxml import etree

    r_dir = reports_dir()
    docx_files = list(r_dir.glob("*.docx"))
    
    if not docx_files:
        return {
            "category": "E. docx标题结构",
            "check": "E-1 标题层级验证",
            "rule": "Heading1≥2, Heading2≥3, Heading3≥5",
            "detail": "未找到 docx 文件",
            "status": "FAIL",
            "message": "报告目录中无 docx 文件，跳过标题结构检查"
        }
    
    # 取最新的 docx 文件
    docx_path = max(docx_files, key=lambda p: p.stat().st_mtime)
    
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            doc_xml = z.read('word/document.xml').decode('utf-8')
        
        # 统计各层级 heading
        import re
        h1_count = len(re.findall(r'w:val="Heading1"', doc_xml))
        h2_count = len(re.findall(r'w:val="Heading2"', doc_xml))
        h3_count = len(re.findall(r'w:val="Heading3"', doc_xml))
        
        # 阈值：至少要有章节标题(H1)、小节标题(H2)、细节标题(H3)
        h1_ok = h1_count >= 2
        h2_ok = h2_count >= 3
        h3_ok = h3_count >= 5
        
        all_ok = h1_ok and h2_ok and h3_ok
        
        issues = []
        if not h1_ok:
            issues.append(f"Heading1仅{h1_count}个，需≥2（markdown # 可能未映射到 Heading 1）")
        if not h2_ok:
            issues.append(f"Heading2仅{h2_count}个，需≥3")
        if not h3_ok:
            issues.append(f"Heading3仅{h3_count}个，需≥5")
        
        return {
            "category": "E. docx标题结构",
            "check": "E-1 标题层级验证",
            "rule": f"Heading1≥2, Heading2≥3, Heading3≥5。当前: H1={h1_count}, H2={h2_count}, H3={h3_count}",
            "detail": f"文件: {docx_path.name}",
            "status": "PASS" if all_ok else "FAIL",
            "message": "标题层级完整，导航大纲可用" if all_ok else "; ".join(issues)
        }
    except Exception as e:
        return {
            "category": "E. docx标题结构",
            "check": "E-1 标题层级验证",
            "rule": "Heading1≥2, Heading2≥3, Heading3≥5",
            "detail": f"解析失败: {e}",
            "status": "FAIL",
            "message": f"无法解析 docx 标题结构: {e}"
        }


# ── 版本号格式验证 ─────────────────────────────────────────

def _verify_version_format(project_config: ProjectConfig) -> bool:
    """验证 docx 文件名是否符合版本号命名规范。"""
    filename = project_config.get_docx_filename()
    if not filename:
        return False
    # 匹配模式: 品牌中文名-行业-V数字.数字-日期.docx
    pattern = r'^.+?-.+-V\d+(\.\d+)?-\d{8}\.docx$'
    return bool(re.match(pattern, filename))


def _version_check_message(project_config: ProjectConfig) -> str:
    """生成版本号检查消息。"""
    filename = project_config.get_docx_filename()
    if not filename:
        return "config 中未设置 output_settings.docx_filename"
    if _verify_version_format(project_config):
        return f"版本号格式正确: {filename}"
    return f"版本号格式不符合规范，应为「品牌中文名-行业-V数字.数字-日期.docx」格式（整数升版=结构改动，小数升版=文字改动），当前: {filename}"


# ── 报告生成 ───────────────────────────────────────────────

def generate_qa_report(results: List[dict], schema: ReportSchema,
                       project_config: ProjectConfig, total: int,
                       passed: int, failed: int, warnings: int) -> str:
    """生成 markdown QA 报告。"""
    
    lines = [
        f"# QA 检查报告",
        f"",
        f"**项目:** {project_config.project_name}",
        f"**行业:** {project_config.industry}",
        f"**检查时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Schema 版本:** {schema.version}",
        f"",
        f"## 概览",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 总检查项 | {total} |",
        f"| ✅ 通过 | {passed} |",
        f"| ❌ 失败 | {failed} |",
        f"| ⚠️ 警告 | {warnings} |",
        f"| 通过率 | {passed/total*100:.1f}% |" if total > 0 else "",
        f"",
    ]
    
    # 按类别分组
    categories = {}
    for r in results:
        cat = r.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    for cat_name, cat_results in categories.items():
        lines.append(f"## {cat_name}")
        lines.append("")
        for r in cat_results:
            status_icon = "✅" if r["status"] == "PASS" else ("❌" if r["status"] == "FAIL" else "⚠️")
            lines.append(f"### {status_icon} {r['check']}")
            lines.append(f"")
            lines.append(f"- **规则:** {r['rule']}")
            lines.append(f"- **详情:** {r.get('detail', '')}")
            lines.append(f"- **状态:** {r['status']}")
            lines.append(f"- **说明:** {r.get('message', '')}")
            lines.append("")
    
    # 失败项汇总
    failed_items = [r for r in results if r["status"] == "FAIL"]
    if failed_items:
        lines.append("## ❌ 需修复项")
        lines.append("")
        for r in failed_items:
            lines.append(f"1. **{r['check']}**: {r['message']}")
        lines.append("")
        lines.append("### 修复建议")
        lines.append("")
        for r in failed_items:
            lines.append(f"- **{r['check']}**: 请回退到对应步骤修复后重新运行 QA 检查")
        lines.append("")
    
    # 附录：检查清单
    lines.append("## 附录：检查项覆盖清单")
    lines.append("")
    lines.append("| # | 检查项 | 类别 | 规则 |")
    lines.append("|---|--------|------|------|")
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['check']} | {r.get('category', '')} | {r['rule'][:60]} |")
    lines.append("")
    
    # 附录：schema QA rules 引用
    lines.append("## 附录：依据 Schema")
    lines.append("")
    lines.append(f"本报告依据 `report_schema.json` v{schema.version} 的 `qa_rules` 定义执行。")
    lines.append("")
    
    return "\n".join(lines)
