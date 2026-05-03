import playwright from 'playwright';

const brands = [
  { name: '瑞幸咖啡', id: '6349791448' },
  { name: '库迪', id: '7791266545' },
  { name: '古茗', id: '2809775704' },
  { name: '幸运咖', id: '6519396553' },
  { name: '茉莉奶白', id: '7577524421' },
  { name: '霸王茶姬', id: '5652018762' },
  { name: '喜茶', id: '2804387887' },
  { name: '星巴克', id: 'starbucks' },
  { name: '茶百道', id: '6502206666' },
  { name: '奈雪的茶', id: '5884674413' },
  { name: 'CoCo', id: '2030619861' },
  { name: '爷爷不泡茶', id: '7769072120' },
  { name: '沪上阿姨', id: '3921865344' },
  { name: '乐乐茶', id: '6253473981' },
  { name: '皮爷咖啡', id: '6360528436' },
  { name: 'M Stand', id: '6345199298' },
  { name: 'Manner', id: '6808111794' },
  { name: '茉酸奶', id: '5188894132' },
  { name: '树夏酸奶', id: '7144806571' },
];

async function scrapeFromExistingTabs(browser, brand) {
  const url = brand.id === 'starbucks' ? 'https://weibo.com/starbucks' : `https://weibo.com/u/${brand.id}`;
  const contexts = browser.contexts();
  if (!contexts.length) return [];
  
  const ctx = contexts[0];
  const pages = await ctx.pages();
  
  // Find existing tab with same URL
  const existingPage = pages.find(p => {
    const pageUrl = p.url();
    return pageUrl.includes(`/u/${brand.id}`) || (brand.id === 'starbucks' && pageUrl.includes('/starbucks'));
  });
  
  if (existingPage) {
    await existingPage.waitForTimeout(2000);
    
    for (let i = 0; i < 3; i++) {
      await existingPage.evaluate(() => window.scrollBy(0, 300));
      await existingPage.waitForTimeout(1000);
    }
    
    const articles = await existingPage.evaluate(() => {
      const arts = document.querySelectorAll('article');
      return Array.from(arts).map(a => a.innerText.trim()).filter(t => t.length > 30).slice(0, 10);
    });
    
    return articles;
  }
  return [];
}

async function navigateAndScrape(browser, brand) {
  const url = brand.id === 'starbucks' ? 'https://weibo.com/starbucks' : `https://weibo.com/u/${brand.id}`;
  const contexts = browser.contexts();
  const ctx = contexts[0];
  const page = await ctx.newPage();
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(4000);
    
    for (let i = 0; i < 4; i++) {
      await page.evaluate(() => window.scrollBy(0, 400));
      await page.waitForTimeout(800);
    }
    
    const articles = await page.evaluate(() => {
      const arts = document.querySelectorAll('article');
      return Array.from(arts).map(a => a.innerText.trim()).filter(t => t.length > 30).slice(0, 10);
    });
    
    await page.close();
    return articles;
  } catch (e) {
    await page.close();
    return [];
  }
}

async function main() {
  const browser = await playwright.chromium.connectOverCDP('http://127.0.0.1:9333');
  const results = {};
  
  for (const brand of brands) {
    process.stderr.write(`\n[${brands.indexOf(brand)+1}/${brands.length}] ${brand.name}... `);
    
    // Try existing tabs first
    let articles = await scrapeFromExistingTabs(browser, brand);
    
    if (!articles.length) {
      // Navigate to the page
      articles = await navigateAndScrape(browser, brand);
    }
    
    results[brand.name] = articles;
    process.stderr.write(`found ${articles.length} articles`);
    
    await new Promise(r => setTimeout(r, 8000));
  }
  
  await browser.close();
  
  const fs = await import('fs');
  fs.writeFileSync('/tmp/weibo_scraped_2026-05-03.json', JSON.stringify(results, null, 2));
  console.log('Results saved to /tmp/weibo_scraped_2026-05-03.json');
}

main().catch(e => { console.error(e); process.exit(1); });
