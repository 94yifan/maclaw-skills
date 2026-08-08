# -*- coding: utf-8 -*-
"""Generate marketing_flywheel_final.svg — 1:1 vector replica, Chinese-clear typography."""
import math

S = 1.08
CX, CY = 1300.0, 1380.0
W, H = 2600, 3260

FONT = "'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans CJK SC','Apple Color Emoji','Segoe UI Emoji',sans-serif"

def pt(r, phi):
    a = math.radians(phi)
    return (CX + r * math.sin(a), CY - r * math.cos(a))

def arc(r, phi1, phi2):
    x1, y1 = pt(r, phi1)
    x2, y2 = pt(r, phi2)
    return f'M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}'

def topbar(x, y, w, barh, r=10):
    return (f'M {x+r:.1f} {y:.1f} H {x+w-r:.1f} Q {x+w:.1f} {y:.1f} {x+w:.1f} {y+r:.1f} '
            f'V {y+barh:.1f} H {x:.1f} V {y+r:.1f} Q {x:.1f} {y:.1f} {x+r:.1f} {y:.1f} Z')

def rect_edge(p, q, hw, hh):
    dx, dy = q[0] - p[0], q[1] - p[1]
    if abs(dx) < 1e-9:
        return (p[0], p[1] + math.copysign(hh, dy))
    if abs(dy) < 1e-9:
        return (p[0] + math.copysign(hw, dx), p[1])
    t = min(hw / abs(dx), hh / abs(dy))
    return (p[0] + dx * t, p[1] + dy * t)

P = []  # parts

# ---------------- defs ----------------
defs = f'''
<defs>
<filter id="sh" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#00000026"/></filter>
<marker id="mGStart" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" viewBox="0 0 12 12" refX="2" refY="6" orient="auto"><path d="M 11 1 L 1 6 L 11 11 Z" fill="#8A8F98"/></marker>
<marker id="mGEnd" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" viewBox="0 0 12 12" refX="10" refY="6" orient="auto"><path d="M 1 1 L 11 6 L 1 11 Z" fill="#8A8F98"/></marker>
<marker id="mYEnd" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" viewBox="0 0 12 12" refX="10" refY="6" orient="auto"><path d="M 1 1 L 11 6 L 1 11 Z" fill="#E3B23C"/></marker>
<marker id="mBEnd" markerUnits="userSpaceOnUse" markerWidth="13" markerHeight="13" viewBox="0 0 12 12" refX="10" refY="6" orient="auto"><path d="M 1 1 L 11 6 L 1 11 Z" fill="#5B8DEF"/></marker>
<path id="outerArc" d="M 975.1 487.3 A 950 950 0 0 1 1624.9 487.3" fill="none"/>
</defs>
'''

# ---------------- title ----------------
P.append(f'<text x="{CX}" y="78" font-size="45" font-weight="bold" fill="#1F2937" text-anchor="middle" letter-spacing="1">营销哲学飞轮：六大哲学 × 行动循环 × 现实检验</text>')
P.append(f'<text x="{CX}" y="134" font-size="25" fill="#4B5563" text-anchor="middle" letter-spacing="1">以人的尊严为基石，在价值张力中不断创造更好的生活可能性</text>')
P.append(f'<rect x="1080" y="172" width="440" height="4" rx="2" fill="#E3B23C"/>')

# ---------------- flywheel group ----------------
P.append(f'<g transform="translate({CX} {CY}) scale({S}) translate({-CX} {-CY})">')

# discs (back to front)
P.append(f'<circle cx="{CX}" cy="{CY}" r="1030" fill="#F4EDDB"/>')
P.append(f'<circle cx="{CX}" cy="{CY}" r="780" fill="#E3EDFB"/>')
P.append(f'<circle cx="{CX}" cy="{CY}" r="560" fill="#2B3040"/>')
# boundary strokes
P.append(f'<circle cx="{CX}" cy="{CY}" r="1030" fill="none" stroke="#D8C49A" stroke-width="3.5"/>')
P.append(f'<circle cx="{CX}" cy="{CY}" r="780" fill="none" stroke="#C0D3F0" stroke-width="3"/>')
P.append(f'<circle cx="{CX}" cy="{CY}" r="560" fill="none" stroke="#3D4356" stroke-width="3"/>')
P.append(f'<circle cx="{CX}" cy="{CY}" r="250" fill="#111318"/>')

