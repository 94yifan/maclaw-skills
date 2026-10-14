#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曼拾 business card (浅色底 clover logo + 逸凡 real card info) → photo-like mockups."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")   # 浅色底：红圆+白蒲公英
OUT = os.path.join(BASE, "manshi-card")
os.makedirs(OUT, exist_ok=True)

RED = (248, 34, 62)
INK = (38, 36, 35)
DARK = (72, 68, 66)
MID = (112, 107, 103)
GREY = (152, 147, 142)
F_SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_SERIF = "/System/Library/Fonts/Supplemental/Songti.ttc"

def font(p, s, i=0):
    return ImageFont.truetype(p, s, index=i)

# ------------------------------------------------------------ textures
def low_freq(w, h, scale=14, seed=1):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.6))
    return (np.array(img, np.float32) - 128) / 128.0

def paper_base(w, h, base=(252, 250, 246), seed=11, tooth=3.2):
    rng = np.random.default_rng(seed)
    arr = np.zeros((h, w, 3), np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    fine = rng.normal(0, tooth, (h, w))
    fibre = rng.normal(0, 1.0, (h, w))
    fibre = np.array(Image.fromarray(((fibre + 8) * 14).clip(0, 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(0.5)), np.float32)
    fibre = (fibre - fibre.mean()) * 0.34
    blotch = low_freq(w, h, scale=110, seed=seed + 5) * 1.4
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    light = 1.0 + 0.030 * (1 - yy / h) - 0.016 * (xx / w)
    lum = fine + fibre + blotch
    for c in range(3):
        arr[..., c] = arr[..., c] * light + lum
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def ink_on_paper(layer, paper):
    ink = layer.split()[3].filter(ImageFilter.GaussianBlur(0.45)).point(lambda v: int(v * 0.94))
    grain = np.array(paper, np.float32) / 255.0
    colored = Image.new("RGB", layer.size, (255, 255, 255))
    colored.paste(layer.convert("RGB"), (0, 0), layer.split()[3])
    arr = np.array(colored, np.float32) * grain
    arr = np.array(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35)), np.float32)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(ink)
    return out

def edge_definition(card):
    alpha = np.array(card.split()[3], np.float32)
    inner = np.array(Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), np.float32)
    rim = np.clip(inner - alpha, 0, 255) / 255.0
    arr = np.array(card.convert("RGB"), np.float32) * (1 - 0.012 * (1 - rim)[..., None]) + rim[..., None] * 3.0
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(card.split()[3].filter(ImageFilter.GaussianBlur(0.35)))
    return out

def logo_img(diameter):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    s = diameter / max(lg.size)
    return lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)

def paste_logo(layer, cx, cy, d):
    lg = logo_img(d)
    layer.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))

def badge(layer, cx, cy, d, letter, fnt):
    d_ = ImageDraw.Draw(layer)
    d_.ellipse([cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2], fill=RED)
    bb = d_.textbbox((0, 0), letter, font=fnt)
    d_.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), letter, font=fnt, fill=(255, 255, 255))

def tracked(draw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x

def center(draw, y, text, fnt, fill, tracking=0, w=1800):
    tw = sum(draw.textlength(c, font=fnt) for c in text) + tracking * (len(text) - 1)
    tracked(draw, ((w - tw) / 2, y), text, fnt, fill, tracking)

# ------------------------------------------------------------ card faces
CW, CH = 1800, 1080   # 90 x 54 mm

def build_front():
    paper = paper_base(CW, CH, seed=11)
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paste_logo(layer, CW / 2, 375, 380)
    f_brand = font(F_SANS, 118, 1)
    center(d, 610, "曼拾", f_brand, INK, tracking=26)
    center(d, 800, "MEANS PLUS", font(F_SANS, 34, 0), MID, tracking=16)
    d.line([(CW / 2 - 150, 880), (CW / 2 + 150, 880)], fill=(232, 227, 221), width=3)
    center(d, 910, "陪伴长期主义品牌创造势能", font(F_SANS, 38, 1), (128, 123, 119), tracking=8)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)

