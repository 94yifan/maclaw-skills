# -*- coding: utf-8 -*-
"""
PITAKA 报告 docx 组装：typeset 四件套 + 图表插入 + 附录。
用法：python3 build_pitaka_docx.py [--version V1] [--date 20261017]
"""
import sys, os, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from config import ProjectConfig
from steps.docx_builder import build_chapter_map
from typeset import ReportConfig, ReportTypesetter, DataTable

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "project_config_PITAKA.json"

ap = argparse.ArgumentParser()
ap.add_argument("--version", default="V1")
ap.add_argument("--date", default="20261017")
ap.add_argument("--out", default="")
args = ap.parse_args()

pc = ProjectConfig(CONFIG)
cm = build_chapter_map(pc)

CONTENT = BASE / "output/PITAKA_20261017/content"
REPORTS = BASE / "output/reports"

CH4 = CONTENT / "ch4_deep/PITAKA_deep.md"
def rd(p):
    p = Path(p)
    return p.read_text(encoding="utf-8") if p.exists() else ""

chart_dir = BASE / "output/PITAKA_20261017/charts"
charts = [
    ("图1：六大品牌主流款参考价对比", chart_dir / "chart_price_band.png",
     "数据来源：媒体与电商页面快照，2026年10月；LLC 价格未获取，未列入"),
    ("图2：芳纶壳零售价相当于代工价的倍数", chart_dir / "chart_price_ladder.png",
     "数据来源：1688 批发价、什么值得买/中关村在线零售价快照，2026年10月"),
    ("图3：用户负面评价的主题分布", chart_dir / "chart_pain_dist.png",
     "数据来源：本次调研抓取的公开用户评论与视频文案，样本 12 条"),
]

parts = []
parts.append("# PITAKA 品牌与手机壳赛道分析报告")
parts.append(rd(CONTENT / "brand_overview.md"))
parts.append(rd(CONTENT / "product_matrix.md"))
parts.append(rd(CONTENT / "channel_supply_chain.md"))
parts.append(rd(CONTENT / "ch1_findings.md"))
parts.append(rd(CONTENT / "ch2_industry.md"))
parts.append(rd(CONTENT / "ch2_chain_map.md"))
# deep brands 逐个
for brand in ["图拉斯", "CASETIFY", "决色", "LLC", "邦克仕"]:
    parts.append(rd(CONTENT / "ch3_competitive" / f"deep_{brand}.md"))
parts.append(rd(CONTENT / "ch3_competitive/summary_brands.md"))
parts.append(rd(CONTENT / "ch3_competitive/competition_patterns.md"))
parts.append(rd(CONTENT / "ch3_content_types.md"))

# 图表位置标记
chart_block = ["## 数据可视化：跨品牌对比", ""]
for cap, _, src in charts:
    chart_block.append(f"### {cap}")
    chart_block.append(src)
    chart_block.append("")
parts.append("\n".join(chart_block))

parts.append(rd(CH4))
parts.append(rd(CONTENT / "ch5_gap.md"))
parts.append(rd(CONTENT / "ch6_strategy.md"))
parts.append(rd(CONTENT / "ch6_opportunity_map.md"))
parts.append(rd(CONTENT / "ch10_innovation.md"))
parts.append(rd(CONTENT / "appendix_b_pain_points.md"))
parts.append(rd(CONTENT / "appendix_c_content_types.md"))
parts.append(rd(CONTENT / "appendix_d_data_notes.md"))

md = "\n\n".join(p for p in parts if p and p.strip())
tmp_md = REPORTS / "_combined_PITAKA.md"
tmp_md.write_text(md, encoding="utf-8")
print("combined chars:", len(md))

cfg = ReportConfig(
    company="燃创咨询（BreaC）",
    title="PITAKA 品牌与手机壳赛道分析报告",
    subtitle="高端手机壳 / 芳纶纤维赛道",
    client="PITAKA",
    framework="赛道框定 → 行业格局与产业链 → 竞品五维扫描 → 本品诊断 → 差距对比 → 策略建议 → 创品与机会地图",
    date="2026年10月17日",
    font="PingFang SC",
)
out_name = args.out or f"PITAKA-高端手机壳-{args.version}-{args.date}.docx"
out_path = REPORTS / out_name

ts = ReportTypesetter(cfg)
ts.convert(str(tmp_md), str(out_path))
print("typeset saved:", out_path, out_path.stat().st_size, "bytes")

# ── 插入图表图片（在对应小节标题后）──
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

doc = Document(str(out_path))
paras = doc.paragraphs
inserted = 0
for cap, img, src in charts:
    if not Path(img).exists():
        print("MISSING chart:", img)
        continue
    target = None
    for p in paras:
        if p.text.strip() == cap:
            target = p
            break
    if target is None:
        print("caption not found:", cap)
        continue
    ip = OxmlElement("w:p")
    target._p.addnext(ip)
    para = Paragraph(ip, target._parent)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(img), width=Inches(6.0))
    inserted += 1

# 封面后强制分页：给第一个正文章节加 page_break_before，兼容不同渲染器
for para in doc.paragraphs:
    if para.style.name.startswith("Heading") and para.text.strip():
        para.paragraph_format.page_break_before = True
        break

doc.save(str(out_path))
print("images inserted:", inserted)
print("final:", out_path)
