#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曼拾图片排版流水线 · 渲染 + 自动适配。

用法:
  # 直接渲染现成 HTML
  python3 render_page.py --html page.html --png out.png --width 2480 --height 3508
  # 自动定缩放：给一个暴露 build(K)->html_path 的模块
  python3 render_page.py --builder make_page:build --png out.png --fit 0.90 1.05
"""
import argparse, importlib, os, subprocess, sys
import numpy as np
from PIL import Image

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def render(html_path, out_png, w, h, bg="ffffffff"):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-sandbox", "--force-device-scale-factor=1",
                    f"--default-background-color={bg}", f"--window-size={w},{h}",
                    f"--screenshot={out_png}", f"file://{html_path}"], capture_output=True, timeout=240)
    return out_png


def measure(png, thresh=245):
    """返回 (正文底部, 页脚顶部, 间隔) —— 数字量测，不靠眼睛"""
    a = np.array(Image.open(png).convert("L")).astype(int)
    r = (a < thresh).sum(1)
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


def check(png, height, min_gap=60, wide=1500):
    """校验：未被裁切 + 通栏块不压页脚"""
    a = np.array(Image.open(png).convert("L")).astype(int)
    r = (a < 245).sum(1)
    rows = np.where(r > 0)[0]
    clipped = bool((a[-30:] < 245).sum() > 0)
    wide_bottom = int(np.where(r > wide)[0].max()) if (r > wide).any() else -1
    cb, ft, gap = measure(png)
    return {"clipped": clipped or (rows.max() >= height - 2), "wide_bottom": wide_bottom,
            "content_bottom": cb, "footer_top": ft, "gap": gap, "gap_ok": gap >= min_gap}


def fit(builder, png, w, h, lo, hi, tol=0.01, min_gap=60):
    mod_name, fn_name = builder.split(":")
    fn = getattr(importlib.import_module(mod_name), fn_name)
    best = None
    while hi - lo > tol:
        mid = round((lo + hi) / 2, 3)
        html = fn(mid)
        probe = png.replace(".png", "_probe.png")
        render(html, probe, w, h)
        m = check(probe, h, min_gap=min_gap)
        print(f"  K {mid}: content {m['content_bottom']} footer {m['footer_top']} gap {m['gap']} "
              f"wide_bottom {m['wide_bottom']} clipped {m['clipped']}", flush=True)
        if m["clipped"] or not m["gap_ok"] or m["wide_bottom"] >= m["footer_top"]:
            hi = mid
        else:
            lo = mid
            best = mid
    return best or lo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html"); ap.add_argument("--builder"); ap.add_argument("--png", required=True)
    ap.add_argument("--width", type=int, default=2480); ap.add_argument("--height", type=int, default=3508)
    ap.add_argument("--fit", nargs=2, type=float, metavar=("LO", "HI"))
    a = ap.parse_args()
    if a.fit:
        k = fit(a.builder, a.png, a.width, a.height, a.fit[0], a.fit[1])
        print("chosen K", k)
        render(getattr(importlib.import_module(a.builder.split(":")[0]), a.builder.split(":")[1])(k),
               a.png, a.width, a.height)
    else:
        render(a.html, a.png, a.width, a.height)
    print("check:", check(a.png, a.height))
