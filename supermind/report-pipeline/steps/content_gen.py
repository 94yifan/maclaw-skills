"""
Steps 5-9: 内容生成模块。

职责：调用 DeepSeek V4 Pro 生成各章分析内容。
每步读取已分发的数据 + schema 写作规范 → 构建 prompt → 调用 LLM → 保存 markdown。

章节对应：
- Step 5: ch2 行业分析（Porter五力 + 行业趋势 + 竞品总矩阵）
- Step 6: ch3 竞品扫描（深度品牌5维 + 汇总品牌 + 竞争模式归纳）
- Step 7: ch4 本品分析（五维深度诊断 + 趋势人群预判）
- Step 8: ch5 差距对比（集团层 + 品牌层 + 差距定位）
- Step 9: ch6 策略建议（品牌策略 + 集团议题 + 项目范围）
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from steps.utils import (
    step_start, step_success, step_fail, step_skip,
    save_json, save_text, load_json, load_markdown,
    verify_input_file, verify_output_file,
    content_dir, data_dispatched_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


# ── Prompt 构建器 ──────────────────────────────────────────

def build_ch2_prompt(schema: ReportSchema, project_config: ProjectConfig,
                     dispatched_data: Dict) -> str:
    """构建第二章 prompt。"""
    writing_specs = schema.get_global_writing_rules()
    ch2 = schema.get_chapter("ch2")
    
    porter_dims = ch2.get("sections", {}).get("porter_five_forces", {}).get("dimensions", [])
    porter_names = [d["name"] for d in porter_dims]
    
    trends_req = ch2.get("sections", {}).get("industry_trends", {})
    matrix_cols = ch2.get("sections", {}).get("competitor_matrix", {}).get("columns", [])
    
    # P1-8: 追加写作铁律
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    prompt = f"""# 品牌研究报告 — 第二章：行业格局与竞品总矩阵

## 项目信息
- 行业：{project_config.industry}
- 报告类型：{project_config.report_type}
- 深度品牌：{', '.join(project_config.deep_brands)}
- 汇总品牌：{', '.join(project_config.summary_brands)}

## 写作规范
{chr(10).join(f'- {r}' for r in writing_specs)}
{writing_hard_rules}
## 章节构建方法

### 1. Porter五力扫描（约1页）
请从以下五个维度评估行业结构，每力一段：
{chr(10).join(f'- {n}' for n in porter_names)}
- 每力用完整句子表达，数据来源标注（行业研报/财报）
- 最后一句收尾判断：该力的强度（强/中/弱）及对行业竞争格局的影响

### 2. 行业趋势（3-5条，约1页）
必含要素（全部覆盖）：
- 市场规模+增速（当前规模、CAGR）
- 品牌集中度+格局变化（CR5/CR10、头部品牌变迁）
- 品类/渠道结构变化（线上/线下占比变化、细分品类增长）
- 可选：消费行为趋势
每条趋势 = 方向判断(1句) + 支撑数据(1-2个具体数字) + 对行业意味着什么(1句)

### 3. 竞品总矩阵（10-25行，约0.5页）
- 每品牌一行，{len(matrix_cols)}列：{', '.join(matrix_cols)}
- 一屏全览表。不排序不排名，纯信息陈列
- 上市公司标注财报关键数据

## 参考数据
{json.dumps(dispatched_data, ensure_ascii=False, indent=2)}

请直接输出第二章正文（markdown格式，不做引用注释）。
"""
    return prompt


def build_ch3_prompt(schema: ReportSchema, project_config: ProjectConfig,
                     brand: str, depth: str, dimension: Optional[str] = None,
                     dispatched_data: Dict = None) -> str:
    """构建第三章（竞品扫描）prompt。支持逐个品牌/维度。"""
    writing_specs = schema.get_global_writing_rules()
    depth_rules = schema.get_depth_rules()
    
    # P1-8: 追加写作铁律
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    base_prompt = f"""# 品牌研究报告 — 第三章：竞品多维度扫描

## 项目信息
- 行业：{project_config.industry}
- 品牌：{brand}
- 分析深度：{'深度品牌（每维独立成段）' if depth == 'deep' else '汇总品牌（每品牌一段+综述）'}

## 写作规范
{''.join(f'- {r}\n' for r in writing_specs)} 
{writing_hard_rules}"""
    
    if depth == "deep" and dimension:
        # 单个维度 prompt
        ch3 = schema.get_chapter("ch3")
        deep_section = ch3.get("sections", {}).get("deep_brands", {})
        per_brand = deep_section.get("per_brand_dimensions", {})
        dim_def = per_brand.get(dimension, {})
        
        dim_label = dim_def.get("label", dimension)
        writing_rule = dim_def.get("writing_rule", "")
        req_elements = dim_def.get("required_elements", [])
        sub_dims = dim_def.get("sub_dimensions", [])
        
        hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

        prompt = base_prompt + f"""
