#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Photo-realistic paper business-card mockups for the Manshi (曼拾) light-bg logo. v2"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")
OUT = os.path.join(BASE, "manshi-card")
os.makedirs(OUT, exist_ok=True)

RED = (248, 34, 62)
INK = (38, 36, 35)
DARK = (70, 66, 64)
MID = (108, 103, 99)
GREY = (150, 145, 140)

F_SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_SERIF = "/System/Library/Fonts/Supplemental/Songti.ttc"

def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)

# ------------------------------------------------------------------ helpers
def low_freq(w, h, scale=14, seed=1):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.6))
    return (np.array(img, np.float32) - 128) / 128.0

def paper_base(w, h, base=(252, 250, 246), seed=11, tooth=3.4):
    """Warm uncoated paper: fine tooth grain + faint fibre streaks + soft light gradient."""
    rng = np.random.default_rng(seed)
    arr = np.zeros((h, w, 3), np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    fine = rng.normal(0, tooth, (h, w))
    fibre = rng.normal(0, 1.0, (h, w))
    fibre = np.array(Image.fromarray(((fibre + 8) * 14).clip(0, 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(0.5)), np.float32)
    fibre = (fibre - fibre.mean()) * 0.36
    blotch = low_freq(w, h, scale=110, seed=seed + 5) * 1.5
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    light = 1.0 + 0.030 * (1 - yy / h) - 0.016 * (xx / w)          # light from upper-left
    lum = fine + fibre + blotch
    for c in range(3):
        arr[..., c] = arr[..., c] * light + lum
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def ink_on_paper(layer_rgba, paper):
    """Make flat vector art read as ink soaked into uncoated stock."""
    ink = layer_rgba.split()[3].filter(ImageFilter.GaussianBlur(0.45)).point(lambda v: int(v * 0.94))
    grain = np.array(paper, np.float32) / 255.0
    colored = Image.new("RGB", layer_rgba.size, (255, 255, 255))
    colored.paste(layer_rgba.convert("RGB"), (0, 0), layer_rgba.split()[3])
    arr = np.array(colored, np.float32) * grain
    arr = np.array(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35)), np.float32)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(ink)
    return out

def edge_definition(card):
    """Slightly darken / soften the cut edge so it doesn't look razor sharp."""
    w, h = card.size
    alpha = np.array(card.split()[3], np.float32)
    inner = np.array(Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), np.float32)
    rim = np.clip(inner - alpha, 0, 255) / 255.0
    arr = np.array(card.convert("RGB"), np.float32)
    arr = arr * (1 - 0.012 * (1 - rim)[..., None]) + rim[..., None] * 3.0
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(card.split()[3].filter(ImageFilter.GaussianBlur(0.35)))
    return out

def paste_logo(layer, cx, cy, diameter):
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    s = diameter / max(logo.size)
    logo = logo.resize((max(1, int(logo.width * s)), max(1, int(logo.height * s))), Image.LANCZOS)
    layer.alpha_composite(logo, (int(cx - logo.width / 2), int(cy - logo.height / 2)))

def text_tracked(draw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x

def text_center(draw, y, text, fnt, fill, tracking=0, w=1800):
    tw = sum(draw.textlength(c, font=fnt) for c in text) + tracking * (len(text) - 1)
    text_tracked(draw, ((w - tw) / 2, y), text, fnt, fill, tracking)

# ------------------------------------------------------------------ card faces
CARD_W, CARD_H = 1800, 1080          # 90 x 54 mm

def build_front():
    paper = paper_base(CARD_W, CARD_H, seed=11)
    layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paste_logo(layer, CARD_W / 2, CARD_H / 2 - 62, 430)
    f_co = font(F_SANS, 44, index=1)
    f_en = font(F_SANS, 27, index=0)
    text_center(d, CARD_H - 224, "上海曼拾文化传播有限公司", f_co, (92, 88, 85), tracking=7)
    text_center(d, CARD_H - 156, "SHANGHAI MANSHI CULTURE COMMUNICATION CO., LTD.", f_en, GREY, tracking=4)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)

def build_back():
    paper = paper_base(CARD_W, CARD_H, seed=23)
    layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paste_logo(layer, 330, 300, 210)
    d.text((232, 470), "李逸凡", font=font(F_SERIF, 112, index=1), fill=INK)
    d.text((236, 626), "创始人 / FOUNDER", font=font(F_SANS, 42, index=1), fill=RED)
    d.line([(232, 726), (1568, 726)], fill=(226, 221, 215), width=3)
    f_body = font(F_SANS, 46, index=1)
    d.text((232, 786), "M", font=font(F_SANS, 40, index=1), fill=RED)
    d.text((330, 780), "177 0341 8418", font=f_body, fill=DARK)
    d.text((232, 866), "W", font=font(F_SANS, 40, index=1), fill=RED)
    d.text((330, 860), "liyifan09041", font=f_body, fill=DARK)
    text_center(d, CARD_H - 130, "上海曼拾文化传播有限公司  ·  小红书整合营销", font(F_SANS, 36, index=1), MID, tracking=5)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)

