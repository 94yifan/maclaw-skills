/**
 * 补全被截断的长微博正文（m.weibo.cn statuses/show API）
 */
import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync } from 'fs';

const PATH = '/tmp/tea-raw-2026-09-12.json';
const raw = JSON.parse(readFileSync(PATH, 'utf8'));

function cleanHtml(html) {
  return (html || '').replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/\n{3,}/g, '\n\n').trim();
}

const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
const ctx = browser.contexts()[0];
let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
if (!page) page = await ctx.newPage();
await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
await new Promise(r => setTimeout(r, 2500));

const need = raw.brands.filter(b => b.items && b.items.some(it => it.t.includes('全文')));
console.log('需补全品牌数:', need.length);

for (const b of need) {
  process.stdout.write(`[${b.brand}] `);
  const containerid = '107603' + b.uid;
  const metas = await page.evaluate(async ({ uid, containerid }) => {
    const out = [];
    for (let pg = 1; pg <= 2; pg++) {
      const url = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=${containerid}${pg > 1 ? '&page=' + pg : ''}`;
      try {
        const resp = await window.fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const d = await resp.json();
        const cards = (d?.data?.cards || []).filter(c => c.mblog);
        for (const c of cards) out.push({ id: c.mblog.id, created: c.mblog.created_at });
        if (!cards.length) break;
      } catch (e) { break; }
      await new Promise(r => setTimeout(r, 700));
    }
    return out;
  }, { uid: b.uid, containerid });

  const targets = b.items.filter(it => it.t.includes('全文'));
  const ids = [];
  for (const it of targets) {
    const m = metas.find(x => x.created === it.d) || metas.find(x => Math.abs(Date.parse(x.created) - Date.parse(it.d)) < 120000);
    if (m) ids.push(m.id);
  }
  if (!ids.length) { process.stdout.write('无匹配id\n'); continue; }

  const fulls = await page.evaluate(async ({ ids }) => {
    const res = {};
    for (const id of ids) {
      try {
        const r = await window.fetch('https://m.weibo.cn/statuses/show?id=' + id, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const j = await r.json();
        res[id] = (j && j.ok && j.data && j.data.text) ? j.data.text : '';
      } catch (e) { res[id] = ''; }
      await new Promise(r => setTimeout(r, 1200));
    }
    return res;
  }, { ids });

  let fixed = 0;
  for (const it of targets) {
    const m = metas.find(x => x.created === it.d) || metas.find(x => Math.abs(Date.parse(x.created) - Date.parse(it.d)) < 120000);
    if (!m) continue;
    const full = fulls[m.id];
    if (full) {
      const c = cleanHtml(full);
      if (c.length > it.t.length) { it.t = c; fixed++; }
    }
  }
  process.stdout.write(`补全${fixed}/${targets.length}条\n`);
  await new Promise(r => setTimeout(r, 5000 + Math.random() * 2000));
}

await browser.close();
writeFileSync(PATH, JSON.stringify(raw, null, 2));
console.log('=== 写回完成 ===', PATH);