# yellow dashed flow arrows between environment cards
for phi in (30, 90, 150, 210, 270, 330):
    P.append(f'<path d="{arc(905, phi + 8, phi + 52)}" fill="none" stroke="#E3B23C" stroke-width="3" stroke-dasharray="10 6" stroke-linecap="round" marker-end="url(#mYEnd)"/>')

# blue clockwise arcs in the action band
for phi in (72, 144, 216, 288):
    P.append(f'<path d="{arc(700, phi - 14, phi + 14)}" fill="none" stroke="#5B8DEF" stroke-width="4.5" stroke-linecap="round" marker-end="url(#mBEnd)"/>')

# outer ring label
P.append(f'<text font-size="26" font-weight="bold" fill="#6B5632" letter-spacing="2"><textPath href="#outerArc" xlink:href="#outerArc" startOffset="50%" text-anchor="middle">市场／消费者／社会／文化／技术／自然／商业生态</textPath></text>')

# action-cycle label pills (12 o'clock)
P.append(f'<rect x="1180" y="610" width="240" height="44" rx="22" fill="#FFFFFF" stroke="#6C9AE8" stroke-width="2"/>')
P.append(f'<text x="{CX}" y="639" font-size="21" font-weight="bold" fill="#1D4ED8" text-anchor="middle">行动循环 (Dewey)</text>')
P.append(f'<rect x="1090" y="662" width="420" height="40" rx="20" fill="#FFFFFF" stroke="#6C9AE8" stroke-width="2"/>')
P.append(f'<text x="{CX}" y="689" font-size="19" font-weight="bold" fill="#3B6CC9" text-anchor="middle">Inquiry → Action → Learning</text>')

# inner ring badge
P.append(f'<rect x="1175" y="775" width="250" height="52" rx="12" fill="#232836" stroke="#E8C45C" stroke-width="2"/>')
P.append(f'<text x="{CX}" y="799" font-size="22" font-weight="bold" fill="#FFFFFF" text-anchor="middle">价值张力内核</text>')
P.append(f'<text x="{CX}" y="819" font-size="12.5" fill="#C9CFDD" text-anchor="middle">在张力中思考：我们究竟在乎什么？</text>')

# ---------------- environment cards ----------------
envs = [
    ("消费者与人的真实生活", "👥", ["行为与选择", "认知与信念", "情感与需求", "生活质量与幸福感"]),
    ("市场与商业环境", "📈", ["竞争格局", "行业趋势", "商业模式", "ROI/成本/增长"]),
    ("社会与文化文化环境", "🌐", ["文化价值观", "社会规范", "舆论与公共议题", "群体与身份"]),
    ("技术与媒介环境", "🤖", ["技术变革", "媒介生态", "数据与算法", "信息流动方式"]),
    ("自然与资源环境", "🍃", ["生态与可持续性", "资源与能源", "环境影响", "未来代价"]),
    ("长期与系统影响", "∞", ["品牌长期信任", "社会长期影响", "代际与文明", "系统性后果"]),
]
env_phis = [30, 90, 150, 210, 270, 330]
for (name, ic, bullets), phi in zip(envs, env_phis):
    cx, cy = pt(905, phi)
    x, y, w, h = cx - 115, cy - 75, 230, 150
    P.append(f'<g filter="url(#sh)">')
    P.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="10" fill="#FFFDF7" stroke="#D9C9A3" stroke-width="2"/>')
    P.append(f'<path d="{topbar(x, y, w, 34)}" fill="#F1E7CF"/>')
    P.append(f'<text x="{cx:.1f}" y="{y+23:.1f}" font-size="15.5" font-weight="bold" fill="#6B5632" text-anchor="middle">{name} {ic}</text>')
    for i, b in enumerate(bullets):
        P.append(f'<text x="{x+14:.1f}" y="{y+46+i*22:.1f}" font-size="13" fill="#4A4237">· {b}</text>')
    P.append('</g>')

