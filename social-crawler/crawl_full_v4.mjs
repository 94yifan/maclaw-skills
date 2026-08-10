import { chromium } from 'playwright';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks', username: true },
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

const results = [];

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function crawlBrand(ctx, brand) {
  const page = await ctx.newPage();
  try {
    const url = brand.username 
      ? `https://weibo.com/${brand.uid}`
      : `https://weibo.com/u/${brand.uid}`;
    
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
    await page.waitForTimeout(4000);
    
    const text = await page.evaluate(() => {
      const feed = document.querySelector('[node-type="feed_list"]') || 
                   document.querySelector('.WB_feed') ||
                   document.body;
      return feed.innerText.slice(0, 3000);
    });
    
    results.push({ brand: brand.name, uid: brand.uid, content: text });
    console.log(`✓ ${brand.name}: ${text.length} chars`);
  } catch (err) {
    console.log(`✗ ${brand.name}: ${err.message}`);
    results.push({ brand: brand.name, uid: brand.uid, error: err.message });
  } finally {
    await page.close();
  }
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const ctx = browser.contexts()[0];
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    console.log(`[${i+1}/${brands.length}] ${brand.name}`);
    await crawlBrand(ctx, brand);
    if (i < brands.length - 1) await sleep(8000);
  }
  
  // Save results
  const fs = await import('fs');
  fs.writeFileSync('/Users/yifansmacmini/.openclaw/workspace/social-crawler/weibo_raw_20260516.json', JSON.stringify(results, null, 2));
  console.log('\nSaved to weibo_raw_20260516.json');
}

main().catch(err => { console.error('Fatal:', err.message); process.exit(0); });
