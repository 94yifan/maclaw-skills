import pkg from '/Users/yifansmacmini/.openclaw/workspace/social-crawler/node_modules/playwright-core/index.js';
const { chromium } = pkg;

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
  { name: '挪瓦咖啡', uid: '7268463229' },
];

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  const nd = ds => { const p=ds.split('-'); return (p.length===2 ? String(parseInt(p[0])).padStart(2,'0')+'-'+String(parseInt(p[1])).padStart(2,'0') : ds); };
  return nd(dateStr) === y || nd(dateStr) === t;
}

function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) return false;
  if (/加入群|粉丝群\s*\d/.test(text)) return false;
  return true;
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

async function crawlBrand(page, brand) {
  const url = 'https://m.weibo.cn/u/' + brand.uid;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(5000);
  for (const y of [0, 600, 1200, 1800]) {
    await page.evaluate((Y) => window.scrollTo(0, Y), y);
    await page.waitForTimeout(2000);
  }
  const posts = await page.evaluate(() => {
    const results = [];
    const cards = document.querySelectorAll('.card');
    for (const card of cards) {
      const timeEl = card.querySelector('span.time');
      const textEl = card.querySelector('.weibo-text');
      if (!timeEl || !textEl) continue;
      const timeStr = timeEl.innerText.trim();
      const text = textEl.innerText.trim().slice(0, 350);
      if (text.length > 10) {
        results.push({
          date: timeStr.split(' ')[0],
          time: timeStr.split(' ')[1] || '',
          text
        });
      }
    }
    return results;
  });
  return posts;
}

const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
let page;
try {
  const ctx = browser.contexts()[0];
  page = await ctx.newPage();
} catch(e) {
  page = await browser.newPage();
}
await page.setViewportSize({ width: 390, height: 844 });

const rawData = {};
for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i + 1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    const filtered = posts.filter(p => isTargetDay(p.date)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    rawData[b.name] = { all: filtered, cats };
    const total = filtered.length;
    console.log(total + '条 (新' + cats['新品'].length + ' IP' + cats['IP'].length + ' 营' + cats['营销'].length + ')');
  } catch (e) {
    rawData[b.name] = { all: [], cats: { '新品': [], 'IP': [], '营销': [] } };
    process.stdout.write('err: ' + e.message.slice(0, 40) + ' ');
  }
  await page.waitForTimeout(5000);
}
await browser.close();

// 保存原始数据
const now = new Date();
const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
const fs = await import('fs');
fs.writeFileSync('/tmp/tea-raw-' + dateStr + '.json', JSON.stringify(rawData, null, 2));
console.log('\n=== 原始数据已写入 /tmp/tea-raw-' + dateStr + '.json ===');
