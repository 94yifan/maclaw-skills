import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const CDP_URL = 'http://127.0.0.1:9333';
const OUTPUT = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-05-14.md';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks' },
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

function isTargetDay(timeStr) {
  const fullMatch = timeStr.match(/^(\d+)-(\d+)\s+\d+:\d+$/);
  if (fullMatch) {
    const day = parseInt(fullMatch[2]);
    const today = 14;
    return day === today || day === today - 1;
  }
  if (/小时前|分钟前|刚刚/.test(timeStr)) return true;
  return true;
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

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function crawlBrand(page, brand) {
  const isStarbucks = brand.uid === 'starbucks';
  const url = isStarbucks
    ? `https://m.weibo.cn/n/starbucks`
    : `https://m.weibo.cn/u/${brand.uid}`;
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await sleep(4000);
    await page.evaluate(() => window.scrollTo(0, 800));
    await sleep(2000);

    const posts = await page.evaluate(() => {
      const cards = document.querySelectorAll('.card');
      const results = [];
      for (const card of cards) {
        const timeEl = card.querySelector('span.time');
        const textEl = card.querySelector('.weibo-text');
        if (!timeEl || !textEl) continue;
        const timeStr = timeEl.innerText.trim();
        const text = textEl.innerText.trim().slice(0, 400);
        if (text.length > 10) {
          results.push({ date: timeStr, text });
        }
      }
      return results;
    });

    const now = new Date();
    const targetDate = now.getDate();
    const targetMonth = now.getMonth() + 1;

    const filtered = posts.filter(p => {
      const fullMatch = p.date.match(/^(\d+)-(\d+)\s+\d+:\d+$/);
      if (fullMatch) {
        const month = parseInt(fullMatch[1]);
        const day = parseInt(fullMatch[2]);
        if (month !== targetMonth) return false;
        return day === targetDate || day === targetDate - 1;
      }
      if (/小时前|分钟前|刚刚/.test(p.date)) return true;
      return false;
    });

    return filtered.filter(p => isValid(p.text));
  } catch(e) {
    console.error(`[${brand.name}] Error: ${e.message}`);
    return [];
  }
}

async function main() {
  console.log('Connecting to CDP...');
  const browser = await chromium.connectOverCDP(CDP_URL);
  const context = browser.contexts()[0] || await browser.newContext();
  const page = context.pages()[0] || await context.newPage();
  
  const results = {};
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    console.log(`[${i+1}/${brands.length}] Crawling ${brand.name}...`);
    const posts = await crawlBrand(page, brand);
    results[brand.name] = posts;
    console.log(`  -> Found ${posts.length} posts`);
    if (i < brands.length - 1) await sleep(8000);
  }

  await browser.close();

  const output = { date: '2026-05-14', brands: results, crawledAt: new Date().toISOString() };
  writeFileSync(OUTPUT, JSON.stringify(output, null, 2));
  console.log(`Done. Output: ${OUTPUT}`);
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
