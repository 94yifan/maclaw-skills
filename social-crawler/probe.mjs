import { chromium } from 'playwright-core';
const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();

// Go to luckin page
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
// Wait for dynamic content
await page.waitForTimeout(5000);

// Scroll to load feed
await page.evaluate(() => window.scrollTo(0, 300));
await page.waitForTimeout(2000);

// Try to find ANY text content that looks like posts
const allContent = await page.evaluate(() => {
  // Get all text nodes near divs
  const result = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  let node;
  while (node = walker.nextNode()) {
    const tag = node.tagName;
    if (tag === 'DIV' || tag === 'ARTICLE') {
      const text = node.innerText || '';
      if (text.length > 50 && text.length < 500 && !text.includes('登录') && !text.includes('注册') && !text.includes('帮助中心')) {
        result.push({ tag, text: text.slice(0,200), id: node.id, class: node.className.slice(0,80) });
      }
    }
  }
  return result.slice(0, 8);
});

console.log('Found content blocks:', JSON.stringify(allContent, null, 2));

// Check specific IDs that might contain feed
const ids = ['pl_feedlist_index', 'plc_main', 'plc_frame', 'feedlist', 'feed_list', 'module_show'];
for (const id of ids) {
  const el = document.getElementById(id);
  if (el) console.log('Found ID:', id, el.innerText.slice(0,100));
}

// Check for any element containing '转发' or '评论' which would indicate post content
const postIndicators = await page.evaluate(() => {
  const els = document.querySelectorAll('*');
  let found = [];
  for (const el of els) {
    if (el.children.length === 0) continue; // skip leaf nodes
    const text = el.innerText || '';
    if ((text.includes('转发') || text.includes('评论') || text.includes('赞')) && text.length > 100 && text.length < 400) {
      found.push({ tag: el.tagName, id: el.id, cls: el.className.slice(0,60), text: text.slice(0,150) });
    }
  }
  return found.slice(0, 5);
});
console.log('Post indicators:', JSON.stringify(postIndicators, null, 2));

await browser.close();
