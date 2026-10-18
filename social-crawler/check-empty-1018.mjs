import { chromium } from 'playwright-core';
const list = [['Manner','6808111794'],['树夏酸奶','7144806571'],['挪瓦咖啡','7268463229'],['古茗','2809775704']];
const b = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
for (const [n,uid] of list) {
  await page.goto('https://m.weibo.cn/u/'+uid, { waitUntil:'domcontentloaded', timeout:25000 }).catch(()=>{});
  await new Promise(r=>setTimeout(r,2000));
  const title = await page.title().catch(()=>'');
  const url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid+'&containerid=107603'+uid;
  const r = await page.evaluate(async(u)=>{ const x=await fetch(u,{credentials:'include'}); const t=await x.text(); return {s:x.status,len:t.length,head:t.slice(0,200)}; }, url);
  console.log(n, '| title:', title, '| status', r.s, 'len', r.len, '|', r.head.replace(/\n/g,' '));
  await new Promise(r=>setTimeout(r,5000));
}
await page.close().catch(()=>{});
