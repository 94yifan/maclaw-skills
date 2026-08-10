import { chromium } from 'playwright';

const CDP_URL = 'http://127.0.0.1:9333';
const browser = await chromium.connectOverCDP(CDP_URL);
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();

await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'networkidle', timeout: 20000 });
await page.waitForTimeout(3000);

// Try different selectors
const result = await page.evaluate(() => {
  // Check various possible selectors
  const selectors = [
    '[node-type="feed_list_content"]',
    '.WB_feed .WB_card',
    '.WB_feed_type',
    '[action-type="feed_list_item"]',
    '.content',
    '[class*="content"]',
  ];
  
  let output = {};
  for (const sel of selectors) {
    const els = document.querySelectorAll(sel);
    if (els.length > 0) {
      output[sel] = els.length + ' items, first: ' + (els[0].innerText?.slice(0, 100) || 'no text');
    }
  }
  
  // Get body text
  output.bodyText = document.body.innerText.slice(0, 500);
  output.url = window.location.href;
  
  return output;
});

console.log(JSON.stringify(result, null, 2));
await browser.close();