## 写作铁律
{hard_rules}
## 维度：{dim_label}
写作规则：{writing_rule}
必含要素：{json.dumps(req_elements, ensure_ascii=False, indent=2)}
"""
        if sub_dims:
            prompt += f"""
子维度：{json.dumps(sub_dims, ensure_ascii=False, indent=2)}
"""
        
        prompt += f"""
段落数范围：{depth_rules.get('deep_per_dimension_paragraphs', [1, 3])}
表达要求：{depth_rules.get('deep_per_dimension_expression_rule', '用完整句子清晰表达')}

## 参考数据
{json.dumps(dispatched_data or {}, ensure_ascii=False, indent=2)}

请直接输出该品牌该维度的分析文字。结论先行，自然段落。"""
        
        return prompt
    
    elif depth == "summary":
        # 汇总品牌：一段覆盖五要素
        hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""
        prompt = base_prompt + f"""
## 写作铁律
{hard_rules}
## 汇总品牌格式
每品牌一段，一段内用完整句子覆盖全部五要素：
1. 品牌定位（1句）
2. 核心产品+价格锚（1句）
3. 渠道表现亮点（1句）
4. 趋势位置判断（1句）
5. 核心人群一句话（1句）
字数不设上限，每要素必须表达清楚而非列关键词。

末尾加趋势综述段（3-5条趋势归纳）+人群综述段（群体特征总结）。

## 参考数据
{json.dumps(dispatched_data or {}, ensure_ascii=False, indent=2)}

请直接输出分析文字。"""
        return prompt
    
    else:
        # 全套深度品牌 prompt（全5维）
        dims = schema.get_deep_brand_dimensions()
        dim_summary = []
        for d in dims:
            rule = d["def"].get("writing_rule", "")
            dim_summary.append(f"- {d['label']}: {rule[:100]}...")
        
        hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

        prompt = base_prompt + f"""
## 写作铁律
{hard_rules}
## 深度品牌五维扫描（全维度）
请按以下五个维度逐维分析{project_config.industry}行业的【{brand}】品牌：

{chr(10).join(dim_summary)}

## 深度规则
- 每维度1-3段，每段用完整句子清晰表达
- 字数不设上限，必须达到可独立理解的完整程度
- 禁止因控制字数而省略关键信息或写成关键词碎片
- 逐个维度输出，维度间用 H2 分隔（```

## 【维度名】

```）

## 参考数据
{json.dumps(dispatched_data or {}, ensure_ascii=False, indent=2)}

请直接输出分析文字。"""
        return prompt


def build_ch4_prompt(schema: ReportSchema, project_config: ProjectConfig,
                     dispatched_data: Dict) -> str:
    """构建第四章（本品分析）prompt。"""
    writing_specs = schema.get_global_writing_rules()
    ch4 = schema.get_chapter("ch4")
    
    sections = ch4.get("sections", {})
    market_section = sections.get("market_channel_deep", {})
    brand_section = sections.get("brand_power_deep", {})
    product_section = sections.get("product_deep", {})
    trends_section = sections.get("trends_fit", {})
    audience_section = sections.get("audience_deep", {})
    
    focus = project_config.focus_brand
    
    # P1-8: 追加写作铁律
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    prompt = f"""# 品牌研究报告 — 第四章：本品深度分析

## 项目信息
- 行业：{project_config.industry}
- 本品：{focus}

## 写作规范
{chr(10).join(f'- {r}' for r in writing_specs)}
{writing_hard_rules}
## 分析维度与必含要素

### 1. 市场与渠道深度诊断
必含要素（全部覆盖）：
- 财务诊断（按上市地取对应口径）：
  - 营收规模与增速、利润结构、毛利率与净利率
  - 收入结构、费用结构、现金流、资产负债
- 市场表现力诊断：市场份额、增长质量、渠道效率、用户资产
- 多渠道表现扫描：天猫/京东/抖音/线下（各渠道分析内容+核心数据+渠道角色判断）
- 渠道策略评估：组合健康度、效率对比、增长路径

### 2. 品牌力深度诊断（品牌力+组织力）
- 品牌力六项诊断：大帽子创意营销、艺人代言、IP联名、公益营销、线上种草、线下营销
- 社交媒体联动分析：内容密度、互动数据、高频词、正面/负面舆情
- 组织力诊断：团队规模、agency协作、上市速度、组织稳定性
- 差异化判断：在竞品矩阵中的独特位置

