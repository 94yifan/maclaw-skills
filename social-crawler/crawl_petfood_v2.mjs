/**
 * Pet Food Brand Weibo Crawler v2 — Fixed selectors
 * Uses <article> tags (Weibo new layout)
 * Summarizes brand activity over time range
 */

import { chromium } from 'playwright-core';
import { writeFileSync, mkdirSync } from 'fs';

// VERIFIED active UIDs (confirmed by checking pages)
const brands = [
  { name: '比乐宠食', uid: '6360189550', note: '可能有新号, 老号只有1条微博' },
  { name: '伯纳天纯', uid: '3057698573', note: '活跃, 2865条, 3.2万粉' },
  { name: '麦富迪', uid: '2774933017', note: '待确认UID' },
  { name: '蓝氏LEGENDSANDY', uid: '6969015029', note: '已确认活跃' },
  { name: '顽皮Wanpy', uid: '2613757204', note: '待确认' },
  { name: '比瑞吉', uid: '1820536387', note: '待确认' },
  { name: '疯狂小狗', uid: '5231861614', note: '待确认' },
  { name: '鲜朗', uid: '6350667496', note: '待确认' },
  { name: '卫仕', uid: '5574123629', note: '待确认' },
  { name: '好主人', uid: '5606152241', note: '旺旺集团旗下' },
];

async function run() {
  const PORTS = [9333, 9222, 9500];
  let browser;
  for (const port of PORTS) {
    try {
      browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
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

  const output = {
    crawlDate: new Date().toISOString().split('T')[0],
    results: []
  };

  for (const brand of brands) {
    console.log(`\n=== ${brand.name} (${brand.uid}) ===`);
    const url = `https://weibo.com/u/${brand.uid}`;

    const result = { name: brand.name, uid: brand.uid, posts: [], error: null };

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(5000);

      // Check if account has content
      const hasContent = await page.$('article');
      if (!hasContent) {
        result.error = 'No article elements found - account may be dead';
        console.log(result.error);
        output.results.push(result);
        continue;
      }

      // Scrolling: use evaluate to scroll window smoothly multiple times
      for (let i = 0; i < 8; i++) {
        await page.evaluate(() => {
          window.scrollBy(0, 1200);
        });
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1500);

      // Extract all article posts
      const posts = await page.evaluate(() => {
        const articles = document.querySelectorAll('article');
        return Array.from(articles).map((el, idx) => {
          // Find all text within the article
          const allText = el.textContent || '';
          // Find time link - look for <a> tags containing time format like "7-9" or "2-5"
          const timeEl = el.querySelector('a[href*="/"]');
          const timeText = timeEl ? timeEl.textContent.trim() : '';

          // Get links for post URLs
          const links = Array.from(el.querySelectorAll('a')).map(a => a.href).filter(h => h.includes('weibo.com/'));
          const postUrl = links.length > 0 ? links.find(l => l.match(/\/\d+\/[a-zA-Z0-9]+/)) || links[0] : '';

          return {
            idx,
            time: timeText,
            text: allText.replace(/\s+/g, ' ').trim().slice(0, 400),
            url: postUrl
          };
        });
      });

      // Filter: marketing-relevant posts
      const relevant = posts.filter(p => {
        const t = p.text;
        return /代言|联名|签约|合作|新品|首发|重磅|公益|大使|明星|冠军|品牌升级|发布会|上市|限量|20周年/.test(t);
      });

      result.posts = posts.slice(0, 30);
      result.marketing = relevant;
      result.totalFound = posts.length;
      result.marketingCount = relevant.length;

      console.log(`Found ${posts.length} posts (${relevant.length} marketing-relevant)`);
      if (relevant.length > 0) {
        relevant.slice(0, 5).forEach(p => console.log(`  [${p.time}] ${p.text.slice(0, 100)}`));
      }

    } catch (e) {
      result.error = e.message;
      console.log(`Error: ${e.message}`);
    }

    output.results.push(result);
  }

  await page.close();
  writeFileSync('/tmp/openclaw/petfood-weibo-v2.json', JSON.stringify(output, null, 2));
  console.log('\nDone. Saved to /tmp/openclaw/petfood-weibo-v2.json');
  process.exit(0);
}

run().catch(e => { console.error('FATAL:', e); process.exit(1); });
