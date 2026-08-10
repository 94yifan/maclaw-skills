import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const ctx = browser.contexts()[0] || await browser.newContext();
const page = await ctx.newPage();
await page.setViewportSize({ width: 390, height: 844 });

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
];

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const url = 'https://m.weibo.cn/u/' + b.uid;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(4000);
  for (const y of [0, 600, 1200]) {
    await page.evaluate((Y) => window.scrollTo(0, Y), y);
    await page.waitForTimeout(1500);
  }
  const posts = await page.evaluate(() => {
    const cards = document.querySelectorAll('.card');
    const results = [];
    for (const card of cards) {
      const timeEl = card.querySelector('span.time');
      const textEl = card.querySelector('.weibo-text');
      if (timeEl && textEl) {
        results.push({
          time: timeEl.innerText.trim(),
          text: textEl.innerText.trim().slice(0, 80)
        });
      }
    }
    return results;
  });
  console.log('[' + (i+1) + '/' + brands.length + '] ' + b.name + ': ' + posts.length + '条 | 最近:' + posts[0]?.time);
  await page.waitForTimeout(3000);
}

await browser.close();
