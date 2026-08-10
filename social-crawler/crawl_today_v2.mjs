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

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  // 相对时间：几分钟前、几小时前 → 今天
  if (/分[钟]?前|小时前|刚刚/.test(dateStr)) return true;
  // 匹配 MM-DD 格式
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  return dateStr === y || dateStr === t;
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
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(5000);
  for (const y of [0, 400, 800, 1200, 1600, 2000]) {
    await page.evaluate((Y) => window.scrollTo(0, Y), y);
    await page.waitForTimeout(1500);
  }
  const posts = await page.evaluate(() => {
    const results = [];
    const cards = document.querySelectorAll('.card');
    for (const card of cards) {
      const timeEl = card.querySelector('span.time, .time, [class*=time]');
      const textEl = card.querySelector('.weibo-text');
      if (!timeEl || !textEl) continue;
      let timeStr = timeEl.innerText.trim();
      if (!timeStr) {
        const h4 = card.querySelector('h4');
        if (h4) timeStr = h4.innerText.trim().split('来自')[0].trim();
      }
      const text = textEl.innerText.trim().slice(0, 400);
      if (text.length > 10) {
        results.push({ date: timeStr.split(' ')[0], text });
      }
    }
    return results;
  });
  return posts;
}

async function main() {
  console.log('Connecting to CDP on port 9333...');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
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
      process.stdout.write('err: ' + e.message.slice(0, 60) + ' ');
    }
    await page.waitForTimeout(5000);
  }
  await browser.close();

  const now = new Date();
  const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
  const fs = await import('fs');
  fs.writeFileSync('/tmp/tea-raw-' + dateStr + '-v2.json', JSON.stringify(rawData, null, 2));
  console.log('\n=== 原始数据已写入 /tmp/tea-raw-' + dateStr + '-v2.json ===');
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
