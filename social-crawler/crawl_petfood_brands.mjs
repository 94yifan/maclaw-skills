/**
 * Pet Food Brand Weibo Crawler — Adapted from tea-brand-daily-report
 * Crawls last ~6 months of Weibo posts for pet food brands
 * Focus: marketing campaigns, endorsements, brand messages
 */

import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: '比乐宠粮', uid: '6360189550', group: '福贝宠食' },
  { name: '伯纳天纯', uid: '3057698573', group: '上海依蕴' },
  { name: '麦富迪', uid: '2774933017', group: '乖宝宠物' },
  { name: '蓝氏Legendsandy', uid: '6969015029', group: '吉家宠物' },
  { name: '鲜朗', uid: '6350667496', group: '-' },
  { name: '比瑞吉', uid: '1820536387', group: '比瑞吉' },
  { name: '顽皮Wanpy', uid: '2613757204', group: '中宠股份' },
  { name: '疯狂小狗', uid: '5231861614', group: '吉家宠物' },
  { name: '卫仕', uid: '5574123629', group: '宠幸' },
];

const output = {
  crawlDate: new Date().toISOString().split('T')[0],
  crawlTime: new Date().toTimeString().slice(0,5),
  brands: []
};

async function run() {
  // Connect to Chrome CDP
  const PORTS = [9333, 9222, 9500];
  let browser;
  for (const port of PORTS) {
    try {
      browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
      break;
    } catch (e) {
      if (port === PORTS[PORTS.length - 1]) process.exit(1);
    }
  }

  const context = browser.contexts()[0] || browser;
  const page = await context.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });

  const sixMonthsAgo = new Date();
  sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

  for (const brand of brands) {
    console.log('Crawling:', brand.name, brand.uid);
    const url = 'https://weibo.com/u/' + brand.uid;

    const brandData = {
      name: brand.name,
      group: brand.group,
      uid: brand.uid,
      posts: [],
      marketingCampaigns: [],
      endorsements: [],
      brandMentions: []
    };

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
      await page.waitForTimeout(5000);

      // Scroll to load posts — scroll more to get more historical data
      for (let s = 0; s < 6; s++) {
        await page.evaluate((pos) => window.scrollTo(0, pos), s * 1000);
        await page.waitForTimeout(2000);
      }

      // Try multiple selectors to find posts
      const posts = await page.$$eval('[node-type="feed_list_content"]', els =>
        els.map(el => ({
          time: el.querySelector('[node-type="datetime"]')?.getAttribute('title')?.trim() ||
                el.querySelector('.time')?.textContent?.trim() || '',
          text: el.querySelector('.detail_text')?.textContent?.trim() || el.textContent?.trim() || '',
          type: 'feed'
        }))
      );

      // Fallback: try alternate selector
      let altPosts = [];
      if (posts.length === 0) {
        altPosts = await page.$$eval('[action-type="feed_list_item"]', els =>
          els.map(el => ({
            time: el.querySelector('[node-type="datetime"]')?.getAttribute('title')?.trim() ||
                  el.querySelector('.time')?.textContent?.trim() || '',
            text: el.querySelector('[node-type="feed_list_content"]')?.textContent?.trim() || el.textContent?.trim() || '',
            type: 'alt'
          }))
        );
      }

      const allPosts = posts.length > 0 ? posts : altPosts;

      // Filter: only posts from last 6 months, and only marketing-relevant
      for (const post of allPosts) {
        if (!post.time) continue;

        // Try to parse time
        let postDate;
        if (post.time.includes('-')) {
          postDate = new Date(post.time);
        } else if (post.time.includes('年')) {
          const m = post.time.match(/(\d+)年(\d+)月(\d+)日/);
          if (m) postDate = new Date(`${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`);
        }

        if (postDate && postDate < sixMonthsAgo) continue;

        // Filter: marketing-relevant keywords
        const lower = post.text.toLowerCase();
        const isRelevant =
          /代言|联名|签约|合作|campaign|短剧|明星|冠军|大使|守护官|推荐官|品牌升级|新装|全新|重磅|首发|公益|爱心|限定|上市|发布/.test(lower);

        const postData = {
          time: post.time,
          snippet: post.text.slice(0, 300) + (post.text.length > 300 ? '...' : ''),
          relevant: isRelevant
        };

        brandData.posts.push(postData);

        if (isRelevant) {
          brandData.marketingCampaigns.push(postData);
        }
      }

    } catch (e) {
      brandData.error = e.message;
    }

    output.brands.push(brandData);
    console.log(`  => ${brandData.posts.length} posts (${brandData.marketingCampaigns.length} marketing-relevant)`);
    await page.waitForTimeout(3000);
  }

  await page.close();

  // Save output
  writeFileSync('/tmp/openclaw/petfood-weibo-crawl-20260712.json', JSON.stringify(output, null, 2));
  console.log('\nDone. Saved to /tmp/openclaw/petfood-weibo-crawl-20260712.json');

  // Print summary
  console.log('\n=== MARKETING SUMMARY ===\n');
  for (const b of output.brands) {
    console.log(`\n## ${b.name} (${b.group})`);
    for (const p of b.marketingCampaigns) {
      console.log(`  [${p.time}] ${p.snippet}`);
    }
  }

  process.exit(0);
}

run().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});
