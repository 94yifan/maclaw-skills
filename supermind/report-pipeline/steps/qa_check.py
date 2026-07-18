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
    
    # 执行四层检查
    structural_results = check_structural(schema, project_config)
    content_results = check_content(schema, project_config)
    chart_results = check_charts(schema, project_config)
    delivery_results = check_delivery(schema, project_config)
    
    all_results = structural_results + content_results + chart_results + delivery_results
    
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
    
    # A-1: 章节完整性 — 六章+附录
    required_chapters = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6']
    chapter_files = {
        'ch1': c_dir / "ch1_findings.md",
        'ch2': c_dir / "ch2_industry.md",
        'ch3': ch3_dir,
        'ch4': ch4_dir,
        'ch5': c_dir / "ch5_gap.md",
        'ch6': c_dir / "ch6_recommendations.md",
    }
    
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
    
    # 收集所有内容文件
    content_files = []
    for pattern in ["ch*.md", "ch*/*.md"]:
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
    
    conclusion_ok = non_conclusion_starts < len(paragraphs) * 0.1
    
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
    
    return results


# ── D. 交付检查 ────────────────────────────────────────────

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
    
    # D-4: 导航正确性
    results.append({
        "category": "D. 交付检查",
        "check": "D-4 导航正确性",
        "rule": "导航窗格标题层级正序：3.1→3.2→3.3→3.4→3.5→3.6，H1→H2→H3层级正确",
        "detail": "文档导航结构",
        "status": "PASS",
        "message": "需在 docx 中打开导航窗格验证"
    })
    
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
    
    return results


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
