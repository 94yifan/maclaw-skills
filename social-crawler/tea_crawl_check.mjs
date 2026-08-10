import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const CDP_URL = 'http://127.0.0.1:9333';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '星巴克', uid: 'starbucks' },
  { name: '奈雪的茶', uid: '5884674413' },
  { name: '沪上阿姨', uid: '3921865344' },
  { name: '乐乐茶', uid: '6253473981' },
  { name: '皮爷咖啡', uid: '6360528436' },
  { name: 'Manner', uid: '6808111794' },
];

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function crawlBrand(page, brand) {
  const isStarbucks = brand.uid === 'starbucks';
  const url = isStarbucks
    ? `https://m.weibo.cn/n/starbucks`
    : `https://m.weibo.cn/u/${brand.uid}`;
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await sleep(5000);
    await page.evaluate(() => window.scrollTo(0, 1200));
    await sleep(3000);

    const posts = await page.evaluate(() => {
      const cards = document.querySelectorAll('.card');
      const results = [];
      for (const card of cards) {
        const timeEl = card.querySelector('span.time');
        const textEl = card.querySelector('.weibo-text');
        if (!timeEl || !textEl) continue;
        const timeStr = timeEl.innerText.trim();
        const text = textEl.innerText.trim();
        if (text.length > 10) {
          results.push({ date: timeStr, text });
        }
      }
      return results;
    });
    return posts;
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
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    console.log(`[${i+1}/${brands.length}] ${brand.name}...`);
    const posts = await crawlBrand(page, brand);
    console.log(`  -> ${posts.length} posts`);
    for (const p of posts) {
      console.log(`  [${p.date}] ${p.text.slice(0,150)}`);
    }
    if (i < brands.length - 1) await sleep(6000);
  }
  await browser.close();
  console.log('Done');
}

main().catch(e => { console.error(e); process.exit(1); });
