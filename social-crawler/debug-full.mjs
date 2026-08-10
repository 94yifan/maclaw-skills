import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const ctx = browser.contexts()[0] || await browser.newContext();
const page = await ctx.newPage();
await page.setViewportSize({ width: 390, height: 844 });

function isTargetDay(dateStr) {
  if (!dateStr) return false;
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

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks' },
  { name: '茶百道', uid: '6502206660' },
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

const results = {};
for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const url = 'https://m.weibo.cn/u/' + b.uid;
  try {
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
          results.push({ date: timeStr.split(' ')[0], time: timeStr.split(' ')[1] || '', text });
        }
      }
      return results;
    });
    
    const filtered = posts.filter(p => isTargetDay(p.date)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log('[' + (i+1) + '/' + brands.length + '] ' + b.name + ': ' + posts.length + '总帖, ' + filtered.length + '过滤后, ' + total + '条归类 | 最近:' + (posts[0]?.date || '?'));
    if (posts.length > 0) console.log('  首帖时间:', posts[0].date, posts[0].time);
  } catch (e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('[' + (i+1) + '/' + brands.length + '] ' + b.name + ': ERROR ' + e.message.slice(0, 50));
  }
  await page.waitForTimeout(5000);
}
await browser.close();
console.log('\n=== RESULTS ===');
console.log(JSON.stringify(results, null, 2));
