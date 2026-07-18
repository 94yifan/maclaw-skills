"""
Step 4: 数据自动分发模块。

职责：按 schema.data_sources.*.mapping 配置，将 data/raw/ 中的原始数据
自动分发到 data/dispatched/ 下，按章节→品牌→维度组织。

分发逻辑：
1. 读取所有 raw/*.json
2. 按每个数据源的 mapping 配置，将字段路由到对应(chapter, brand, dimension)
3. 输出 dispatched/{chapter}/{brand}_{dimension}.json
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from steps.utils import (
    step_start, step_success, step_fail,
    save_json, load_json, verify_input_file, verify_output_dir,
    data_raw_dir, data_dispatched_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


def dispatch_all(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """
    Step 4 主入口：自动分发所有已采集的数据。
    返回 dispatched 目录路径。
    """
    step_start("data_dispatch", "数据自动分发 — 按 schema.mapping 路由数据")
    
    raw_dir = data_raw_dir()
    dispatched_dir = data_dispatched_dir()
    
    # 1. 获取所有数据源的 mapping 定义
    sources = schema.get_all_data_sources_with_mappings()
    
    dispatch_stats = {
        "total_records_dispatched": 0,
        "targets_written": 0,
        "data_sources_processed": 0
    }
    
    # 逐 source 处理
    for src in sources:
        source_key = src["source_key"]
        mapping = src.get("mapping", {})
        if not mapping:
            continue
        
        # 查找对应的 raw 数据
        raw_file_stem = source_key.replace(".", "_")
        raw_files = list(raw_dir.glob(f"{raw_file_stem}*.json"))
        if not raw_files:
            continue
        
        for raw_file in raw_files:
            try:
                raw_data = load_json(raw_file)
            except (FileNotFoundError, ValueError):
                continue
            
            if not isinstance(raw_data, dict) and not isinstance(raw_data, list):
                continue
            
            # 按 mapping 分发
            for target_path, field_list in mapping.items():
                # target_path 格式: "ch3.deep_brands.market_channel" 或 "ch3.deep_brands.product"
                target_data = extract_fields_for_target(raw_data, field_list, source_key)
                if not target_data:
                    continue
                
                # 提取品牌名（从文件名或数据中）
                brand = extract_brand_from_file(raw_file.stem, source_key)
                if not brand:
                    # 无品牌名的数据（如行业研报）→ 存为 industry_level
                    brand = "_industry_level_"
                
                # 生成输出文件名
                target_slug = target_path.replace(".", "_")
                out_filename = f"{target_slug}_{brand}.json"
                out_path = dispatched_dir / out_filename
                
                save_json({
                    "source_key": source_key,
                    "source_file": str(raw_file.name),
                    "brand": brand,
                    "target_path": target_path,
                    "data": target_data
                }, out_path)
                dispatch_stats["targets_written"] += 1
                dispatch_stats["total_records_dispatched"] += len(target_data) if isinstance(target_data, list) else 1
        
        dispatch_stats["data_sources_processed"] += 1
    
    # 写入分发报告
    report_path = dispatched_dir / "_dispatch_report.json"
    save_json({
        "project": project_config.project_name,
        "generated_at": __import__('datetime').datetime.now().isoformat(),
        "stats": dispatch_stats,
        "targets": list(dispatched_dir.glob("*.json"))
    }, report_path)
    
    print(f"  ✓ 处理了 {dispatch_stats['data_sources_processed']} 个数据源")
    print(f"  ✓ 写入 {dispatch_stats['targets_written']} 个分发目标")
    print(f"  ✓ 共分发 {dispatch_stats['total_records_dispatched']} 条数据记录")
    
    verify_output_dir(dispatched_dir, "data_dispatch")
    step_success("data_dispatch", [str(report_path)])
    return dispatched_dir


def extract_fields_for_target(raw_data: Any, field_list: List[str], source_key: str) -> Any:
    """
    从原始数据中提取 field_list 对应的字段。
    支持 dict 和 list[dict] 格式。
    """
    if isinstance(raw_data, list):
        # list of records → 提取每个记录的字段
        extracted = []
        for item in raw_data:
            if isinstance(item, dict):
                record = {}
                for f in field_list:
                    if f in item:
                        record[f] = item[f]
                    elif f == "全部字段":
                        record = item
                        break
                if record:
                    extracted.append(record)
        return extracted
    
    elif isinstance(raw_data, dict):
        if "全部字段" in field_list:
            return raw_data
        result = {}
        for f in field_list:
            if f in raw_data:
                result[f] = raw_data[f]
            # 支持嵌套点路径
            elif "." in f:
                parts = f.split(".")
                val = raw_data
                for part in parts:
                    if isinstance(val, dict):
                        val = val.get(part)
                    else:
                        val = None
                        break
                if val is not None:
                    result[f] = val
        return result
    
    return raw_data


def extract_brand_from_file(stem: str, source_key: str) -> str:
    """从文件名中提取品牌名。"""
    prefix = source_key.replace(".", "_")
    if stem.startswith(prefix):
        rest = stem[len(prefix):]
        if rest.startswith("_"):
            rest = rest[1:]
        if rest and rest != "_industry_level":
            return rest
    return ""
