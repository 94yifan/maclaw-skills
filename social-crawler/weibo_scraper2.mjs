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

async function scrapeBrandCDP(browserWS, brand) {
  const browser = await playwright.chromium.connectOverCDP(browserWS);
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    await page.goto(`https://weibo.com/u/${brand.uid}`, { 
      waitUntil: 'domcontentloaded',
      timeout: 15000 
    });
    
    // Wait for JS to render content
    await page.waitForTimeout(4000);
    
    // Extract posts using page.evaluate
    const content = await page.evaluate(() => {
      // Try scrolling to trigger lazy load
      window.scrollTo(0, 300);
      window.scrollTo(0, 600);
      
      // Get raw page text for debugging
      const bodyText = document.body.innerText;
      const lines = bodyText.split('\n').filter(l => l.trim().length > 0);
      return lines.slice(0, 30).join('\n');
    });
    
    await browser.close();
    return { name: brand.name, uid: brand.uid, content, error: null };
  } catch (e) {
    await browser.close();
    return { name: brand.name, uid: brand.uid, content: '', error: e.message };
  }
}

async function main() {
  console.log('Connecting to Chrome via CDP...');
  const browserWS = 'http://localhost:9333';
  
  for (const brand of brands) {
    console.log(`\n=== ${brand.name} (${brand.uid}) ===`);
    const result = await scrapeBrandCDP(browserWS, brand);
    if (result.content) {
      console.log(result.content.substring(0, 2000));
    } else {
      console.log(`Error: ${result.error || 'No content'}`);
    }
    await new Promise(r => setTimeout(r, 2000));
  }
}

main().catch(console.error);