import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' }, { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' }, { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' }, { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' }, { name: '星巴克', uid: 'starbucks' },
  { name: '茶百道', uid: '6502206666' }, { name: '奈雪的茶', uid: '5884674413' },
  { name: 'CoCo', uid: '2030619861' }, { name: '爷爷不泡茶', uid: '7769072120' },
  { name: '沪上阿姨', uid: '3921865344' }, { name: '乐乐茶', uid: '6253473981' },
  { name: '皮爷咖啡', uid: '6360528436' }, { name: 'M Stand', uid: '6345199298' },
  { name: 'Manner', uid: '6808111794' }, { name: '茉酸奶', uid: '5188894132' },
  { name: '树夏酸奶', uid: '7144806571' },
];

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const fmt = d => String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  const nd = ds => {
    const p = ds.split(/[-/.]/);
    if (p.length < 2) return ds;
    return String(parseInt(p[0])).padStart(2,'0') + '-' + String(parseInt(p[1])).padStart(2,'0');
  };
  return nd(dateStr) === fmt(yesterday) || nd(dateStr) === fmt(today);
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

console.log('=== Connecting to Chrome via CDP port 9333 ===');
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0] || await browser.newContext();
const page = await ctx.newPage();
await page.setViewportSize({ width: 390, height: 844 });

const allResults = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write(`[${i+1}/19] ${b.name}... `);

  const url = b.uid === 'starbucks'
    ? 'https://m.weibo.cn/u/1802303610'
    : `https://m.weibo.cn/u/${b.uid}`;

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(4000);

    // Deep scroll: scroll 25 times to load more cards
    for (let s = 0; s < 25; s++) {
      await page.evaluate(() => window.scrollBy(0, 400));
      await page.waitForTimeout(1200);
    }

    // Wait a bit for lazy images
    await page.waitForTimeout(2000);

    const posts = await page.evaluate(() => {
      const results = [];
      const cards = document.querySelectorAll('.card, .card-wrap, .weibo-card');
      for (const card of cards) {
        const timeEl = card.querySelector('.time, .weibo-time, .card-time');
        const textEl = card.querySelector('.weibo-text, .card-text, .weibo-main, .content');
        if (!timeEl || !textEl) continue;
        const timeStr = (timeEl.innerText || timeEl.textContent || '').trim();
        const text = (textEl.innerText || textEl.textContent || '').trim().slice(0, 500);
        if (text.length > 10) {
          results.push({ date: timeStr.split(' ')[0], text });
        }
      }
      return results;
    });

    // Also try grabbing all visible weibo-item or similar structures
    const post2 = await page.evaluate(() => {
      const r = [];
      const allDivs = document.querySelectorAll('div[class*="card"], div[class*="weibo"], div[class*="item"]');
      for (const d of allDivs) {
        const txt = (d.innerText || '').trim();
        if (txt.length < 20) continue;
        const tm = d.querySelector('.time, span[class*="time"]');
        const dateStr = tm ? (tm.innerText || tm.textContent || '').trim().split(' ')[0] : '';
        if (dateStr) {
          r.push({ date: dateStr, text: txt.slice(0, 500) });
        }
      }
      return r;
    });

    // Merge both methods
    const seen = new Set();
    const all = [...posts, ...post2].filter(p => {
      const key = p.date + '|' + p.text.slice(0, 80);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    const filtered = all.filter(p => {
      if (!isTargetDay(p.date)) return false;
      const t = p.text;
      if (t.length < 15) return false;
      if (/抱歉.*不存在|暂无.*内容/.test(t)) return false;
      if (/粉丝群\s*\d/.test(t)) return false;
      return true;
    });

    // Deduplicate by content similarity
    const finalPosts = [];
    const textSeen = new Set();
    for (const p of filtered) {
      const core = p.text.replace(/#[^#]+#/g, '').replace(/@\S+/g, '').trim().slice(0, 60);
      if (textSeen.has(core)) continue;
      textSeen.add(core);
      finalPosts.push(p);
    }

    const cats = { '新品': [], 'IP': [], '营销': [] };
    finalPosts.forEach(p => cats[classify(p.text)].push({ text: p.text, date: p.date }));
    allResults[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(`${total}条 (新${cats['新品'].length} IP${cats['IP'].length} 营${cats['营销'].length})`);
    finalPosts.forEach(p => console.log(`  [${p.date}] ${p.text.slice(0, 120)}`));

  } catch (e) {
    allResults[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log(`err: ${e.message.slice(0, 50)}`);
  }

  await page.waitForTimeout(5000);
}

await browser.close();

// Write raw JSON
const now = new Date();
const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
const jsonPath = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.json';
writeFileSync(jsonPath, JSON.stringify({ date: dateStr, results: allResults }, null, 2));
console.log(`\n=== Raw JSON saved to ${jsonPath} ===`);
