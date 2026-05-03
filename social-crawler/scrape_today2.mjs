import playwright from 'playwright';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', username: 'starbucks' },
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

async function scrapeBrandCDP(browserWS, brand) {
  const browser = await playwright.chromium.connectOverCDP(browserWS);
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    const url = brand.username 
      ? `https://weibo.com/${brand.username}` 
      : `https://weibo.com/u/${brand.uid}`;
    
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // Try multiple scrolls to trigger lazy loading
    for (let i = 0; i < 5; i++) {
      await page.evaluate(() => window.scrollBy(0, 300));
      await page.waitForTimeout(1500);
    }
    
    // Extract posts - look for article or div elements
    const content = await page.evaluate(() => {
      // Try to get the main feed content
      const articles = document.querySelectorAll('article');
      const divs = document.querySelectorAll('[class*="content"]');
      const feeds = document.querySelectorAll('[class*="feed"]');
      
      // Get all text content
      const body = document.body.innerText;
      
      // Find posts by looking for timestamps
      const lines = body.split('\n');
      const relevant = [];
      let inPost = false;
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        // Detect timestamp patterns (e.g. "今天 10:00", "昨天 12:00", "4-30 14:00")
        if (/今天|昨天|\d+-\d+\s+\d+:\d+/.test(trimmed) && trimmed.length < 200) {
          inPost = true;
        }
        if (inPost) {
          relevant.push(trimmed);
          if (relevant.length > 100) break;
        }
      }
      
      return relevant.join('\n') || body.substring(0, 3000);
    });
    
    await browser.close();
    return { name: brand.name, uid: brand.uid || brand.username, content, error: null };
  } catch (e) {
    await browser.close();
    return { name: brand.name, uid: brand.uid || brand.username, content: '', error: e.message };
  }
}

async function main() {
  const browserWS = 'http://localhost:9333';
  const results = [];
  
  for (const brand of brands) {
    console.error(`\n=== ${brand.name} ===`);
    const result = await scrapeBrandCDP(browserWS, brand);
    results.push(result);
    if (result.error) {
      console.error(`Error: ${result.error}`);
    } else {
      console.error(result.content ? result.content.substring(0, 500) : 'No content');
    }
    await new Promise(r => setTimeout(r, 10000));
  }
  
  // Write JSON to a temp file for debugging
  const fs = await import('fs');
  fs.writeFileSync('/tmp/weibo_results.json', JSON.stringify(results, null, 2));
  console.log('Done - results in /tmp/weibo_results.json');
}

main().catch(console.error);
