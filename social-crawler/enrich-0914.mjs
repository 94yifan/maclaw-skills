import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync } from 'fs';

const raw = JSON.parse(readFileSync('/tmp/tea-raw-2026-09-14.json', 'utf8'));

const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
const ctx = browser.contexts()[0] || await browser.newContext();
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();

function cleanHtml(html) {
  return (html || '').replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '')
    .replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>')
    .replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&nbsp;/g,' ')
    .replace(/\n{3,}/g,'\n\n').trim();
}

for (const brand of raw.brands) {
  const truncated = (brand.items || []).filter(it => it.t.includes('全文'));
  if (!truncated.length) continue;
  // fetch all posts with ids
  const cid = '107603' + brand.uid;
  let all = [];
  for (let p = 1; p <= 2; p++) {
    const url = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${brand.uid}&containerid=${cid}` + (p>1?`&page=${p}`:'');
    const r = await page.evaluate(async (u) => {
      const resp = await window.fetch(u, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const d = await resp.json();
      return (d?.data?.cards||[]).filter(c=>c.mblog).map(c=>({id:c.mblog.id, created:c.mblog.created_at, isLong:c.mblog.isLongText, txt:c.mblog.text}));
    }, url).catch(()=>[]);
    all.push(...r);
    await new Promise(r2=>setTimeout(r2, 900));
  }
  for (const it of truncated) {
    const match = all.find(a => a.created === it.d);
    if (!match) { console.log('no match', brand.brand, it.d); continue; }
    const ext = await page.evaluate(async (id) => {
      const resp = await window.fetch(`https://m.weibo.cn/statuses/extend?id=${id}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const d = await resp.json();
      return d?.data?.longTextContent || '';
    }, match.id).catch(()=> '');
    if (ext) {
      it.t = cleanHtml(ext);
      console.log('enriched', brand.brand, it.d, it.t.length);
    } else {
      console.log('extend empty', brand.brand, it.d);
    }
    await new Promise(r2=>setTimeout(r2, 800));
  }
  await new Promise(r2=>setTimeout(r2, 2000));
}

await browser.close();
writeFileSync('/tmp/tea-raw-2026-09-14.json', JSON.stringify(raw, null, 2));
console.log('DONE');
