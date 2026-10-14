#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曼拾品牌释义 · A4 竖版 v4（可读性优先版）
- 核心文字改黑色 #1A1A1A，字号放大，行距放宽，不做堆叠
- 只用四个 VI 色做色块与强调：白 / 红 #F8223E / 浅红 #F93957 / 淡粉 #FFEADF
"""
import os, subprocess
import numpy as np
from PIL import Image

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
OUT = os.path.join(BASE, "manshi-card", "v4")
os.makedirs(OUT, exist_ok=True)
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")
PATTERN = os.path.join(BASE, "manshi-card", "v3", "phoenix_pattern.png")
CLOVER = os.path.join(BASE, "manshi-card", "v4", "clover_shape.png")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

P1 = "曼拾，至今已经迈入第十年，成立至今我们始终致力于帮助品牌在社交媒体平台洞察人心，点亮情绪，制造趋势，引领声潮。"
P2 = "红色，代表了我们对这份事业的热情与创想，更是我们想要传播的爱的颜色。"
P3 = "中心的五叶草，象征着幸运与传播，我们期待以品牌的好产品为媒介，借由我们的传播，把爱和幸运带给每一个人。"
P4 = "五叶草的形态，我们选择了心型，这代表了我们在创立初期就不变的初心、不断坚定的使命，和始终践行的价值观："
HEARTS = [
    ("1", "感恩心", "GRATITUDE", "感恩并回馈",
     "感谢客户选择我们，让我们有体面的工作；感谢同事加入，让我们成为彼此背靠的战友。用这份感恩心把每一个客户的服务交付做好，也把这份感恩心，通过我们的公益助学基金不断践行，回馈社会。"),
    ("2", "利他心", "ALTRUISM", "成人达己", "主动给出去，先想对方怎样更好。"),
    ("3", "创意心", "CREATIVITY", "创意破局", "只做有效营销，帮助客户生意真正增长跃升。"),
    ("4", "成长心", "GROWTH", "每日精进", "曼拾要做社会大学的一站，让每位伙伴在这里都能完成自我成长与实现。"),
    ("5", "成事心", "IMPACT", "结果说话", "成有用事，用结果说话。"),
]
P5 = "连通五心的根茎，是我们积极乐观不放弃的恒心。"
P6 = "LOGO底纹采用了中华传统纹样：凤纹，来源于新石器时代开始中华文明对于光明的追求与向往。自商周起，凤纹便伴随着中华民族一起成长着。"
Q1 = "《山海经·南山经》中写，凤皇的羽毛上天然带着花纹，首文曰德，翼文曰义，背文曰礼，膺文曰仁，腹文曰信。"
P7 = "这是凤凰的信念长在了身上，化成了纹路。我们期待也可以成为这样矢志不渝的传播人。"
Q2 = "《诗经·大雅》中写到：凤凰于飞、翙翙其羽"
P8 = "凤凰高飞、群鸟相随，这与我们的目标一致：理解人心，制造趋势，引领更多传播的涟漪。"
P9 = "用凤纹做底纹，我们期待藉此讲出的，不止是中华文化的传承自信，更是这背后代表的标准、希望和引领："
BLOCKS = [
    ("择善而栖", "我们选择同行的是信仰长期主义的客户与伙伴"),
    ("和鸣而传", "我们选择解码时代中用户的心声，传播爱的声音；不断制造趋势，引领声潮"),
    ("浴火新生", "我们期待自己始终在迭代，在10年开启的篇章中，不断新生"),
]
FOOT = "曼拾·社交媒体整合营销"


def hearts_html():
    rows = []
    for idx, (num, cn, en, four, desc) in enumerate(HEARTS):
        cls = " first" if idx == 0 else ""
        rows.append(f"""
    <div class="heart{cls}">
      <div class="coin">{num}</div>
      <div class="hb">
        <div class="hn"><b>{cn}</b><i class="en">{en}</i><u class="en">{four}</u></div>
        <p>{desc}</p>
      </div>
    </div>""")
    return "\n".join(rows)


def build(K=1.0):
    s = lambda n: round(n * K)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#FFFFFF;-webkit-font-smoothing:antialiased}}
body{{font-family:'Hiragino Sans GB','Songti SC',sans-serif;color:#1A1A1A}}
.serif{{font-family:'Songti SC','Hiragino Sans GB',serif}}
.en{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-style:normal}}
.red{{color:#F8223E}}.lr{{color:#F93957}}
body{{width:2480px;height:3508px;overflow:hidden;position:relative}}
.pad{{position:absolute;left:{s(112)}px;right:{s(112)}px;top:{s(98)}px;bottom:{s(76)}px;
  display:flex;flex-direction:column}}
.head{{display:flex;align-items:center;justify-content:space-between}}
.head img{{width:{s(134)}px;height:{s(134)}px}}
.bname{{font-size:{s(86)}px;letter-spacing:{s(12)}px;line-height:1;color:#F8223E}}
.ben{{font-size:{s(28)}px;letter-spacing:{s(9)}px;margin-top:{s(6)}px;color:#F93957}}
.y10{{background:#F8223E;color:#fff;font-size:{s(26)}px;letter-spacing:{s(5)}px;
  padding:{s(9)}px {s(24)}px;border-radius:{s(40)}px;margin-left:{s(24)}px}}
.tag{{text-align:right;font-size:{s(28)}px;line-height:1.6;color:#F8223E;letter-spacing:{s(3)}px}}
.tag span{{color:#F93957;font-size:{s(20)}px;letter-spacing:{s(4)}px}}
.lead{{font-size:{s(52)}px;line-height:1.55;margin-top:{s(38)}px;padding-left:{s(34)}px;
  border-left:{s(12)}px solid #F8223E;font-weight:500}}
.p{{font-size:{s(44)}px;line-height:1.68;margin-top:{s(22)}px;text-align:justify}}
.p b{{color:#F8223E}}
.small{{font-size:{s(38)}px;line-height:1.7;margin-top:{s(20)}px;color:#3A3836}}
.h2{{font-size:{s(62)}px;line-height:1.3;margin-top:{s(58)}px;color:#F8223E;font-weight:600;
  position:relative;z-index:1}}
.feng{{position:relative}}
.feng .wm{{position:absolute;right:-{s(10)}px;top:-{s(46)}px;width:{s(450)}px;opacity:0.13;z-index:0}}
.feng .wm.clover{{width:{s(285)}px;top:-{s(34)}px;right:-{s(4)}px;opacity:0.10}}
.sec{{margin-top:{s(40)}px}}
.heart{{display:flex;gap:{s(26)}px;padding-top:{s(24)}px;margin-top:{s(24)}px;
  border-top:{s(3)}px solid #FFEADF}}
.heart.first{{border-top:none;padding-top:0;margin-top:{s(10)}px}}
.coin{{width:{s(60)}px;height:{s(60)}px;border-radius:50%;background:#F8223E;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:{s(34)}px;flex:0 0 {s(60)}px;
  font-family:'Helvetica Neue',Arial,sans-serif;font-weight:600}}
.hn{{display:flex;align-items:baseline;gap:{s(18)}px}}
.hn b{{font-size:{s(56)}px;color:#F8223E;letter-spacing:{s(4)}px}}
.hn i{{font-size:{s(30)}px;color:#F93957;letter-spacing:{s(4)}px}}
.hn u{{text-decoration:none;font-size:{s(32)}px;color:#8A5049;margin-left:{s(10)}px}}
.heart p{{font-size:{s(42)}px;line-height:1.62;margin-top:{s(10)}px;text-align:justify;color:#1A1A1A}}
.stem{{background:#FFEADF;border-left:{s(14)}px solid #F8223E;border-radius:{s(4)}px;
  padding:{s(20)}px {s(30)}px;margin-top:{s(22)}px;font-size:{s(44)}px;line-height:1.6}}
.stem b{{color:#F8223E}}
.quote{{background:#FFEADF;border-left:{s(14)}px solid #F93957;border-radius:{s(4)}px;
  padding:{s(20)}px {s(30)}px;margin-top:{s(20)}px;font-size:{s(42)}px;line-height:1.7;text-align:justify}}
.trio{{display:flex;gap:{s(26)}px;margin-top:{s(30)}px}}
.tri{{flex:1 1 0;background:#FFEADF;border-radius:{s(16)}px;padding:{s(24)}px {s(26)}px}}
.tri h3{{font-size:{s(50)}px;color:#F8223E;letter-spacing:{s(3)}px;font-weight:600}}
.tri p{{font-size:{s(38)}px;line-height:1.62;margin-top:{s(14)}px;color:#1A1A1A}}
footer{{margin-top:auto;padding-top:{s(26)}px;display:flex;justify-content:space-between;
  align-items:flex-end;font-size:{s(28)}px;color:#3A3836;letter-spacing:{s(3)}px}}
footer .en{{color:#F93957;letter-spacing:{s(6)}px}}
</style></head><body><div class="pad">
  <div class="head">
    <div style="display:flex;align-items:center">
      <img src="{LOGO}">
      <div style="margin-left:{s(26)}px">
        <div class="bname serif">曼拾</div>
        <div class="ben en">MEANSPLUS</div>
      </div>
      <span class="y10">第十年</span>
    </div>
    <div class="tag">品牌释义<br><span class="en">BRAND STORY</span></div>
  </div>

  <div class="lead">{P1}</div>
  <p class="p">{P2}</p>

  <div class="sec feng">
    <img class="wm clover" src="{CLOVER}">
    <div class="h2 serif">五叶草 · 幸运的传播</div>
    <p class="p">{P3}</p>
    <p class="p">{P4}</p>
    {hearts_html()}
    <div class="stem">{P5.replace("恒心", "<b>恒心</b>")}</div>
  </div>

  <div class="sec feng">
    <img class="wm" src="{PATTERN}">
    <div class="h2 serif">凤纹 · 中华的来处</div>
    <p class="p">{P6}</p>
    <div class="quote">{Q1}</div>
    <p class="p">{P7}</p>
    <div class="quote">{Q2}</div>
    <p class="p">{P8}</p>
    <p class="p">{P9}</p>
    <div class="trio">
      {"".join(f'<div class="tri"><h3 class="serif">{a}</h3><p>{b}</p></div>' for a, b in BLOCKS)}
    </div>
  </div>

  <footer>
    <div>{FOOT}</div>
    <div class="en">MEANSPLUS</div>
  </footer>
</div></body></html>"""
    p = os.path.join(OUT, "brand_story_v4_a4.html")
    open(p, "w").write(html)
    return p


def render(html_path, out_png, w=2480, h=3508):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    "--force-device-scale-factor=1", "--default-background-color=ffffffff",
                    f"--window-size={w},{h}", f"--screenshot={out_png}", f"file://{html_path}"],
                   capture_output=True, timeout=240)
    return out_png


def measure(png):
    a = np.array(Image.open(png).convert("L")).astype(int)
    r = (a < 245).sum(1)
    rows = np.where(r > 0)[0]
    if len(rows) == 0:
        return 0, 0, 0
    bottom = int(rows.max()); y = bottom
    while y > 0 and r[y - 1] > 0:
        y -= 1
    ft = y; y2 = ft - 1
    while y2 > 0 and r[y2] == 0:
        y2 -= 1
    return y2, ft, ft - y2


if __name__ == "__main__":
    for K in (1.0, 0.95):
        png = os.path.join(OUT, f"_probe{int(K*100)}.png")
        render(build(K), png)
        cb, ft, gap = measure(png)
        print(f"K {K}: content {cb} footer {ft} gap {gap}")
