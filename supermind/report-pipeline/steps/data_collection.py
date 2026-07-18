"""
Step 3: 数据采集模块。

职责：按 schema.data_sources 定义逐源采集数据。
调用方式：通过 browser / web_search / web_fetch 等工具，不自实现爬虫。

本模块不直接调用浏览器，而是输出 JSON 采集指令集供上游 Agent 执行，
或接收预采集的数据文件进行格式化和验证。

数据采集分支（按 schema.data_sources 定义）：
1. 财报数据（按上市地：A股→巨潮+东方财富、港股→披露易、美股→SEC EDGAR）
2. 电商数据（天猫/京东/抖音）
3. 行业研报（券商/咨询/协会）
4. 排名/认证
5. 社交/营销动态
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from steps.utils import (
    step_start, step_success, step_fail,
    save_json, load_json, verify_input_file, verify_output_dir,
    data_raw_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


def collect_all(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """
    Step 3 主入口：生成数据采集指令集，供上游 Agent 执行。
    输出：data/raw/source_instructions.json（采集指令）
    
    实际运行时，Agent 会逐条执行这些指令，将结果保存到 data/raw/ 下。
    """
    step_start("data_collection", "数据采集 — 生成采集指令并验证已有数据")
    
    raw_dir = data_raw_dir()
    sources = schema.get_all_data_sources_with_mappings()
    
    # 生成采集指令清单
    instructions = []
    for src in sources:
        instruction = {
            "source_key": src["source_key"],
            "name": src["name"],
            "category": src["category"],
            "priority": src["priority"],
            "extraction_fields": src["extraction_fields"],
            "mapping": to_mapping_human_readable(src.get("mapping", {})),
            "industry_adapter": get_industry_hints(schema, project_config, src["source_key"]),
            "brands": determine_brands_for_source(project_config, src["source_key"]),
        }
        instructions.append(instruction)
    
    # 添加采集状态（检查已有数据）
    status_summary = []
    for instr in instructions:
        source_file = raw_dir / f"{instr['source_key'].replace('.', '_')}.json"
        if source_file.exists():
            existing = load_json(source_file)
            instr["_status"] = "already_collected"
            instr["_data_count"] = len(existing) if isinstance(existing, list) else 1
            status_summary.append(f"  ✓ {instr['name']}: 已采集 ({instr.get('_data_count', '?')}条)")
        else:
            instr["_status"] = "pending_collection"
            status_summary.append(f"  ⏳ {instr['name']}: 待采集")
    
    instruction_file = raw_dir / "source_instructions.json"
    save_json({
        "generated_at": datetime.now().isoformat(),
        "project": project_config.project_name,
        "industry": project_config.industry,
        "instructions": instructions
    }, instruction_file)
    
    # Print status
    for line in status_summary:
        print(f"  {line}")
    
    # 验证已有数据的完整性
    pending = [i for i in instructions if i["_status"] == "pending_collection"]
    if pending:
        print(f"\n  ⚠ {len(pending)} 个数据源待采集:")
        for p in pending:
            print(f"    - {p['name']} ({p['source_key']})")
        print("  请使用 web_search / web_fetch / browser 工具逐一采集。")
    else:
        print(f"  ✓ 所有数据源均已采集")
    
    step_success("data_collection", [str(instruction_file)])
    return instruction_file


def to_mapping_human_readable(mapping: dict) -> List[str]:
    """将 mapping 转为人类可读的描述列表。"""
    readable = []
    for target, fields in mapping.items():
        if isinstance(fields, list):
            readable.append(f"→ {target}: {', '.join(fields)}")
    return readable


def get_industry_hints(schema: ReportSchema, project_config: ProjectConfig, source_key: str) -> dict:
    """获取跨行业适配提示。"""
    adapter = schema.get_industry_adapter(project_config.industry_type)
    if not adapter:
        return {}
    
    # Map source categories to adapter sections
    category_map = {
        "ecommerce": "ecommerce_channel_differences",
        "financial": None,
        "industry": "ranking_certification_sources",
        "social_media": None,
    }
    
    cat = source_key.split(".")[0]
    section_key = category_map.get(cat)
    if section_key and section_key in adapter:
        return adapter[section_key]
    return {}


def determine_brands_for_source(project_config: ProjectConfig, source_key: str) -> List[str]:
    """确定某数据源需要采集哪些品牌的数据。"""
    # 行业/研报类 -> 整个行业，品牌粒度不细分
    if source_key.startswith("industry") or source_key.startswith("financial.annual_report"):
        return ["__industry_level__"]
    # 电商/社交 -> 每个品牌
    return project_config.deep_brands + project_config.summary_brands


def verify_collected_data(schema: ReportSchema, project_config: ProjectConfig) -> bool:
    """Step 3 完成时验证：检查所有 P0 数据源是否已采集完整。"""
    raw_dir = data_raw_dir()
    sources = schema.get_all_data_sources_with_mappings()
    all_ok = True
    
    for src in sources:
        if src["priority"] not in ("P0", "P1"):
            continue
        source_file = raw_dir / f"{src['source_key'].replace('.', '_')}.json"
        if not source_file.exists():
            if src["priority"] == "P0":
                print(f"  ✗ P0 数据源未采集: {src['name']}")
                all_ok = False
            else:
                print(f"  ⚠ P1 数据源未采集: {src['name']}")
    
    return all_ok


def save_collected_data(source_key: str, data: Any, brand: str = "") -> Path:
    """
    保存采集到的数据到 data/raw/。
    
    用法（由上游 Agent 调用）：
        from steps.data_collection import save_collected_data
        save_collected_data("ecommerce.tmall", sku_data, "品牌A")
    """
    raw_dir = data_raw_dir()
    filename = source_key.replace(".", "_")
    if brand:
        filename = f"{filename}_{brand}"
    filepath = raw_dir / f"{filename}.json"
    return save_json(data, filepath)
