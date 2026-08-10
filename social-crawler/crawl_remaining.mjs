import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const remaining = [
  { name: 'Manner', uid: '6808111794' },
  { name: '茉酸奶', uid: '5188894132' },
  { name: '树夏酸奶', uid: '7144806571' },
];

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  const nd = ds => { const p=ds.split('-'); return (p.length===2 ? String(parseInt(p[0])).padStart(2,'0')+'-'+String(parseInt(p[1])).padStart(2,'0') : ds); };
  return nd(dateStr) === y || nd(dateStr) === t;
}

function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) return false;
  if (/加入群|粉丝群\s*\d/.test(text)) return false;
  return true;
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

const browser = await chromium.connectOverCDP('http://localhost:9333');
let page;
try {
  const ctx = browser.contexts()[0];
  page = await ctx.newPage();
} catch(e) {
  page = await browser.newPage();
}
await page.setViewportSize({ width: 390, height: 844 });

const results = {};
for (let i = 0; i < remaining.length; i++) {
  const b = remaining[i];
  process.stdout.write('[' + (i+1) + '/3] ' + b.name + '... ');
  try {
    const url = 'https://m.weibo.cn/u/' + b.uid;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(5000);
    for (const y of [0, 600, 1200, 1800]) {
      await page.evaluate((Y) => window.scrollTo(0, Y), y);
      await page.waitForTimeout(2000);
    }
    const posts = await page.evaluate(() => {
      const results = [];
      const cards = document.querySelectorAll('.card');
      for (const card of cards) {
        const timeEl = card.querySelector('span.time');
        const textEl = card.querySelector('.weibo-text');
        if (!timeEl || !textEl) continue;
        const timeStr = timeEl.innerText.trim();
        const text = textEl.innerText.trim().slice(0, 350);
        if (text.length > 10) results.push({ date: timeStr.split(' ')[0], text });
      }
      return results;
    });
    const filtered = posts.filter(p => isTargetDay(p.date)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条 (新' + cats['新品'].length + ' IP' + cats['IP'].length + ' 营' + cats['营销'].length + ')');
  } catch (e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + e.message.slice(0, 50));
  }
  await page.waitForTimeout(5000);
}
await browser.close();
const now = new Date();
const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
writeFileSync('/tmp/remaining_' + dateStr + '.json', JSON.stringify({ date: dateStr, results }, null, 2));
console.log('=== 剩余3品牌数据已写入 /tmp/remaining_' + dateStr + '.json ===');
