/**
 * Pet Food Brand Weibo Crawler v4 — Correct UIDs + Dual selectors
 * Supports both article tags (new Weibo) and node-type (legacy)
 */

import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

// CORRECT UIDs — verified via search + page check
const brands = [
  { name: '伯纳天纯', uid: '3057698573', note: '2865条微博, 3.2万粉, 活跃' },
  { name: '麦富迪Myfoodie', uid: '2950260497', note: '乖宝旗下, 官方蓝V' },
  { name: '比乐宠粮', uid: '6360189550', note: '老号仅1条, 可能有新号' },
  { name: '蓝氏LEGENDSANDY', uid: '6969015029', note: '吉家旗下, 蓝V' },
  { name: '比瑞吉', uid: '1820536387', note: '官方蓝V' },
  { name: '顽皮Wanpy', uid: '2613757204', note: '中宠旗下, 蓝V' },
  { name: '疯狂小狗', uid: '5231861614', note: '吉家旗下, 蓝V' },
  { name: '卫仕', uid: '5574123629', note: '蓝V' },
  { name: '鲜朗', uid: '6350667496', note: '官方蓝V' },
  { name: '好主人', uid: '5606152241', note: '旺旺集团, 蓝V' },
];

async function crawlBrand(page, uid, name) {
  const result = { name, uid, posts: [], error: null };
  try {
    const url = `https://weibo.com/u/${uid}?tabtype=home`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Scroll multiple times with longer waits
    for (let s = 0; s < 5; s++) {
      await page.evaluate(() => window.scrollBy(0, 1200));
      await page.waitForTimeout(2500);
    }

    // Try both selectors
    const posts = await page.evaluate(() => {
      // Method 1: article tags (new Weibo)
      let articles = document.querySelectorAll('article');
      let items = Array.from(articles);

      // Method 2: feed_list (legacy)
      if (items.length === 0) {
        items = document.querySelectorAll('[node-type="feed_list_content"]');
        items = Array.from(items);
      }

      // Method 3: feed_list_item (legacy alt)
      if (items.length === 0) {
        items = document.querySelectorAll('[action-type="feed_list_item"]');
        items = Array.from(items);
      }

      return items.map(el => ({
        text: el.textContent.replace(/\s+/g, ' ').trim().slice(0, 500),
        time: el.querySelector('[node-type="datetime"]')?.getAttribute('title')
          || el.querySelector('a[href*="/"]')?.textContent?.trim()
          || ''
      }));
    });

    if (posts.length === 0) {
      result.error = 'No posts found (all selectors failed)';
      return result;
    }

    // Filter marketing-relevant
    const relevant = posts.filter(p =>
      /代言|联名|签约|合作|新品|首发|重磅|公益|大使|明星|冠军|品牌升级|发布会|上市|限量|20周年|声明|酥化|推出|官宣/.test(p.text)
    );

    result.posts = posts.slice(0, 20);
    result.marketingPosts = relevant.slice(0, 10);
    result.totalFound = posts.length;
    result.marketingCount = relevant.length;

  } catch (e) {
    result.error = e.message;
  }
  return result;
}

async function run() {
  let browser;
  for (const port of [9333, 9222, 9500]) {
    try {
      browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
      console.log('CDP connected:', port);
      break;
    } catch (e) { if (port === 9500) { console.log('CDP_FAILED'); process.exit(1); } }
  }

  const context = browser.contexts()[0] || browser;
  const page = await context.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('https://weibo.com', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(5000);

  const results = [];
  for (const b of brands) {
    console.log(`\n--- ${b.name} (${b.uid}) ---`);
    const r = await crawlBrand(page, b.uid, b.name);
    results.push(r);
    console.log(`  ${r.error || `${r.totalFound} posts, ${r.marketingCount} marketing`}`);
    if (r.marketingPosts?.length > 0) {
      r.marketingPosts.slice(0, 3).forEach(p => console.log(`  [${p.time}] ${p.text.slice(0, 80)}`));
    }
    await page.waitForTimeout(5000);
  }

  await page.close();
  writeFileSync('/tmp/openclaw/petfood-weibo-v4.json', JSON.stringify(results, null, 2));
  console.log('\nDONE');
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });
