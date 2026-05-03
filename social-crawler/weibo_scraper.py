#!/usr/bin/env python3
"""
Scrape Weibo brand content using OpenClaw's managed Chrome (port 18800).
Each brand is loaded fresh, JS extracts posts, then we move to next brand.
"""
import json
import subprocess
import time
import os

BRANDS = [
    ("瑞幸咖啡", "https://weibo.com/u/6349791448"),
    ("库迪", "https://weibo.com/u/7791266545"),
    ("古茗", "https://weibo.com/u/2809775704"),
    ("茉莉奶白", "https://weibo.com/u/7577524421"),
    ("霸王茶姬", "https://weibo.com/u/5652018762"),
    ("喜茶", "https://weibo.com/u/2804387887"),
    ("星巴克", "https://weibo.com/starbucks"),
    ("茶百道", "https://weibo.com/u/6502206666"),
    ("奈雪的茶", "https://weibo.com/u/5884674413"),
    ("CoCo", "https://weibo.com/u/2030619861"),
    ("爷爷不泡茶", "https://weibo.com/u/7769072120"),
    ("沪上阿姨", "https://weibo.com/u/3921865344"),
    ("乐乐茶", "https://weibo.com/u/6253473981"),
    ("皮爷咖啡", "https://weibo.com/u/6360528436"),
    ("M Stand", "https://weibo.com/u/6345199298"),
    ("Manner", "https://weibo.com/u/6808111794"),
    ("茉酸奶", "https://weibo.com/u/5188894132"),
    ("树夏酸奶", "https://weibo.com/u/7144806571"),
]

EXTRACTOR = """() => {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const scroll = async () => {
    for (let i = 0; i < 5; i++) {
      window.scrollBy(0, 500);
      await delay(300);
    }
    window.scrollTo(0, 0);
  };
  await scroll();
  await delay(1000);
  
  // Find all post containers - try multiple selectors
  let posts = [];
  const containers = document.querySelectorAll('[class*="_content_"], [class*="item_"]');
  
  // Try to get all text content blocks
  const allContent = [];
  const seen = new Set();
  
  // Look for the main feed area
  const feedArea = document.querySelector('[class*="woo"]') || document.body;
  const paragraphs = feedArea.querySelectorAll('p, div[style], span');
  
  // Try scrolling approach - get all text visible after scrolling
  const results = {
    title: document.title,
    url: window.location.href,
    bodyText: document.body.innerText.slice(0, 8000),
    html: document.body.innerHTML.slice(0, 50000)
  };
  
  return JSON.stringify(results);
}"""

def get_tab_id():
    """Get the tab ID for the OpenClaw browser."""
    result = subprocess.run(
        ["curl", "-s", "http://127.0.0.1:18800/json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        for tab in data:
            if tab.get("type") == "page" and "weibo" in tab.get("url", ""):
                return tab["id"]
        if data:
            return data[0]["id"]
    except:
        pass
    return None

def navigate_and_extract(tab_id, url, brand_name):
    """Navigate to URL and extract content via CDP."""
    # Use browser tool to navigate
    import requests
    
    # First navigate
    ws_url = f"ws://127.0.0.1:18800/devtools/page/{tab_id}"
    from websocket import create_connection
    
    def send_cmd(ws, method, params=None):
        ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        return json.loads(ws.recv())
    
    try:
        ws = create_connection(ws_url)
        # Navigate
        send_cmd(ws, "Page.navigate", {"url": url})
        time.sleep(5)  # Wait for page load
        
        # Scroll and get content
        send_cmd(ws, "Runtime.evaluate", {
            "expression": """
            (async () => {
              for(let i=0; i<5; i++) { window.scrollBy(0,400); await new Promise(r=>setTimeout(r,400)); }
              window.scrollTo(0,0);
              await new Promise(r=>setTimeout(r,1000));
              return document.body.innerText.slice(0, 8000);
            })()
            """,
            "awaitPromise": True
        })
        
        resp = send_cmd(ws, "Runtime.evaluate", {
            "expression": "document.body.innerText.slice(0, 8000)"
        })
        ws.close()
        
        text = resp.get("result", {}).get("value", "") if resp else ""
        return text
    except Exception as e:
        return f"Error: {e}"

# For now, use the browser tool API
def main():
    # Get tab ID
    tab_id = get_tab_id()
    print(f"Tab ID: {tab_id}")
    
    for brand_name, url in BRANDS:
        print(f"\\n=== Scraping {brand_name}: {url} ===")
        text = navigate_and_extract(tab_id, url, brand_name)
        print(text[:500])
        time.sleep(2)

if __name__ == "__main__":
    main()
