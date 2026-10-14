#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曼拾 品牌文化一页（中英双语）：凤凰 + 五心 + 使命愿景价值观。
A4 竖版（2480×3508，300dpi）与 16:9 横版（3840×2160）两个尺寸，用 Chrome 无头渲染。"""
import os, subprocess, textwrap

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")
OUT = os.path.join(BASE, "manshi-card", "brand-onepager")
os.makedirs(OUT, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

HEARTS = [
    ("一", "感恩心", "GRATITUDE", "记人好处", "感谢客户选择我们，感谢同事并肩；成就团体，就是成就自己。"),
    ("二", "利他心", "ALTRUISM", "成人达己", "先想对方怎样更好；公益是它日常的样子。"),
    ("三", "创意心", "CREATIVITY", "创意破局", "用不一样的说法，让人真的记住。"),
    ("四", "成长心", "GROWTH", "每日精进", "成为社会大学的一站，让每个人在市场里更值钱。"),
    ("五", "成事心", "IMPACT", "结果说话", "成有用事，用结果说话，结果论断。"),
]

PHOENIX_CN = [
    "我们的底子来自很远的地方。凤凰最早的意思是吉兆，不是权力——它挑地方落，非梧桐不栖。在上古的用法里，凤是雄、凰是雌，合称本身就是共生，谁也不压谁。",
    "我们的做法是当下的事。蒲公英的种子不用谁去吹，风一来，自己就飞，落在真实的人心里，长出复利。",
]
PHOENIX_EN = [
    "Our roots reach far back: the phoenix first meant good fortune, not power — it lands only on worthy ground; in its oldest reading Feng is male and Huang is female, together one, neither above the other. What we do belongs to now: dandelion seeds need no one to blow them; when the wind comes they travel on their own, land in real people's hearts, and compound.",
]

VISION_CN = [
    ("对客户", "用更少的营销费用，换更高效的生意成长，陪客户成为有行业影响力的 TOP 品牌。"),
    ("对伙伴", "成为社会大学的一站，陪伙伴成为有行业影响力的营销专家。"),
    ("对公司", "做出被知晓、能撬动行业的好案例与方法论，成为头部社交营销机构。"),
]

CSS_COMMON = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:#FCFAF7;color:#262423;-webkit-font-smoothing:antialiased}
.cn{font-family:'Hiragino Sans GB','Songti SC',sans-serif}
.serif{font-family:'Songti SC','Hiragino Sans GB',serif}
.en{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif}
.red{color:#F8223E}
.grey{color:#8C8781}
.mid{color:#5E5A57}
.rule{background:#EAE4DD}
"""


def hearts_html(size="a4"):
    rows = []
    for num, cn, en, four, desc in HEARTS:
        rows.append(f"""
      <div class="heart">
        <div class="badge cn">{num}</div>
        <div class="htext">
          <div class="hname"><span class="serif red">{cn}</span><span class="en hen">{en}</span></div>
          <div class="hfour cn">{four}</div>
          <div class="hdesc cn">{desc}</div>
        </div>
      </div>""")
    return "\n".join(rows)


def build_a4(K=0.75):
    """A4 竖版 2480×3508 @300dpi；K = 全局字号/间距缩放"""
    def s(n):
        return round(n * K)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS_COMMON}
