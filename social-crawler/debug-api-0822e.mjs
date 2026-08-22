import { chromium } from 'playwright-core';

const targets = [
  { name: 'Manner', uid: '6808111794' },
  { name: '树夏酸奶', uid: '7144806571' },
  { name: '挪瓦咖啡', uid: '7268463229' },
  { name: '瑞幸咖啡', uid: '6349791448' }, // control
];

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();

for (const t of targets) {
  await page.goto('https://m.weibo.cn/u/' + t.uid, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(e => console.log('goto err', e.message.slice(0,50)));
  await new Promise(r => setTimeout(r, 4000));
  const info = await page.evaluate(() => {
    // look for __INITIAL_STATE__ or config with containerid
    const scripts = [...document.querySelectorAll('script')].map(s => s.textContent || '');
    let found = null;
    for (const s of scripts) {
      const m = s.match(/"containerid":"(\d+)"/);
      if (m) { found = m[1]; break; }
    }
    const bodyText = (document.body.innerText || '').slice(0, 200);
    return { url: location.href, foundContainer: found, bodyText };
  });
  console.log(t.name, JSON.stringify(info));
  await new Promise(r => setTimeout(r, 5000));
}
await browser.close();