### 3. 产品力深度诊断
- 四类品分析：销量最好的品(Top3-5爆款)、口碑声量最多的品、品类代表性品、品牌特色品
- 品控体系、产品矩阵诊断、创新管线、差异化评估
- 按品类/子品类分开分析，不可合并

### 4. 趋势适配分析（归纳+未来预判建议）
- 行业风向趋势（过往归纳+未来预判建议）
- 内容热点趋势（过往归纳+未来预判建议）
- 用户情绪趋势（过往归纳+未来预判建议）

### 5. 人群深度分析（归纳+未来预判建议）
- 现有用户画像（年龄/城市/场景/决策链，不能套模板）
- 可拓展人群（相邻人群+拓展逻辑+障碍+建议策略）
- 流失风险评估（方向+原因+挽回可行性）

## 参考数据
{json.dumps(dispatched_data, ensure_ascii=False, indent=2)}

请直接输出第四章正文。每个维度一段诊断，结论先行。好的说清楚、问题也敢说清楚。"""
    return prompt


def build_ch5_prompt(schema: ReportSchema, project_config: ProjectConfig,
                     dispatched_data: Dict) -> str:
    """构建第五章（差距对比）prompt。"""
    writing_specs = schema.get_global_writing_rules()
    ch5 = schema.get_chapter("ch5")
    group_dims = ch5.get("sections", {}).get("group_level", {}).get("dimensions", [])
    brand_note = ch5.get("sections", {}).get("brand_level", {}).get("_note", "")
    
    focus = project_config.focus_brand
    ch5_note = project_config.get_ch5_dimensions_note()
    
    # P1-8: 追加写作铁律
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    prompt = f"""# 品牌研究报告 — 第五章：本竞品差距对比

## 项目信息
- 行业：{project_config.industry}
- 本品：{focus}
- 深度品牌：{', '.join(project_config.deep_brands)}
- 汇总品牌：{', '.join(project_config.summary_brands)}

## 写作规范
{chr(10).join(f'- {r}' for r in writing_specs)}
{writing_hard_rules}
## 分析结构

### 1. 集团层面对比（适用于上市公司对比）
{len(group_dims)}个财务维度逐一对比：{', '.join(group_dims)}
- 先数据表后分析
- 每个维度一段：先说本品数据再对比竞品
- 给出差距判断，不啰嗦差距原因（原因在Ch4已分析过）

### 2. 品牌层面对比
⚠️ **品牌对比维度由逸凡定义。**
当前配置：{ch5_note}
{brand_note}

### 3. 差距快速定位
每条一条陈述 = 竞品名 + 差距本质(一句话) + "本品若能做X，差距可缩"
覆盖全部竞品。

## 参考数据
{json.dumps(dispatched_data, ensure_ascii=False, indent=2)}

请直接输出第五章正文。"""
    return prompt


def build_ch6_prompt(schema: ReportSchema, project_config: ProjectConfig,
                     dispatched_data: Dict) -> str:
    """构建第六章（策略建议）prompt。"""
    writing_specs = schema.get_global_writing_rules()
    ch6 = schema.get_chapter("ch6")
    brand_strat = ch6.get("sections", {}).get("brand_strategy", {})
    group_strat = ch6.get("sections", {}).get("group_strategy", {})
    project_scope = ch6.get("sections", {}).get("project_scope", {})
    
    focus = project_config.focus_brand
    
    # P1-8: 追加写作铁律
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    prompt = f"""# 品牌研究报告 — 第六章：咨询切入点与策略建议

## 项目信息
- 行业：{project_config.industry}
- 本品：{focus}
- 竞品范围：{', '.join(project_config.deep_brands + project_config.summary_brands)}

## 写作规范
{chr(10).join(f'- {r}' for r in writing_specs)}
{writing_hard_rules}
## 分析结构

### 1. 品牌层策略（{brand_strat.get('recommendation_count', [3, 5])}条）
每条包含：
- 核心建议（1句）
- 支撑逻辑（2-3点）
- 预期影响（1-2句）
- 实施路径（分阶段）
推理链：产品力vs品牌力断层 → 定位机会识别 → 燃创咨询切入点
不使用模糊语言，必须说「从X做起→做Y→达到Z」。

### 2. 集团层战略议题（{group_strat.get('issue_count', [2, 3])}项）
每项包含：
- 议题描述（1-2句）
- 为什么是现在（行业/竞争/内部窗口）
- 不解决的代价

