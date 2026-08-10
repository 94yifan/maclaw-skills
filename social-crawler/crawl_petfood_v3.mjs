/**
 * Pet Food Brand Weibo Crawler v3 — Using browser.evaluate directly
 * Falls back to search-based approach for brands we can't crawl
 */

import { writeFileSync, readFileSync, existsSync } from 'fs';
import { chromium } from 'playwright-core';

const PORTS = [9333, 9222, 9500];

// We'll try each brand one at a time via CDP, with robust error handling
async function crawlBrand(page, uid, brandName) {
  console.log(`\n--- ${brandName} (${uid}) ---`);
  const result = { name: brandName, uid, posts: [], error: null };

  try {
    const url = `https://weibo.com/u/${uid}`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(8000);

    // Scroll multiple times to trigger content loading
    for (let s = 0; s < 5; s++) {
      await page.evaluate(() => window.scrollBy(0, 1000));
      await page.waitForTimeout(3000);
    }

    // Extract posts using evaluate (works with user's login context)
    const posts = await page.evaluate(() => {
      const articles = document.querySelectorAll('article');
      if (articles.length === 0) return null;

      return Array.from(articles).map(el => ({
        text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 500),
        time: (el.querySelector('a[href*="weibo.com"]')?.textContent || '').trim()
      }));
    });

    if (!posts || posts.length === 0) {
      result.error = 'No article elements';
      console.log('  No articles found');
      return result;
    }

    result.posts = posts;
    
    // Identify marketing-relevant posts
    const marketing = posts.filter(p => {
      const t = p.text;
      return /代言|联名|签约|合作|新品|首发|重磅|公益|大使|明星|冠军|品牌升级|发布会|上市|限量|20周年|声明|酥化|推出/.test(t);
    });

    result.marketingCount = marketing.length;
    result.marketingPosts = marketing.slice(0, 10);

    console.log(`  Posts: ${posts.length}, Marketing: ${marketing.length}`);
    marketing.slice(0, 5).forEach(p => console.log(`  [${p.time}] ${p.text.slice(0, 80)}`));

  } catch (e) {
    result.error = e.message;
    console.log(`  Error: ${e.message}`);
  }

  return result;
}

async function run() {
  let browser;
  for (const port of PORTS) {
    try {
      browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
      console.log('Connected to CDP port', port);
      break;
    } catch (e) {
      if (port === PORTS[PORTS.length - 1]) {
        console.log('CDP_CONNECTION_FAILED');
        process.exit(1);
      }
    }
  }

  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  // Use existing user context
  const results = [];

  // Try each brand
  const brands = [
    { name: '伯纳天纯', uid: '3057698573' },
    { name: '比乐宠粮', uid: '6360189550' },
    { name: '麦富迪', uid: '2774933017' },
    { name: '蓝氏LEGENDSANDY', uid: '6969015029' },
    { name: '顽皮Wanpy', uid: '2613757204' },
    { name: '比瑞吉', uid: '1820536387' },
    { name: '疯狂小狗', uid: '5231861614' },
  ];

  for (const b of brands) {
    const r = await crawlBrand(page, b.uid, b.name);
    results.push(r);
    await page.waitForTimeout(5000);
  }

  await page.close();
  writeFileSync('/tmp/openclaw/petfood-weibo-v3.json', JSON.stringify(results, null, 2));
  console.log('\n=== DONE ===');
  console.log(JSON.stringify(results.map(r => ({
    name: r.name,
    posts: r.posts?.length || 0,
    marketing: r.marketingCount || 0,
    error: r.error
  })), null, 2));
  process.exit(0);
}

run().catch(e => { console.error('FATAL:', e); process.exit(1); });
