import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const ctx = browser.contexts()[0] || await browser.newContext();
const page = await ctx.newPage();
await page.setViewportSize({ width: 390, height: 844 });

// Test with 瑞幸咖啡
const uid = '6349791448';
const url = 'https://m.weibo.cn/u/' + uid;
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
await page.waitForTimeout(5000);

for (const y of [0, 600, 1200, 1800]) {
  await page.evaluate((Y) => window.scrollTo(0, Y), y);
  await page.waitForTimeout(2000);
}

const posts = await page.evaluate(() => {
  const results = [];
  const cards = document.querySelectorAll('.card');
  console.log('Cards found:', cards.length);
  for (const card of cards) {
    const timeEl = card.querySelector('span.time');
    const textEl = card.querySelector('.weibo-text');
    if (timeEl && textEl) {
      results.push({
        time: timeEl.innerText.trim(),
        text: textEl.innerText.trim().slice(0, 100)
      });
    }
  }
  return results;
});

console.log('Posts:', JSON.stringify(posts, null, 2));
await browser.close();
