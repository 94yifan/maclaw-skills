import { chromium } from 'playwright-core';
const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'networkidle', timeout: 20000 });
await page.waitForTimeout(2000);

// Get body text to understand what's rendering
const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
console.log('Body text:', bodyText);

// Check for any content blocks
const divCount = await page.evaluate(() => document.querySelectorAll('div').length);
const spanCount = await page.evaluate(() => document.querySelectorAll('span').length);
console.log('Divs:', divCount, 'Spans:', spanCount);

// Get all classes that appear more than 5 times
const classCounts = await page.evaluate(() => {
  const counts = {};
  document.querySelectorAll('[class]').forEach(el => {
    const cls = el.className;
    if (cls && typeof cls === 'string') {
      counts[cls] = (counts[cls] || 0) + 1;
    }
  });
  return Object.entries(counts).filter(([,c]) => c > 3).slice(0, 10);
});
console.log('Top classes:', JSON.stringify(classCounts));

await browser.close();
