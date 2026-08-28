#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sop_diagram.py — 热点借势营销 SOP 流程图生成器

用法:
  python3 generate_sop_diagram.py [输出.html路径]

生成 standalone HTML（内联CSS+内联SVG），纵向流程图。
默认输出文件: coco-hotspot-flow.html
"""

import sys
import os

# ── 画布尺寸 ──────────────────────────────────────────
CANVAS_W = 780
CANVAS_H = 800

# ── 颜色 ──────────────────────────────────────────────
COLOR_BLUE = '#2563eb'
COLOR_AMBER = '#d97706'
COLOR_RED = '#dc2626'
COLOR_GREEN = '#059669'
COLOR_PURPLE = '#7c3aed'
COLOR_TEAL = '#0d9488'
COLOR_DARK = '#1e293b'
COLOR_LIGHT = '#f8fafc'
COLOR_WHITE = '#ffffff'

# ── 节点数据 ──────────────────────────────────────────
# 每个节点: (y, 宽度, 颜色, 标题, 副标题/子行列表, 类型)
# 类型: input/process/decision/output
NODES = [
    {
        'y': 30,
        'w': 300,
        'color': COLOR_BLUE,
        'title': '热点出现',
        'subtitle': '',
        'type': 'input',
    },
    {
        'y': 110,
        'w': 340,
        'color': COLOR_AMBER,
        'title': '热点追踪 · 三问判断',
        'subtitle': '1 能不能玩梗  2 是不是二创期  3 挂不挂得上品牌',
        'type': 'decision',
        'branch': {
            'label': '任一不过',
            'target_y': 110,
            'target_x': 620,
            'label_text': '放弃',
            'color': COLOR_RED,
        },
    },
    {
        'y': 210,
        'w': 360,
        'color': COLOR_GREEN,
        'title': '快速响应 · 执行周期 5-7天',
        'subtitle': '达人1-2天 · 投流2-3天 · 搜索起势同步',
        'type': 'process',
    },
    {
        'y': 300,
        'w': 360,
        'color': COLOR_PURPLE,
        'title': '内容打法 · 四类可做内容',
        'subtitle': '表情包 · AI视觉 · 营销号话题 · 素人UGC',
        'type': 'process',
    },
    {
        'y': 390,
        'w': 400,
        'color': COLOR_TEAL,
        'title': '投放配套 · 效果广告',
        'subtitle': '人群 · 四向定向\n渠道 · 信息流 视频流 搜索卡热点词',
        'type': 'process',
    },
    {
        'y': 530,
        'w': 360,
        'color': COLOR_BLUE,
        'title': '总结 · 预算分配与验证',
        'subtitle': '预算 · KOL48% 信息流30% 视频流15% 搜索7%\n验证 · 话题溢出 2.2 倍',
        'type': 'output',
    },
]


def build_svg() -> str:
    """构建 SVG 内容字符串"""
    cx = CANVAS_W // 2  # 主轴中心 x
    node_h = 70  # 标准节点高度
    padding = 18  # 节点内边距

    parts = []

    # ── defs: 箭头 marker ──
    parts.append(f'''<defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,5 L0,10 Z" fill="{COLOR_DARK}"/>
    </marker>
    <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,5 L0,10 Z" fill="{COLOR_RED}"/>
    </marker>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,5 L0,10 Z" fill="{COLOR_BLUE}"/>
    </marker>
  </defs>''')

    # ── 背景 ──
    parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{COLOR_LIGHT}"/>')

    # ── 标题 ──
    parts.append(
        f'<text x="{cx}" y="22" text-anchor="middle" '
        f'font-family="-apple-system, PingFang SC, sans-serif" '
        f'font-size="18" font-weight="700" fill="{COLOR_DARK}">热点借势营销 SOP</text>'
    )
    parts.append(
        f'<text x="{cx}" y="40" text-anchor="middle" '
        f'font-family="-apple-system, PingFang SC, sans-serif" '
        f'font-size="12" fill="#64748b">追踪 → 判断 → 响应 → 植入 → 投放 → 沉淀</text>'
    )

    # 调整节点 y 偏移（为标题腾出空间）
    y_offset = 55

    # ── 节点 ──
    node_positions = []
    for i, node in enumerate(NODES):
        ny = node['y'] + y_offset
        nw = node['w']
        nx = cx - nw // 2
        color = node['color']
        title = node['title']
        subtitle = node.get('subtitle', '')

        # 计算节点高度（有副标题的加高）
        nh = node_h
        if subtitle:
            lines = subtitle.split('\n')
            nh = node_h + (len(lines) - 1) * 18 + 8

        node_positions.append({'x': nx, 'y': ny, 'w': nw, 'h': nh, 'cx': nx + nw // 2})

        # 节点矩形（圆角）
        radius = 12
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="{radius}" ry="{radius}" '
            f'fill="{color}" fill-opacity="0.08" stroke="{color}" stroke-width="2"/>'
        )

        # 左侧色条
        parts.append(
            f'<rect x="{nx}" y="{ny}" width="6" height="{nh}" rx="3" ry="3" fill="{color}"/>'
        )

        # 标题文字
        parts.append(
            f'<text x="{nx + padding}" y="{ny + 28}" '
            f'font-family="-apple-system, PingFang SC, sans-serif" '
            f'font-size="15" font-weight="600" fill="{color}">{title}</text>'
        )

        # 副标题文字
        if subtitle:
            for j, line in enumerate(subtitle.split('\n')):
                parts.append(
                    f'<text x="{nx + padding}" y="{ny + 48 + j * 18}" '
                    f'font-family="-apple-system, PingFang SC, sans-serif" '
                    f'font-size="11" fill="#475569">{line}</text>'
                )

        # 分支节点（放弃）
        if 'branch' in node:
            branch = node['branch']
            bx = cx + nw // 2 + 50  # 右侧（cx 是画布中心，节点以 cx 为中心）
            by = ny + nh // 2
            # 分支箭头
            parts.append(
                f'<line x1="{nx + nw}" y1="{by}" x2="{bx - 5}" y2="{by}" '
                f'stroke="{COLOR_RED}" stroke-width="2" fill="none" '
                f'marker-end="url(#arrow-red)"/>'
            )
            # 标签
            parts.append(
                f'<text x="{nx + nw + 8}" y="{by - 8}" '
                f'font-family="-apple-system, PingFang SC, sans-serif" '
                f'font-size="10" fill="{COLOR_RED}">任一不过</text>'
            )
            # 放弃节点
            bw, bh = 70, 36
            parts.append(
                f'<rect x="{bx}" y="{by - bh // 2}" width="{bw}" height="{bh}" rx="18" ry="18" '
                f'fill="{COLOR_RED}" fill-opacity="0.1" stroke="{COLOR_RED}" stroke-width="2"/>'
            )
            parts.append(
                f'<text x="{bx + bw // 2}" y="{by + 5}" text-anchor="middle" '
                f'font-family="-apple-system, PingFang SC, sans-serif" '
                f'font-size="13" font-weight="600" fill="{COLOR_RED}">放弃</text>'
            )

        # 连接线到下一个节点
        if i < len(NODES) - 1:
            next_ny = NODES[i + 1]['y'] + y_offset
            parts.append(
                f'<line x1="{cx}" y1="{ny + nh}" x2="{cx}" y2="{next_ny}" '
                f'stroke="{COLOR_DARK}" stroke-width="2" fill="none" '
                f'marker-end="url(#arrow)"/>'
            )

    # ── 底部回流箭头（虚线，从最后节点底部绕左侧回顶部）──
    last = node_positions[-1]
    first = node_positions[0]
    bottom_y = last['y'] + last['h']
    # 向下一点
    arrow_y = bottom_y + 15
    # 向左到画布左边
    left_x = 30
    # 向上到第一个节点顶部
    top_y = first['y'] - 15

    parts.append(
        f'<path d="M {cx} {bottom_y} '
        f'L {cx} {arrow_y} '
        f'L {left_x} {arrow_y} '
        f'L {left_x} {top_y} '
        f'L {first['cx']} {top_y}" '
        f'stroke="{COLOR_BLUE}" stroke-width="2" fill="none" '
        f'stroke-dasharray="6,4" marker-end="url(#arrow-blue)"/>'
    )

    # 回流标注
    parts.append(
        f'<text x="{left_x + 5}" y="{(arrow_y + top_y) // 2}" '
        f'font-family="-apple-system, PingFang SC, sans-serif" '
        f'font-size="11" fill="{COLOR_BLUE}" writing-mode="tb">'
        f'沉淀打法，复用到下一个热点</text>'
    )

    return '\n'.join(parts)


def build_html() -> str:
    """构建完整 HTML"""
    svg_content = build_svg()
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>热点借势营销 SOP</title>
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
<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">
{svg_content}
</svg>
</div>
</body>
</html>'''


def main():
    # 输出路径
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    else:
        out_path = os.path.join(os.getcwd(), 'coco-hotspot-flow.html')

    html = build_html()
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ SOP 流程图已生成: {out_path}')


if __name__ == '__main__':
    main()
