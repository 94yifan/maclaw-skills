import { chromium } from 'playwright-core';

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
];

function classifyPost(text) {
  if (!text || text.length < 5) return null;
  const isIP = /联名|代言|品牌大使|合作伙伴|ip合作|×|x |合作款|限量/.test(text) ||
    /明星|代言人|大使|官宣|签约/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|新上市|全新|升级|回归|出道|新鲜/.test(text) && !/暂无/.test(text);
  if (isIP) return 'IP';
  if (isNew) return '新品';
  return '营销';
}

function cleanText(t) {
  if (!t) return '';
  return t.replace(/^展开全文|^收起全文|[\[\]]/g, '').replace(/\n+/g, ' ').trim().slice(0, 300);
}

async function crawlBrand(page, brand) {
  const url = 'https://m.weibo.cn/u/' + brand.uid;
  let retries = 2;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(8000);
      
      const cards = await page.evaluate(() => {
        const items = document.querySelectorAll('.card, .m-panel, [class*="m-blog"], [class*="item"], [class*="card-major"], [class*="card-item"]');
        let result = [];
        for (const item of items) {
          const text = item.innerText || '';
          if (/\d{1,2}-\d{1,2}|\d+分钟前|\d+小时前|\d+天前/.test(text) && text.length > 30) {
            const lines = text.split('\n').filter(l => l.trim());
            const timeLine = lines.find(l => /\d{1,2}-\d{1,2}/.test(l) || /分钟前|小时前|天前/.test(l));
            const contentLines = lines.filter(l => 
              !l.includes('评论') && 
              !l.includes('赞') && 
              l !== timeLine &&
              !/^\d+$/.test(l)
            );
            const content = contentLines.join(' ');
            if (content.length > 15) {
              result.push({ text: content.slice(0, 300), time: timeLine || '' });
            }
          }
        }
        return result.slice(0, 10);
      });
      
      if (cards.length > 0) return cards;
      
    } catch(e) {
      console.log('  异常:', e.message.slice(0, 80));
    }
    await page.waitForTimeout(3000);
  }
  return [];
}

const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();
await page.setViewportSize({ width: 390, height: 844 });

const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
  const posts = await crawlBrand(page, b);
  results[b.name] = { posts };
  process.stdout.write(posts.length + '条\n');
  if (i < brands.length - 1) {
    await page.waitForTimeout(5000 + Math.random() * 3000);
  }
}

const fs = await import('fs');
fs.writeFileSync('/tmp/tea-crawl-0518.json', JSON.stringify(results, null, 2));
console.log('\n抓取完成，已保存 /tmp/tea-crawl-0518.json');

await browser.close();
process.exit(0);