# ---------------- action cycle cards ----------------
acts = [
    ("🔍", "探索与假设", ["观察现实，发现问题与机会", "形成初步假设与价值主张"]),
    ("🧪", "行动与实验", ["设计方案与原型", "小规模实验，进入真实场景"]),
    ("🧠", "经验与学习", ["收集数据与反馈", "理解用户与情境，形成洞察与新认知"]),
    ("🔄", "反思与修正", ["反思假设与方案", "修正价值判断与方向，更新认知与行动"]),
    ("🚀", "升级与再创造", ["基于洞察与学习，优化方案", "创造新的价值与体验"]),
]
act_phis = [36, 108, 180, 252, 324]
for (ic, name, lines), phi in zip(acts, act_phis):
    cx, cy = pt(690, phi)
    x, y, w, h = cx - 110, cy - 56, 220, 112
    P.append(f'<g filter="url(#sh)">')
    P.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="10" fill="#FFFFFF" stroke="#6C9AE8" stroke-width="2.5"/>')
    P.append(f'<path d="{topbar(x, y, w, 34)}" fill="#D8E6FB"/>')
    P.append(f'<text x="{cx:.1f}" y="{y+23:.1f}" font-size="16" font-weight="bold" fill="#24519B" text-anchor="middle">{ic} {name}</text>')
    P.append(f'<text x="{cx:.1f}" y="{y+50:.1f}" font-size="12.5" fill="#3A4659" text-anchor="middle">{lines[0]}</text>')
    P.append(f'<text x="{cx:.1f}" y="{y+68:.1f}" font-size="12.5" fill="#3A4659" text-anchor="middle">{lines[1]}</text>')
    P.append('</g>')

# ---------------- philosophy cards ----------------
phils = [
    ("⚖️", "康德：义务论", "#3B82F6", "#DBEAFE", "#1D4ED8", "我们『能做不能做』？",
     ["尊重人的尊严与自主性", "不把人当工具手段", "诚实、透明、公平", "不可操纵或欺骗"]),
    ("👤", "亚里士多德：美德论", "#F59E0B", "#FEF3C7", "#B45309", "什么是值得追求？",
     ["追求人的\"繁荣\"(eudaimonia)", "培养实践智慧(phronesis)", "在情境中判断(biogenesis)", "将角色与生活方式共同构建"]),
    ("❓", "尼采：价值重估", "#8B5CF6", "#EDE9FE", "#6D28D9", "为什么它值得？",
     ["通过价值体系来批判旧道德", "拥抱权力、生命、身体塑造", "直面一切既有价值", "创造新的可能性"]),
    ("☯️", "老子：价值消解", "#10B981", "#D1FAE5", "#047857", "真的需要如此三分吗？",
     ["天下皆知美之为斯恶已", "超越二元对立：善/恶、有/无、得/失", "道法自然", "顺势而为", "无为而无不为"]),
    ("📊", "功利主义：结果检验", "#C08A1E", "#FBF0D8", "#92600A", "结果如何？",
     ["最大化总体幸福/效用如何？", "量导幸福与痛苦如何比较？", "短期vs长期结果？", "社会与未来影响如何？"]),
]
phil_phis = [0, 60, 120, 180, 240]
phil_centers = {phi: pt(420, phi) for phi in phil_phis}
for (ic, name, border, bar, tcol, q, bullets), phi in zip(phils, phil_phis):
    cx, cy = phil_centers[phi]
    x, y, w, h = cx - 140, cy - 79, 280, 158
    P.append(f'<g filter="url(#sh)">')
    P.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="10" fill="#FFFFFF" stroke="{border}" stroke-width="2.5"/>')
    P.append(f'<path d="{topbar(x, y, w, 32)}" fill="{bar}"/>')
    P.append(f'<text x="{cx:.1f}" y="{y+22:.1f}" font-size="15.5" font-weight="bold" fill="{tcol}" text-anchor="middle">{name} {ic}</text>')
    P.append(f'<text x="{cx:.1f}" y="{y+46:.1f}" font-size="13" fill="#3F3F46" text-anchor="middle"><tspan font-weight="bold" fill="#52525B">核心问题</tspan>：「{q}」</text>')
    for i, b in enumerate(bullets):
        P.append(f'<text x="{x+14:.1f}" y="{y+68+i*18:.1f}" font-size="12.5" fill="#3F3F46">· {b}</text>')
    P.append('</g>')

