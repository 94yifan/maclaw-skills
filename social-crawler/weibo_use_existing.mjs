import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  
  // Get all targets that are weibo
  const targets = await browser.targets();
  const weiboTargets = targets.filter(t => t.url().includes('weibo.com'));
  console.log('Weibo targets:', weiboTargets.length);
  for (const t of weiboTargets) {
    console.log(' -', t.url());
  }
  
  // Attach to existing weibo pages
  for (const target of weiboTargets.slice(0, 3)) {
    const page = await target.page();
    if (page) {
      const url = page.url();
      console.log('\nPage URL:', url);
      
      // Try to extract content
      try {
        const text = await page.evaluate(() => {
          const feed = document.querySelector('[node-type="feed_list"]') || 
                       document.querySelector('.WB_feed') ||
                       document.body;
          return feed.innerText.slice(0, 2000);
        });
        console.log('Content:', text.slice(0, 500));
      } catch(e) {
        console.log('Error:', e.message);
      }
    }
  }
  
  // Now try to get brand pages using existing CDP connection
  // Find or create brand pages
  const brandUids = ['6349791448', '5652018762', '2804387887'];
  for (const uid of brandUids) {
    console.log(`\n--- Checking brand uid:${uid} ---`);
    const existingTarget = targets.find(t => t.url().includes(`/u/${uid}`));
    if (existingTarget) {
      const page = await existingTarget.page();
      if (page) {
        const text = await page.evaluate(() => {
          const feed = document.querySelector('[node-type="feed_list"]') || document.body;
          return feed.innerText.slice(0, 500);
        });
        console.log('Found page:', text.slice(0, 200));
      }
    }
  }
  
  console.log('\nDone');
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(0);
});