body{{width:2480px;height:3508px;overflow:hidden;position:relative}}
.pad{{position:absolute;left:190px;right:190px;top:170px;bottom:150px;display:flex;flex-direction:column}}
.bars{{display:flex;gap:{s(16)}px;margin-bottom:{s(44)}px}}
.bars i{{display:block;width:{s(18)}px;height:{s(120)}px;border-radius:{s(6)}px}}
header{{display:flex;align-items:center;justify-content:space-between}}
.brand{{display:flex;align-items:center;gap:{s(44)}px}}
.brand img{{width:{s(300)}px;height:{s(300)}px}}
.bname{{font-size:{s(120)}px;letter-spacing:{s(16)}px;line-height:1}}
.ben{{font-size:{s(34)}px;letter-spacing:{s(12)}px;margin-top:{s(18)}px}}
.tag{{text-align:right;font-size:{s(30)}px;line-height:1.7}}
h2{{font-size:{s(74)}px;line-height:1.35;font-weight:600}}
h2 .en{{font-size:{s(34)}px;letter-spacing:2px;display:block;margin-top:{s(16)}px;font-weight:400}}
p.body{{font-size:{s(41)}px;line-height:1.78;margin-top:{s(26)}px;text-align:justify}}
p.enbody{{font-size:{s(31)}px;line-height:1.62;margin-top:{s(14)}px;color:#8C8781}}
.heart{{display:flex;gap:{s(38)}px;margin-top:{s(52)}px;align-items:flex-start}}
.badge{{width:{s(74)}px;height:{s(74)}px;border-radius:50%;background:#F8223E;color:#fff;
  font-size:{s(40)}px;display:flex;align-items:center;justify-content:center;flex:0 0 {s(74)}px;margin-top:{s(8)}px}}
.hname{{display:flex;align-items:baseline;gap:{s(22)}px}}
.hname span:first-child{{font-size:{s(82)}px;font-weight:600;letter-spacing:{s(6)}px}}
.hen{{font-size:{s(32)}px;letter-spacing:{s(6)}px;color:#B9B3AD}}
.hfour{{font-size:{s(46)}px;margin-top:{s(12)}px;letter-spacing:{s(4)}px}}
.hdesc{{font-size:{s(38)}px;line-height:1.6;color:#6E6A66;margin-top:{s(10)}px}}
.stem{{display:flex;gap:{s(38)}px;margin-top:{s(60)}px;align-items:baseline}}
.stem b{{font-size:{s(46)}px;font-weight:600;letter-spacing:{s(4)}px}}
.stem span{{font-size:{s(38)}px;color:#6E6A66}}
.mvo{{margin-top:{s(56)}px;border-left:{s(6)}px solid #F8223E;padding-left:{s(40)}px}}
.mvo h3{{font-size:{s(46)}px;font-weight:600;letter-spacing:{s(4)}px}}
.mvo h3 em{{font-style:normal;font-size:{s(30)}px;color:#B9B3AD;letter-spacing:{s(4)}px;margin-left:{s(18)}px}}
.mvo p{{font-size:{s(37)}px;line-height:1.72;margin-top:{s(14)}px;color:#4A4744}}
.mvo p.enbody{{font-size:{s(29)}px}}
.mvsub{{font-size:{s(35)}px;line-height:1.7;color:#4A4744;margin-top:{s(12)}px}}
.mvsub b{{font-weight:600;color:#262423;margin-right:{s(10)}px}}
footer{{margin-top:auto;padding-top:{s(26)}px;display:flex;
  justify-content:space-between;align-items:flex-end;font-size:{s(30)}px;letter-spacing:{s(3)}px}}
</style></head><body>
<div class="pad">
  <div class="bars"><i style="background:#F8223E"></i><i style="background:#F93957"></i>
    <i style="background:#FF94B9"></i><i style="background:#FFEADF"></i>
    <i style="background:#65CDBC"></i><i style="background:#8CF160"></i><i style="background:#EFFD5B"></i>
    <i style="background:#D27D33"></i></div>
  <header>
    <div class="brand">
      <img src="{LOGO}">
      <div>
        <div class="bname serif">曼拾</div>
        <div class="ben en grey">MEANSPLUS</div>
      </div>
    </div>
    <div class="tag cn grey">品牌文化 · 一页<br><span class="en">CULTURE IN ONE PAGE</span></div>
  </header>

  <div class="rule" style="height:3px;margin:{s(56)}px 0 0"></div>

  <div style="margin-top:{s(56)}px">
    <h2 class="serif">凤凰是风，蒲公英是种子<span class="en grey">THE PHOENIX IS THE WIND. THE DANDELION IS THE SEED.</span></h2>
    <p class="body cn">{PHOENIX_CN[0]}</p>
    <p class="body cn" style="margin-top:{s(18)}px">{PHOENIX_CN[1]}</p>
    <p class="enbody en">{PHOENIX_EN[0]}</p>
  </div>

  <div class="rule" style="height:2px;margin:{s(54)}px 0 0"></div>

  <div style="margin-top:{s(56)}px">
    <h2 class="serif" style="font-size:{s(66)}px">五颗心<span class="en grey">FIVE HEARTS</span></h2>
    <p class="body cn" style="margin-top:{s(20)}px">花蕊是初心：只做有效营销，帮助客户生意真正增长跃升。</p>
    <p class="enbody en" style="margin-top:{s(8)}px">The centre is our founding intent: only marketing that works.</p>
    {hearts_html()}
    <div class="stem">
      <b class="cn red">茎 · 积极不放弃</b><b class="en" style="font-size:{s(32)}px;letter-spacing:{s(5)}px;color:#B9B3AD">THE STEM: NEVER GIVE UP</b>
      <span class="cn">人生绝非一马平川，困难面前勇登攀。它撑着上面五颗心。</span>
    </div>
  </div>

  <div class="rule" style="height:2px;margin:{s(60)}px 0 0"></div>

  <div class="mvo" style="margin-top:{s(52)}px">
    <h3 class="cn">使命<em class="en">MISSION</em></h3>
    <p class="cn">陪伴长期主义品牌创造势能。</p>
    <p class="enbody en">Stand with brands that play the long game — and build their momentum.</p>
  </div>
  <div class="mvo" style="margin-top:{s(34)}px">
    <h3 class="cn">愿景<em class="en">VISION</em></h3>
    {"".join(f'<div class="mvsub cn"><b>{k}</b>{v}</div>' for k, v in VISION_CN)}
  </div>
  <div class="mvo" style="margin-top:{s(34)}px">
    <h3 class="cn">价值观<em class="en">VALUES</em></h3>
    <p class="cn">态度至诚（怀感恩心，做利他者）· 结果导向（成有用事，用结果说话）· 积极不放弃（积极乐观，永不放弃）</p>
    <p class="enbody en">SINCERITY · RESULTS · NEVER GIVE UP</p>
  </div>
  <footer class="cn grey">
    <div>曼拾·社交媒体整合营销</div>
    <div class="en" style="letter-spacing:{s(5)}px">INTEGRATED MARKETING &amp; BRANDING | MCN</div>
  </footer>
</div>
</body></html>"""
    p = os.path.join(OUT, "onepager_a4.html")
    open(p, "w").write(html)
    return p


def build_169():
    """16:9 横版 3840×2160"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS_COMMON}
body{{width:3840px;height:2160px;overflow:hidden;position:relative}}
.wrap{{position:absolute;left:150px;right:150px;top:120px;bottom:70px;display:flex;flex-direction:column}}
header{{display:flex;align-items:center;justify-content:space-between}}
.brand{{display:flex;align-items:center;gap:30px}}
.brand img{{width:170px;height:170px}}
.bname{{font-size:66px;letter-spacing:10px}}
.ben{{font-size:22px;letter-spacing:9px;margin-top:8px}}
.tag{{text-align:right;font-size:20px;line-height:1.6;letter-spacing:3px}}
.cols{{display:flex;gap:90px;margin-top:64px}}
.left{{flex:1 1 46%}}
.right{{flex:1 1 54%}}
h2{{font-size:44px;line-height:1.3;font-weight:600}}
h2 .en{{font-size:21px;letter-spacing:2px;display:block;margin-top:10px;font-weight:400}}
p.body{{font-size:26px;line-height:1.72;margin-top:16px;text-align:justify}}
p.enbody{{font-size:20px;line-height:1.55;margin-top:8px;color:#8C8781}}
.heart{{display:flex;gap:22px;margin-top:26px;align-items:flex-start}}
.badge{{width:44px;height:44px;border-radius:50%;background:#F8223E;color:#fff;font-size:24px;
  display:flex;align-items:center;justify-content:center;flex:0 0 44px;margin-top:4px}}
.hname{{display:flex;align-items:baseline;gap:14px}}
.hname span:first-child{{font-size:46px;font-weight:600;letter-spacing:4px}}
.hen{{font-size:19px;letter-spacing:4px;color:#B9B3AD}}
.hfour{{font-size:26px;margin-top:6px;letter-spacing:3px}}
.hdesc{{font-size:22px;line-height:1.5;color:#6E6A66;margin-top:4px}}
.stem{{display:flex;gap:22px;margin-top:34px;align-items:baseline}}
.stem b{{font-size:26px;font-weight:600;letter-spacing:3px}}
.stem span{{font-size:22px;color:#6E6A66}}
.mvo{{margin-top:28px;border-left:4px solid #F8223E;padding-left:24px}}
.mvo h3{{font-size:26px;font-weight:600;letter-spacing:3px}}
.mvo h3 em{{font-style:normal;font-size:18px;color:#B9B3AD;letter-spacing:3px;margin-left:12px}}
.mvo p{{font-size:22px;line-height:1.6;margin-top:8px;color:#4A4744}}
.mvo p.enbody{{font-size:18px;margin-top:4px}}
.mvsub{{font-size:21px;line-height:1.55;color:#4A4744;margin-top:6px}}
.mvsub b{{font-weight:600;color:#262423;margin-right:8px}}
.rules{{display:flex;gap:12px;margin-top:34px}}
.rules i{{display:block;width:10px;height:74px;border-radius:4px}}
footer{{position:absolute;left:150px;right:150px;bottom:110px;display:flex;justify-content:space-between;
  align-items:flex-end;font-size:19px;letter-spacing:3px;padding-top:26px;border-top:2px solid #EAE4DD}}
</style></head><body><div class="wrap">
  <header>
    <div class="brand">
      <img src="{LOGO}">
      <div>
        <div class="bname serif">曼拾</div>
        <div class="ben en grey">MEANSPLUS</div>
      </div>
    </div>
    <div class="tag cn grey">品牌文化 · 一页<br><span class="en">CULTURE IN ONE PAGE</span></div>
  </header>
  <div class="cols">
    <div class="left">
      <h2 class="serif">凤凰是风，蒲公英是种子<span class="en grey">THE PHOENIX IS THE WIND. THE DANDELION IS THE SEED.</span></h2>
      <p class="body cn">{PHOENIX_CN[0]}</p>
      <p class="body cn" style="margin-top:10px">{PHOENIX_CN[1]}</p>
      <p class="enbody en">{PHOENIX_EN[0]}</p>
      <div class="mvo" style="margin-top:36px">
        <h3 class="cn">使命<em class="en">MISSION</em></h3>
        <p class="cn">陪伴长期主义品牌创造势能。</p>
        <p class="enbody en">Stand with brands that play the long game — and build their momentum.</p>
      </div>
      <div class="mvo">
        <h3 class="cn">愿景<em class="en">VISION</em></h3>
        {"".join(f'<div class="mvsub cn"><b>{k}</b>{v}</div>' for k, v in VISION_CN)}
      </div>
      <div class="mvo">
        <h3 class="cn">价值观<em class="en">VALUES</em></h3>
        <p class="cn">态度至诚（怀感恩心，做利他者）· 结果导向（成有用事，用结果说话）· 积极不放弃</p>
      </div>
    </div>
    <div class="right">
      <h2 class="serif" style="font-size:40px">五颗心<span class="en grey">FIVE HEARTS</span></h2>
      <p class="body cn" style="margin-top:10px">花蕊是初心：只做有效营销，帮助客户生意真正增长跃升。</p>
      <p class="enbody en" style="margin-top:4px">The centre is our founding intent: only marketing that works.</p>
      {hearts_html('169')}
      <div class="stem">
        <b class="cn red">茎 · 积极不放弃</b>
        <b class="en" style="font-size:19px;letter-spacing:4px;color:#B9B3AD">THE STEM: NEVER GIVE UP</b>
        <span class="cn">人生绝非一马平川，困难面前勇登攀。它撑着上面五颗心。</span>
      </div>
      <div class="rules"><i style="background:#F8223E"></i><i style="background:#F93957"></i>
        <i style="background:#FF94B9"></i><i style="background:#FFEADF"></i><i style="background:#65CDBC"></i>
        <i style="background:#8CF160"></i><i style="background:#EFFD5B"></i><i style="background:#D27D33"></i></div>
    </div>
  </div>
  <footer class="cn grey">
    <div>曼拾·社交媒体整合营销</div>
    <div class="en" style="letter-spacing:4px">INTEGRATED MARKETING &amp; BRANDING | MCN</div>
  </footer>
</div></body></html>"""
    p = os.path.join(OUT, "onepager_169.html")
    open(p, "w").write(html)
    return p


def render(html_path, out_png, w, h):
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           "--force-device-scale-factor=1", "--default-background-color=fffcfaf7",
           f"--window-size={w},{h}", f"--screenshot={out_png}", f"file://{html_path}"]
    subprocess.run(cmd, capture_output=True, timeout=180)
    return out_png


def measure_gap(png):
    """返回 (内容底部, 页脚顶部, 间隔)"""
    import numpy as np
    from PIL import Image
    a = np.array(Image.open(png).convert("L")).astype(int)
    r = (a < 190).sum(1)
    rows = np.where(r > 0)[0]
    if len(rows) == 0:
        return 0, 0, 0
    bottom = int(rows.max())
    # 从底部往上找页脚块的起点
    y = bottom
    while y > 0 and r[y - 1] > 0:
        y -= 1
    footer_top = y
    # 页脚之上最近的一段内容
    y2 = footer_top - 1
    while y2 > 0 and r[y2] == 0:
        y2 -= 1
    content_bottom = y2
    return content_bottom, footer_top, footer_top - content_bottom


def fit_a4(lo=0.60, hi=1.10, tol=0.008):
    """二分找一个全局缩放 K：内容与页脚间隔 >= 70px 的前提下尽量放大"""
    import numpy as np
    from PIL import Image
    best = None
    while hi - lo > tol:
        mid = round((lo + hi) / 2, 3)
        png = os.path.join(OUT, "_probe.png")
        render(build_a4(mid), png, 2480, 3508)
        cb, ft, gap = measure_gap(png)
        print(f"  K {mid} -> content {cb}, footer {ft}, gap {gap}", flush=True)
        if gap < 70:
            hi = mid
        else:
            lo = mid
            best = mid
    return best or lo


if __name__ == "__main__":
    z = fit_a4()
    print("chosen zoom", z, flush=True)
    a4 = render(build_a4(z), os.path.join(OUT, "曼拾品牌文化一页_A4竖版.png"), 2480, 3508)
    print("a4", a4)
    w169 = render(build_169(), os.path.join(OUT, "曼拾品牌文化一页_16-9横版.png"), 3840, 2160)
    print("169", w169)