# ---------------- center: human dignity ----------------
P.append(f'<circle cx="{CX}" cy="1272" r="26" fill="#FFFFFF"/>')
P.append(f'<path d="M 1250 1362 A 50 50 0 0 0 1350 1362 Z" fill="#FFFFFF"/>')
P.append(f'<text x="{CX}" y="1408" font-size="28" font-weight="bold" fill="#FFFFFF" text-anchor="middle">人的尊严</text>')
P.append(f'<text x="{CX}" y="1444" font-size="17" fill="#D1D5DB" text-anchor="middle" letter-spacing="2">Human Dignity</text>')
P.append(f'<text x="{CX}" y="1482" font-size="17.5" fill="#FFFFFF" text-anchor="middle">一切判断的基石，不可逾越的伦理底线</text>')

# ---------------- gray dashed double arrows: spokes to center ----------------
for phi in phil_phis:
    x1, y1 = pt(258, phi)
    x2, y2 = pt(332, phi)
    P.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#8A8F98" stroke-width="2" stroke-dasharray="6 5" stroke-linecap="round" marker-start="url(#mGStart)" marker-end="url(#mGEnd)"/>')

# ---------------- gray dashed double arrows: pentagon loop ----------------
for a, b in [(0, 60), (60, 120), (120, 180), (180, 240), (240, 0)]:
    pa, pb = phil_centers[a], phil_centers[b]
    ea = rect_edge(pa, pb, 140, 79)
    eb = rect_edge(pb, pa, 140, 79)
    P.append(f'<line x1="{ea[0]:.1f}" y1="{ea[1]:.1f}" x2="{eb[0]:.1f}" y2="{eb[1]:.1f}" stroke="#8A8F98" stroke-width="2" stroke-dasharray="6 5" stroke-linecap="round" marker-start="url(#mGStart)" marker-end="url(#mGEnd)"/>')

P.append('</g>')

# ---------------- bottom-left box: 六者关系说明 ----------------
P.append(f'<rect x="90" y="2560" width="1170" height="420" rx="12" fill="#FDFBF5" stroke="#D9C9A3" stroke-width="2" filter="url(#sh)"/>')
P.append(f'<path d="{topbar(90, 2560, 1170, 56)}" fill="#F1E7CF"/>')
P.append(f'<text x="120" y="2598" font-size="22" font-weight="bold" fill="#6B5632">六者关系说明</text>')
rows = [
    ("1. ", "康德", "#1D4ED8", "：守住不可逾越的伦理底线"),
    ("2. ", "亚里士多德", "#B45309", "：指引值得追求的好生活"),
    ("3. ", "尼采", "#6D28D9", "：质疑价值的来源与合理性"),
    ("4. ", "老子", "#047857", "：松动二元对立，打开更多可能"),
    ("5. ", "功利主义", "#92600A", "：让思想进入行动，在循环中学习进化"),
]
for i, (pre, name, col, rest) in enumerate(rows):
    y = 2648 + i * 48
    P.append(f'<text x="120" y="{y}" font-size="20" fill="#4A4237">{pre}<tspan font-weight="bold" fill="{col}">{name}</tspan>{rest}</text>')
P.append(f'<line x1="120" y1="2880" x2="1230" y2="2880" stroke="#E0D2AE" stroke-width="1.5"/>')
P.append(f'<text x="120" y="2904" font-size="20" fill="#1F2937"><tspan font-weight="bold">总结</tspan>：六者共同构成一个持续自我修正与创造的哲学飞轮</text>')