def build_back():
    paper = paper_base(CW, CH, seed=23)
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # left brand column
    paste_logo(layer, 320, 320, 240)
    d.text((190, 470), "曼拾", font=font(F_SANS, 74, 1), fill=INK)
    tracked(d, (192, 580), "MEANS PLUS", font(F_SANS, 24, 0), MID, tracking=6)
    d.line([(690, 150), (690, 930)], fill=(228, 223, 217), width=3)
    # right info column
    d.text((750, 170), "李逸凡", font=font(F_SERIF, 104, 1), fill=INK)
    d.text((1075, 212), "YIFAN LI", font=font(F_SANS, 38, 0), fill=(150, 145, 141))
    d.text((752, 330), "创始人  FOUNDER", font=font(F_SANS, 44, 1), fill=RED)
    d.text((752, 412), "小红书平台官方认证营销专家讲师（全平台6位）", font=font(F_SANS, 32, 1), fill=(120, 115, 111))
    d.line([(750, 482), (1660, 482)], fill=(228, 223, 217), width=3)
    rows = [("T", "86-17703418418"),
            ("E", "yifan@meansplus.com"),
            ("W", "liyifan09041")]
    f_l = font(F_SANS, 34, 0)
    f_t = font(F_SANS, 38, 1)
    y = 532
    for letter, text in rows:
        badge(layer, 778, y + 23, 46, letter, f_l)
        d.text((824, y), text, font=f_t, fill=DARK)
        y += 72
    # address block (hanging indent, two lines CN + two lines EN)
    badge(layer, 778, y + 27, 46, "A", f_l)
    f_addr = font(F_SANS, 32, 1)
    d.text((824, y + 6), "上海市浦东新区沪南路2157弄", font=f_addr, fill=DARK)
    d.text((824, y + 50), "复地万科活力中心2号2716-2717室", font=f_addr, fill=DARK)
    f_en = font(F_SANS, 28, 0)
    d.text((824, y + 100), "Room 2716-2717, No.2 Fudi Vanke Vitality Center,", font=f_en, fill=(146, 141, 137))
    d.text((824, y + 138), "Lane 2157, Hunan Road, Pudong New Area, Shanghai", font=f_en, fill=(146, 141, 137))
    center(d, CH - 92, "小红书首批整合营销代理商  ·  小红书、B站官方认证MCN", font(F_SANS, 28, 1), (146, 141, 137), tracking=3)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)

# ------------------------------------------------------------ scenes
def _coeffs(quad, rect):
    A, B = [], []
    for (x, y), (u, v) in zip(rect, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return tuple(np.linalg.solve(np.array(A), np.array(B)).tolist())

def desk(W, H, base=(241, 234, 224), seed=5, grain=2.2):
    rng = np.random.default_rng(seed)
    arr = np.zeros((H, W, 3), np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - W * 0.30) ** 2 + (yy - H * 0.20) ** 2) / (1.0 * max(W, H))
    fall = np.clip(1.07 - 0.40 * r ** 1.35, 0.50, 1.20)
    macro = low_freq(W, H, scale=150, seed=seed + 3) * 4.5
    g = rng.normal(0, grain, (H, W))
    for c in range(3):
        arr[..., c] = arr[..., c] * fall + macro + g
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        v = int(rng.normal(0, 26)); rr = int(rng.integers(1, 3))
        d.ellipse([x, y, x + rr, y + rr], fill=(int(np.clip(base[0] + v, 0, 255)),
                                                int(np.clip(base[1] + v, 0, 255)),
                                                int(np.clip(base[2] + v, 0, 255))))
    return img.filter(ImageFilter.GaussianBlur(0.3))

