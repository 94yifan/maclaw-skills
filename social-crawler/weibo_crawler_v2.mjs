import { chromium } from 'playwright';

const CDP_URL = 'http://127.0.0.1:9333';
const REPORT_DATE = '2026-05-10';
const OUTPUT_FILE = `/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_${REPORT_DATE}_raw.txt`;

// Connect to CDP
let browser;
try {
  browser = await chromium.connectOverCDP(CDP_URL);
  console.log('CDP connected');
} catch (e) {
  console.error('CDP connection failed:', e.message);
  process.exit(1);
}

const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks', isUsername: true },
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

const fs = await import('fs');
let output = `茶饮品牌热点日报 ${REPORT_DATE}\n\n`;

for (const brand of brands) {
  console.log(`=== ${brand.name} ===`);
  try {
    const url = brand.isUsername 
      ? `https://weibo.com/u/${brand.uid}`
      : `https://weibo.com/u/${brand.uid}`;
    
    await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(3000);
    
    // Get page content - try multiple approaches
    const content = await page.evaluate(() => {
      // Get body text directly
      const body = document.body.innerText;
      
      // Look for specific Weibo feed structure
      const feedContent = {
        bodyText: body.substring(0, 8000),
        hasLogin: document.querySelector('.WB_header') || document.querySelector('.pcb'),
        url: window.location.href
      };
      
      return feedContent;
    });
    
    output += `【${brand.name}】\n${content.bodyText}\n\n`;
    console.log(`Got ${content.bodyText.length} chars`);
    
  } catch (e) {
    console.error(`Error: ${brand.name} - ${e.message}`);
    output += `【${brand.name}】\n[Error: ${e.message}]\n\n`;
  }
  
  await page.waitForTimeout(8000);
}

fs.writeFileSync(OUTPUT_FILE, output);
console.log(`\nRaw data saved to ${OUTPUT_FILE}`);

await browser.close();