# ------------------------------------------------------------------ scene
def _quad_to_coeffs(quad, rect):
    A, B = [], []
    for (x, y), (u, v) in zip(rect, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return tuple(np.linalg.solve(np.array(A), np.array(B)).tolist())

def desk(W, H, base=(240, 233, 223), seed=5, grain=2.2):
    rng = np.random.default_rng(seed)
    arr = np.zeros((H, W, 3), np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.30, H * 0.20
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (1.0 * max(W, H))
    fall = np.clip(1.07 - 0.40 * r ** 1.35, 0.50, 1.20)
    macro = low_freq(W, H, scale=150, seed=seed + 3) * 4.5
    g = rng.normal(0, grain, (H, W))
    for c in range(3):
        arr[..., c] = arr[..., c] * fall + macro + g
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    # a few faint dust specks
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x, y = rng.integers(0, W), rng.integers(0, H)
        v = int(rng.normal(0, 26))
        rr = int(rng.integers(1, 3))
        d.ellipse([x, y, x + rr, y + rr], fill=(int(np.clip(base[0] + v, 0, 255)),
                                                int(np.clip(base[1] + v, 0, 255)),
                                                int(np.clip(base[2] + v, 0, 255))))
    return img.filter(ImageFilter.GaussianBlur(0.3))

def place(scene, card, cx, cy, width, rot=0.0, keystone=1.0, shadow=1.0, focus=1.0):
    cw = int(width); ch = int(card.height * width / card.width)
    c = card.resize((cw, ch), Image.LANCZOS)
    if keystone != 1.0:
        inset = (cw - cw * keystone) / 2
        coefs = _quad_to_coeffs([(inset, 0), (cw - inset, 0), (cw, ch), (0, ch)], [(0, 0), (cw, 0), (cw, ch), (0, ch)])
        c = c.transform((cw, ch), Image.PERSPECTIVE, coefs, Image.BICUBIC)
    c = c.rotate(rot, resample=Image.BICUBIC, expand=True)
    if focus < 1.0:
        c = c.filter(ImageFilter.GaussianBlur((1 - focus) * 2.0))
    x, y = int(cx - c.width / 2), int(cy - c.height / 2)
    alpha = c.split()[3]
    # contact shadow (tight, dark) -> penumbra -> ambient
    for dx, dy, blur, op, tone in [(3, 5, 7, 0.50, (96, 86, 78)),
                                   (10, 16, 20, 0.34, (112, 102, 92)),
                                   (26, 42, 55, 0.26, (126, 116, 106))]:
        sh = Image.new("L", scene.size, 0)
        sh.paste(alpha, (x + dx, y + dy))
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, o=op * shadow: int(v * o))
        scene.paste(Image.new("RGB", scene.size, tone), (0, 0), sh)
    # gentle surface shading on the card itself (paper is never perfectly flat)
    w, h = c.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    shade = 1.0 + 0.018 * (1 - yy / h) - 0.010 * (xx / w) - 0.02 * ((xx / w - 0.5) ** 2) * 4
    arr = np.array(c.convert("RGB"), np.float32) * shade[..., None]
    c = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
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

# ------------------------------------------------------------------ scenes
def scene_single(W=2400, H=1500):
    s = desk(W, H, seed=5)
    s = place(s, build_front(), W * 0.50, H * 0.53, W * 0.62, rot=-6.0)
    return finish(s)

def scene_pair(W=2400, H=1600):
    s = desk(W, H, seed=9)
    s = place(s, build_back(), W * 0.355, H * 0.56, W * 0.50, rot=8.0, shadow=0.95, focus=0.86)
    s = place(s, build_front(), W * 0.635, H * 0.45, W * 0.50, rot=-3.5)
    return finish(s)

def scene_closeup(W=1620, H=2160):
    s = desk(W, H, seed=13)
    s = place(s, build_front(), W * 0.52, H * 0.52, W * 0.92, rot=-8.0)
    return finish(s, vig=0.22)

if __name__ == "__main__":
    for name, im in [("card_single_photo", scene_single()), ("card_pair_photo", scene_pair()),
                     ("card_closeup_photo", scene_closeup())]:
        im.save(os.path.join(OUT, name + ".png")); print(name, im.size)
    build_front().save(os.path.join(OUT, "card_front_flat.png"))
    build_back().save(os.path.join(OUT, "card_back_flat.png"))
    print("done")