def place(scene, card, cx, cy, width, rot=0.0, keystone=1.0, shadow=1.0, focus=1.0):
    cw = int(width); ch = int(card.height * width / card.width)
    c = card.resize((cw, ch), Image.LANCZOS)
    if keystone != 1.0:
        inset = (cw - cw * keystone) / 2
        c = c.transform((cw, ch), Image.PERSPECTIVE,
                        _coeffs([(inset, 0), (cw - inset, 0), (cw, ch), (0, ch)], [(0, 0), (cw, 0), (cw, ch), (0, ch)]),
                        Image.BICUBIC)
    c = c.rotate(rot, resample=Image.BICUBIC, expand=True)
    if focus < 1.0:
        c = c.filter(ImageFilter.GaussianBlur((1 - focus) * 2.0))
    x, y = int(cx - c.width / 2), int(cy - c.height / 2)
    alpha = c.split()[3]
    for dx, dy, blur, op, tone in [(3, 5, 7, 0.50, (96, 86, 78)), (10, 16, 20, 0.34, (112, 102, 92)),
                                   (26, 42, 55, 0.26, (126, 116, 106))]:
        sh = Image.new("L", scene.size, 0)
        sh.paste(alpha, (x + dx, y + dy))
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, o=op * shadow: int(v * o))
        scene.paste(Image.new("RGB", scene.size, tone), (0, 0), sh)
    w_, h_ = c.size
    yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32)
    shade = 1.0 + 0.018 * (1 - yy / h_) - 0.010 * (xx / w_) - 0.02 * ((xx / w_ - 0.5) ** 2) * 4
    c = Image.fromarray(np.clip(np.array(c.convert("RGB"), np.float32) * shade[..., None], 0, 255).astype(np.uint8)).convert("RGBA")
    c.putalpha(alpha)
    scene.paste(c, (x, y), c)
    return scene

def finish(img, vig=0.20, grain=2.4):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt((xx - w * 0.46) ** 2 + (yy - h * 0.46) ** 2) / (0.74 * max(w, h))
    img = Image.fromarray(np.clip(np.array(img, np.float32) * np.clip(1 - vig * r ** 2, 0, 1)[..., None], 0, 255).astype(np.uint8))
    arr = np.array(img, np.float32)
    rng = np.random.default_rng(99)
    arr += rng.normal(0, grain, arr.shape[:2])[..., None]
    arr[..., 0] *= 1.012; arr[..., 2] *= 0.994
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def scene_single(W=2400, H=1500):
    s = desk(W, H, seed=5)
    s = place(s, build_front(), W * 0.50, H * 0.53, W * 0.66, rot=-6.0)
    return finish(s)

def scene_pair(W=2400, H=1600):
    s = desk(W, H, seed=9)
    s = place(s, build_back(), W * 0.365, H * 0.56, W * 0.55, rot=8.0, shadow=0.95, focus=0.86)
    s = place(s, build_front(), W * 0.635, H * 0.46, W * 0.55, rot=-3.5)
    return finish(s)

def scene_closeup_front(W=1620, H=2160):
    s = desk(W, H, seed=13)
    s = place(s, build_front(), W * 0.52, H * 0.52, W * 0.96, rot=-8.0)
    return finish(s, vig=0.22)

def scene_closeup_back(W=1620, H=2160):
    s = desk(W, H, seed=17)
    s = place(s, build_back(), W * 0.52, H * 0.52, W * 0.98, rot=6.0)
    return finish(s, vig=0.22)

if __name__ == "__main__":
    build_front().convert("RGB").save(os.path.join(OUT, "曼拾名片_正面平面稿.png"))
    build_back().convert("RGB").save(os.path.join(OUT, "曼拾名片_背面平面稿.png"))
    for name, im in [("曼拾名片_正面单张", scene_single()), ("曼拾名片_正反面叠放", scene_pair()),
                     ("曼拾名片_竖版正面", scene_closeup_front()), ("曼拾名片_竖版背面", scene_closeup_back())]:
        im.save(os.path.join(OUT, name + ".png")); print(name, im.size)
    print("done")
