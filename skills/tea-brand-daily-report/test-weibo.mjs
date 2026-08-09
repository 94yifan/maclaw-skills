import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();

await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 });
await page.waitForTimeout(6000);

const content = await page.evaluate(() => {
  const textEl = document.querySelector('.weibo-text');
  const timeEl = document.querySelector('span.time');
  const cards = document.querySelectorAll('.card');
  return {
    text: textEl ? textEl.innerText.slice(0, 100) : 'NOT FOUND',
    time: timeEl ? timeEl.innerText : 'NOT FOUND',
    cardCount: cards.length,
    url: document.location.href,
    loginStatus: document.querySelector('.nick')?.innerText || 'not logged in'
  };
});

console.log(JSON.stringify(content, null, 2));
await browser.close();
