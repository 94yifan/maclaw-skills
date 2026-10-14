#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三家企业抬头名片：正反面叠放效果图（企业抬头面 + 李逸凡个人信息面），版式对齐 REF 图。"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
LOGO = os.path.join(BASE, "manshi-logo", "manshi_logo_transparent_2000.png")
OUT = os.path.join(BASE, "manshi-card", "letterhead")
os.makedirs(OUT, exist_ok=True)

F_SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_SERIF = "/System/Library/Fonts/Supplemental/Songti.ttc"
RED = (248, 34, 62)
INK = (38, 36, 35)
DARK = (72, 68, 66)
MID = (112, 107, 103)
GREY = (150, 145, 140)


def font(p, s, i=0):
    return ImageFont.truetype(p, s, index=i)


def low_freq(w, h, scale=14, seed=1):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.6))
    return (np.array(img, np.float32) - 128) / 128.0


def paper_base(w, h, base=(252, 250, 246), seed=11, tooth=3.4):
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
    light = 1.0 + 0.030 * (1 - yy / h) - 0.016 * (xx / w)
    lum = fine + fibre + blotch
    for c in range(3):
        arr[..., c] = arr[..., c] * light + lum
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def ink_on_paper(layer_rgba, paper):
    ink = layer_rgba.split()[3].filter(ImageFilter.GaussianBlur(0.45)).point(lambda v: int(v * 0.94))
    grain = np.array(paper, np.float32) / 255.0
    colored = Image.new("RGB", layer_rgba.size, (255, 255, 255))
    colored.paste(layer_rgba.convert("RGB"), (0, 0), layer_rgba.split()[3])
    arr = np.array(colored, np.float32) * grain
    arr = np.array(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(0.35)), np.float32)
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


def paste_logo(layer, cx, cy, diameter):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    s = diameter / max(lg.size)
    lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
    layer.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))


def text_tracked(draw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def text_center(draw, y, text, fnt, fill, tracking=0, w=1800):
    tw = sum(draw.textlength(c, font=fnt) for c in text) + tracking * (len(text) - 1)
    text_tracked(draw, ((w - tw) / 2, y), text, fnt, fill, tracking)


CW, CH = 1800, 1080


def build_company_face(company, sub=None):
    """企业抬头面：花标 + 公司名"""
    paper = paper_base(CW, CH, seed=11)
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paste_logo(layer, CW / 2, CH / 2 - 62, 430)
    text_center(d, CH - 224, company, font(F_SANS, 44, 1), (92, 88, 85), tracking=7)
    if sub:
        text_center(d, CH - 156, sub, font(F_SANS, 27, 0), GREY, tracking=4)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)


def build_info_face(company, person="李逸凡", title="创始人", role_en="FOUNDER",
                    mobile="177 0341 8418", wechat="liyifan09041"):
    """个人信息面：小 logo + 姓名 + 职务 + 联系方式 + 底部公司行"""
    paper = paper_base(CW, CH, seed=23)
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    paste_logo(layer, 330, 300, 210)
    d.text((232, 470), person, font=font(F_SERIF, 112, 1), fill=INK)
    d.text((236, 626), f"{title} / {role_en}", font=font(F_SANS, 42, 1), fill=RED)
    d.line([(232, 726), (1568, 726)], fill=(226, 221, 215), width=3)
    d.text((232, 786), "M", font=font(F_SANS, 40, 1), fill=RED)
    d.text((330, 780), mobile, font=font(F_SANS, 46, 1), fill=DARK)
    d.text((232, 866), "W", font=font(F_SANS, 40, 1), fill=RED)
    d.text((330, 860), wechat, font=font(F_SANS, 46, 1), fill=DARK)
    text_center(d, CH - 130, company, font(F_SANS, 36, 1), MID, tracking=5)
    card = Image.alpha_composite(paper.convert("RGBA"), ink_on_paper(layer, paper))
    return edge_definition(card)


# ---------------- scene（对齐 REF 图 / 曼拾名片效果图_正反面） ----------------
def desk(W, H, base=(241, 234, 224), seed=9, grain=2.2):
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


def place(scene, card, cx, cy, width, rot=0.0, shadow=1.0, focus=1.0):
    cw = int(width); ch = int(card.height * width / card.width)
    c = card.resize((cw, ch), Image.LANCZOS)
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


def finish(img, vig=0.18, grain=2.4):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt((xx - w * 0.46) ** 2 + (yy - h * 0.46) ** 2) / (0.74 * max(w, h))
    img = Image.fromarray(np.clip(np.array(img, np.float32) * np.clip(1 - vig * r ** 2, 0, 1)[..., None], 0, 255).astype(np.uint8))
    arr = np.array(img, np.float32)
    rng = np.random.default_rng(99)
    arr += rng.normal(0, grain, arr.shape[:2])[..., None]
    arr[..., 0] *= 1.012; arr[..., 2] *= 0.994
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def make_pair(company, sub=None, W=2400, H=1600):
    s = desk(W, H, seed=9)
    s = place(s, build_info_face(company), W * 0.365, H * 0.56, W * 0.55, rot=8.0, shadow=0.95, focus=0.86)
    s = place(s, build_company_face(company, sub), W * 0.635, H * 0.46, W * 0.55, rot=-3.5)
    return finish(s)


COMPANIES = ["上海蓁熹文化传播有限公司", "上海燃创品牌咨询有限公司", "深圳市玄女令品牌管理有限公司"]

if __name__ == "__main__":
    for c in COMPANIES:
        im = make_pair(c)
        im.save(os.path.join(OUT, f"{c}_名片正反面.png"))
        im.save(os.path.join(OUT, f"{c}_名片正反面.jpg"), quality=93, subsampling=0)
        build_info_face(c).convert("RGB").save(os.path.join(OUT, f"{c}_个人面平面稿.png"))
        print(c, "ok")
