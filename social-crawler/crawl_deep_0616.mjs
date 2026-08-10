import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: '1741514817' },
  { name: '茶百道', uid: '6502206666' },
  { name: '奈雪的茶', uid: '5884674413' },
  { name: 'CoCo', uid: '2030619861' },
  { name: '爷爷不泡茶', uid: '7769072120' },
  { name: '沪上阿姨', uid: '3921865344' },
  { name: '乐乐茶', uid: '6253473981' },
  { name: '皮爷咖啡', uid: '6360528436' },
  { name: 'M Stand', uid: '6345199298' },
  { name: 'Manner', uid: '6808111794' },
  { name: '茉酸奶', uid: '5188894132' },
  { name: '树夏酸奶', uid: '7144806571' },
];

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  if (/分[钟]?前|小时前|刚刚/.test(dateStr)) return true;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const fmt = d => String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  return dateStr === fmt(yesterday) || dateStr === fmt(today);
}

function cleanText(t) {
  if (!t) return '';
  return t.replace(/^展开全文|^收起全文/g, '').replace(/\s+/g, ' ').trim().slice(0, 500);
}

console.log('=== Connecting to CDP 9333 ===');
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const page = await browser.newPage();
await page.setViewportSize({ width: 390, height: 844 });

const allData = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write(`[${i+1}/19] ${b.name}... `);

  const url = `https://m.weibo.cn/u/${b.uid}`;
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(4000);

    // Deep scroll - 30 times to ensure we get enough content
    for (let s = 0; s < 30; s++) {
      await page.evaluate(() => window.scrollBy(0, 400));
      await page.waitForTimeout(800);
    }
    await page.waitForTimeout(2000);

    // Method 1: card-based extraction
    const posts = await page.evaluate(() => {
      const results = [];
      const cards = document.querySelectorAll('.card');
      for (const card of cards) {
        const timeEl = card.querySelector('.time, span.time');
        const textEl = card.querySelector('.weibo-text');
        if (!timeEl) continue;
        const timeStr = (timeEl.innerText || timeEl.textContent || '').trim();
        const text = textEl ? (textEl.innerText || textEl.textContent || '').trim() : '';
        if (text.length > 15) {
          results.push({ date: timeStr.split(' ')[0], text: text.slice(0, 500) });
        }
      }
      return results;
    });

    // Method 2: look for all text blocks with time info
    const posts2 = await page.evaluate(() => {
      const results = [];
      const allText = document.body.innerText;
      // Split by MM-DD or hh:mm patterns that m.weibo.cn uses
      const blocks = allText.split(/\n(?=\d{1,2}-\d{1,2}\s|\d{1,2}月\d{1,2}日)/);
      for (const block of blocks) {
        const lines = block.split('\n').filter(l => l.trim());
        const timeLine = lines.find(l => /\d{1,2}-\d{1,2}/.test(l) || /\d{1,2}月\d{1,2}日/.test(l));
        if (!timeLine) continue;
        const content = lines.filter(l => !l.includes('评论') && !l.includes('赞') && l !== timeLine).join(' ').trim();
        if (content.length > 20) {
          results.push({ date: timeLine.replace(/\s.*$/, ''), text: content.slice(0, 500) });
        }
      }
      return results;
    });

    // Merge and deduplicate
    const merged = [...posts, ...posts2];
    const seen = new Set();
    const unique = [];
    for (const p of merged) {
      const key = p.text.slice(0, 100);
      if (seen.has(key)) continue;
      seen.add(key);
      unique.push(p);
    }

    const filtered = unique.filter(p => {
      if (!isTargetDay(p.date)) return false;
      const t = p.text;
      if (t.length < 15) return false;
      if (/抱歉.*不存在|暂无.*内容/.test(t)) return false;
      if (/粉丝群\s*\d/.test(t)) return false;
      return true;
    });

    // Text-dedup
    const finalPosts = [];
    const textCore = new Set();
    for (const p of filtered) {
      const core = p.text.replace(/#[^#]+#/g, '').replace(/@\S+/g, '').trim().slice(0, 60);
      if (textCore.has(core)) continue;
      textCore.add(core);
      finalPosts.push(p);
    }

    const cats = { '新品': [], 'IP': [], '营销': [] };
    finalPosts.forEach(p => {
      const t = p.text;
      const isIP = /联名|代言|×/.test(t) || /品牌大使|代言人/.test(t);
      const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t);
      const cat = isIP ? 'IP' : isNew ? '新品' : '营销';
      cats[cat].push(p);
    });

    allData[b.name] = cats;
    const total = finalPosts.length;
    const ns = cats['新品'].length;
    const ips = cats['IP'].length;
    const ms = cats['营销'].length;
    console.log(`${total}条 (新${ns} IP${ips} 营${ms})`);
    if (total > 0) {
      finalPosts.forEach(p => console.log(`  [${p.date}] ${cleanText(p.text).slice(0, 150)}`));
    }

  } catch (e) {
    allData[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log(`err: ${e.message.slice(0, 60)}`);
  }

  await page.waitForTimeout(5000);
}

await browser.close();

const dateStr = '2026-06-16';
const jsonPath = `/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_${dateStr}.json`;
writeFileSync(jsonPath, JSON.stringify({ date: dateStr, results: allData }, null, 2));
console.log(`\n=== Saved to ${jsonPath} ===`);
process.exit(0);
