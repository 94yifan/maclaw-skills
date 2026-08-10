import { chromium } from 'playwright';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448', type: 'uid' },
  { name: '库迪', uid: '7791266545', type: 'uid' },
  { name: '古茗', uid: '2809775704', type: 'uid' },
  { name: '幸运咖', uid: '6519396553', type: 'uid' },
  { name: '茉莉奶白', uid: '7577524421', type: 'uid' },
  { name: '霸王茶姬', uid: '5652018762', type: 'uid' },
  { name: '喜茶', uid: '2804387887', type: 'uid' },
  { name: '星巴克', uid: 'starbucks', type: 'username' },
  { name: '茶百道', uid: '6502206666', type: 'uid' },
  { name: '奈雪的茶', uid: '5884674413', type: 'uid' },
  { name: 'CoCo', uid: '2030619861', type: 'uid' },
  { name: '爷爷不泡茶', uid: '7769072120', type: 'uid' },
  { name: '沪上阿姨', uid: '3921865344', type: 'uid' },
  { name: '乐乐茶', uid: '6253473981', type: 'uid' },
  { name: '皮爷咖啡', uid: '6360528436', type: 'uid' },
  { name: 'M Stand', uid: '6345199298', type: 'uid' },
  { name: 'Manner', uid: '6808111794', type: 'uid' },
  { name: '茉酸奶', uid: '5188894132', type: 'uid' },
  { name: '树夏酸奶', uid: '7144806571', type: 'uid' },
];

const results = [];

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function crawlBrand(browser, brand) {
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Navigate to Weibo profile
    const url = brand.type === 'username' 
      ? `https://weibo.com/u/${brand.uid}`
      : `https://weibo.com/u/${brand.uid}`;
    
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(3000);
    
    // Get page content for analysis
    const content = await page.content();
    
    // Try to extract posts from the page
    const posts = await page.evaluate(() => {
      const items = document.querySelectorAll('[node-type="feed_list"] div[data-pid]');
      return Array.from(items).slice(0, 20).map(item => {
        const textEl = item.querySelector('.WB_text');
        const timeEl = item.querySelector('.WB_from');
        const text = textEl ? textEl.innerText.trim() : '';
        const time = timeEl ? timeEl.innerText.trim() : '';
        const linkEl = item.querySelector('a[node-type="feed_list_item_date"]');
        const link = linkEl ? linkEl.href : '';
        return { text, time, link };
      }).filter(p => p.text.length > 0);
    });
    
    if (posts.length === 0) {
      // Fallback: get all text content
      const rawContent = await page.evaluate(() => {
        const feedList = document.querySelector('[node-type="feed_list"]') || document.body;
        return feedList.innerText.slice(0, 5000);
      });
      results.push({ brand: brand.name, uid: brand.uid, posts: [], rawContent, raw: true });
    } else {
      results.push({ brand: brand.name, uid: brand.uid, posts, raw: false });
    }
    
    console.log(`✓ ${brand.name}: ${posts.length} posts found`);
  } catch (err) {
    console.log(`✗ ${brand.name}: error - ${err.message}`);
    results.push({ brand: brand.name, uid: brand.uid, error: err.message });
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    console.log(`[${i+1}/${brands.length}] Crawling ${brand.name}...`);
    await crawlBrand(browser, brand);
    if (i < brands.length - 1) {
      console.log(`  Sleeping 8s before next brand...`);
      await sleep(8000);
    }
  }
  
  // Output results
  console.log('\n=== CRAWL RESULTS ===');
  console.log(JSON.stringify(results, null, 2));
  
  await browser.disconnect();
}

main().catch(console.error);
