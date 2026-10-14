#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曼拾品牌释义一页 v3：逸凡定稿文案 + 四个 VI 色（#FFFFFF / #F8223E / #F93957 / #FFEADF）。
输出 A4 竖版 2480×3508 与 16:9 横版 3840×2160，Chrome 无头渲染。"""
import os, subprocess
import numpy as np
from PIL import Image

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
OUT = os.path.join(BASE, "manshi-card", "v3")
os.makedirs(OUT, exist_ok=True)
LOGO_RED = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")      # 白底上的 logo
LOGO_LIGHT = os.path.join(BASE, "manshi-logo", "manshi_logo_dark_art_transparent_2000.png")  # 红底上的 logo
PATTERN = os.path.join(OUT, "phoenix_pattern.png")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ---------------------------------------------------------------- 文案（逸凡定稿，逐字不改）
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
    ("择善而栖", "我们选择同行的是信仰长期主义的客户与伙伴", "pink"),
    ("和鸣而传", "我们选择解码时代中用户的心声，传播爱的声音；不断制造趋势，引领声潮", "red"),
    ("浴火新生", "我们期待自己始终在迭代，在10年开启的篇章中，不断新生", "light"),
]
FOOT = "曼拾·社交媒体整合营销"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:#FFFFFF;color:#F8223E;-webkit-font-smoothing:antialiased}
body{font-family:'Hiragino Sans GB','Songti SC',sans-serif}
.serif{font-family:'Songti SC','Hiragino Sans GB',serif}
.en{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif}
.red{color:#F8223E}.lr{color:#F93957}.pk{background:#FFEADF}.onred{color:#FFFFFF}
.bgred{background:#F8223E}.bglr{background:#F93957}.bgpk{background:#FFEADF}
h1,h2,h3{font-weight:600}
"""


def hearts_html(cls="heart"):
    out = []
    for num, cn, en, four, desc in HEARTS:
        out.append(f"""
    <div class="{cls}">
      <div class="coin"><span>{num}</span></div>
      <div class="hbody">
        <div class="hname"><b class="serif">{cn}</b><i class="en">{en}</i><u class="en">{four}</u></div>
        <div class="hdesc">{desc}</div>
      </div>
    </div>""")
    return "\n".join(out)


def build(zoom=1.0):
    s = lambda n: round(n * zoom)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}
body{{width:2480px;height:3508px;overflow:hidden;position:relative}}
.pad{{position:absolute;left:{s(150)}px;right:{s(150)}px;top:{s(130)}px;bottom:{s(110)}px;
  display:flex;flex-direction:column}}
