import playwright from 'playwright';

const brands = [
  { name: '瑞幸咖啡', uid: '5308260857' },
  { name: '库迪咖啡', uid: '7497928702' },
  { name: '古茗茶饮', uid: '7480804260' },
  { name: '茉莉奶白', uid: '7541451616' },
  { name: '霸王茶姬', uid: '7453081605' },
  { name: '喜茶', uid: '612941' },
  { name: '乐乐茶', uid: '6212294155' },
  { name: 'T9tea', uid: '7609260234' },
  { name: '奈雪的茶', uid: '6615096941' },
  { name: '一只酸奶牛', uid: '740685496' },
  { name: '益禾堂', uid: '7468036877' },
  { name: 'CoCo都可', uid: '164208115' },
  { name: '书亦烧仙草', uid: '6617749221' },
  { name: '悸动烧仙草', uid: '7469168385' },
  { name: '沪上阿姨', uid: '7459931033' },
  { name: '茶百道', uid: '6615096942' },
  { name: '七分甜', uid: '7458273805' },
];

async function scrapeBrand(browser, brand) {
  const context = browser.contexts()[0];
  const page = await context.newPage();
  
  try {
    await page.goto(`https://weibo.com/u/${brand.uid}`, { 
      waitUntil: 'networkidle',
      timeout: 20000 
    });
    
    // Wait for content to load
    await page.waitForTimeout(3000);
    
    // Try to extract posts from the page
    const posts = await page.evaluate(() => {
      const items = document.querySelectorAll('.woo-panel-main');
      const results = [];
      
      // Look for Weibo post items
      const postItems = document.querySelectorAll('[action-type="feed_list_item"], .vue-recycle-scroller__item-view');
      
      document.querySelectorAll('.WB_feed .WB_cardwrap, .WB_feed_type').forEach(el => {
        const contentEl = el.querySelector('.WB_text, .feed_content');
        const timeEl = el.querySelector('.WB_from, .feed_from');
        const likeEl = el.querySelector('.WB_row_line li:nth-child(3) span, .item_agree');
        const cmtEl = el.querySelector('.WB_row_line li:nth-child(2) a, .item评论');
        const repostsEl = el.querySelector('.WB_row_line li:nth-child(1) a, .item转发');
        
        if (contentEl) {
          results.push({
            content: contentEl.innerText?.trim() || '',
            time: timeEl?.innerText?.trim() || '',
            likes: likeEl?.innerText?.trim() || '',
            comments: cmtEl?.innerText?.trim() || '',
            reposts: repostsEl?.innerText?.trim() || ''
          });
        }
      });
      
      return results;
    });
    
    await page.close();
    return { name: brand.name, uid: brand.uid, posts, error: null };
  } catch (e) {
    await page.close();
    return { name: brand.name, uid: brand.uid, posts: [], error: e.message };
  }
}

async function main() {
  console.log('Connecting to Chrome via CDP...');
  const browser = await playwright.chromium.connectOverCDP('http://localhost:9333');
  
  console.log('Scraping Weibo for tea brands...');
  const results = [];
  
  for (const brand of brands) {
    console.log(`Scraping ${brand.name} (${brand.uid})...`);
    const result = await scrapeBrand(browser, brand);
    results.push(result);
    console.log(`  -> Got ${result.posts.length} posts, error: ${result.error || 'none'}`);
    
    // Small delay between requests
    await new Promise(r => setTimeout(r, 1500));
  }
  
  console.log('\n--- SCRAPED DATA ---');
  console.log(JSON.stringify(results, null, 2));
  
  await browser.close();
}

main().catch(console.error);