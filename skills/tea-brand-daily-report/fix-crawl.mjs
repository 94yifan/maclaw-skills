import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const ctx = browser.contexts()[0];
const allPages = ctx.pages();

// 找一个已登录的微博页面（非captcha）
let loginPage = null;
for (const p of allPages) {
  const url = p.url();
  if (url.includes('weibo.cn/u/') && !url.includes('captcha')) {
    loginPage = p;
    break;
  }
}

if (!loginPage) {
  // 都没登录，只能新建
  loginPage = await ctx.newPage();
  await loginPage.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await loginPage.waitForTimeout(6000);
}

// 测试抓取瑞幸
await loginPage.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 });
await loginPage.waitForTimeout(6000);

const posts = await loginPage.evaluate(() => {
  const cards = document.querySelectorAll('.card');
  const results = [];
  for (const card of cards) {
    const timeEl = card.querySelector('span.time');
    const textEl = card.querySelector('.weibo-text');
    if (!timeEl || !textEl) continue;
    const timeStr = timeEl.innerText.trim();
    const text = textEl.innerText.trim().slice(0, 350);
    if (text.length > 10) {
      results.push({ date: timeStr.split(' ')[0], time: timeStr.split(' ')[1] || '', text });
    }
  }
  return results;
});

console.log('Posts found:', posts.length);
posts.forEach((p, i) => console.log(`  ${i+1}. [${p.date} ${p.time}] ${p.text.slice(0,80)}`));

await browser.close();
