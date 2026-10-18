import { chromium } from 'playwright-core';
const list = [['Manner','6808111794'],['树夏酸奶','7144806571'],['挪瓦咖啡','7268463229']];
const b = await chromium.connectOverCDP('http://127.0.0.1:9333', { timeout: 20000 });
console.log('connected');
const ctx = b.contexts()[0];
const pages = await ctx.pages();
let page = pages.find(p=>p.url().includes('m.weibo.cn/u/'));
if (!page) { page = await ctx.newPage(); await page.goto('https://m.weibo.cn/', { waitUntil:'domcontentloaded', timeout:20000 }).catch(e=>console.log('goto err',e.message)); }
console.log('page:', page.url());
for (const [n,uid] of list) {
  const url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid+'&containerid=107603'+uid;
  let r;
  try {
    r = await page.evaluate(async(u)=>{ const x=await fetch(u,{credentials:'include'}); const t=await x.text(); let j=null; try{j=JSON.parse(t)}catch(e){}; return {s:x.status,len:t.length,ok:j&&j.ok, cards:(j&&j.data&&j.data.cards)?j.data.cards.length:null, total:(j&&j.data&&j.data.cardlistInfo)?j.data.cardlistInfo.total:null, head:t.slice(0,120)}; }, url);
  } catch(e) { r = {err: e.message}; }
  console.log(n, JSON.stringify(r));
  await new Promise(r=>setTimeout(r,6000));
}
process.exit(0);
