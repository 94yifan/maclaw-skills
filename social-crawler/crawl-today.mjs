import puppeteer from 'puppeteer-core';
import { writeFileSync } from 'fs';

const WS_URL = 'ws://127.0.0.1:18800/devtools/browser/11d3404d-f69e-4c7c-9e3e-0400c5fe5ae8';

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

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('Connecting to browser...');
  const browser = await puppeteer.connect({
    browserWSEndpoint: WS_URL,
    defaultViewport: null
  });
  
  const pages = await browser.pages();
  const page = pages[0];
  if (!page) {
    console.error('No page found');
    await browser.disconnect();
    return;
  }
  
  console.log('Connected. Testing fetch...');
  
  // Test one request
  const testUrl = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=6349791448&containerid=1076036349791448';
  const testResult = await page.evaluate(async (url) => {
    const res = await fetch(url, {
      credentials: 'include',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await res.json();
    if (data.ok && data.data && data.data.cards) {
      const cards = data.data.cards.filter(c => c.card_group && c.mblog);
      return { ok: true, count: cards.length };
    }
    return { ok: false, msg: data.msg || 'no data' };
  }, testUrl);
  
  console.log('Test result:', JSON.stringify(testResult, null, 2));
  
  if (!testResult.ok) {
    console.log('API test failed, check cookies');
    await browser.disconnect();
    return;
  }
  
  // Fetch all brands
  const allResults = {};
  
  for (const brand of brands) {
    let uid = brand.uid;
    if (uid === 'starbucks') {
      // star bucks special - try numeric uid from MEMORY
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
        allResults[brand.name] = { uid: brand.uid, error: result.msg || 'no data' };
        console.log(`  -> Error: ${result.msg}`);
      }
      
    } catch (err) {
      allResults[brand.name] = { uid: brand.uid, error: err.message };
      console.log(`  -> Error: ${err.message}`);
    }
    
    await sleep(3000 + Math.random() * 2000);
  }
  
  // Save all results
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
    if (data.error) {
      console.log(`  ${name}: ERROR - ${data.error}`);
    }
  }
  console.log(`\nTotal: ${totalRecent} recent items across ${brandsWithData}/${brands.length} brands`);
  
  await browser.disconnect();
}

function stripHtml(html) {
  return html.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
