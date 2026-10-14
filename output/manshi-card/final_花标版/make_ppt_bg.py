#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用 PPT 浅色底背景图（曼拾品牌色 + 浅色底 logo 右上角）— 6 版"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")
OUT = os.path.join(BASE, "manshi-card", "ppt-bg")
os.makedirs(OUT, exist_ok=True)

# 品牌元素色
RED     = (248, 34, 62)    # 主红
CORAL   = (249, 57, 87)    # 副红
PINK    = (255, 148, 185)  # 粉
PEACH   = (255, 234, 223)  # 奶粉
TEAL    = (101, 205, 188)
GREEN   = (140, 241, 96)
YELLOW  = (239, 253, 91)
ORANGE  = (210, 125, 51)
PALETTE = [TEAL, GREEN, YELLOW, ORANGE, RED]
WARM    = [RED, CORAL, PINK, PEACH]

W, H = 3840, 2160
MARGIN = 210
LOGO_D = 250

def bg(base=(252, 250, 247), top_boost=0.02):
    """浅色底：竖向柔和渐变 + 极轻纸纹"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr = np.zeros((H, W, 3), np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    grad = 1.0 + top_boost * (1 - yy / H) - 0.008 * (xx / W)
    arr *= grad[..., None]
    rng = np.random.default_rng(3)
    arr += rng.normal(0, 1.1, (H, W))[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img.convert("RGBA")

def put_logo(img, d=LOGO_D, margin=MARGIN, pos="tr"):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    s = d / max(lg.size)
    lg = lg.resize((int(lg.width * s), int(lg.height * s)), Image.LANCZOS)
    if pos == "tr":
        xy = (W - margin - lg.width, margin)
    elif pos == "tl":
        xy = (margin, margin)
    else:
        xy = (margin, H - margin - lg.height)
    img.alpha_composite(lg, xy)
    return img

def watermark(img, cx, cy, d, opacity=0.055, color=None):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    a = np.array(lg.split()[3], np.float32) * opacity
    if color is not None:
        rgb = np.zeros((lg.height, lg.width, 3), np.float32)
        rgb[..., 0], rgb[..., 1], rgb[..., 2] = color
        lg = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    lg.putalpha(Image.fromarray(a.astype(np.uint8)))
    s = d / max(lg.size)
    lg = lg.resize((int(lg.width * s), int(lg.height * s)), Image.LANCZOS)
    img.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))
    return img

def bars_v(img, x, y, colors, w=16, gap=16, h=170, radius=8):
    d = ImageDraw.Draw(img)
    for i, c in enumerate(colors):
        x0 = x + i * (w + gap)
        d.rounded_rectangle([x0, y, x0 + w, y + h], radius=radius, fill=c)
    return img

def dots(img, x, y, colors, r=13, gap=44):
    d = ImageDraw.Draw(img)
    for i, c in enumerate(colors):
        cx = x + i * gap
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=c)
    return img

def strip(img, colors, y, h=14, alpha=255):
    """底部横向彩条：等分整幅宽度"""
    d = ImageDraw.Draw(img)
    n = len(colors)
    for i, c in enumerate(colors):
        x0 = int(W * i / n)
        x1 = int(W * (i + 1) / n)
        d.rectangle([x0, y, x1, y + h], fill=c + (alpha,))
    return img

def hline(img, y, color=(235, 230, 224, 255), x0=MARGIN, x1=W - MARGIN, w=2):
    ImageDraw.Draw(img).rectangle([x0, y, x1, y + w], fill=color)
    return img

def col_segment(img, y, colors, total=760, h=12, x=MARGIN):
    d = ImageDraw.Draw(img)
    seg = total / len(colors)
    for i, c in enumerate(colors):
        d.rectangle([x + i * seg, y, x + (i + 1) * seg - 6, y + h], fill=c)
    return img

def radial_soft(img, cx, cy, radius, color, alpha=0.5):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(radius * 0.35)).point(lambda v: int(v * alpha))
    img.paste(Image.new("RGB", (W, H), color), (0, 0), m)
    return img

def grain(img, amount=0.7):
    arr = np.array(img.convert("RGB"), np.float32)
    rng = np.random.default_rng(7)
    arr += rng.normal(0, amount, arr.shape[:2])[..., None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(img.split()[3])
    return out

# ------------------------------------------------------------------ v1 极简
def v1():
    img = bg()
    bars_v(img, MARGIN, MARGIN, PALETTE, w=16, gap=16, h=170)
    hline(img, H - MARGIN - 6)
    col_segment(img, H - MARGIN, PALETTE, total=760, h=12)
    put_logo(img)
    return grain(img)

# ------------------------------------------------------------------ v2 底部色带
def v2():
    img = bg(base=(253, 247, 245))
    strip(img, PALETTE, H - 16, h=16)
    radial_soft(img, int(W * 0.12), int(H * 0.95), 900, PEACH, 0.55)
    dots(img, MARGIN + 20, MARGIN + 30, PALETTE, r=14, gap=48)
    put_logo(img)
    return grain(img)

# ------------------------------------------------------------------ v3 左侧竖彩带
def v3():
    img = bg()
    d = ImageDraw.Draw(img)
    n = len(PALETTE)
    total_h = H * 0.62
    y0 = (H - total_h) / 2
    for i, c in enumerate(PALETTE):
        x0 = 96 + i * 26
        seg = total_h / n
        d.rounded_rectangle([x0, y0 + i * seg, x0 + 10, y0 + (i + 1) * seg - 10], radius=5, fill=c)
    put_logo(img)
    hline(img, H - MARGIN, color=(238, 233, 227, 255))
    return grain(img)

# ------------------------------------------------------------------ v4 花标水印
def v4():
    img = bg(base=(253, 248, 246))
    watermark(img, int(W * 0.24), int(H * 0.80), 1500, opacity=0.06, color=RED)
    dots(img, MARGIN, H - MARGIN - 6, WARM, r=13, gap=46)
    put_logo(img)
    return grain(img)

# ------------------------------------------------------------------ v5 弧线
def v5():
    img = bg()
    d = ImageDraw.Draw(img)
    cx, cy = -260, H + 260
    for i, (c, rr, a) in enumerate([(RED, 1500, 255), (PINK, 1330, 210), (TEAL, 1160, 150), (ORANGE, 990, 120)]):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).arc([cx - rr, cy - rr, cx + rr, cy + rr], start=272, end=360, fill=c + (a,), width=10)
        img.alpha_composite(lay)
    strip(img, PALETTE, H - 12, h=12)
    put_logo(img)
    return grain(img)

# ------------------------------------------------------------------ v6 圆点网格
def v6():
    img = bg(base=(251, 250, 249))
    d = ImageDraw.Draw(img)
    step = 62
    rng = np.random.default_rng(11)
    for gy in range(MARGIN, H - MARGIN + 1, step):
        for gx in range(MARGIN, W - MARGIN + 1, step):
            t = (gx / W) * 0.9 + (gy / H) * 0.1
            if t > 0.62:
                continue
            a = int(np.clip(70 * (1 - t / 0.62), 0, 70))
            d.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=RED + (a,))
    col_segment(img, H - MARGIN, PALETTE, total=760, h=12)
    put_logo(img)
    return grain(img)

VERSIONS = [("01_极简留白", v1), ("02_底部色带", v2), ("03_左侧竖彩带", v3),
            ("04_花标水印", v4), ("05_弧线", v5), ("06_圆点网格", v6)]

if __name__ == "__main__":
    for name, fn in VERSIONS:
        im = fn()
        im.convert("RGB").save(os.path.join(OUT, f"PPT背景_{name}_3840x2160.png"))
        im.convert("RGB").resize((1920, 1080), Image.LANCZOS).save(os.path.join(OUT, f"PPT背景_{name}_1920x1080.png"))
        print(name, "ok")
