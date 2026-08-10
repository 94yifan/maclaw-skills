import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks' },
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
  { name: '林里LINLEE', uid: '7608120899' },
  { name: '柠季', uid: '7592401864' },
  { name: '挪瓦咖啡', uid: '7268463229' }
];

const today = new Date();
const dateStr = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';
const dateFile = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
const crawlTime = today.toTimeString().slice(0,5);

const output = { date: dateStr, crawlTime, brands: [] };

const PORTS = [9333, 9222, 9500];
let browser;
for (const port of PORTS) {
  try {
    browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
    console.log('Connected to CDP port', port);
    break;
  } catch (e) {
    if (port === PORTS[PORTS.length - 1]) {
      console.log('CDP_CONNECTION_FAILED');
      process.exit(1);
    }
  }
}

const context = browser.contexts()[0] || browser;
const page = await context.newPage();
await page.setViewportSize({ width: 1280, height: 900 });

const now = new Date();
const yesterday = new Date(now);
yesterday.setDate(yesterday.getDate() - 1);
yesterday.setHours(10, 0, 0, 0);

for (const brand of brands) {
  console.log('Crawling', brand.name);
  const url = brand.uid === 'starbucks'
    ? 'https://weibo.com/starbucks'
    : 'https://weibo.com/u/' + brand.uid;
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(5000);
    await page.evaluate((pos) => window.scrollTo(0, pos), 0);
    await page.waitForTimeout(2000);
    await page.evaluate((pos) => window.scrollTo(0, pos), 800);
    await page.waitForTimeout(2000);
    await page.evaluate((pos) => window.scrollTo(0, pos), 1600);
    await page.waitForTimeout(2000);
    await page.evaluate((pos) => window.scrollTo(0, pos), 2400);
    await page.waitForTimeout(2000);
  } catch (e) {
    output.brands.push({ name: brand.name, error: e.message });
    await page.waitForTimeout(10000);
    continue;
  }

  const posts = await page.$$eval('[node-type="feed_list_content"]', els =>
    els.map(el => ({
      time: el.querySelector('.time')?.textContent?.trim() || '',
      text: el.querySelector('.detail_text')?.textContent?.trim() || el.textContent?.trim() || ''
    }))
  );

  if (posts.length === 0) {
    const alt = await page.$$eval('[action-type="feed_list_item"]', els =>
      els.map(el => ({
        time: el.querySelector('.time')?.textContent?.trim() || el.querySelector('[node-type="datetime"]')?.textContent?.trim() || '',
        text: el.querySelector('.text')?.textContent?.trim() || el.querySelector('.detail')?.textContent?.trim() || el.textContent?.trim() || ''
      }))
    );
    if (alt.length > 0) posts.push(...alt);
  }

  const filtered = posts.filter(p => {
    if (!p.text || p.text.length < 15) return false;
    if (p.text.includes('登录注册')) return false;
    if (p.text.includes('加入群') || p.text.includes('粉丝群')) return false;
    const t = new Date(p.time);
    if (isNaN(t.getTime())) return true;
    return t >= yesterday && t <= now;
  });

  output.brands.push({ name: brand.name, posts: filtered });
  await page.waitForTimeout(10000);
}

await browser.disconnect();

writeFileSync('/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateFile + '.json', JSON.stringify(output, null, 2));
console.log('Done, saved to memory/weibo_daily_' + dateFile + '.json');
