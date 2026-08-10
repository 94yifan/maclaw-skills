import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9333');
const p = await b.newPage();
await p.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
await p.waitForTimeout(5000);
await p.evaluate(() => window.scrollTo(0, 500));
await p.waitForTimeout(2000);

// Check every div that has meaningful text
const divs = await p.evaluate(() => {
  const all = document.querySelectorAll('div');
  let result = [];
  for (const d of all) {
    const t = d.innerText || '';
    if (t.length > 80 && t.length < 600 && !t.includes('登录') && !t.includes('注册') && !t.includes('帮助') && !t.includes('无障碍')) {
      result.push({ cls: d.className.slice(0,60), id: d.id, text: t.replace(/\n/g,' ').slice(0,180) });
    }
  }
  return result;
});
console.log('Divs with content:', JSON.stringify(divs.slice(0,6), null, 2));
await b.close();
