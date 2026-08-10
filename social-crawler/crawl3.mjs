import { chromium } from 'playwright';
import { writeFileSync } from 'fs';

const WS_ENDPOINT = 'ws://127.0.0.1:18800/devtools/browser/11d3404d-f69e-4c7c-9e3e-0400c5fe5ae8';

async function main() {
  const browser = await chromium.connectOverCDP(WS_ENDPOINT);
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('weibo.cn'));
  
  console.log('Current URL:', page.url());
  
  // Get cookies
  const cookies = await context.cookies();
  const weiboCookies = cookies.filter(c => c.domain.includes('weibo'));
  console.log(`Weibo cookies: ${weiboCookies.length}`);
  console.log('Weibo cookie names:', weiboCookies.map(c => c.name).join(', '));
  console.log('SUB present:', weiboCookies.some(c => c.name === 'SUB'));
  
  // Test the API raw response for 瑞幸
  const apiUrl = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=6349791448&containerid=1076036349791448';
  
  const rawResult = await page.evaluate(async (url) => {
    try {
      const res = await fetch(url, {
        credentials: 'include',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await res.json();
      
      // Look at the structure
      const structure = {
        ok: data.ok,
        msg: data.msg,
        hasData: !!data.data,
        hasCards: !!(data.data && data.data.cards),
        cardsType: data.data?.cards ? typeof data.data.cards : 'no cards',
        cardsLength: data.data?.cards?.length || 0,
        cardKeys: data.data?.cards?.length > 0 ? Object.keys(data.data.cards[0]).join(',') : 'no cards',
        firstCardTypes: data.data?.cards?.slice(0,3).map(c => c.card_type || 'no type') || [],
        cardlistInfoTitle: data.data?.cardlistInfo?.title || null,
        mblogCount: data.data?.cards ? data.data.cards.filter(c => c.card_group && c.mblog).length : 0,
        // Show first card's full structure
        firstCardStructure: data.data?.cards?.length > 0 ? JSON.stringify(data.data.cards[0]).substring(0,500) : 'none'
      };
      
      return structure;
    } catch(e) {
      return { error: e.message };
    }
  }, apiUrl);
  
  console.log('\nAPI Structure:', JSON.stringify(rawResult, null, 2));
  
  // If the structure doesn't match, try looking at mblog location in a different way
  // Maybe mblog is directly in the card, not in card_group
  const altCheck = await page.evaluate(async (url) => {
    const res = await fetch(url, {
      credentials: 'include',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await res.json();
    const cards = data.data?.cards || [];
    
    const cardTypes = cards.map(c => ({
      type: c.card_type,
      hasMblog: !!c.mblog,
      hasCardGroup: !!c.card_group,
      // If card_group exists, check if items inside have mblog
      groupMblogCount: c.card_group ? c.card_group.filter(g => g.mblog).length : 0,
      // Look for mblog at different levels
      keys: Object.keys(c).join(',')
    }));
    
    return { cardCount: cards.length, cardDetails: cardTypes.slice(0,5) };
  }, apiUrl);
  
  console.log('\nAlt check:', JSON.stringify(altCheck, null, 2));
  
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
