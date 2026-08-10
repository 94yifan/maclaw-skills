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
  { name: '星巴克', uid: '1741514817' },
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
  { name: '挪瓦咖啡', uid: '7268463229' },
];

function cleanText(t) {
  if (!t) return '';
  return t.replace(/^展开全文|^收起全文|[\[\]]/g, '').replace(/\n+/g, ' ').trim().slice(0, 300);
}

async function crawlBrand(page, brand) {
  const url = 'https://m.weibo.cn/u/' + brand.uid;
  let retries = 2;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 12000 });
      await page.waitForTimeout(2500);
      const cards = await page.evaluate(() => {
        const items = document.querySelectorAll('.card, .m-panel, [class*="m-blog"], [class*="item"]');
        let result = [];
        for (const item of items) {
          const text = item.innerText || '';
          if (/\d{1,2}-\d{1,2}|\d+分钟前|\d+小时前/.test(text) && text.length > 30) {
            const lines = text.split('\n').filter(l => l.trim());
            const timeLine = lines.find(l => /\d{1,2}-\d{1,2}/.test(l) || /分钟前|小时前/.test(l));
            const content = lines.filter(l => !l.includes('评论') && !l.includes('赞') && l !== timeLine).join(' ');
            if (content.length > 15) result.push({ text: content, time: timeLine || '' });
          }
        }
        if (result.length === 0) {
          const allText = document.body.innerText;
          const blocks = allText.split(/(\d{1,2}-\d{1,2}|\d+分钟前)/);
          for (let i = 1; i < blocks.length; i += 2) {
            const time = blocks[i] || '';
            const content = (blocks[i-1] || '') + time + (blocks[i+1] || '');
            if (content.length > 40) result.push({ text: content.slice(-250), time });
          }
        }
        return result.slice(0, 10);
      });
      if (cards.length > 0) return cards;
    } catch(e) {}
    await page.waitForTimeout(2000);
  }
  return [];
}

console.log('Connecting to CDP on 9333...');
const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();
const allData = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    allData[b.name] = posts.map(p => ({ text: cleanText(p.text), time: p.time }));
    process.stdout.write(posts.length + '条\n');
  } catch(e) {
    allData[b.name] = [];
    process.stdout.write('错误: ' + e.message + '\n');
  }
  await page.waitForTimeout(3000 + Math.random() * 2000);
}

const outPath = '/tmp/tea-raw-2026-06-14.json';
writeFileSync(outPath, JSON.stringify(allData, null, 2));
console.log('\nSaved raw data to ' + outPath);
await browser.close();
process.exit(0);
