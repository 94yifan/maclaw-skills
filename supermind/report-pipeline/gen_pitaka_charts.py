# -*- coding: utf-8 -*-
"""PITAKA 报告图表：内联 SVG + Chrome 无头截图，数据均来自事实底稿。"""
import subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "output/PITAKA_20261017/charts"
OUT.mkdir(parents=True, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAVY = "#1F3864"
NAVY_L = "#4A6491"
GOLD = "#B08D57"
GREY = "#8A8F98"
LIGHT = "#EDF1F8"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html(title, subtitle, body, source, w=1600, h=900):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:#fff;font-family:'PingFang SC','Heiti SC',sans-serif;color:#222}}
.wrap{{padding:56px 90px 10px}}
.brand{{font-size:20px;letter-spacing:2px;color:{GOLD};font-weight:600}}
h1{{font-size:40px;font-weight:600;color:{NAVY};margin-top:14px}}
.sub{{font-size:20px;color:{GREY};margin-top:12px}}
.src{{margin-top:26px;font-size:16px;color:{GREY}}}
.rule{{height:3px;width:88px;background:{GOLD};margin:22px 0 28px}}
</style></head><body><div class="wrap">
<div class="brand">燃创咨询 BreaC</div>
<h1>{esc(title)}</h1>
<div class="sub">{esc(subtitle)}</div>
<div class="rule"></div>
{body}
</div><div class="src" style="padding-left:90px">{esc(source)}</div></body></html>"""


def hbar_chart(items, unit="", label_w=250, bar_area=950, row_h=92):
    """items: [(label, value, note)] 水平条形。"""
    maxv = max(v for _, v, _ in items)
    parts = []
    y = 0
    for label, v, note in items:
        width = bar_area * (v / maxv)
        parts.append(f"""
<g transform="translate(0,{y})">
  <text x="{label_w-18}" y="34" text-anchor="end" font-size="24" fill="#333">{esc(label)}</text>
  <rect x="{label_w}" y="8" width="{width:.1f}" height="38" fill="{NAVY}" rx="2"/>
  <text x="{label_w+width+16:.1f}" y="35" font-size="24" font-weight="600" fill="{NAVY}">{esc(note)}</text>
</g>""")
        y += row_h
    return f'<svg width="1390" height="{y}" viewBox="0 0 1390 {y}">' + "".join(parts) + "</svg>"


def col_chart(items, unit="元/倍", col_w=200, gap=90, area_h=330):
    maxv = max(v for _, v, _ in items)
    parts = []
    x = 0
    for label, v, note in items:
        h = area_h * (v / maxv)
        y = area_h - h + 40
        parts.append(f"""
<g transform="translate({x},0)">
  <rect x="0" y="{y:.1f}" width="{col_w}" height="{h:.1f}" fill="{NAVY}" rx="2"/>
  <text x="{col_w/2}" y="{y-16:.1f}" text-anchor="middle" font-size="26" font-weight="600" fill="{NAVY}">{esc(note)}</text>
  <text x="{col_w/2}" y="{area_h+86}" text-anchor="middle" font-size="22" fill="#333">{esc(label)}</text>
</g>""")
        x += col_w + gap
    total_w = x - gap
    return f'<svg width="{total_w}" height="{area_h+120}" viewBox="0 0 {total_w} {area_h+120}">' + "".join(parts) + "</svg>"


def render(name, page):
    hp = OUT / f"{name}.html"
    hp.write_text(page, encoding="utf-8")
    png = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1.5", "--window-size=1600,900",
                    f"--screenshot={png}", f"file://{hp}"],
                   capture_output=True, timeout=60)
    print(png, png.exists(), png.stat().st_size if png.exists() else 0)


# 图1 主流款参考价
items1 = [
    ("CASETIFY", 500, "约 500 元"),
    ("PITAKA", 400, "300–500 元"),
    ("图拉斯 TORRAS", 200, "约 200 元"),
    ("邦克仕 Benks", 169, "169 元"),
    ("决色 DEFENSE", 133, "116–150 元"),
]
body1 = hbar_chart(items1)
render("chart_price_band", html(
    "六大品牌主流款参考价",
    "芳纶与高端手机壳，单位：元；LLC 价格未获取，未列入",
    body1,
    "数据来源：新浪财经、什么值得买、中关村在线公开价格快照，2026 年 10 月"))

# 图2 加价倍数
items2 = [
    ("决色 DEFENSE", 1.07, "1.07x"),
    ("邦克仕 Benks", 1.21, "1.21x"),
    ("PITAKA", 2.86, "2.86x"),
    ("CASETIFY", 3.57, "3.57x"),
]
body2 = col_chart(items2)
render("chart_price_ladder", html(
    "芳纶壳零售价相当于代工价的倍数",
    "以 1688 芳纶壳批发价约 140 元为基准，越靠右说明品牌溢价越高",
    body2,
    "数据来源：1688 批发报价与公开零售价快照，2026 年 10 月；倍数为映射推算，不是成本核算"))

# 图3 痛点分布
items3 = [
    ("防摔与边缘保护不足", 4, "4 条"),
    ("价格溢价与替代品", 3, "3 条"),
    ("手感与磁吸体验", 2, "2 条"),
    ("重量与厚度", 1, "1 条"),
    ("品牌叙事可信度", 1, "1 条"),
]
body3 = hbar_chart(items3)
render("chart_pain_dist", html(
    "用户负面评价的主题分布",
    "公开评论与视频文案样本，共 10 条负面评价，一条可涉及多个主题",
    body3,
    "数据来源：什么值得买评论页、抖音视频文案，抓取时间 2026 年 10 月"))
