import { chromium } from 'playwright-core';
import { execSync } from 'child_process'; import { writeFileSync } from 'fs';
import { spawn } from 'child_process';

// Launch Chrome with CDP
execSync('pkill -9 -f "Google Chrome" 2>/dev/null; sleep 1; rm -rf /tmp/weibo-cdp 2>/dev/null');

const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--remote-debugging-port=9333',
  '--user-data-dir=/tmp/weibo-cdp',
  '--headless=new',
  '--disable-gpu', '--disable-software-rasterizer',
  '--no-sandbox', '--no-first-run',
  '--disable-background-networking', '--disable-sync',
  '--disable-extensions', '--disable-component-update'
], { stdio: 'ignore', detached: true });
chrome.unref();

// Wait for CDP
for (let i = 0; i < 20; i++) {
  await new Promise(r => setTimeout(r, 1000));
  try {
    const resp = await fetch('http://127.0.0.1:9333/json/version');
    if (resp.ok) break;
  } catch(e) {}
  if (i === 19) { console.log('CDP_TIMEOUT'); process.exit(1); }
}

console.log('CDP connected, logging in...');
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
const ctx = browser.contexts()[0];
const page = await ctx.newPage();

// Go to login page
await page.goto('https://passport.weibo.cn/signin/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 3000));

// Click "账号登录" tab
try {
  const tabBtn = await page.$('text=账号登录');
  if (tabBtn) await tabBtn.click();
  await new Promise(r => setTimeout(r, 2000));
} catch(e) {}

// Fill in credentials
const phoneInput = await page.$('input[type="tel"], input[name="username"], input[placeholder*="手机"]');
if (phoneInput) {
  await phoneInput.fill('15364917418');
  await new Promise(r => setTimeout(r, 1000));
}

const pwdInput = await page.$('input[type="password"], input[name="password"], input[placeholder*="密码"]');
if (pwdInput) {
  await pwdInput.fill('940904');
  await new Promise(r => setTimeout(r, 1000));
}

// Click login button
const loginBtn = await page.$('button[type="submit"], a[class*="login"], [class*="submit"]');
if (loginBtn) {
  await loginBtn.click();
  console.log('Login submitted!');
} else {
  // Try form submit
  await page.evaluate(() => document.querySelector('form')?.submit());
}

// Wait for login to process
await new Promise(r => setTimeout(r, 8000));

// Check login status
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 5000));

const text = await page.evaluate(() => document.body.innerText);
const loggedIn = !text.includes('前方有点拥堵') && text.includes('粉丝');
console.log('LOGGED_IN:', loggedIn, 'LEN:', text.length);

if (loggedIn) {
  console.log('Login success! Starting crawl...');
  // Save screenshot for confirmation
  await page.screenshot({ path: '/tmp/weibo-loggedin-confirm.png' });
  
  // Now crawl all 19 brands
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

  const results = {};
  const today = new Date();

  for (let i = 0; i < brands.length; i++) {
    const b = brands[i];
    const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
    process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
    
    try {
      await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await new Promise(r => setTimeout(r, 5000));
      await page.evaluate(() => window.scrollTo(0, 800)).catch(() => {});
      await new Promise(r => setTimeout(r, 2000));
      
      const bodyText = await page.evaluate(() => document.body.innerText);
      const lines = bodyText.split('\n').filter(l => l.trim().length > 3);
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
    
    await new Promise(r => setTimeout(r, 5000));
  }

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
    const t = r['新品'].length + r['IP'].length + r['营销'].length;
    if (t === 0) continue;
    activeBrands.push(brand.name);
    totalAll['新品'] += r['新品'].length; totalAll['IP'] += r['IP'].length; totalAll['营销'] += r['营销'].length;
    report += '## ' + brand.name + '\n\n【新品上市】\n';
    if (r['新品'].length) r['新品'].forEach(tx => report += '- ' + tx.slice(0, 250) + '\n'); else report += '- 暂无新品\n';
    report += '\n【IP联名/艺人宣发】\n';
    if (r['IP'].length) r['IP'].forEach(tx => report += '- ' + tx.slice(0, 250) + '\n'); else report += '- 暂无IP联名/艺人宣发\n';
    report += '\n【营销活动】\n';
    if (r['营销'].length) r['营销'].forEach(tx => report += '- ' + tx.slice(0, 250) + '\n'); else report += '- 暂无营销活动\n';
    report += '\n---\n\n';
    tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
  }

  if (tableRows) {
    report += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n' + tableRows;
    report += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
    const newB = activeBrands.filter(b => results[b]['新品'].length > 0);
    const ipB = activeBrands.filter(b => results[b]['IP'].length > 0);
    report += '## 今日行业洞察\n\n';
    if (newB.length) report += '1. **新品动态**：' + newB.join('、') + ' 等品牌有新品发布。\n\n';
    if (ipB.length) report += '2. **IP联名**：' + ipB.join('、') + ' 等品牌有IP联名动态。\n\n';
    report += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌有更新。\n';
  } else {
    report += '今日暂无品牌更新数据。\n';
  }

  const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-06-01.md';
  writeFileSync(outFile, report);
  console.log('\n=== 报告已写入 ' + outFile + ' ===');
} else {
  console.log('Login failed');
  await page.screenshot({ path: '/tmp/weibo-login-fail.png' });
}

await browser.close();
process.exit(0);
