import { chromium } from 'playwright-core';
const b = await chromium.connectOverCDP('http://127.0.0.1:18800', { timeout: 60000 });
const ctx = b.contexts()[0] || await b.newContext();
const page = await ctx.newPage();
await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(e=>console.log('nav err', e.message));
await new Promise(r=>setTimeout(r,3000));
const res = await page.evaluate(async () => {
  const r = await fetch('https://m.weibo.cn/api/container/getIndex?type=uid&value=6349791448&containerid=1076036349791448', {credentials:'include', headers:{'X-Requested-With':'XMLHttpRequest'}});
  const t = await r.text();
  let d=null; try{d=JSON.parse(t)}catch(e){}
  return {status:r.status, ok:d?.ok, total:d?.data?.cardlistInfo?.total, n:(d?.data?.cards||[]).filter(c=>c.mblog).length, first:d?.data?.cards?.find(c=>c.mblog)?.mblog?.created_at, txt:(d?.data?.cards?.find(c=>c.mblog)?.mblog?.text||'').slice(0,80)};
});
console.log(JSON.stringify(res,null,1));
await page.close();
await b.close();
