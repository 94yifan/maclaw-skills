import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();

await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
await new Promise(r => setTimeout(r, 3000));
console.log('URL now:', page.url());

// raw fetch test
const url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=6349791448&containerid=1076036349791448';
const result = await page.evaluate(async (fetchUrl) => {
  try {
    const resp = await window.fetch(fetchUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    const data = await resp.json();
    return { status: resp.status, ok: data.ok, msg: data.msg || '', keys: data.data ? Object.keys(data.data) : [], cardCount: data.data?.cards?.length || 0, cardsSample: (data.data?.cards || []).slice(0, 3).map(c => ({ t: c.card_type, hasMblog: !!c.mblog, hasGroup: !!c.card_group, title: c.title?.text || '' })) };
  } catch(e) {
    return { err: e.message };
  }
}, url);
console.log(JSON.stringify(result, null, 2));
await browser.close();
