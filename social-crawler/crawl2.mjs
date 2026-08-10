import { chromium } from 'playwright';
import { writeFileSync } from 'fs';

const WS_ENDPOINT = 'ws://127.0.0.1:18800/devtools/browser/11d3404d-f69e-4c7c-9e3e-0400c5fe5ae8';

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
  { name: '树夏酸奶', uid: '7144806571' }
];

function stripHtml(html) {
  return html.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('Connecting to browser via Playwright...');
  const browser = await chromium.connectOverCDP(WS_ENDPOINT);
  
  // Get existing pages
  const contexts = browser.contexts();
  console.log(`Found ${contexts.length} browser contexts`);
  
  // Use the default context's pages
  let context = contexts[0];
  let pages = context.pages();
  console.log(`Found ${pages.length} pages in default context`);
  console.log('Available pages:', pages.map(p => ({ url: p.url().substring(0,60) })));
  
  // Find or create the m.weibo.cn page
  let page = pages.find(p => p.url().includes('weibo.cn'));
  if (!page) {
    console.log('Creating new page...');
    page = await context.newPage();
    await page.goto('https://m.weibo.cn', { waitUntil: 'domcontentloaded', timeout: 30000 });
  }
  
  console.log(`Using page: ${page.url().substring(0,60)}`);
  
  // Test one request
  const testUrl = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=6349791448&containerid=1076036349791448';
  console.log('Testing API request...');
  
  const testResult = await page.evaluate(async (url) => {
    try {
      const res = await fetch(url, {
        credentials: 'include',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await res.json();
      if (data.ok && data.data && data.data.cards) {
        const cards = data.data.cards.filter(c => c.card_group && c.mblog);
        return { ok: true, count: cards.length, msg: data.msg };
      }
      return { ok: false, msg: data.msg || 'no data' };
    } catch(e) {
      return { ok: false, msg: e.message };
    }
  }, testUrl);
  
  console.log('Test result:', JSON.stringify(testResult));
  
  if (!testResult.ok) {
    console.log('API test failed. Trying to navigate to m.weibo.cn first...');
    await page.goto('https://m.weibo.cn', { waitUntil: 'networkidle', timeout: 30000 });
    
    // Retry
    const retryResult = await page.evaluate(async (url) => {
      try {
        const res = await fetch(url, {
          credentials: 'include',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        if (data.ok && data.data && data.data.cards) {
          return { ok: true, count: data.data.cards.length, msg: data.msg };
        }
        return { ok: false, msg: data.msg || 'no data' };
      } catch(e) {
        return { ok: false, msg: e.message };
      }
    }, testUrl);
    
    console.log('Retry result:', JSON.stringify(retryResult));
    
    if (!retryResult.ok) {
      console.log('Still failed. Checking cookie/login state...');
      const cookies = await page.context().cookies();
      console.log(`Cookies count: ${cookies.length}`);
      const weiboCookies = cookies.filter(c => c.domain.includes('weibo'));
      console.log(`Weibo cookies count: ${weiboCookies.length}`);
      console.log('Weibo cookie names:', weiboCookies.map(c => c.name).join(', '));
      
      // Try direct page navigation to a brand page
      await page.goto('https://m.weibo.cn/profile/6349791448', { waitUntil: 'networkidle', timeout: 30000 });
      console.log(`Navigated to profile page, URL: ${page.url().substring(0,80)}`);
      const bodyText = await page.evaluate(() => document.body.innerText.substring(0,300));
      console.log('Body text:', bodyText);
      
      await browser.close();
      return;
    }
  }
  
  // Now fetch all brands
  const allResults = {};
  
  for (const brand of brands) {
    let uid = brand.uid;
    if (uid === 'starbucks') {
      uid = '1741514817';
    }
    
    const apiUrl = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=107603${uid}`;
    
    try {
      console.log(`Fetching ${brand.name} (${uid})...`);
      
      const result = await page.evaluate(async (url) => {
        const res = await fetch(url, {
          credentials: 'include',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        return { ok: data.ok, data: data.data || null, msg: data.msg || null };
      }, apiUrl);
      
      if (result.ok && result.data) {
        const cards = result.data.cards || [];
        const mblogCards = cards.filter(c => c.card_group && c.mblog).map(c => c.mblog);
        
        // Filter to last 24h
        const now = Date.now();
        const oneDayAgo = now - 24 * 60 * 60 * 1000;
        const recentCards = mblogCards.filter(cb => {
          const created = new Date(cb.created_at).getTime();
          return !isNaN(created) && created >= oneDayAgo;
        });
        
        allResults[brand.name] = {
          uid: brand.uid,
          totalCards: mblogCards.length,
          recentCount: recentCards.length,
          items: recentCards.map(cb => ({
            text: stripHtml(cb.text || ''),
            created_at: cb.created_at,
            id: cb.id
          }))
        };
        console.log(`  -> ${recentCards.length} recent items (${mblogCards.length} total)`);
      } else {
        allResults[brand.name] = { uid: brand.uid, error: result.msg || 'no data', totalCards: 0, recentCount: 0, items: [] };
        console.log(`  -> Error: ${result.msg}`);
      }
      
    } catch (err) {
      allResults[brand.name] = { uid: brand.uid, error: err.message, totalCards: 0, recentCount: 0, items: [] };
      console.log(`  -> Error: ${err.message}`);
    }
    
    await sleep(3000 + Math.random() * 2000);
  }
  
  // Save results
  writeFileSync('/tmp/tea-crawl-2026-07-06.json', JSON.stringify(allResults, null, 2));
  console.log('\nSaved to /tmp/tea-crawl-2026-07-06.json');
  
  // Summary
  let totalRecent = 0;
  let brandsWithData = 0;
  for (const [name, data] of Object.entries(allResults)) {
    if (data.recentCount > 0) {
      totalRecent += data.recentCount;
      brandsWithData++;
    }
  }
  console.log(`\nTotal: ${totalRecent} recent items across ${brandsWithData}/${brands.length} brands`);
  
  // Print items per brand
  console.log('\n--- Per brand breakdown ---');
  for (const [name, data] of Object.entries(allResults)) {
    console.log(`  ${name}: ${data.recentCount || 0} items${data.error ? ` (ERROR: ${data.error})` : ''}`);
  }
  
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
