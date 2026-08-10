#!/usr/bin/env python3
"""
WeChat Article Reader with GLM Vision API
==========================================
Reads WeChat public account articles (mp.weixin.qq.com) using Playwright,
extracts HTML text and analyzes embedded images via GLM-4V vision model.

Usage:
    /tmp/wechat_venv/bin/python3 wechat_glm_reader.py <article_url> \\
        [--model glm-4v-plus] [--max-images 10] [--json] [--skip-glm]

Output:
    article.json in output dir with title/author/date/text_content/images[]
    Each image record includes image_url, local_path, and ocr_text (if GLM used)

Environment:
    Requests GLM API key at ~/.openclaw/config/glm.json
    Uses Playwright (chromium) for browser rendering
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime

GLM_API_KEY_PATH = os.path.expanduser("~/.openclaw/config/glm.json")


# ─── Config ────────────────────────────────────────────────────────────────

def load_glm_key():
    """Load GLM API key from config file."""
    try:
        with open(GLM_API_KEY_PATH) as f:
            return json.load(f)["api_key"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"[ERROR] Cannot load GLM API key from {GLM_API_KEY_PATH}: {e}", file=sys.stderr)
        sys.exit(1)


GLM_API_KEY = load_glm_key()
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
DEFAULT_MODEL = "glm-4v"
OUTPUT_DIR = "/tmp/wechat_reader"

# ─── Image Analysis via GLM-4V ─────────────────────────────────────────────

def analyze_image_with_glm(image_path, model=DEFAULT_MODEL, retries=2):
    """
    Send an image to GLM-4V and get text description.
    Uses OpenAI-compatible API format.
    """
    from openai import OpenAI

    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".webp": "image/webp", ".gif": "image/gif"}
    mime = mime_map.get(ext, "image/png")
    data_url = f"data:{mime};base64,{img_data}"

    client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)

    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text":
                            "请仔细阅读这张图片中的所有文字内容，包括标题、小标题、正文、"
                            "数据、标签、图表标注等所有可见的文字信息。请完整输出，"
                            "不要省略。如果包含中英文，全部输出。最后给出这张图的核心信息总结。"}
                    ]
                }],
                max_tokens=2048,
                temperature=0.1,
            )
            return resp.choices[0].message.content

        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt
                print(f"  [WARN] GLM API call failed (attempt {attempt+1}): {e}", file=sys.stderr)
                print(f"  [WARN] Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"  [ERROR] GLM API call failed after {retries+1} attempts: {e}", file=sys.stderr)
                return f"[OCR FAILED: {str(e)}]"


# ─── Playwright Article Extraction ──────────────────────────────────────────

def extract_article(url, output_dir=OUTPUT_DIR):
    """
    Open WeChat article with Playwright, extract text, download images.
    Returns dict with article metadata and content.
    """
    from playwright.sync_api import sync_playwright

    os.makedirs(output_dir, exist_ok=True)
    slug = re.sub(r'[^a-zA-Z0-9_-]', '', url.split('/')[-1]) or "article"
    slug = slug[:50]

    result = {
        "url": url,
        "title": "",
        "article_source": "",
        "publish_date": "",
        "text_content": "",
        "images": [],
        "extracted_at": datetime.now().isoformat(),
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 430, "height": 932},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Mobile/15E148 MicroMessenger/8.0.47"
            )
        )
        page = context.new_page()

        print(f"[INFO] Navigating to: {url}", file=sys.stderr)
        page.goto(url, wait_until="networkidle", timeout=30000)

        try:
            page.wait_for_selector("#js_content", timeout=10000)
        except:
            print("[WARN] #js_content not found, trying fallback...", file=sys.stderr)

        # Scroll to trigger lazy loading
        print("[INFO] Scrolling to trigger image lazy loading...", file=sys.stderr)
        prev_height = 0
        for i in range(20):
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(0.3)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == prev_height and i > 3:
                break
            prev_height = new_height

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)

        # Extract metadata
        try:
            title_el = page.query_selector("#activity-name")
            if title_el:
                result["title"] = title_el.inner_text().strip()
        except:
            pass

        try:
            author_el = page.query_selector("#js_name")
            if author_el:
                result["article_source"] = author_el.inner_text().strip()
        except:
            pass

        try:
            date_text = page.evaluate("""() => {
                const el = document.querySelector('#publish_time');
                if (el) return el.innerText.trim();
                const els = document.querySelectorAll('em');
                for (const e of els) {
                    if (e.innerText.match(/\\d{4}/)) return e.innerText.trim();
                }
                return '';
            }""")
            result["publish_date"] = date_text or ""
        except:
            pass

        # Extract HTML text content
        try:
            text_content = page.evaluate("""() => {
                const content = document.getElementById('js_content');
                if (!content) return '';
                const clone = content.cloneNode(true);
                clone.querySelectorAll('img, script, style, svg').forEach(el => el.remove());
                return clone.innerText.trim();
            }""")
            result["text_content"] = text_content or ""
        except:
            pass

        # Get all image data-src URLs
        image_urls = page.evaluate("""() => {
            const content = document.getElementById('js_content');
            if (!content) return [];
            const imgs = content.querySelectorAll('img[data-src]');
            const urls = [];
            imgs.forEach((img, i) => {
                const src = img.getAttribute('data-src') || img.src;
                if (src && src.includes('mmbiz.qpic.cn')) {
                    urls.push({
                        index: i,
                        url: src,
                        alt: img.alt || '',
                        // Try currentSrc then data-src for the actual URL
                        width: img.width || img.naturalWidth,
                        height: img.height || img.naturalHeight
                    });
                }
            });
            return urls;
        }""")

        print(f"[INFO] Found {len(image_urls)} images in article", file=sys.stderr)

        # Download images
        for idx, img_info in enumerate(image_urls):
            img_url = img_info["url"]
            clean_url = img_url.split("#")[0]
            ext = ".jpg"
            if "fmt=png" in clean_url or ".png" in clean_url:
                ext = ".png"
            elif "fmt=jpeg" in clean_url or ".jpeg" in clean_url:
                ext = ".jpg"
            elif "fmt=gif" in clean_url:
                ext = ".gif"
            elif "fmt=webp" in clean_url:
                ext = ".webp"

            img_path = os.path.join(output_dir, f"img_{idx:03d}{ext}")
            print(f"  [IMG {idx+1}/{len(image_urls)}] Downloading...", file=sys.stderr)

            try:
                import requests as req
                resp = req.get(clean_url, timeout=30, headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
                })
                if resp.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(resp.content)

                    img_record = {
                        "index": idx,
                        "url": clean_url,
                        "local_path": img_path,
                        "size_bytes": len(resp.content),
                        "width": img_info.get("width", 0),
                        "height": img_info.get("height", 0),
                        "alt": img_info.get("alt", ""),
                    }
                    result["images"].append(img_record)
                else:
                    print(f"  [WARN] Download failed: HTTP {resp.status_code}", file=sys.stderr)
            except Exception as e:
                print(f"  [WARN] Download error: {e}", file=sys.stderr)

        browser.close()

    return result


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Read WeChat article with GLM vision")
    parser.add_argument("url", help="WeChat article URL (mp.weixin.qq.com)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"GLM model (default: {DEFAULT_MODEL})")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--max-images", type=int, default=0,
                        help="Max images to analyze with GLM (0 = all)")
    parser.add_argument("--skip-glm", action="store_true", help="Skip GLM analysis")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if "mp.weixin.qq.com" not in args.url:
        print("[ERROR] Not a valid WeChat article URL", file=sys.stderr)
        sys.exit(1)

    slug = re.sub(r'[^a-zA-Z0-9_-]', '', args.url.split('/')[-1])[:30]
    output_dir = os.path.join(args.output_dir, slug)
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Extract article
    print(f"[INFO] Step 1: Extracting article content...", file=sys.stderr)
    article = extract_article(args.url, output_dir=output_dir)

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Title: {article['title']}", file=sys.stderr)
    print(f"Source: {article['article_source']}", file=sys.stderr)
    print(f"Date: {article['publish_date']}", file=sys.stderr)
    print(f"Text length: {len(article['text_content'])} chars", file=sys.stderr)
    print(f"Images: {len(article['images'])}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # Step 2: Analyze images with GLM
    if not args.skip_glm and article["images"]:
        max_analyze = args.max_images if args.max_images > 0 else len(article["images"])
        print(f"[INFO] Step 2: Analyzing {max_analyze}/{len(article['images'])} "
              f"images with GLM {args.model}...", file=sys.stderr)

        for img in article["images"][:max_analyze]:
            print(f"\n  [{img['index']+1}/{max_analyze}] "
                  f"({img.get('width',0)}x{img.get('height',0)}, "
                  f"{img.get('size_bytes',0)//1024}KB)...", file=sys.stderr)
            ocr_text = analyze_image_with_glm(img["local_path"], model=args.model)
            img["ocr_text"] = ocr_text
            preview = ocr_text[:150].replace("\n", " ")
            print(f"  → {preview}...", file=sys.stderr)

        # Mark un-analyzed images
        for img in article["images"][max_analyze:]:
            img["ocr_text"] = "[SKIPPED]"

    # Step 3: Save result
    result_path = os.path.join(output_dir, "article.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] Result saved to: {result_path}", file=sys.stderr)

    # Output
    if args.json:
        print(json.dumps(article, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"标题: {article['title']}")
        print(f"公众号: {article['article_source']}")
        print(f"日期: {article['publish_date']}")
        print(f"\n--- 正文文本 ---")
        if article["text_content"]:
            print(article["text_content"])
        else:
            print("(无文本内容，全部为图片)")

        if article.get("images") and article["images"][0].get("ocr_text"):
            print(f"\n--- 图片文字分析 ({len(article['images'])} 张图) ---")
            for img in article["images"]:
                print(f"\n[图片 {img['index']+1}/{len(article['images'])}] "
                      f"{img.get('alt', '')} ({img.get('width',0)}x{img.get('height',0)})")
                if img.get("ocr_text") and img["ocr_text"] != "[SKIPPED]":
                    print(img["ocr_text"])
                elif img["ocr_text"] == "[SKIPPED]":
                    print("  (未分析)")
                else:
                    print("  (分析失败)")

        print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
