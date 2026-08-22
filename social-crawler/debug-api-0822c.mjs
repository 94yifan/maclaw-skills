import { chromium } from 'playwright-core';

const targets = [
  { name: 'Manner', uid: '6808111794' },
  { name: '树夏酸奶', uid: '7144806571' },
  { name: '挪瓦咖啡', uid: '7268463229' },
];

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();

for (const t of targets) {
  await page.goto('https://m.weibo.cn/u/' + t.uid, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(e => console.log('goto err', e.message.slice(0,50)));
  await new Promise(r => setTimeout(r, 4000));
  const info = await page.evaluate(() => {
    // find containerid in any script or data attribute
    const html = document.documentElement.innerHTML;
    const m = html.match(/containerid["']?\s*[:=]\s*["'](\d+)["']/g);
    const tabs = [...document.querySelectorAll('.tab, [class*="tab"]')].map(x => x.textContent.trim()).slice(0,8);
    return { url: location.href, title: document.title, tabs, containerMatches: m ? m.slice(0,5) : [] };
  });
  console.log(t.name, JSON.stringify(info, null, 1));
  await new Promise(r => setTimeout(r, 5000));
}
await browser.close();
