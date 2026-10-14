#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Photo-like mockups of 逸凡's business card (from the designer's reference image)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = "/Users/yifansmacmini/.openclaw/workspace/output"
OUT = os.path.join(BASE, "manshi-card")
REF = "/tmp/yf_ref.png"          # RGB copy of the inbound CMYK screenshot
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- card art
def card_art(width=2100, box=(89, 0, 1053, 575)):
    src = Image.open(REF).convert("RGB").crop(box)
    art = src.resize((width, int(src.height * width / src.width)), Image.LANCZOS)
    art = art.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=3))
    w, h = art.size

    # paper grain (multiply) so the card is not a flat digital white
    rng = np.random.default_rng(4)
    fine = rng.normal(0, 3.0, (h, w))
    fibre = np.array(Image.fromarray(((rng.normal(0, 1.0, (h, w)) + 8) * 14).clip(0, 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(0.5)), np.float32)
    fibre = (fibre - fibre.mean()) * 0.3
    arr = np.array(art, np.float32) + fine[..., None] * 0.55 + fibre[..., None]
    art = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.3))

    # soft lighting falloff across the printed surface
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    shade = 1.0 + 0.028 * (1 - yy / h) - 0.018 * (xx / w) - 0.03 * ((xx / w - 0.45) ** 2)
    arr = np.array(art, np.float32) * shade[..., None]
    art = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return art.convert("RGBA")

def rounded_alpha(size, radius=10):
    w, h = size
    m = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 4 - 1, h * 4 - 1], radius=radius * 4, fill=255)
    return m.resize((w, h), Image.LANCZOS)

# ---------------------------------------------------------------- scene bits
def low_freq(w, h, scale=14, seed=1):
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.6))
    return (np.array(img, np.float32) - 128) / 128.0

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

def _quad_to_coeffs(quad, rect):
    A, B = [], []
    for (x, y), (u, v) in zip(rect, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return tuple(np.linalg.solve(np.array(A), np.array(B)).tolist())

def place(scene, card, cx, cy, width, rot=0.0, keystone=1.0, shadow=1.0, focus=1.0, angle=(26, 42, 55)):
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
    for dx, dy, blur, op, tone in [(3, 5, 7, 0.50, (96, 86, 78)), (10, 16, 20, 0.34, (112, 102, 92)),
                                   (angle[0], angle[1], angle[2], 0.26, (126, 116, 106))]:
        sh = Image.new("L", scene.size, 0)
        sh.paste(alpha, (x + dx, y + dy))
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, o=op * shadow: int(v * o))
        scene.paste(Image.new("RGB", scene.size, tone), (0, 0), sh)
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

# ---------------------------------------------------------------- scenes
def scene_single(W=2400, H=1500):
    art = card_art()
    art.putalpha(rounded_alpha(art.size, radius=8))
    s = desk(W, H, seed=5)
    s = place(s, art, W * 0.50, H * 0.52, W * 0.78, rot=-5.0, keystone=0.99)
    return finish(s)

def scene_stack(W=2400, H=1600):
    art1 = card_art(); art1.putalpha(rounded_alpha(art1.size, radius=8))
    art2 = art1.rotate(-13, resample=Image.BICUBIC, expand=True)
    s = desk(W, H, seed=9)
    s = place(s, art2, W * 0.40, H * 0.55, W * 0.62, rot=0.0, shadow=0.9, focus=0.84)
    s = place(s, art1, W * 0.60, H * 0.47, W * 0.68, rot=-4.0)
    return finish(s)

def scene_closeup(W=1620, H=2160):
    art = card_art()
    art.putalpha(rounded_alpha(art.size, radius=8))
    s = desk(W, H, seed=13)
    s = place(s, art, W * 0.52, H * 0.52, W * 1.02, rot=-7.0, keystone=0.985)
    return finish(s, vig=0.22)

if __name__ == "__main__":
    a = scene_single(); a.save(os.path.join(OUT, "名片效果图_单张.png")); print("single", a.size)
    b = scene_stack();  b.save(os.path.join(OUT, "名片效果图_双张.png")); print("stack", b.size)
    c = scene_closeup(); c.save(os.path.join(OUT, "名片效果图_竖版.png")); print("closeup", c.size)
    card_art().convert("RGB").save(os.path.join(OUT, "名片平面稿_正面.png"))
    print("done")
