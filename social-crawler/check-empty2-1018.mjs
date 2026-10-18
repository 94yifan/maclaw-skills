import { chromium } from 'playwright-core';
const list = [['Manner','6808111794'],['树夏酸奶','7144806571'],['挪瓦咖啡','7268463229']];
const b = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = b.contexts()[0];
const pages = await ctx.pages();
const page = pages.find(p=>p.url().includes('m.weibo.cn')) || pages[0];
console.log('using page:', page.url());
for (const [n,uid] of list) {
  const url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid+'&containerid=107603'+uid;
  const r = await page.evaluate(async(u)=>{ try{ const x=await fetch(u,{credentials:'include',headers:{'X-Requested-With':'XMLHttpRequest'}}); const t=await x.text(); let j=null; try{j=JSON.parse(t)}catch(e){}; return {s:x.status,len:t.length,ok:j&&j.ok, cards:(j&&j.data&&j.data.cards)?j.data.cards.length:null, head:t.slice(0,150)};}catch(e){return {err:e.message}} }, url);
  console.log(n, JSON.stringify(r));
  await new Promise(r=>setTimeout(r,6000));
}
