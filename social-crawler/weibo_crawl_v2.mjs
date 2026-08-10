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

async function crawlBrand(browser, brand, index) {
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Try search page first (public content)
    const searchUrl = `https://s.weibo.com/user?q=${encodeURIComponent(brand.name)}&Refer=index`;
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(5000);
    
    // Try getting feed list content
    const feedContent = await page.evaluate(() => {
      // Try various selectors for Weibo feed
      const selectors = [
        '[node-type="feed_list"]',
        '.WB_feed',
        '.WB_feed_timeline',
        '[class*="feed_list"]',
        '[id*="Pl_Official_MyProfileFeed"]',
      ];
      
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) return el.innerText.slice(0, 3000);
      }
      
      // Fallback: get entire body text
      return document.body.innerText.slice(0, 5000);
    });
    
    // Also try direct profile with longer wait
    const profileUrl = brand.type === 'username' 
      ? `https://weibo.com/${brand.uid}`
      : `https://weibo.com/u/${brand.uid}`;
    
    await page.goto(profileUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(5000);
    
    const profileContent = await page.evaluate(() => {
      const feedEl = document.querySelector('[node-type="feed_list"]') || 
                     document.querySelector('.WB_feed') ||
                     document.querySelector('[id*="Pl_Official_MyProfileFeed"]') ||
                     document.body;
      return feedEl.innerText.slice(0, 3000);
    });
    
    results.push({ 
      brand: brand.name, 
      uid: brand.uid, 
      searchContent: feedContent.slice(0, 1500),
      profileContent: profileContent.slice(0, 1500)
    });
    
    console.log(`✓ ${brand.name}: done (search:${feedContent.length} profile:${profileContent.length})`);
  } catch (err) {
    console.log(`✗ ${brand.name}: ${err.message}`);
    results.push({ brand: brand.name, uid: brand.uid, error: err.message });
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    console.log(`[${i+1}/${brands.length}] ${brand.name}`);
    await crawlBrand(browser, brand, i);
    if (i < brands.length - 1) {
      await sleep(8000);
    }
  }
  
  console.log('\n=== RESULTS ===');
  for (const r of results) {
    console.log(`\n--- ${r.brand} ---`);
    console.log(`Search: ${r.searchContent?.slice(0, 200) || 'N/A'}`);
    console.log(`Profile: ${r.profileContent?.slice(0, 200) || 'N/A'}`);
  }
}

main().catch(console.error);
