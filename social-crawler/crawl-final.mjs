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
  return html.replace(/<br\s*\/?>/gi, '\n')
             .replace(/<[^>]*>/g, '')
             .replace(/&amp;/g, '&')
             .replace(/&lt;/g, '<')
             .replace(/&gt;/g, '>')
             .replace(/&quot;/g, '"')
             .replace(/&#39;/g, "'")
             .replace(/&#34;/g, '"')
             .replace(/&nbsp;/g, ' ')
             .replace(/\n{3,}/g, '\n\n')
             .trim();
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('Connecting...');
  const browser = await chromium.connectOverCDP(WS_ENDPOINT);
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('weibo.cn'));
  
  if (!page) {
    console.error('No weibo page found');
    await browser.close();
    return;
  }
  
  console.log(`Page: ${page.url()}`);
  
  const allResults = {};
  const now = Date.now();
  const oneDayAgo = now - 24 * 60 * 60 * 1000;
  
  for (const brand of brands) {
    let uid = brand.uid;
    if (uid === 'starbucks') {
      uid = '1741514817'; // mapped numeric UID
    }
    
    const apiUrl = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=107603${uid}`;
    
    try {
      process.stdout.write(`Fetching ${brand.name}...`);
      
      // Include raw data for items for better analysis
      const result = await page.evaluate(async (url) => {
        const res = await fetch(url, {
          credentials: 'include',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        if (data.ok && data.data && data.data.cards) {
          const items = data.data.cards
            .filter(c => c.mblog)
            .map(c => ({
              text: c.mblog.text,
              created_at: c.mblog.created_at,
              id: c.mblog.id,
              mid: c.mblog.mid,
              scheme: c.scheme
            }));
          return { ok: true, count: items.length, items };
        }
        return { ok: false, msg: data.msg || 'no data', items: [] };
      }, apiUrl);
      
      if (result.ok && result.items.length > 0) {
        // Filter to last 24h
        const recentItems = result.items.filter(item => {
          const created = new Date(item.created_at).getTime();
          return !isNaN(created);
        });
        
        // Further filter to 24h
        const last24hItems = recentItems.filter(item => {
          const created = new Date(item.created_at).getTime();
          return created >= oneDayAgo;
        });
        
        allResults[brand.name] = {
          uid: brand.uid,
          totalCards: result.items.length,
          recentCount: last24hItems.length,
          items: last24hItems.map(item => ({
            text: item.text,
            created_at: item.created_at,
            id: item.id,
            scheme: item.scheme
          }))
        };
        console.log(` ${last24hItems.length} recent (${result.items.length} total)`);
      } else {
        allResults[brand.name] = { uid: brand.uid, error: result.msg, totalCards: 0, recentCount: 0, items: [] };
        console.log(` error: ${result.msg}`);
      }
      
    } catch (err) {
      allResults[brand.name] = { uid: brand.uid, error: err.message, totalCards: 0, recentCount: 0, items: [] };
      console.log(` error: ${err.message}`);
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
