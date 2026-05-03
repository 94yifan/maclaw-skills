#!/usr/bin/env python3
"""Scrape Weibo brand content via CDP WebSocket"""
import json
import time
import re
from websocket import create_connection

BRANDS = [
    ("瑞幸咖啡", "luckincoffee瑞幸咖啡", "6349791448"),
    ("库迪", "CottiCoffee库迪咖啡", "7791266545"),
    ("古茗", "古茗茶饮", "2809775704"),
    ("幸运咖", "幸运咖", "6519396553"),
    ("茉莉奶白", "茉莉奶白MollyTea", "7577524421"),
    ("霸王茶姬", "霸王茶姬CHAGEE", "5652018762"),
    ("喜茶", "喜茶", "2804387887"),
    ("星巴克", "星巴克中国", None),  # username-based
    ("茶百道", "茶百道ChaPanda", "6502206666"),
    ("奈雪的茶", "奈雪的茶", "5884674413"),
    ("CoCo", "CoCo都可官方", "2030619861"),
    ("爷爷不泡茶", "爷爷不泡茶官方微博", "7769072120"),
    ("沪上阿姨", "沪上阿姨", "3921865344"),
    ("乐乐茶", "楽楽茶LELECHA", "6253473981"),
    ("皮爷咖啡", "PeetsCoffee皮爷咖啡", "6360528436"),
    ("M Stand", "MStand", "6345199298"),
    ("Manner", "MANNER官微", "6808111794"),
    ("茉酸奶", "茉酸奶MOREYOGURT", "5188894132"),
    ("树夏酸奶", "树夏", "7144806571"),
]

def cdp_send(ws, method, params=None):
    msg_id = 1
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    ws.send(json.dumps(msg))
    resp = ws.recv()
    return json.loads(resp)

def get_page_id_for_brand(ws, brand_name):
    """Find the page ID for a brand's weibo page"""
    resp = cdp_send(ws, "Target.getTargets")
    ws.close()
    targets = resp.get("result", {}).get("targetInfos", [])
    for t in targets:
        if t.get("type") == "page" and brand_name in t.get("title", ""):
            return t.get("targetId")
    return None

def navigate_and_scrape(ws_url, page_id, url):
    """Navigate to URL and get rendered content"""
    ws = create_connection(ws_url)
    
    # First enable Page domain
    cdp_send(ws, "Page.enable")
    
    # Navigate
    cdp_send(ws, "Page.navigate", {"url": url})
    
    # Wait for content to load
    time.sleep(8)
    
    # Scroll to trigger lazy load
    for _ in range(5):
        cdp_send(ws, "Runtime.evaluate", {
            "expression": "window.scrollBy(0, 400);"
        })
        time.sleep(2)
    
    # Get content via DOM snapshot
    resp = cdp_send(ws, "Runtime.evaluate", {
        "expression": """
        (function() {
            var text = document.body.innerText;
            var lines = text.split('\\n').filter(function(l) { return l.trim().length > 0; });
            // Get last 100 lines (most recent posts)
            return lines.slice(-100).join('\\n');
        })()
        """
    })
    
    ws.close()
    
    result = resp.get("result", {}).get("result", {})
    if result.get("type") == "string":
        return result.get("value", "")
    return ""

def main():
    # First get page IDs
    ws_url_base = "ws://127.0.0.1:9333/devtools/page/"
    
    # Find all open tabs
    all_targets = []
    try:
        ws = create_connection("ws://127.0.0.1:9333/devtools/page/")
        resp = cdp_send(ws, "Target.getTargets")
        all_targets = resp.get("result", {}).get("targetInfos", [])
        ws.close()
    except:
        pass
    
    print(json.dumps(all_targets, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