# ---------------- bottom-right box: 飞轮如何运转 ----------------
P.append(f'<rect x="1320" y="2560" width="1190" height="420" rx="12" fill="#FBFDFF" stroke="#C4D6F2" stroke-width="2" filter="url(#sh)"/>')
P.append(f'<path d="{topbar(1320, 2560, 1190, 56)}" fill="#D8E6FB"/>')
P.append(f'<text x="1350" y="2598" font-size="22" font-weight="bold" fill="#24519B">飞轮如何运转</text>')

flow = ["价值张力内核", "形成初步判断", "杜威行动循环", "进入真实实验", "功利主义检验",
        "观察真实结果", "反馈回内核", "修正认知与价值", "升级与再创造", "产生新的判断与行动"]
row1_x = [1340, 1564, 1788, 2012, 2236]
row2_x = [2236, 2012, 1788, 1564, 1340]

for i, (bx, label) in enumerate(zip(row1_x, flow[:5])):
    P.append(f'<rect x="{bx}" y="2630" width="200" height="64" rx="8" fill="#FFFFFF" stroke="#6C9AE8" stroke-width="2"/>')
    P.append(f'<text x="{bx+100}" y="2668" font-size="20" font-weight="bold" fill="#1F2937" text-anchor="middle">{label}</text>')
    if i < 4:
        gx = bx + 200
        P.append(f'<path d="M {gx+6} 2652 L {gx+6} 2672 L {gx+20} 2662 Z" fill="#4A7ED8"/>')
# down arrow
P.append(f'<line x1="2336" y1="2694" x2="2336" y2="2712" stroke="#4A7ED8" stroke-width="3"/>')
P.append(f'<path d="M 2326 2712 L 2346 2712 L 2336 2726 Z" fill="#4A7ED8"/>')

for i, (bx, label) in enumerate(zip(row2_x, flow[5:])):
    P.append(f'<rect x="{bx}" y="2724" width="200" height="64" rx="8" fill="#FFFFFF" stroke="#6C9AE8" stroke-width="2"/>')
    P.append(f'<text x="{bx+100}" y="2762" font-size="20" font-weight="bold" fill="#1F2937" text-anchor="middle">{label}</text>')
    if i < 4:
        gx = bx - 24  # gap starts at bx-24 (previous box ends at bx-24)
        P.append(f'<path d="M {gx+18} 2746 L {gx+18} 2766 L {gx+4} 2756 Z" fill="#4A7ED8"/>')

# loop-back arrow (box10 -> box1)
P.append(f'<path d="M 1330 2766 C 1290 2766 1290 2648 1328 2648" fill="none" stroke="#4A7ED8" stroke-width="3" stroke-linecap="round"/>')
P.append(f'<path d="M 1328 2636 L 1317 2652 L 1339 2652 Z" fill="#4A7ED8"/>')

P.append(f'<text x="1915" y="2860" font-size="19" fill="#374151" text-anchor="middle">这是一个永不停止的循环，推动我们持续创造更好的生活与社会价值。</text>')

# ---------------- bottom black banner ----------------
P.append(f'<rect x="90" y="3030" width="2420" height="140" rx="14" fill="#111318"/>')
P.append(f'<circle cx="240" cy="3100" r="30" fill="none" stroke="#FFFFFF" stroke-width="4"/>')
P.append(f'<circle cx="240" cy="3100" r="19" fill="none" stroke="#FFFFFF" stroke-width="3"/>')
P.append(f'<circle cx="240" cy="3100" r="9" fill="#FFFFFF"/>')
P.append(f'<text x="1350" y="3088" font-size="25" font-weight="bold" fill="#FFFFFF" text-anchor="middle">核心目的：用商业的力量，创造更多人愿意选择并因此过上更好生活的现实可能性。</text>')
P.append(f'<text x="1350" y="3134" font-size="20" fill="#E5E7EB" text-anchor="middle">不是影响选择，而是创造选择；不是追求短期转化，而是长期价值与人类繁荣。</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
{defs}
<rect width="{W}" height="{H}" fill="#FFFFFF"/>
{chr(10).join(P)}
</svg>
'''

out = "/Users/yifansmacmini/.openclaw/workspace/supermind/output/marketing_flywheel_final.svg"
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print("written", out, len(svg), "bytes")
