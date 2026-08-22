import { chromium } from 'playwright-core';

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
let page = (await ctx.pages()).find(p => p.url().includes('weibo.com'));
if (!page) page = await ctx.newPage();

// go to weibo.com user page first to be same-origin
await page.goto('https://weibo.com/u/6808111794', { waitUntil: 'domcontentloaded', timeout: 25000 }).catch(e => console.log('goto err', e.message.slice(0,50)));
await new Promise(r => setTimeout(r, 5000));

for (const t of targets) {
  const url = `https://weibo.com/ajax/statuses/mymblog?uid=${t.uid}&page=1&feature=0`;
  const r = await page.evaluate(async (fetchUrl) => {
    try {
      const resp = await window.fetch(fetchUrl, { credentials: 'include' });
      const data = await resp.json();
      const list = data?.data?.list || [];
      return { ok: data.ok, total: data?.data?.total, count: list.length,
        first: list.slice(0,3).map(x => ({ created: x.created_at, text: (x.text_raw || x.text || '').slice(0,70) })) };
    } catch(e) { return { err: e.message }; }
  }, url);
  console.log(t.name, JSON.stringify(r, null, 1));
  await new Promise(r => setTimeout(r, 6000));
}
await browser.close();