/* header */
.head{{display:flex;align-items:center;justify-content:space-between}}
.head img{{width:{s(190)}px;height:{s(190)}px}}
.bname{{font-size:{s(96)}px;letter-spacing:{s(14)}px;line-height:1}}
.ben{{font-size:{s(26)}px;letter-spacing:{s(10)}px;color:#F93957;margin-top:{s(8)}px}}
.y10{{background:#F8223E;color:#fff;font-size:{s(26)}px;letter-spacing:{s(6)}px;
  padding:{s(10)}px {s(26)}px;border-radius:{s(40)}px;margin-left:{s(28)}px}}
.tag{{text-align:right;font-size:{s(26)}px;line-height:1.6;color:#F93957;letter-spacing:{s(3)}px}}
/* 段落块 */
.p1{{background:#F8223E;color:#fff;font-size:{s(40)}px;line-height:1.62;padding:{s(44)}px {s(50)}px;
  border-radius:{s(18)}px;margin-top:{s(46)}px}}
.p2{{background:#FFEADF;color:#F8223E;font-size:{s(36)}px;line-height:1.6;padding:{s(34)}px {s(50)}px;
  border-radius:{s(18)}px;margin-top:{s(22)}px}}
.plain{{font-size:{s(36)}px;line-height:1.62;margin-top:{s(22)}px;text-align:justify}}
.clover{{display:flex;align-items:center;gap:{s(44)}px;margin-top:{s(34)}px}}
.clover img{{width:{s(230)}px;height:{s(230)}px;flex:0 0 {s(230)}px}}
.clover p{{font-size:{s(35)}px;line-height:1.62;text-align:justify}}
/* 五心 */
.heart{{display:flex;gap:{s(26)}px;padding:{s(22)}px {s(30)}px;border-radius:{s(14)}px;margin-top:{s(14)}px}}
.heart:nth-child(even){{background:#FFEADF}}
.coin{{width:{s(58)}px;height:{s(58)}px;border-radius:50%;background:#F8223E;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:{s(30)}px;flex:0 0 {s(58)}px;
  font-family:'Helvetica Neue',Arial,sans-serif;margin-top:{s(6)}px}}
.hname{{display:flex;align-items:baseline;gap:{s(16)}px}}
.hname b{{font-size:{s(50)}px;letter-spacing:{s(4)}px}}
.hname i{{font-style:normal;font-size:{s(24)}px;letter-spacing:{s(4)}px;color:#F93957}}
.hname u{{text-decoration:none;font-size:{s(24)}px;letter-spacing:{s(3)}px;color:#F93957}}
.hdesc{{font-size:{s(33)}px;line-height:1.5;margin-top:{s(8)}px}}
.stembar{{background:#F8223E;color:#fff;font-size:{s(34)}px;letter-spacing:{s(2)}px;margin-top:{s(26)}px;
  padding:{s(26)}px {s(40)}px;border-radius:{s(18)}px}}
/* 凤纹 */
.feng{{margin-top:{s(48)}px;position:relative}}
.feng .wm{{position:absolute;right:-{s(40)}px;top:{s(10)}px;width:{s(560)}px;opacity:0.16;z-index:0}}
.h2{{font-size:{s(56)}px;letter-spacing:{s(4)}px;position:relative;z-index:1}}
.quote{{background:#FFEADF;color:#F8223E;font-size:{s(33)}px;line-height:1.58;margin-top:{s(22)}px;
  padding:{s(28)}px {s(38)}px;border-left:{s(10)}px solid #F8223E;border-radius:0 {s(14)}px {s(14)}px 0;
  position:relative;z-index:1}}
/* 三个色块 */
.trio{{display:flex;gap:{s(22)}px;margin-top:{s(34)}px}}
.tri{{flex:1 1 0;border-radius:{s(18)}px;padding:{s(30)}px {s(28)}px}}
.tri h3{{font-size:{s(44)}px;letter-spacing:{s(4)}px}}
.tri p{{font-size:{s(29)}px;line-height:1.5;margin-top:{s(12)}px}}
.tri.pink{{background:#FFEADF;color:#F8223E}}
.tri.red{{background:#F8223E;color:#fff}}
.tri.light{{background:#F93957;color:#fff}}
footer{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
  font-size:{s(26)}px;letter-spacing:{s(4)}px;color:#F93957;padding-top:{s(30)}px}}
</style></head><body><div class="pad">
  <div class="head">
    <div style="display:flex;align-items:center">
      <img src="{LOGO_RED}">
      <div style="margin-left:{s(28)}px">
        <div class="bname serif">曼拾</div>
        <div class="ben en">MEANSPLUS</div>
      </div>
      <span class="y10">第十年</span>
    </div>
    <div class="tag">品牌释义<br><span class="en">BRAND STORY</span></div>
  </div>

  <div class="p1">{P1}</div>
  <div class="p2">{P2}</div>
  <div class="clover">
    <img src="{LOGO_RED}">
    <p>{P3}</p>
  </div>

  <div class="plain" style="margin-top:{s(34)}px">{P4}</div>
  {hearts_html()}
  <div class="stembar">{P5}</div>

  <div class="feng">
    <img class="wm" src="{PATTERN}">
    <div class="h2 serif">凤纹 · 中华的来处</div>
    <div class="plain" style="margin-top:{s(20)}px">{P6}</div>
    <div class="quote">{Q1}</div>
    <div class="plain" style="margin-top:{s(18)}px">{P7}</div>
    <div class="quote">{Q2}</div>
    <div class="plain" style="margin-top:{s(18)}px">{P8}</div>
    <div class="plain" style="margin-top:{s(22)}px">{P9}</div>
    <div class="trio">
      <div class="tri pink"><h3 class="serif">{BLOCKS[0][0]}</h3><p>{BLOCKS[0][1]}</p></div>
      <div class="tri red"><h3 class="serif">{BLOCKS[1][0]}</h3><p>{BLOCKS[1][1]}</p></div>
      <div class="tri light"><h3 class="serif">{BLOCKS[2][0]}</h3><p>{BLOCKS[2][1]}</p></div>
    </div>
  </div>

  <footer>
    <div>{FOOT}</div>
    <div class="en">MEANSPLUS</div>
  </footer>
</div></body></html>"""
    p = os.path.join(OUT, "brand_story_a4.html")
    open(p, "w").write(html)
    return p


def render(html_path, out_png, w, h):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    "--force-device-scale-factor=1", "--default-background-color=ffffffff",
                    f"--window-size={w},{h}", f"--screenshot={out_png}", f"file://{html_path}"],
                   capture_output=True, timeout=240)
    return out_png


def measure(png, H):
    a = np.array(Image.open(png).convert("L")).astype(int)
    r = (a < 245).sum(1)          # 红/粉块都算内容
    rows = np.where(r > 0)[0]
    if len(rows) == 0:
        return 0, 0, 0
    bottom = int(rows.max())
    y = bottom
    while y > 0 and r[y - 1] > 0:
        y -= 1
    footer_top = y
    y2 = footer_top - 1
    while y2 > 0 and r[y2] == 0:
        y2 -= 1
    return y2, footer_top, footer_top - y2


def fit(lo=0.55, hi=1.05, tol=0.008):
    best = None
    while hi - lo > tol:
        mid = round((lo + hi) / 2, 3)
        png = os.path.join(OUT, "_probe.png")
        render(build(mid), png, 2480, 3508)
        cb, ft, gap = measure(png, 3508)
        print(f"  K {mid} gap {gap} (content {cb} / footer {ft})", flush=True)
        if gap < 60:
            hi = mid
        else:
            lo = mid
            best = mid
    return best or lo


# ---------------------------------------------------------------- 16:9 横版
def build_169(zoom=1.0):
    s = lambda n: round(n * zoom)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}
body{{width:3840px;height:2160px;overflow:hidden;position:relative}}
.pad{{position:absolute;left:{s(120)}px;right:{s(120)}px;top:{s(96)}px;bottom:{s(70)}px;
  display:flex;flex-direction:column}}
.head{{display:flex;align-items:center;justify-content:space-between}}
.head img{{width:{s(120)}px;height:{s(120)}px}}
.bname{{font-size:{s(60)}px;letter-spacing:{s(9)}px;line-height:1}}
.ben{{font-size:{s(17)}px;letter-spacing:{s(7)}px;color:#F93957;margin-top:{s(5)}px}}
.y10{{background:#F8223E;color:#fff;font-size:{s(17)}px;letter-spacing:{s(4)}px;
  padding:{s(7)}px {s(18)}px;border-radius:{s(26)}px;margin-left:{s(18)}px}}
.tag{{text-align:right;font-size:{s(17)}px;line-height:1.6;color:#F93957;letter-spacing:{s(3)}px}}
.cols{{display:flex;gap:{s(60)}px;margin-top:{s(38)}px;flex:1 1 auto;min-height:0}}
.l{{flex:1 1 55%;display:flex;flex-direction:column}}
.r{{flex:1 1 45%;position:relative;display:flex;flex-direction:column;justify-content:space-between}}
.p1{{background:#F8223E;color:#fff;font-size:{s(25)}px;line-height:1.6;padding:{s(24)}px {s(28)}px;border-radius:{s(12)}px}}
.p2{{background:#FFEADF;color:#F8223E;font-size:{s(23)}px;line-height:1.55;padding:{s(18)}px {s(28)}px;
  border-radius:{s(12)}px;margin-top:{s(14)}px}}
.plain{{font-size:{s(23)}px;line-height:1.58;margin-top:{s(14)}px;text-align:justify}}
.clover{{display:flex;align-items:center;gap:{s(24)}px;margin-top:{s(16)}px}}
.clover img{{width:{s(130)}px);height:{s(130)}px}}
.clover img{{width:{s(130)}px;height:{s(130)}px;flex:0 0 {s(130)}px}}
.clover p{{font-size:{s(22)}px;line-height:1.56;text-align:justify}}
.heart{{display:flex;gap:{s(16)}px;padding:{s(12)}px {s(18)}px;border-radius:{s(10)}px;margin-top:{s(9)}px}}
.heart:nth-child(even){{background:#FFEADF}}
.coin{{width:{s(34)}px;height:{s(34)}px;border-radius:50%;background:#F8223E;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:{s(19)}px;flex:0 0 {s(34)}px;
  font-family:'Helvetica Neue',Arial,sans-serif;margin-top:{s(3)}px}}
.hname{{display:flex;align-items:baseline;gap:{s(10)}px}}
.hname b{{font-size:{s(30)}px;letter-spacing:{s(3)}px}}
.hname i{{font-style:normal;font-size:{s(15)}px;letter-spacing:{s(3)}px;color:#F93957}}
.hname u{{text-decoration:none;font-size:{s(15)}px;letter-spacing:{s(2)}px;color:#F93957}}
.hdesc{{font-size:{s(20)}px;line-height:1.45;margin-top:{s(4)}px}}
.stembar{{background:#F8223E;color:#fff;font-size:{s(21)}px;margin-top:{s(16)}px;padding:{s(14)}px {s(22)}px;
  border-radius:{s(12)}px}}
.h2{{font-size:{s(34)}px;letter-spacing:{s(3)}px;position:relative;z-index:1}}
.wm{{position:absolute;right:-{s(20)}px;top:-{s(10)}px;width:{s(330)}px;opacity:0.16;z-index:0}}
.quote{{background:#FFEADF;font-size:{s(20)}px;line-height:1.5;margin-top:{s(14)}px;
  padding:{s(16)}px {s(22)}px;border-left:{s(6)}px solid #F8223E;border-radius:0 {s(8)}px {s(8)}px 0;
  position:relative;z-index:1}}
.trio{{display:flex;gap:{s(14)}px;margin-top:{s(22)}px}}
.tri{{flex:1 1 0;border-radius:{s(12)}px;padding:{s(18)}px {s(18)}px}}
.tri h3{{font-size:{s(26)}px;letter-spacing:{s(3)}px}}
.tri p{{font-size:{s(17)}px;line-height:1.45;margin-top:{s(8)}px}}
.tri.pink{{background:#FFEADF;color:#F8223E}}
.tri.red{{background:#F8223E;color:#fff}}
.tri.light{{background:#F93957;color:#fff}}
footer{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
  font-size:{s(17)}px;letter-spacing:{s(3)}px;color:#F93957;padding-top:{s(18)}px}}
</style></head><body><div class="pad">
  <div class="head">
    <div style="display:flex;align-items:center">
      <img src="{LOGO_RED}">
      <div style="margin-left:{s(18)}px">
        <div class="bname serif">曼拾</div>
        <div class="ben en">MEANSPLUS</div>
      </div>
      <span class="y10">第十年</span>
    </div>
    <div class="tag">品牌释义<br><span class="en">BRAND STORY</span></div>
  </div>
  <div class="cols">
    <div class="l">
      <div class="p1">{P1}</div>
      <div class="p2">{P2}</div>
      <div class="clover"><img src="{LOGO_RED}"><p>{P3}</p></div>
      <div class="plain" style="margin-top:{s(18)}px">{P4}</div>
      {hearts_html()}
      <div class="stembar">{P5}</div>
    </div>
    <div class="r">
      <img class="wm" src="{PATTERN}">
      <div class="h2 serif">凤纹 · 中华的来处</div>
      <div class="plain">{P6}</div>
      <div class="quote">{Q1}</div>
      <div class="plain">{P7}</div>
      <div class="quote">{Q2}</div>
      <div class="plain">{P8}</div>
      <div class="plain">{P9}</div>
    </div>
  </div>
  <div class="trio">
    <div class="tri pink"><h3 class="serif">{BLOCKS[0][0]}</h3><p>{BLOCKS[0][1]}</p></div>
    <div class="tri red"><h3 class="serif">{BLOCKS[1][0]}</h3><p>{BLOCKS[1][1]}</p></div>
    <div class="tri light"><h3 class="serif">{BLOCKS[2][0]}</h3><p>{BLOCKS[2][1]}</p></div>
  </div>
  <footer>
    <div>{FOOT}</div>
    <div class="en">MEANSPLUS</div>
  </footer>
</div></body></html>"""
    p = os.path.join(OUT, "brand_story_169.html")
    open(p, "w").write(html)
    return p


def fit169(lo=0.6, hi=1.1, tol=0.01):
    """16:9：内容不能超出画布，取尽量大的 K"""
    best = None
    while hi - lo > tol:
        mid = round((lo + hi) / 2, 3)
        png = os.path.join(OUT, "_probe169.png")
        render(build_169(mid), png, 3840, 2160)
        cb, ft, gap = measure(png, 2160)
        print(f"  169 K {mid} gap {gap} (content {cb} / footer {ft})", flush=True)
        if gap < 40:
            hi = mid
        else:
            lo = mid
            best = mid
    return best or lo


if __name__ == "__main__":
    z = fit()
    print("chosen K", z, flush=True)
    render(build(z), os.path.join(OUT, "曼拾品牌释义_A4竖版.png"), 2480, 3508)
    print("done a4", flush=True)
    z2 = fit169()
    print("chosen K169", z2, flush=True)
    render(build_169(z2), os.path.join(OUT, "曼拾品牌释义_16-9横版.png"), 3840, 2160)
    print("done 169", flush=True)
