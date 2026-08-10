import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const REAL_CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const REAL_PROFILE = '/Users/yifansmacmini/Library/Application Support/Google/Chrome';

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
  const t = text || '';
  const isIP = /联名|代言|×|品牌大使/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

function cleanText(text) {
  return text.replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '')
    .replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '')
    .replace(/展开全文|收起全文/g, '')
    .replace(/关注\s*@\S+|转发\s*\d+|评论\s*\d+/g, '')
    .replace(/抽\d+位|送\d+份|抽奖/ig, '')
    .replace(/\s{3,}/g, ' ')
    .trim();
}

console.log('=== Launching real Chrome with real profile ===');
const context = await chromium.launchPersistentContext(REAL_PROFILE, {
  headless: false,
  executablePath: REAL_CHROME,
  args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
});

// Stealth
await context.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
});

const page = await context.newPage();

// First check if already logged in with existing cookies
console.log('Checking login status...');
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 6000));
let text = await page.evaluate(() => document.body.innerText);
let isLoggedIn = !text.includes('前方有点拥堵') && text.includes('粉丝');

if (!isLoggedIn) {
  console.log('Need login. Getting QR code...');
  await page.goto('https://passport.weibo.cn/signin/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 6000));
  await page.screenshot({ path: '/tmp/weibo-login-final.png' });
  writeFileSync('/tmp/weibo-login-signal.txt', 'SCREENSHOT_READY');
  console.log('LOGIN_SCREENSHOT at /tmp/weibo-login-final.png');
  
  // Wait for login - poll
  for (let i = 0; i < 120; i++) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 10000 });
      await new Promise(r => setTimeout(r, 4000));
      text = await page.evaluate(() => document.body.innerText);
      isLoggedIn = !text.includes('前方有点拥堵') && text.includes('粉丝');
      if (isLoggedIn) {
        console.log('Login detected after ' + (i*3) + 's!');
        break;
      }
    } catch(e) {}
    if (i % 10 === 0) console.log('Waiting for login... ' + (i*3) + 's');
  }
}

if (!isLoggedIn) {
  console.log('LOGIN_FAILED');
  await context.close();
  process.exit(1);
}

console.log('LOGGED_IN! Starting crawl of 19 brands...');
console.log('Page content length:', text.length);

// Parse what we can see
const lines = text.split('\n').filter(l => l.trim().length > 3);
console.log('Total lines:', lines.length);

// Find date patterns and posts
let currentDate = '';
let currentContent = '';
const allPosts = [];

for (let j = 0; j < lines.length; j++) {
  const line = lines[j].trim();
  const dateMatch = line.match(/(\d{1,2}[-/]\d{1,2})\s+\d{1,2}:\d{2}/);
  if (dateMatch) {
    if (currentContent && currentContent.length > 20 && currentDate) {
      allPosts.push({ date: currentDate, text: currentContent });
    }
    currentDate = dateMatch[1];
    currentContent = '';
  } else if (line.length > 5 && !line.includes('帮助中心') && !line.includes('微博客服') && 
             !line.includes('营业执照') && !line.includes('Copyright') && !line.includes('开放平台') &&
             !line.includes('举报') && !line.includes('热搜') && !line.includes('推荐') &&
             !line.includes('超话') && !line.includes('关注推荐') && !line.match(/^\d+\/\d+$/) &&
             !line.match(/^\d+[.\d]*万/) && !line.includes('转评赞') && !line.includes('视频累计播放') &&
             !line.match(/^\d+万粉丝/) && !line.match(/^\d+关注/) && line.length > 15) {
    currentContent += (currentContent ? ' ' : '') + line;
  }
}
if (currentContent && currentContent.length > 20 && currentDate) {
  allPosts.push({ date: currentDate, text: currentContent });
}

console.log('Raw posts found:', allPosts.length);
const todayPosts = allPosts.filter(p => isTargetDay(p.date));
console.log('Target day posts:', todayPosts.length);
todayPosts.slice(0, 5).forEach((p, i) => console.log(`  ${i}: [${p.date}] ${p.text.substring(0, 100)}`));

// Categorize target day posts
const results = {};
for (const brand of brands) {
  results[brand.name] = { '新品': [], 'IP': [], '营销': [] };
}

// If we can see posts on the first brand page, we can crawl all brands
// But the text parsing above might not be reliable. Let's crawl properly.
console.log('\n=== Full crawl of all 19 brands ===');
const today = new Date();

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  process.stdout.write('[' + (i+1) + '/19] ' + b.name + '... ');
  
  try {
    await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await new Promise(r => setTimeout(r, 6000));
    
    // Scroll for lazy loading
    for (const y of [0, 600, 1200]) {
      try { await page.evaluate((Y) => window.scrollTo(0, Y), y); } catch(e) {}
      await new Promise(r => setTimeout(r, 2000));
    }
    
    const brandText = await page.evaluate(() => document.body.innerText);
    const brandLines = brandText.split('\n').filter(l => l.trim().length > 3);
    
    // Parse posts
    let cDate = '';
    let cContent = '';
    const brandPosts = [];
    
    for (const line of brandLines) {
      const l = line.trim();
      const dm = l.match(/(\d{1,2})[-/](\d{1,2})\s+\d{1,2}:\d{2}/);
      if (dm) {
        if (cContent && cContent.length > 20 && cDate) brandPosts.push({ date: cDate, text: cContent });
        cDate = dm[1] + '-' + dm[2];
        cContent = '';
      } else if (l.length > 15 && !l.includes('帮助中心') && !l.includes('微博客服') && 
                 !l.includes('营业执照') && !l.includes('Copyright') && !l.includes('开放平台') &&
                 !l.includes('举报') && l.length < 500) {
        cContent += (cContent ? ' ' : '') + l;
      }
    }
    if (cContent && cContent.length > 20 && cDate) brandPosts.push({ date: cDate, text: cContent });
    
    const filtered = brandPosts.filter(p => isTargetDay(p.date));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const cleaned = cleanText(p.text);
      if (cleaned.length > 15) cats[classify(cleaned)].push(cleaned);
    }
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条');
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err');
  }
  
  await new Promise(r => setTimeout(r, 6000));
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
  if (newBrands.length) report += '1. **新品动态**：' + newBrands.join('、') + '等' + newBrands.length + '个品牌有新品发布，共' + totalAll['新品'] + '款。\n\n';
  if (ipBrands.length) report += '2. **IP联名**：' + ipBrands.join('、') + '等品牌有IP联名动态。\n\n';
  report += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌在监测时段内有更新。\n';
} else {
  report += '今日暂无品牌更新数据。\n';
}

const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
