#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_budget_pie.py — 热点借势预算分配饼图生成器

用法:
  python3 generate_budget_pie.py [输出.html路径]
  python3 generate_budget_pie.py --kol 48 --info 30 --video 15 --search 7

生成 standalone HTML（内联SVG 饼图）。
默认输出文件: coco-hotspot-budget.html
"""

import sys
import os
import math

# ── 默认配比 ──────────────────────────────────────────
DEFAULT_DATA = [
    {'name': 'KOL',   'pct': 48, 'color': '#2563eb', 'desc': '引爆源头'},
    {'name': '信息流', 'pct': 30, 'color': '#60a5fa', 'desc': '基本盘铺量'},
    {'name': '视频流', 'pct': 15, 'color': '#93c5fd', 'desc': '核心放量'},
    {'name': '搜索',   'pct': 7,  'color': '#f59e0b', 'desc': '杠杆最大'},
]


def parse_args(argv):
    """解析命令行参数，返回 (data, output_path)"""
    out_path = None
    overrides = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--kol':
            overrides['KOL'] = float(argv[i + 1])
            i += 2
        elif arg == '--info':
            overrides['信息流'] = float(argv[i + 1])
            i += 2
        elif arg == '--video':
            overrides['视频流'] = float(argv[i + 1])
            i += 2
        elif arg == '--search':
            overrides['搜索'] = float(argv[i + 1])
            i += 2
        else:
            out_path = arg
            i += 1

    # 应用覆盖
    data = []
    for item in DEFAULT_DATA:
        d = dict(item)
        if d['name'] in overrides:
            d['pct'] = overrides[d['name']]
        data.append(d)

    if out_path is None:
        out_path = os.path.join(os.getcwd(), 'coco-hotspot-budget.html')

    return data, out_path


def polar_to_cartesian(cx, cy, r, angle_deg):
    """角度（从12点方向顺时针）转笛卡尔坐标"""
    rad = math.radians(angle_deg - 90)  # -90 让 0° 在顶部
    x = cx + r * math.cos(rad)
    y = cy + r * math.sin(rad)
    return x, y


def arc_path(cx, cy, r, start_angle, end_angle):
    """生成 SVG path 的弧形扇形（从 start_angle 到 end_angle，顺时针）"""
    # 确保角度差合理
    if end_angle - start_angle >= 360:
        end_angle = start_angle + 359.99

    x1, y1 = polar_to_cartesian(cx, cy, r, start_angle)
    x2, y2 = polar_to_cartesian(cx, cy, r, end_angle)

    large_arc = 1 if (end_angle - start_angle) > 180 else 0

    # 从圆心出发 → 弧线 → 回到圆心
    return (
        f'M {cx},{cy} '
        f'L {x1:.2f},{y1:.2f} '
        f'A {r},{r} 0 {large_arc} 1 {x2:.2f},{y2:.2f} '
        f'Z'
    )


def build_svg(data):
    """构建 SVG 饼图"""
    cx, cy = 180, 200  # 圆心
    r = 130            # 半径

    # 计算各扇形角度
    total = sum(d['pct'] for d in data)
    parts = []

    # ── defs ──
    parts.append('<defs>')
    parts.append(
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur in="SourceAlpha" stdDeviation="3"/>'
        '<feOffset dx="0" dy="2" result="offsetblur"/>'
        '<feFlood flood-color="#000000" flood-opacity="0.15"/>'
        '<feComposite in2="offsetblur" operator="in"/>'
        '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )
    parts.append('</defs>')

    # ── 标题 ──
    parts.append(
        '<text x="400" y="40" text-anchor="middle" '
        'font-family="-apple-system, PingFang SC, sans-serif" '
        'font-size="20" font-weight="700" fill="#1e293b">热点借势 · 预算分配</text>'
    )
    parts.append(
        '<text x="400" y="62" text-anchor="middle" '
        'font-family="-apple-system, PingFang SC, sans-serif" '
        'font-size="13" fill="#64748b">可复用配比（总盘子 100%）</text>'
    )

    # ── 扇形 ──
    start_angle = 0
    for i, d in enumerate(data):
        pct = d['pct']
        if total == 0:
            continue
        angle_span = (pct / total) * 360
        end_angle = start_angle + angle_span

        path = arc_path(cx, cy, r, start_angle, end_angle)
        parts.append(
            f'<path d="{path}" '
            f'fill="{d["color"]}" '
            f'stroke="#ffffff" stroke-width="3" '
            f'filter="url(#shadow)"/>'
        )

        # 扇形内标注百分比
        mid_angle = start_angle + angle_span / 2
        label_r = r * 0.65
        lx, ly = polar_to_cartesian(cx, cy, label_r, mid_angle)
        if pct >= 5:  # 太小的扇形不标注
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                f'dominant-baseline="middle" '
                f'font-family="-apple-system, PingFang SC, sans-serif" '
                f'font-size="15" font-weight="700" fill="#ffffff">{pct:.0f}%</text>'
            )

        start_angle = end_angle

    # ── 图例（右侧竖排）──
    legend_x = 360
    legend_y = 110
    legend_h = 38
    for i, d in enumerate(data):
        ly = legend_y + i * legend_h
        # 色块
        parts.append(
            f'<rect x="{legend_x}" y="{ly - 12}" width="16" height="16" rx="3" '
            f'fill="{d["color"]}"/>'
        )
        # 名称 + 描述
        parts.append(
            f'<text x="{legend_x + 24}" y="{ly}" '
            f'font-family="-apple-system, PingFang SC, sans-serif" '
            f'font-size="14" font-weight="600" fill="#1e293b">{d["name"]} {d["pct"]:.0f}%</text>'
        )
        parts.append(
            f'<text x="{legend_x + 24}" y="{ly + 16}" '
            f'font-family="-apple-system, PingFang SC, sans-serif" '
            f'font-size="11" fill="#94a3b8">{d["desc"]}</text>'
        )

    # ── 底部总结 ──
    parts.append(
        '<text x="400" y="370" text-anchor="middle" '
        'font-family="-apple-system, PingFang SC, sans-serif" '
        'font-size="12" fill="#475569">搜索占比最小、杠杆最大；KOL 是引爆源头，预算不能省</text>'
    )

    return '\n'.join(parts)


def build_html(data):
    """构建完整 HTML"""
    svg_content = build_svg(data)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>热点借势 · 预算分配</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f1f5f9;
    font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif;
    padding: 20px;
  }}
  .container {{
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    padding: 24px;
  }}
  svg {{ display: block; }}
</style>
</head>
<body>
<div class="container">
<svg xmlns="http://www.w3.org/2000/svg" width="780" height="400" viewBox="0 0 780 400">
{svg_content}
</svg>
</div>
</body>
</html>'''


def main():
    data, out_path = parse_args(sys.argv[1:])

    # 校验总和
    total = sum(d['pct'] for d in data)
    if abs(total - 100) > 0.01:
        print(f'⚠️ 警告: 配比总和为 {total}%，建议合计 100%')

    html = build_html(data)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ 预算饼图已生成: {out_path}')
    for d in data:
        print(f'   {d["name"]} {d["pct"]:.0f}% — {d["desc"]}')


if __name__ == '__main__':
    main()
