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
    
    await page.goto(url, { 
      waitUntil: 'domcontentloaded',
      timeout: 20000 
    });
    
    // Wait for JS to render content
    await page.waitForTimeout(5000);
    
    // Scroll to trigger lazy load
    await page.evaluate(() => {
      window.scrollTo(0, 200);
      window.scrollTo(0, 500);
      window.scrollTo(0, 800);
    });
    await page.waitForTimeout(2000);
    
    const content = await page.evaluate(() => {
      const bodyText = document.body.innerText;
      const lines = bodyText.split('\n').filter(l => l.trim().length > 0);
      return lines.slice(0, 50).join('\n');
    });
    
    await browser.close();
    return { name: brand.name, uid: brand.uid || brand.username, content, error: null };
  } catch (e) {
    await browser.close();
    return { name: brand.name, uid: brand.uid || brand.username, content: '', error: e.message };
  }
}

async function main() {
  console.log('Connecting to Chrome via CDP...');
  const browserWS = 'http://localhost:9333';
  const results = [];
  
  for (const brand of brands) {
    console.log(`\n=== ${brand.name} ===`);
    const result = await scrapeBrandCDP(browserWS, brand);
    if (result.error) {
      console.log(`Error: ${result.error}`);
    } else {
      console.log(result.content ? result.content.substring(0, 1500) : 'No content');
    }
    results.push(result);
    await new Promise(r => setTimeout(r, 8000));
  }
  
  // Output JSON for parsing
  console.log('\n--- JSON OUTPUT ---');
  console.log(JSON.stringify(results, null, 2));
}

main().catch(console.error);
