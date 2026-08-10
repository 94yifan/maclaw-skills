import { chromium } from 'playwright';

const CDP_URL = 'http://127.0.0.1:9333';

const BRANDS = [
  { name: '瑞幸咖啡', uid: '6349791448', type: 'uid' },
  { name: '库迪', uid: '7791266545', type: 'uid' },
  { name: '古茗', uid: '2809775704', type: 'uid' },
  { name: '幸运咖', uid: '6519396553', type: 'uid' },
  { name: '茉莉奶白', uid: '7577524421', type: 'uid' },
  { name: '霸王茶姬', uid: '5652018762', type: 'uid' },
  { name: '喜茶', uid: '2804387887', type: 'uid' },
  { name: '星巴克', uid: 'starbucks', type: 'username' },
  { name: '茶百道', uid: '6502206666', type: 'uid' },
  { name: '奈雪的茶', uid: '5884674413', type: 'uid' },
  { name: 'CoCo', uid: '2030619861', type: 'uid' },
  { name: '爷爷不泡茶', uid: '7769072120', type: 'uid' },
  { name: '沪上阿姨', uid: '3921865344', type: 'uid' },
  { name: '乐乐茶', uid: '6253473981', type: 'uid' },
  { name: '皮爷咖啡', uid: '6360528436', type: 'uid' },
  { name: 'M Stand', uid: '6345199298', type: 'uid' },
  { name: 'Manner', uid: '6808111794', type: 'uid' },
  { name: '茉酸奶', uid: '5188894132', type: 'uid' },
  { name: '树夏酸奶', uid: '7144806571', type: 'uid' },
];

const browser = await chromium.connectOverCDP(CDP_URL);
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();
await page.setViewportSize({ width: 1280, height: 900 });

const results = [];

for (let i = 0; i < BRANDS.length; i++) {
  const brand = BRANDS[i];
  try {
    await page.goto(`https://weibo.com/u/${brand.uid}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.evaluate(() => window.scrollBy(0, 500));
    await page.waitForTimeout(2000);
    
    const text = await page.evaluate(() => {
      const items = document.querySelectorAll('[node-type="feed_list_content"]');
      return Array.from(items).slice(0, 10).map(el => el.innerText).join('\n---\n');
    });
    
    results.push({ brand: brand.name, uid: brand.uid, success: true, text });
  } catch (e) {
    results.push({ brand: brand.name, uid: brand.uid, success: false, error: e.message });
  }
  
  if (i < BRANDS.length - 1) {
    await page.waitForTimeout(8000);
  }
}

console.log('===RESULTS_START===');
console.log(JSON.stringify(results, null, 2));
console.log('===RESULTS_END===');

await browser.close();
