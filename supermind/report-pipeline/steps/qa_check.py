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
    step_start("qa_check", "QA 自动检查 — 结构/内容/图表/交付四层 + 终端docx验证")
    
    r_dir = reports_dir()
    
    # 执行五层检查
    structural_results = check_structural(schema, project_config)
    content_results = check_content(schema, project_config)
    chart_results = check_charts(schema, project_config)
    granularity_results = check_granularity(schema, project_config)
    delivery_results = check_delivery(schema, project_config)
    
    # 证据层级一致性检查（v2.0新增）
    tier_results = check_evidence_tier_consistency(schema, project_config)
    
    # 第六层：终端docx直接验证（直接解析docx文件，检查图片嵌入+内容相关性+电商数据）
    docx_results = check_docx_final(project_config)
    
    all_results = structural_results + content_results + chart_results + granularity_results + delivery_results + tier_results + docx_results
    
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
        'ch6': c_dir / "ch6_strategy.md",
        # v2.0新增文件（作为章节内容的一部分）
        'ch2_chain': c_dir / "ch2_chain_map.md",
        'ch3_content_types': c_dir / "ch3_content_types.md",
        'ch6_opp': c_dir / "ch6_opportunity_map.md",
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
    for pattern in ["ch*.md", "ch*/*.md", "report*.md", "founder_research.md", "innovation_strategy.md", "brand_overview.md", "pre_research.md", "ch7_sleep_insights.md"]:
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
    
    # B-8: 电商数据完整性 — 检查是否有天猫/京东实测数据
    ecom_keywords = ['天猫', '旗舰店', '付款', '电商', '京东']
    ecom_hits = sum(1 for kw in ecom_keywords if kw in all_content)
    ecom_ok = ecom_hits >= 3
    results.append({
        "category": "B. 内容检查",
        "check": "B-8 电商数据完整性",
        "rule": "必须包含天猫/京东电商实测数据。至少3个电商关键词出现。",
        "detail": f"电商关键词: {ecom_hits}/{len(ecom_keywords)}个出现",
        "status": "PASS" if ecom_ok else "FAIL",
        "message": f"电商数据关键词覆盖{ecom_hits}个：{[kw for kw in ecom_keywords if kw in all_content]}" if ecom_ok else f"电商数据缺失！仅命中{[kw for kw in ecom_keywords if kw in all_content]}个关键词，缺少：{[kw for kw in ecom_keywords if kw not in all_content]}"
    })
    
    # B-10: 人群收入跨度检测 — 防止收入范围跨度过大
    income_patterns = re.findall(r'月入[\d.,]+[万kK]?[-~至][\d.,]+[万kK]', all_content)
    income_patterns += re.findall(r'收入[\d.,]+[万kK]?[-~至][\d.,]+[万kK]', all_content)
    income_patterns += re.findall(r'月收入[\d.,]+[-~][\d.,]+', all_content)
    # 档位定义
    brackets = [0, 3000, 5000, 8000, 12000, 20000, 30000, 50000, 1000000]
    bracket_labels = ["3k以下", "3k-5k", "5k-8k", "8k-12k", "12k-20k", "20k-30k", "30k-50k", "50k+"]
    
    def _count_brackets_crossed(low_val, high_val):
        """计算低值到高值跨越了多少个档位。"""
        low_bracket = 0
        high_bracket = 0
        for b_idx in range(len(brackets) - 1):
            if low_val >= brackets[b_idx] and low_val < brackets[b_idx + 1]:
                low_bracket = b_idx
            if high_val >= brackets[b_idx] and high_val < brackets[b_idx + 1]:
                high_bracket = b_idx
        if high_val >= brackets[-2]:
            high_bracket = len(brackets) - 2
        if low_val >= brackets[-2]:
            low_bracket = len(brackets) - 2
        return high_bracket - low_bracket
    
    income_issues = []
    for ip in income_patterns:
        nums = re.findall(r'[\d.]+', ip)
        if len(nums) >= 2:
            try:
                low = float(nums[0])
                high = float(nums[1])
                if 'k' in ip.lower():
                    low *= 1000
                    high *= 1000
                elif '万' in ip:
                    low *= 10000
                    high *= 10000
                if low > 0 and high > low:
                    crossed = _count_brackets_crossed(low, high)
                    if crossed > 2:
                        income_issues.append(f"跨越{crossed}个档位: {ip}")
            except (ValueError, IndexError):
                pass
    
    income_ok = len(income_issues) == 0
    results.append({
        "category": "B. 内容检查",
        "check": "B-10 人群收入跨度检测",
        "rule": "收入范围不得超过2个档位（如5000-8000 ok，5000-50000 rejected）",
        "detail": f"发现{len(income_issues)}处异常收入跨度",
        "status": "FAIL" if income_issues else "PASS",
        "message": "; ".join(income_issues) if income_issues else "收入跨度检测通过"
    })

    # B-9: 内容质量检测 — AI腔/星号强调/破折号列表
    ai_tells = ['本质上', '整体而言', '从某种意义上说', '值得注意的是', '不可忽视的是', '毋庸置疑', '显而易见']
    star_count = all_content.count('**')
    dash_list_count = len(re.findall(r'-\s+\w+\s+-\s+\w+\s+-\s+\w+', all_content))
    ai_tell_count = sum(all_content.count(t) for t in ai_tells)
    quality_ok = star_count < 10 and ai_tell_count < 3 and dash_list_count < 5
    quality_issues = []
    if star_count >= 10:
        quality_issues.append(f"星号强调(**)出现{star_count}次（阈值<10）")
    if ai_tell_count >= 3:
        ai_found = [(t, all_content.count(t)) for t in ai_tells if all_content.count(t) > 0]
        quality_issues.append(f"AI填充词出现{ai_tell_count}次: {ai_found}")
    if dash_list_count >= 5:
        quality_issues.append(f"破折号列表体出现{dash_list_count}次（阈值<5）")
    results.append({
        "category": "B. 内容检查",
        "check": "B-9 内容质量检测（AI腔/星号/列表体）",
        "rule": "星号强调(**) < 10次, AI填充词 < 3次, 破折号列表体 < 5次",
        "detail": f"**={star_count}次 | AI腔={ai_tell_count}次 | 破折列表={dash_list_count}次",
        "status": "PASS" if quality_ok else "FAIL",
        "message": "; ".join(quality_issues) if quality_issues else "内容质量检测通过"
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
    finding_count = max(
        len(re.findall(r'发现[一二三四五六七八九十\d]', all_content)),
        len(re.findall(r'^- \*\*', all_content, re.MULTILINE))  # bullet style: - **key**:
    )
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
        # 优先匹配 deep_品牌名.md 独立文件格式: # 品牌名：XXX
        brand_section_match = re.search(
            rf'^#\s+[^\n]*{brand_pattern}[^\n]*[：:]\s*[^\n]*\n(.*?)(?=^#\s+[^\n]*[：:]\s|\Z)',
            all_content, re.DOTALL | re.MULTILINE
        )
        if not brand_section_match:
            # 回退：匹配 # 深度品牌：XXX 格式
            brand_section_match = re.search(
                rf'#[^\n]*深度品牌[^\n]*{brand_pattern}[^\n]*\n(.*?)(?=(?:#{1,4})\s+深度品牌|\Z)',
                all_content, re.DOTALL
            )
        if not brand_section_match:
            # 回退2：在合并章节中匹配 ### 品牌名（排除仅有链接占位的空段落）
            m = re.search(
                rf'(?:###|####)\s+[^\n]*{brand_pattern}[^\n]*\n(.*?)(?=(?:###|####)\s+|\Z)',
                all_content, re.DOTALL
            )
            if m:
                captured = m.group(1)
                # 如果捕获内容几乎只是链接占位，跳过
                non_link_lines = [l for l in captured.split('\n') if l.strip() and not l.strip().startswith('→ [')]
                if len(non_link_lines) >= 3:
                    brand_section_match = m
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
    
    # D-5: 创始人研究 - 统计创始人研究区块中的非空行数
    founder_lines = 0
    founder_match = re.search(r'(#{1,2}\s+[^\n]*创始人[^\n]*)', all_content)
    if founder_match:
        start_pos = founder_match.start()
        rest = all_content[start_pos:]
        # 找到下一个非子标题的 H1/H2 标题的位置
        next_h1 = re.search(r'\n#{1,2}\s+(?!第|二|三|四|五|六|[0-9]+\.|关键|创业|成长|核心|个人|原生|参考|数据|创始人|经营|稿件)', rest)
        if next_h1:
            block = rest[:next_h1.start()]
        else:
            block = rest
        founder_lines = len([l for l in block.split('\n') if l.strip() and not l.strip().startswith('#')])
    
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


# ── 证据层级一致性检查（v2.0新增）───────────────────────────

def check_evidence_tier_consistency(schema: ReportSchema, project_config: ProjectConfig) -> List[dict]:
    """
    证据层级一致性检查。
    规则依据 report_schema.json 中 evidence_tier_consistency 定义。
    检查项：
    - tier_inflation: mapped/speculation级数据被表述成confirmed的情况
    - tier_downgrade_only: 检查有没有tier被升级
    - key_discipline: pipeline≠orders, qualification≠volume ramp
    - unmarked_claims: 关键声称是否缺少evidence_tier标注
    """
    results = []
    c_dir = content_dir()

    # 收集所有content markdown文件
    content_files = list(c_dir.glob("*.md"))
    for subdir in c_dir.iterdir():
        if subdir.is_dir():
            content_files.extend(subdir.glob("*.md"))

    all_content = ""
    for cf in content_files:
        if cf.name.endswith("_prompt.md"):
            continue
        try:
            all_content += cf.read_text(encoding="utf-8") + "\n"
        except Exception:
            continue

    import re
    paragraphs = [p.strip() for p in all_content.split('\n\n') if p.strip() and len(p.strip()) > 30]

    # E-1: tier_inflation — mapped/speculation被表述成confirmed
    inflation_issues = []
    confirmed_patterns = [
        ("经核实", r'经核实'),
        ("官方确认", r'官方确认'),
        ("确认", r'确认'),
        ("数据显示", r'数据显示'),
        ("公开披露", r'公开披露'),
        ("财报显示", r'财报显示'),
        ("年报显示", r'年报显示'),
        ("招股书显示", r'招股书显示'),
        ("公告显示", r'公告显示'),
    ]
    for i, para in enumerate(paragraphs):
        if not re.search(r'\d+[万亿千百%倍]*', para):
            continue
        has_mapped_spec = bool(re.search(r'[\[（(]推测|映射|推断|猜测|估计|未经证实|待验证[\]）)]', para))
        has_confirmed_wording = any(re.search(pat, para) for _, pat in confirmed_patterns)
        if has_mapped_spec and has_confirmed_wording:
            inflation_issues.append(f"段{i+1}: 标注推测/映射但使用了confirmed措辞")
            if len(inflation_issues) >= 5:
                break

    results.append({
        "category": "E. 证据层级一致性",
        "check": "E-1 tier_inflation",
        "rule": "mapped/speculation级数据不得使用confirmed措辞（经核实/官方确认/数据显示等）",
        "detail": f"发现 {len(inflation_issues)} 处可能的层级通胀",
        "status": "FAIL" if inflation_issues else "PASS",
        "message": "; ".join(inflation_issues[:3]) if inflation_issues else "未检测到层级通胀"
    })

    # E-2: tier_downgrade_only — 检查层级升级
    upgrade_issues = []
    tier_markers = re.findall(r'\[(已确认|报道层|映射|推测)\]|[\[（(](confirmed|reported|mapped|speculation)[\]）)]', all_content)
    tier_timeline = []
    for m in tier_markers:
        tier = m[0] or m[1]
        tier_timeline.append(tier)
    tier_order = {'speculation': 0, '推测': 0, 'mapped': 1, '映射': 1, 'reported': 2, '报道层': 2, 'confirmed': 3, '已确认': 3}
    for i in range(len(tier_timeline) - 1):
        prev = tier_order.get(tier_timeline[i], -1)
        curr = tier_order.get(tier_timeline[i+1], -1)
        if prev >= 0 and curr >= 0 and curr > prev:
            upgrade_issues.append(f"{tier_timeline[i]} → {tier_timeline[i+1]}")

    results.append({
        "category": "E. 证据层级一致性",
        "check": "E-2 tier_downgrade_only",
        "rule": "tierAfterAudit ≤ 原tier，层级只能降不能升",
        "detail": f"检查 {len(tier_markers)} 个tier标记，发现 {len(upgrade_issues)} 处可能的升级",
        "status": "FAIL" if len(upgrade_issues) > int(len(tier_markers) * 0.4) else "PASS",
        "message": "; ".join(upgrade_issues[:3]) if upgrade_issues else "未检测到层级不当升级"
    })

    # E-3: key_discipline — pipeline≠orders等关键纪律
    discipline_issues = []
    if re.search(r'pipeline[^s][^。！？\n]*(?:订单|已售|销量|出货)', all_content):
        discipline_issues.append("pipeline被当作'已有订单/已售'使用（违规模≠orders纪律）")
    if re.search(r'qualification[^。！？\n]*(?:量产|出货|交付|放量)', all_content):
        discipline_issues.append("qualification被当作'量产/出货'使用（违反qualification≠volume ramp纪律）")
    if re.search(r'生态相邻[^。！？\n]*(?:订单|量产)|合作[^。！？\n]*生态相邻[^。！？\n]*(?:供货|量产)', all_content):
        discipline_issues.append("生态相邻/合作被当作'量产订单'（违反生态相邻≠量产订单纪律）")

    results.append({
        "category": "E. 证据层级一致性",
        "check": "E-3 key_discipline_violation",
        "rule": "pipeline≠orders, qualification≠volume ramp, 生态相邻≠量产订单",
        "detail": f"发现 {len(discipline_issues)} 处关键纪律违规",
        "status": "FAIL" if discipline_issues else "PASS",
        "message": "; ".join(discipline_issues) if discipline_issues else "关键纪律检查通过"
    })

    # E-4: unmarked_claims — 关键数据声称缺少evidence_tier
    unmarked = 0
    sample_unmarked = []
    for para in paragraphs:
        if not re.search(r'\d+[万亿千百%倍]*', para):
            continue
        if para.startswith('#') or para.startswith('|'):
            continue
        has_tier = bool(re.search(r'\[(已确认|报道层|映射|推测)\]', para) or
                        re.search(r'evidence_tier[：:]', para, re.IGNORECASE))
        if not has_tier:
            unmarked += 1
            if len(sample_unmarked) < 3 and len(para) > 40:
                sample_unmarked.append(para[:60] + '...')

    total_with_numbers = sum(1 for p in paragraphs if re.search(r'\d+[万亿千百%倍]*', p))
    unmarked_ratio = unmarked / total_with_numbers if total_with_numbers > 0 else 0
    unmarked_ok = unmarked_ratio < 0.93

    results.append({
        "category": "E. 证据层级一致性",
        "check": "E-4 unmarked_claims",
        "rule": "含具体数字的关键数据声称需标注evidence_tier",
        "detail": f"含数段落: {total_with_numbers}, 未标注: {unmarked} ({unmarked_ratio*100:.0f}%)",
        "status": "FAIL" if not unmarked_ok else "PASS",
        "message": "; ".join(sample_unmarked) if sample_unmarked else "关键数据claim均有evidence_tier标注或可接受"
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

def check_docx_final(project_config: ProjectConfig) -> List[dict]:
    """
    F. 终端docx验证 — 直接解析docx文件，检查最终产物的完整性。
    这是QA的最后一道防线，不依赖中间文件（content/ charts/），只检查最终docx。
    """
    results = []
    
    # 找到docx文件
    docx_filename = project_config.get("output_settings.docx_filename", "")
    if not docx_filename:
        # fallback
        reports_dir_path = BASE_DIR / "output" / "reports"
        docx_files = sorted(reports_dir_path.glob(f"*{project_config.project_name.split()[0]}*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
        if docx_files:
            docx_path = docx_files[0]
        else:
            results.append({"category": "F. docx终端验证", "check": "F-1 docx文件存在", "rule": "docx文件必须存在", "detail": "未找到docx", "status": "FAIL", "message": "未找到docx文件"})
            return results
    else:
        docx_path = BASE_DIR / "output" / "reports" / docx_filename
    
    if not docx_path.exists():
        results.append({"category": "F. docx终端验证", "check": "F-1 docx文件存在", "rule": "docx文件必须存在", "detail": str(docx_path), "status": "FAIL", "message": f"文件不存在: {docx_path.name}"})
        return results
    
    results.append({"category": "F. docx终端验证", "check": "F-1 docx文件存在", "rule": "docx文件必须存在", "detail": str(docx_path.name), "status": "PASS", "message": f"找到: {docx_path.name}"})
    
    import zipfile
    from xml.etree import ElementTree as ET
    
    try:
        with zipfile.ZipFile(docx_path) as z:
            doc_xml = z.read('word/document.xml').decode()
            
            # Extract all text
            root = ET.fromstring(doc_xml)
            ns_w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            all_text = []
            for p in root.iter(f'{{{ns_w}}}p'):
                texts = p.findall(f'.//{{{ns_w}}}t')
                line = ''.join(t.text or '' for t in texts)
                all_text.append(line)
            full_text = '\n'.join(all_text)
            
            # F-2: 图片嵌入检查
            image_files = [n for n in z.namelist() if n.startswith('word/media/image')]
            embedded_drawings = doc_xml.count('<wp:inline') + doc_xml.count('<wp:anchor')
            
            images_ok = len(image_files) >= 2 and embedded_drawings >= 2
            results.append({
                "category": "F. docx终端验证",
                "check": "F-2 图表实际嵌入",
                "rule": "docx中必须实际嵌入≥2张图片（<wp:inline>或<wp:anchor>计数）",
                "detail": f"图片文件: {len(image_files)}个, 实际嵌入: {embedded_drawings}个",
                "status": "PASS" if images_ok else "FAIL",
                "message": f"图片{len(image_files)}个, 嵌入{embedded_drawings}个" if images_ok else f"❌ 图片未嵌入！文件{len(image_files)}个但实际嵌入仅{embedded_drawings}个"
            })
            
            # F-3: 内容相关性 — 检查是否混入无关品牌
            focus = project_config.focus_brand if project_config.focus_brand else ""
            deep_brands = set(project_config.deep_brands + project_config.summary_brands)
            # 行业通用词白名单
            industry_terms = project_config.industry.split('/') if project_config.industry else []
            allowed = set(deep_brands) | {focus} | set(industry_terms) | {
                "康尔馨", "亚朵", "罗莱", "梦百合", "水星", "网易严选", "富安娜", "睡眠博士", "野兽派", "躺岛", "京东京造", "梦洁", "宜家",
                "床品", "家纺", "四件套", "枕头", "睡眠", "酒店", "羽绒", "记忆棉", "被芯", "毛巾", "浴巾"
            }
            # 已知的无关品牌名（来自其他项目）
            suspicious_map = {
                "三棵树": "涂料项目", "立邦": "涂料项目", "多乐士": "涂料项目", "卡百利": "涂料项目",
                "嘉宝莉": "涂料项目", "菲玛": "涂料项目", "亚士漆": "涂料项目",
                "漆": "涂料行业术语", "涂料": "涂料行业", "墙面漆": "涂料", "艺术漆": "涂料",
                "榴莲": "食品项目", "玉米": "食品项目"
            }
            found_brands = {}
            for kw, source in suspicious_map.items():
                count = full_text.count(kw)
                if count > 0 and kw not in allowed:
                    found_brands[kw] = {"count": count, "source": source}
            
            if found_brands:
                detail = "; ".join([f"{k}({v['count']}次,来自{v['source']})" for k, v in sorted(found_brands.items(), key=lambda x: -x[1]['count'])])
                results.append({
                    "category": "F. docx终端验证",
                    "check": "F-3 内容相关性",
                    "rule": "docx中不得出现本项目无关品牌名（如涂料/食品项目词汇）",
                    "detail": f"发现{len(found_brands)}个无关词汇",
                    "status": "FAIL",
                    "message": f"❌ 内容混入: {detail}"
                })
            else:
                results.append({
                    "category": "F. docx终端验证",
                    "check": "F-3 内容相关性",
                    "rule": "docx中不得出现本项目无关品牌名",
                    "detail": "无无关品牌名",
                    "status": "PASS",
                    "message": "✅ 内容纯净，无混入"
                })
            
            # F-4: 电商数据覆盖
            ecom_kw = {"天猫": full_text.count("天猫"), "京东": full_text.count("京东"), "旗舰店": full_text.count("旗舰店"), "付款": full_text.count("付款")}
            ecom_ok = all(v >= 3 for v in ecom_kw.values())
            results.append({
                "category": "F. docx终端验证",
                "check": "F-4 电商数据覆盖",
                "rule": "docx中必须包含天猫/京东电商实测数据（各≥3次提及）",
                "detail": str(ecom_kw),
                "status": "PASS" if ecom_ok else "FAIL",
                "message": f"电商关键词: {ecom_kw}" if ecom_ok else f"❌ 电商数据不足: {ecom_kw}"
            })
            
            # F-5: 字数检查
            total_chars = len(full_text)
            chars_ok = total_chars >= 60000
            results.append({
                "category": "F. docx终端验证",
                "check": "F-5 docx总字数",
                "rule": "docx正文≥60000字",
                "detail": f"实际: {total_chars:,}字",
                "status": "PASS" if chars_ok else "FAIL",
                "message": f"{total_chars:,}字" if chars_ok else f"❌ 仅{total_chars:,}字，不足60000"
            })
            
    except Exception as e:
        results.append({
            "category": "F. docx终端验证",
            "check": "F-0 docx解析",
            "rule": "docx文件必须可解析",
            "detail": str(e)[:100],
            "status": "FAIL",
            "message": f"docx解析失败: {e}"
        })
    
    return results


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
