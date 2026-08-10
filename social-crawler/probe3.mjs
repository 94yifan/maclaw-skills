import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://localhost:9333');
const p = await b.newPage();

// Try mobile.weibo.cn which is lighter
await p.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
await p.waitForTimeout(4000);
const txt = await p.evaluate(() => document.body.innerText.slice(0, 500));
console.log('Mobile:', txt.replace(/\n/g,' ').slice(0,300));

// Also try the API way
await p.goto('https://weibo.com/ajax/profile/info?uid=6349791448', { waitUntil: 'domcontentloaded', timeout: 10000 });
await p.waitForTimeout(2000);
const apiTxt = await p.evaluate(() => document.body.innerText.slice(0, 300));
console.log('API:', apiTxt.slice(0,200));

await b.close();
