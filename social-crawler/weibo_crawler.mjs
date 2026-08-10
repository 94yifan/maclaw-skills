import { chromium } from 'playwright';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks', isUsername: true },
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

const CDP_URL = 'http://127.0.0.1:9333';
const REPORT_DATE = '2026-05-10';
const OUTPUT_FILE = `/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_${REPORT_DATE}.md`;

// Connect to CDP
let browser;
try {
  browser = await chromium.connectOverCDP(CDP_URL);
  console.log('CDP connected successfully');
} catch (e) {
  console.error('CDP connection failed:', e.message);
  process.exit(1);
}

const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();

// Helper: wait and human-like delay
async function waitAndDelay(seconds) {
  await page.waitForTimeout(seconds * 1000);
}

// Helper: get page content as text
async function extractPageContent(page) {
  return await page.evaluate(() => {
    const cards = document.querySelectorAll('.vue-recycle-scroller__item-view');
    const feedItems = [];
    cards.forEach(card => {
      const textEl = card.querySelector('.WB_text');
      const timeEl = card.querySelector('.WB_detail_expand .WB_from');
      const actEl = card.querySelector('.WB_expand');
      if (textEl) {
        feedItems.push({
          text: textEl.innerText.trim(),
          time: timeEl ? timeEl.innerText.trim() : '',
          expanded: actEl ? actEl.innerText.trim() : ''
        });
      }
    });
    return feedItems;
  });
}

const results = {};
let currentBrand = '';

// Navigate to brand Weibo page
for (const brand of brands) {
  currentBrand = brand.name;
  console.log(`\n=== Crawling: ${brand.name} ===`);
  
  try {
    let url;
    if (brand.isUsername) {
      url = `https://weibo.com/u/${brand.uid}`;
    } else {
      url = `https://weibo.com/u/${brand.uid}`;
    }
    
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await waitAndDelay(5);
    
    // Try to find feed content
    const content = await page.evaluate(() => {
      // Look for Weibo feed items
      const items = document.querySelectorAll('[action-type="feed_list_item"]');
      if (items.length > 0) {
        return Array.from(items).map(item => {
          const textEl = item.querySelector('.WB_text');
          const timeEl = item.querySelector('.WB_detail_expand .WB_from a') || item.querySelector('.WB_from');
          const expandEl = item.querySelector('.WB_expand');
          return {
            text: textEl ? textEl.innerText.replace(/\n/g, ' ').trim() : '',
            time: timeEl ? timeEl.innerText.replace(/\n/g, ' ').trim() : '',
            expanded: expandEl ? expandEl.innerText.replace(/\n/g, ' ').trim() : ''
          };
        });
      }
      
      // Alternative selectors
      const altItems = document.querySelectorAll('.vue-recycle-scroller__item-view');
      if (altItems.length > 0) {
        return Array.from(altItems).map(item => {
          const textEl = item.querySelector('.WB_text');
          const timeEl = item.querySelector('.WB_from');
          const expandEl = item.querySelector('.WB_expand');
          return {
            text: textEl ? textEl.innerText.replace(/\n/g, ' ').trim() : '',
            time: timeEl ? timeEl.innerText.replace(/\n/g, ' ').trim() : '',
            expanded: expandEl ? expandEl.innerText.replace(/\n/g, ' ').trim() : ''
          };
        });
      }
      
      // Generic fallback
      const bodyText = document.body.innerText.substring(0, 5000);
      return [{ text: bodyText, time: '', expanded: '' }];
    });
    
    results[brand.name] = content;
    console.log(`Found ${content.length} items for ${brand.name}`);
    
  } catch (e) {
    console.error(`Error crawling ${brand.name}: ${e.message}`);
    results[brand.name] = [{ text: `[Error: ${e.message}]`, time: '', expanded: '' }];
  }
  
  // Wait 8 seconds between brands
  if (brand !== brands[brands.length - 1]) {
    console.log('Waiting 8 seconds...');
    await waitAndDelay(8);
  }
}

// Write results to file
const fs = await import('fs');
const reportContent = JSON.stringify(results, null, 2);
fs.writeFileSync(OUTPUT_FILE, reportContent);
console.log(`\nResults saved to ${OUTPUT_FILE}`);

await browser.close();
