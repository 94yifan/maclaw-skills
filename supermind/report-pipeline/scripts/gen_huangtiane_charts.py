#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黄天鹅报告图表：仅生成有真实公开数据支撑的价格带对比图。

背景：pipeline Step 12 在缺少电商实测数据时会回落到合成数值（按品牌数量递减的假数据），
这些图表不允许作为交付内容。本脚本用前置调研中可溯源的公开价格线索重建价格对比图，
其余三张因无真实数据支撑一律不生成。
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from steps.charts import generate_png_from_chart_def

# 单枚价格（元），来源见 data_source；mapped 为区间取中值
data = [
    {"name": "黄天鹅", "value": 2.65},
    {"name": "兰皇", "value": 2.50},
    {"name": "圣迪乐", "value": 2.00},
    {"name": "樱姬小町", "value": 1.85},
    {"name": "咯咯哒", "value": 1.50},
    {"name": "德青源", "value": 1.25},
    {"name": "正大蛋业", "value": 0.89},
]

chart_def = {
    "title": "各品牌核心产品单件价对比",
    "data_source": "公开报道整理（黄天鹅2.65元为品牌方自述，正大0.89元为报道价，其余为价格带中值 mapped）",
    "chart_type": "bar",
}

out = BASE_DIR / "output" / "charts" / "chart_brand_comparison_3.png"
brands = [d["name"] for d in data]
res = generate_png_from_chart_def(chart_def, brands, data, out)
print("生成:", res)
