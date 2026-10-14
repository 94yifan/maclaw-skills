#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从曼拾 logo 资产里拆元素（五叶草 / 凤纹），不重画、不引入外部素材。"""
import numpy as np
from PIL import Image

LOGO = "/Users/yifansmacmini/.openclaw/workspace/output/manshi-logo/manshi_logo_transparent_2000.png"
RED = (248, 34, 62)
PATTERN_RED = (249, 57, 87)


def clover(out="clover_shape.png", color=RED):
    """五叶草：取 logo 中的白色像素（R/G/B>235 且 alpha>128）"""
    a = np.array(Image.open(LOGO).convert("RGBA")).astype(int)
    m = (a[..., 0] > 235) & (a[..., 1] > 235) & (a[..., 2] > 235) & (a[..., 3] > 128)
    o = np.zeros(a.shape, np.uint8)
    o[..., 0], o[..., 1], o[..., 2] = color
    o[..., 3] = np.where(m, 255, 0)
    im = Image.fromarray(o)
    im = im.crop(im.getbbox())
    im.save(out)
    return im.size


def phoenix_pattern(out="phoenix_pattern.png", tol=40):
    """凤纹：取 logo 中 #F93957 那一层颜色"""
    a = np.array(Image.open(LOGO).convert("RGBA")).astype(int)
    d = np.abs(a[..., :3] - np.array(PATTERN_RED)).sum(2)
    m = (d < tol) & (a[..., 3] > 50)
    o = np.zeros(a.shape, np.uint8)
    o[..., 0], o[..., 1], o[..., 2] = PATTERN_RED
    o[..., 3] = np.where(m, 255, 0)
    im = Image.fromarray(o)
    im = im.crop(im.getbbox())
    im.save(out)
    return im.size


def sized_logo(width, height, diameter, out, transparent=True, color_bg=(255, 255, 255)):
    """指定尺寸的 logo 交付（透明底 / 白底）"""
    src = Image.open(LOGO).convert("RGBA")
    lg = src.crop(src.getbbox())
    s = diameter / max(lg.size)
    lg = lg.resize((max(1, round(lg.width * s)), max(1, round(lg.height * s))), Image.LANCZOS)
    bg = (0, 0, 0, 0) if transparent else color_bg + (255,)
    canvas = Image.new("RGBA", (width, height), bg)
    canvas.alpha_composite(lg, ((width - lg.width) // 2, (height - lg.height) // 2))
    canvas.save(out)
    return canvas.size


if __name__ == "__main__":
    print("clover", clover())
    print("pattern", phoenix_pattern())
    print("logo 702x180", sized_logo(702, 180, 140, "logo_702x180_white.png", transparent=False))
    print("logo 702x180 alpha", sized_logo(702, 180, 140, "logo_702x180_transparent.png", transparent=True))
