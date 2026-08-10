import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const REAL_CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PROFILE = '/tmp/weibo-stable';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' }, { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' }, { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' }, { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' }, { name: '星巴克', uid: 'starbucks' },
  { name: '茶百道', uid: '6502206666' }, { name: '奈雪的茶', uid: '5884674413' },
  { name: 'CoCo', uid: '2030619861' }, { name: '爷爷不泡茶', uid: '7769072120' },
  { name: '沪上阿姨', uid: '3921865344' }, { name: '乐乐茶', uid: '6253473981' },
  { name: '皮爷咖啡', uid: '6360528436' }, { name: 'M Stand', uid: '6345199298' },
  { name: 'Manner', uid: '6808111794' }, { name: '茉酸奶', uid: '5188894132' },
  { name: '树夏酸奶', uid: '7144806571' },
];

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  const nd = ds => { const p=ds.split(/[-/]/); return p.length===2 ? String(parseInt(p[0])).padStart(2,'0')+'-'+String(parseInt(p[1])).padStart(2,'0') : ds; };
  return nd(dateStr) === y || nd(dateStr) === t;
}

function classify(text) {
  if (/联名|代言|×|品牌大使/.test(text)) return 'IP';
  if (/新品|上市|首发|新系列|新口味|全新|升级回归/.test(text)) return '新品';
  return '营销';
}

function clean(text) {
  return text.replace(/#[^#]+#/g, '').replace(/@\S+/g, '').replace(/展开全文|收起全文/g, '').trim();
}

console.log('Launching Chrome...');
const context = await chromium.launchPersistentContext(PROFILE, {
  headless: false,
  executablePath: REAL_CHROME,
  args: ['--no-sandbox', '--start-minimized']
});
const page = await context.newPage();

// Go to login and screenshot
await page.goto('https://passport.weibo.cn/signin/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 6000));
await page.screenshot({ path: '/tmp/weibo-login-final.png' });
console.log('SCREENSHOT_READY');

// Wait for login
for (let i = 0; i < 120; i++) {
  await new Promise(r => setTimeout(r, 3000));
  try {
    await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 10000 });
    await new Promise(r => setTimeout(r, 5000));
    const t = await page.evaluate(() => document.body.innerText);
    if (!t.includes('前方有点拥堵') && t.includes('粉丝')) {
      console.log('LOGGED_IN after ' + (i*3) + 's!');
      break;
    }
  } catch(e) {}
  if (i % 10 === 0) process.stdout.write(i*3 + 's...');
}

// Crawl ALL brands FAST
console.log('\nCrawling 19 brands...');
const today = new Date();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  process.stdout.write('[' + (i+1) + '] ' + b.name + '... ');
  try {
    await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(r => setTimeout(r, 4000));
    await page.evaluate(() => window.scrollTo(0, 800));
    await new Promise(r => setTimeout(r, 2000));
    
    const text = await page.evaluate(() => document.body.innerText);
    const lines = text.split('\n').filter(l => l.trim().length > 3);
    let cDate = '', cContent = '', posts = [];
    for (const line of lines) {
      const l = line.trim();
      const dm = l.match(/(\d{1,2})[-/](\d{1,2})\s+\d{1,2}:\d{2}/);
      if (dm) {
        if (cContent.length > 20 && cDate) posts.push({ date: cDate, text: cContent });
        cDate = dm[1] + '-' + dm[2];
        cContent = '';
      } else if (l.length > 15 && l.length < 300 && !l.includes('帮助中心') && !l.includes('微博客服') && !l.includes('营业执照') && !l.includes('Copyright') && !l.includes('开放平台')) {
        cContent += (cContent ? ' ' : '') + l;
      }
    }
    if (cContent.length > 20 && cDate) posts.push({ date: cDate, text: cContent });
    
    const filtered = posts.filter(p => isTargetDay(p.date));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const cleaned = clean(p.text);
      if (cleaned.length > 15) cats[classify(cleaned)].push(cleaned);
    }
    results[b.name] = cats;
    console.log((cats['新品'].length + cats['IP'].length + cats['营销'].length) + '条');
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err');
  }
}

await context.close();

// Generate report
const dateStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
const dateDisplay = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';

let report = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：2026年5月31日 08:00 - 6月1日 14:00\n\n---\n\n';
const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
let tableRows = '';
const activeBrands = [];

for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  const total = r['新品'].length + r['IP'].length + r['营销'].length;
  if (total === 0) continue;
  activeBrands.push(brand.name);
  totalAll['新品'] += r['新品'].length; totalAll['IP'] += r['IP'].length; totalAll['营销'] += r['营销'].length;
  report += '## ' + brand.name + '\n\n【新品上市】\n';
  if (r['新品'].length) r['新品'].forEach(t => report += '- ' + t.slice(0, 250) + '\n'); else report += '- 暂无新品\n';
  report += '\n【IP联名/艺人宣发】\n';
  if (r['IP'].length) r['IP'].forEach(t => report += '- ' + t.slice(0, 250) + '\n'); else report += '- 暂无IP联名/艺人宣发\n';
  report += '\n【营销活动】\n';
  if (r['营销'].length) r['营销'].forEach(t => report += '- ' + t.slice(0, 250) + '\n'); else report += '- 暂无营销活动\n';
  report += '\n---\n\n';
  tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
}

if (tableRows) {
  report += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n' + tableRows;
  report += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
  const newBrands = activeBrands.filter(b => results[b]['新品'].length > 0);
  const ipBrands = activeBrands.filter(b => results[b]['IP'].length > 0);
  report += '## 今日行业洞察\n\n';
  if (newBrands.length) report += '1. **新品动态**：' + newBrands.join('、') + ' 等品牌有新品发布。\n\n';
  if (ipBrands.length) report += '2. **IP联名**：' + ipBrands.join('、') + ' 等品牌有IP联名动态。\n\n';
  report += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌有更新。\n';
} else {
  report += '今日暂无品牌更新数据。\n';
}

const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
