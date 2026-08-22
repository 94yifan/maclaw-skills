import { chromium } from 'playwright-core';
import { writeFileSync, readFileSync } from 'fs';

const targets = [
  { name: 'Manner', uid: '6808111794' },
  { name: '树夏酸奶', uid: '7144806571' },
  { name: '挪瓦咖啡', uid: '7268463229' },
];

function cleanHtml(html) {
  return (html || '').replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/\n{3,}/g, '\n\n').trim();
}

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();

await page.goto('https://m.weibo.cn/u/6808111794', { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
await new Promise(r => setTimeout(r, 4000));

for (const t of targets) {
  const url = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${t.uid}&containerid=107603${t.uid}`;
  const r = await page.evaluate(async (fetchUrl) => {
    try {
      const resp = await window.fetch(fetchUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const data = await resp.json();
      const cards = data?.data?.cards || [];
      const mb = cards.filter(c => c.mblog).map(c => c.mblog);
      return { ok: data.ok, msg: data.msg || '', total: data?.data?.cardlistInfo?.total, count: mb.length,
        first: mb.slice(0,3).map(x => ({ created: x.created_at, text: (x.text||'').slice(0,60) })) };
    } catch(e) { return { err: e.message }; }
  }, url);
  console.log(t.name, JSON.stringify(r, null, 1));
  await new Promise(r => setTimeout(r, 6000));
}
await browser.close();
