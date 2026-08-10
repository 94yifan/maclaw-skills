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
  const isIP = /联名|代言|×|品牌大使/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

async function crawlBrand(page, brand) {
  const url = brand.uid === 'starbucks' ? 'https://m.weibo.cn/u/1741514817' : 'https://m.weibo.cn/u/' + brand.uid;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
  } catch(e) {
    try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 }); } catch(e2) {}
  }
  await page.waitForTimeout(5000);

  // Scroll to load more
  for (const y of [0, 800, 1600]) {
    try { await page.evaluate((Y) => window.scrollTo(0, Y), y); } catch(e) {}
    await page.waitForTimeout(1500);
  }

  const posts = await page.evaluate(() => {
    const results = [];
    const cards = document.querySelectorAll('.card');
    for (const card of cards) {
      const timeEl = card.querySelector('.time, .weibo-time, span.time');
      const textEl = card.querySelector('.weibo-text, .card-text, .txt');
      if (!textEl) continue;
      const text = (textEl.innerText || textEl.textContent || '').trim().slice(0, 350);
      const timeStr = timeEl ? timeEl.innerText.trim().split(' ')[0] : '';
      if (text.length > 10) {
        results.push({ date: timeStr, text });
      }
    }
    return results;
  });

  return posts;
}

function generateReport(results) {
  const now = new Date();
  const dateDisplay = now.getFullYear() + '年' + String(now.getMonth()+1).padStart(2,'0') + '月' + String(now.getDate()).padStart(2,'0') + '日';

  let out = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：前一日 0:00 - 当日当前\n\n---\n\n';
  const allBrandData = {};

  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const cats = r;
    allBrandData[brand.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    if (total === 0) continue;

    out += '## ' + brand.name + '\n\n';
    out += '【新品上市】\n';
    if (cats['新品'].length) cats['新品'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无新品\n';
    out += '\n【IP联名/艺人宣发】\n';
    if (cats['IP'].length) cats['IP'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无IP联名/艺人宣发\n';
    out += '\n【营销活动】\n';
    if (cats['营销'].length) cats['营销'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无营销活动\n';
    out += '\n---\n\n';
  }

  const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
  let tableRows = '';
  for (const brand of brands) {
    const r = allBrandData[brand.name];
    if (!r) continue;
    const t = r['新品'].length + r['IP'].length + r['营销'].length;
    if (t === 0) continue;
    totalAll['新品'] += r['新品'].length;
    totalAll['IP'] += r['IP'].length;
    totalAll['营销'] += r['营销'].length;
    tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
  }

  if (tableRows) {
    out += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n';
    out += tableRows;
    out += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';

    const newBrands = Object.keys(allBrandData).filter(b => allBrandData[b]['新品'].length > 0);
    const ipBrands = Object.keys(allBrandData).filter(b => allBrandData[b]['IP'].length > 0);
    const activeBrands = Object.keys(allBrandData).filter(b => {
      const x = allBrandData[b];
      return x['新品'].length + x['IP'].length + x['营销'].length > 0;
    });

    out += '## 今日行业洞察\n\n';
    if (newBrands.length) out += '1. **新品动态**：' + newBrands.join('、') + ' 等品牌有新品发布，共' + totalAll['新品'] + '款新品。\n\n';
    if (ipBrands.length) out += '2. **IP联名**：' + ipBrands.join('、') + ' 等品牌有IP联名/代言人动态。\n\n';
    out += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌今日有更新。\n';
  } else {
    out += '今日暂无品牌更新数据。\n';
  }
  out = out.replace(/\n\n\n+/g, '\n\n');
  return out;
}

// Main
console.log('启动浏览器...');
const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});
const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
});
const page = await context.newPage();
await page.setViewportSize({ width: 390, height: 844 });

const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    const filtered = posts.filter(p => isTargetDay(p.date)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { 
      const cleaned = (p.text || '')
        .replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '')
        .replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '')
        .replace(/展开全文|收起全文/g, '')
        .trim();
      cats[classify(cleaned)].push(cleaned); 
    });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条');
  } catch (e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    process.stdout.write('err: ' + (e.message || '').slice(0, 40) + '\n');
  }
  await page.waitForTimeout(3000 + Math.random() * 2000);
}

await browser.close();

const report = generateReport(results);
const now = new Date();
const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