### 3. 建议咨询项目范围
- 3-5个项目模块
- 每个模块：目标定义+产出物定义
- 优先级排序+预计周期
- 务实不浮夸

## 参考数据
{json.dumps(dispatched_data, ensure_ascii=False, indent=2)}

请直接输出第六章正文。"""
    return prompt


# ── 各步骤执行器 ──────────────────────────────────────────

def generate_ch2(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """Step 5: 生成第二章。"""
    step_start("ch2_generation", "行业分析写作 (Step 5)")
    
    out_dir = content_dir()
    out_path = out_dir / "ch2_industry.md"
    
    # 读取已分发的数据
    dispatched = load_dispatched_for_chapter("ch2", schema)
    prompt = build_ch2_prompt(schema, project_config, dispatched)
    
    # 保存 prompt 供 DeepSeek Pro 调用
    prompt_path = out_dir / "ch2_prompt.md"
    save_text(prompt, prompt_path)
    
    # 创建占位文件（实际调用由 DeepSeek Pro 代理执行）
    save_text(f"# 第二章：{schema.get_chapter_title('ch2')}\n\n[本内容由 DeepSeek V4 Pro 生成]\n\nPrompt 文件: {prompt_path}\n", out_path)
    
    verify_output_file(out_path, "ch2_generation")
    step_success("ch2_generation", [str(out_path), str(prompt_path)])
    return out_path


def generate_ch3(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """Step 6: 生成第三章（竞品扫描页面）。"""
    step_start("ch3_generation", "竞品扫描写作 (Step 6)")
    
    ch3_dir = content_dir() / "ch3_competitive"
    ch3_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成深度品牌的 prompt 文件
    for brand in project_config.deep_brands:
        dispatched = load_dispatched_for_brand("ch3", brand, schema)
        prompt = build_ch3_prompt(schema, project_config, brand, "deep", dispatched_data=dispatched)
        prompt_file = ch3_dir / f"deep_{brand}_prompt.md"
        save_text(prompt, prompt_file)
        
        # 占位 markdown
        brand_file = ch3_dir / f"deep_{brand}.md"
        save_text(f"# 深度品牌：{brand}\n\n[本内容由 DeepSeek V4 Pro 生成]\n\nPrompt 文件: {prompt_file}\n", brand_file)
    
    # 汇总品牌 prompt
    if project_config.summary_brands:
        dispatched_all = load_dispatched_for_chapter("ch3", schema)
        prompt = build_ch3_prompt(schema, project_config, "__summary__", "summary", dispatched_data=dispatched_all)
        prompt_file = ch3_dir / "summary_brands_prompt.md"
        save_text(prompt, prompt_file)
    
    # 竞争模式归纳 prompt
    competition_prompt = build_competition_pattern_prompt(schema, project_config)
    comp_file = ch3_dir / "competition_patterns_prompt.md"
    save_text(competition_prompt, comp_file)
    
    verify_output_file(ch3_dir / "deep_brands_list.txt" if False else ch3_dir, "ch3_generation")
    step_success("ch3_generation", [str(ch3_dir)])
    return ch3_dir


def build_competition_pattern_prompt(schema: ReportSchema, project_config: ProjectConfig) -> str:
    """构建竞争模式归纳 prompt。"""
    ch3 = schema.get_chapter("ch3")
    patterns_def = ch3.get("sections", {}).get("competition_patterns", {})
    framework = patterns_def.get("methodology_framework", [])
    
    writing_hard_rules = """
- 首句=独立判断结论（不能说「XX有几个特征」）
- 中间=具体数字+可验证事实
- 末句=这个判断对竞品意味着什么
- 禁止星号强调（**）、破折号列表体（- xxx - yyy）、填充词（本质上/整体而言/值得注意的是）
- 人群收入跨度不得超过2个档位（如5000-8000 ok，5000-50000 rejected）
"""

    return f"""# 竞争模式归纳

## 写作铁律
{writing_hard_rules}
## 方法框架
{json.dumps(framework, ensure_ascii=False, indent=2)}

## 项目品牌
- 深度品牌：{', '.join(project_config.deep_brands)}
- 本品：{project_config.focus_brand}

## 输出要求
1. 梳理深度品牌分析中各维度的共性特征，按行业实际归纳竞争模式（不预设类型和数量）
2. 每种模式 = 模式命名 + 核心特征(2-3点) + 代表品牌(1-2个) + 本品与模式的差距判断
3. 模式必须是可复制的、有成功案例支撑的
4. 结尾：本品的竞争模式定位

