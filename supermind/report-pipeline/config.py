"""
配置管理模块。

职责：
1. 加载 report_schema.json（机器读版），验证其完整性
2. 加载 project_config.json（手动输入的项目配置）
3. 提供 schema-aware 的规则查询（如某章的必含要素、某数据源的 mapping）
4. 提供跨行业适配配置
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from steps.utils import (
    get_schema,
    load_json,
    verify_input_file,
    SCHEMA_PATH,
    BASE_DIR,
)


class ReportSchema:
    """Schema 配置管理器。包装 report_schema.json 的访问。"""

    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        self._raw: dict = get_schema(schema_path)
        self._path = Path(schema_path) if schema_path else SCHEMA_PATH

    # ── Schema 源信息 ──

    @property
    def version(self) -> str:
        return self._raw.get("_schema_version", "unknown")

    @property
    def description(self) -> str:
        return self._raw.get("_description", "")

    # ── 章节查询 ──

    def get_chapter(self, ch_key: str) -> dict:
        """获取某章定义，如 ch2, ch3."""
        chapters = self._raw.get("chapters", {})
        chapter = chapters.get(ch_key)
        if not chapter:
            raise KeyError(f"Schema 中未找到章节定义: {ch_key}")
        return chapter

    def get_chapter_section(self, ch_key: str, section_key: str) -> dict:
        """获取某章某节的详细定义。"""
        chapter = self.get_chapter(ch_key)
        sections = chapter.get("sections", {})
        section = sections.get(section_key)
        if not section:
            raise KeyError(f"Schema 中未找到章节目录: {ch_key}.{section_key}")
        return section

    def get_chapter_title(self, ch_key: str) -> str:
        return self.get_chapter(ch_key).get("title", ch_key)

    def get_chapter_page_range(self, ch_key: str) -> List[int]:
        return self.get_chapter(ch_key).get("page_range", [1, 1])

    # ── 深度品牌维度 ──

    def get_deep_brand_dimensions(self) -> List[dict]:
        """获取深度品牌各维度的定义清单。"""
        ch3 = self.get_chapter("ch3")
        deep_section = ch3.get("sections", {}).get("deep_brands", {})
        per_brand = deep_section.get("per_brand_dimensions", {})
        dimensions = []
        for dim_key, dim_def in per_brand.items():
            dim_id = dim_def.get("id", dim_key)
            dim_label = dim_def.get("label", dim_key)
            dimensions.append({
                "key": dim_key,
                "id": dim_id,
                "label": dim_label,
                "def": dim_def
            })
        return dimensions

    def get_dimension_writing_rule(self, dim_key: str) -> str:
        """获取某维度的写作规则。"""
        ch3 = self.get_chapter("ch3")
        deep_section = ch3.get("sections", {}).get("deep_brands", {})
        per_brand = deep_section.get("per_brand_dimensions", {})
        dim = per_brand.get(dim_key, {})
        return dim.get("writing_rule", "")

    def get_dimension_required_elements(self, dim_key: str) -> List[dict]:
        """获取某维度的必含要素清单。"""
        ch3 = self.get_chapter("ch3")
        deep_section = ch3.get("sections", {}).get("deep_brands", {})
        per_brand = deep_section.get("per_brand_dimensions", {})
        dim = per_brand.get(dim_key, {})
        return dim.get("required_elements", [])

    # ── 数据源查询 ──

    def get_data_source(self, source_key: str) -> dict:
        """获取某个数据源的定义。"""
        ds = self._raw.get("data_sources", {})
        # 支持两级路径: ecommerce.tmall, financial.annual_report
        parts = source_key.split(".", 1)
        current = ds
        for part in parts:
            current = current.get(part, {})
        if not current:
            raise KeyError(f"Schema 中未找到数据源: {source_key}")
        return current

    def get_data_source_mapping(self, source_key: str) -> dict:
        """获取某个数据源的章节/维度映射。"""
        source = self.get_data_source(source_key)
        return source.get("mapping", {})

    def get_all_data_sources_with_mappings(self) -> List[dict]:
        """获取所有待采集的数据源（含映射关系）。"""
        ds = self._raw.get("data_sources", {})
        results = []
        for category, cat_def in ds.items():
            if category == "social_media":
                # social_media 下有子源
                for sub_key, sub_def in cat_def.items():
                    results.append({
                        "category": category,
                        "source_key": f"{category}.{sub_key}",
                        "name": sub_def.get("name", sub_key),
                        "priority": sub_def.get("priority", "P2"),
                        "extraction_fields": sub_def.get("extraction_fields", []),
                        "mapping": sub_def.get("mapping", {}),
                        "data_source_def": sub_def
                    })
            elif isinstance(cat_def, dict) and "extraction_fields" in cat_def:
                results.append({
                    "category": category,
                    "source_key": category,
                    "name": cat_def.get("name", category),
                    "priority": cat_def.get("priority", "P2"),
                    "extraction_fields": cat_def.get("extraction_fields", []),
                    "mapping": cat_def.get("mapping", {}),
                    "data_source_def": cat_def
                })
            elif isinstance(cat_def, dict):
                # 可能是带子分类的（如 ecommerce, industry）
                for sub_key, sub_def in cat_def.items():
                    if isinstance(sub_def, dict) and "extraction_fields" in sub_def:
                        results.append({
                            "category": category,
                            "source_key": f"{category}.{sub_key}",
                            "name": sub_def.get("name", sub_key),
                            "priority": sub_def.get("priority", "P2"),
                            "extraction_fields": sub_def.get("extraction_fields", []),
                            "mapping": sub_def.get("mapping", {}),
                            "data_source_def": sub_def
                        })
        return results

    # ── 图表规则 ──

    def get_mandatory_charts(self) -> List[dict]:
        return self._raw.get("charts", {}).get("mandatory", [])

    def get_optional_charts(self) -> List[dict]:
        return self._raw.get("charts", {}).get("optional", [])

    def get_chart_rules(self) -> dict:
        return self._raw.get("charts", {}).get("rules", {})

    # ── QA 规则 ──

    def get_qa_rules(self, category: str = "") -> List[dict]:
        """获取 QA 规则。category: structural/content/charts/delivery"""
        qa = self._raw.get("qa_rules", {})
        if category:
            return qa.get(category, [])
        all_rules = []
        for cat, rules in qa.items():
            for r in rules:
                r["_category"] = cat
                all_rules.append(r)
        return all_rules

    # ── 写作规范 ──

    def get_global_writing_rules(self) -> List[str]:
        """获取全局写作规范列表。"""
        specs = self._raw.get("writing_specs", {})
        rules = specs.get("global_rules", {})
        return [f"{k}: {v}" for k, v in rules.items()]

    def get_brand_write_prompt_template(self) -> str:
        """获取 DeepSeek Pro prompt 模板。"""
        specs = self._raw.get("writing_specs", {})
        return specs.get("brand_write_prompt_template",
                         "你是品牌战略咨询顾问，正在撰写{report_type}报告。")

    # ── Cross-industry adapter ──

    def get_industry_adapter(self, industry_type: str) -> dict:
        """获取某行业的适配指南。"""
        adapter = self._raw.get("cross_industry_adapter", {})
        for item in adapter.get("industry_types", []):
            if item.get("type") == industry_type or item.get("type", "").startswith(industry_type):
                return item
        return {}

    # ── 深度规则 ──

    def get_depth_rules(self) -> dict:
        return self._raw.get("_conventions", {}).get("depth_rules", {})

    # ── Pipeline flow ──

    def get_pipeline_steps(self) -> List[dict]:
        return self._raw.get("pipeline_flow", {}).get("steps", [])


class ProjectConfig:
    """项目配置管理器。封装 project_config.json。"""

    def __init__(self, config_path: Union[str, Path]):
        self._path = Path(config_path)
        verify_input_file(self._path, "init", "项目配置")
        self._raw: dict = load_json(self._path)

    @property
    def project_name(self) -> str:
        return self._raw.get("project_name", "未命名项目")

    @property
    def industry(self) -> str:
        return self._raw.get("industry", "")

    @property
    def industry_type(self) -> str:
        return self._raw.get("industry_type", "consumables")

    @property
    def report_type(self) -> str:
        return self._raw.get("report_type", "深度品牌扫描")

    @property
    def framework_version(self) -> str:
        return self._raw.get("framework_version", "V4")

    @property
    def focus_brand(self) -> str:
        return self._raw.get("brands", {}).get("focus", "")

    @property
    def deep_brands(self) -> List[str]:
        return self._raw.get("brands", {}).get("deep", [])

    @property
    def summary_brands(self) -> List[str]:
        return self._raw.get("brands", {}).get("summary", [])

    @property
    def reference_brands(self) -> List[str]:
        return self._raw.get("brands", {}).get("reference", [])

    @property
    def all_brands(self) -> List[str]:
        brands = []
        if self.focus_brand:
            brands.append(self.focus_brand)
        brands.extend(self.deep_brands)
        brands.extend(self.summary_brands)
        brands.extend(self.reference_brands)
        return brands

    @property
    def ecommerce_platforms(self) -> List[str]:
        return self._raw.get("data_sources", {}).get("ecommerce_platforms", [])

    def get(self, key: str, default: Any = None) -> Any:
        """Raw get with dot-path support."""
        parts = key.split(".")
        current = self._raw
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return default
            if current is None:
                return default
        return current

    def get_ch5_dimensions_note(self) -> str:
        return self._raw.get("ch5_brand_comparison_dimensions", "待逸凡定义")

    @property
    def output_subdir(self) -> str:
        """项目隔离输出子目录名，如：康尔馨家纺_20260722_1330"""
        return self._raw.get("output_subdir", "") or (
            self.project_name.replace(" ", "_") + "_" + datetime.now().strftime("%Y%m%d_%H%M")
        )

    def get_docx_filename(self) -> str:
        """获取 output_settings 中的 docx 文件名，无配置时返回空。"""
        output_settings = self._raw.get("output_settings", {})
        return output_settings.get("docx_filename", "")

    def raw(self) -> dict:
        return dict(self._raw)