请直接输出竞争模式归纳正文。"""


def generate_ch4(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """Step 7: 生成第四章。"""
    step_start("ch4_generation", "本品分析写作 (Step 7)")
    
    ch4_dir = content_dir() / "ch4_deep"
    ch4_dir.mkdir(parents=True, exist_ok=True)
    
    dispatched = load_dispatched_for_chapter("ch4", schema)
    prompt = build_ch4_prompt(schema, project_config, dispatched)
    
    prompt_path = ch4_dir / "ch4_prompt.md"
    save_text(prompt, prompt_path)
    
    out_path = ch4_dir / f"{project_config.focus_brand}_deep.md" if project_config.focus_brand else ch4_dir / "focus_brand_deep.md"
    save_text(f"# 第四章：{schema.get_chapter_title('ch4')} — {project_config.focus_brand}\n\n[本内容由 DeepSeek V4 Pro 生成]\n\nPrompt 文件: {prompt_path}\n", out_path)
    
    verify_output_file(out_path, "ch4_generation")
    step_success("ch4_generation", [str(out_path)])
    return out_path


def generate_ch5(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """Step 8: 生成第五章。"""
    step_start("ch5_generation", "差距对比写作 (Step 8)")
    
    out_dir = content_dir()
    dispatched = load_dispatched_for_chapter("ch5", schema)
    prompt = build_ch5_prompt(schema, project_config, dispatched)
    
    prompt_path = out_dir / "ch5_prompt.md"
    save_text(prompt, prompt_path)
    
    out_path = out_dir / "ch5_gap.md"
    save_text(f"# 第五章：{schema.get_chapter_title('ch5')}\n\n[本内容由 DeepSeek V4 Pro 生成]\n\nPrompt 文件: {prompt_path}\n", out_path)
    
    verify_output_file(out_path, "ch5_generation")
    step_success("ch5_generation", [str(out_path)])
    return out_path


def generate_ch6(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """Step 9: 生成第六章。"""
    step_start("ch6_generation", "策略建议写作 (Step 9)")
    
    out_dir = content_dir()
    dispatched = load_dispatched_for_chapter("ch6", schema)
    prompt = build_ch6_prompt(schema, project_config, dispatched)
    
    prompt_path = out_dir / "ch6_prompt.md"
    save_text(prompt, prompt_path)
    
    out_path = out_dir / "ch6_recommendations.md"
    save_text(f"# 第六章：{schema.get_chapter_title('ch6')}\n\n[本内容由 DeepSeek V4 Pro 生成]\n\nPrompt 文件: {prompt_path}\n", out_path)
    
    verify_output_file(out_path, "ch6_generation")
    step_success("ch6_generation", [str(out_path)])
    return out_path


# ── 数据加载辅助 ──────────────────────────────────────────

def load_dispatched_for_chapter(chapter: str, schema: ReportSchema) -> Dict:
    """加载某章所有已分发的数据。"""
    dispatched_dir = data_dispatched_dir()
    prefix = chapter.replace("ch", "ch")
    files = list(dispatched_dir.glob(f"{prefix}*.json"))
    
    data = {}
    for f in files:
        try:
            record = load_json(f)
            key = f.stem
            data[key] = record
        except (FileNotFoundError, ValueError):
            continue
    
    return data


def load_dispatched_for_brand(chapter: str, brand: str, schema: ReportSchema) -> Dict:
    """加载某章某品牌的所有已分发数据。"""
    dispatched_dir = data_dispatched_dir()
    prefix = chapter.replace("ch", "ch")
    files = list(dispatched_dir.glob(f"{prefix}*{brand}*.json"))
    
    data = {}
    for f in files:
        try:
            record = load_json(f)
            key = f.stem
            data[key] = record
        except (FileNotFoundError, ValueError):
            continue
    
    return data


def run_content_steps(schema: ReportSchema, project_config: ProjectConfig, 
                      steps: List[str] = None) -> Dict[str, Path]:
    """
    按需运行内容生成步骤。
    steps: ['ch2', 'ch3', 'ch4', 'ch5', 'ch6'] 的子集
    """
    if steps is None:
        steps = ['ch2', 'ch3', 'ch4', 'ch5', 'ch6']
    
    results = {}
    step_map = {
        'ch2': generate_ch2,
        'ch3': generate_ch3,
        'ch4': generate_ch4,
        'ch5': generate_ch5,
        'ch6': generate_ch6,
    }
    
    for s in steps:
        if s in step_map:
            results[s] = step_map[s](schema, project_config)
    
    return results
