import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

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

function isTargetDay(dateStr, today) {
  if (!dateStr) return false;
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  const nd = ds => { const p=ds.split(/[-/]/); return p.length===2 ? String(parseInt(p[0])).padStart(2,'0')+'-'+String(parseInt(p[1])).padStart(2,'0') : ds; };
  return nd(dateStr) === y || nd(dateStr) === t;
}

function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) return false;
  if (/进入微博/.test(text) || /登录注册/.test(text)) return false;
  return true;
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×|品牌大使/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

const profileDir = '/Users/yifansmacmini/Library/Application Support/Google/Chrome';
console.log('Starting browser with real profile...');
const context = await chromium.launchPersistentContext(profileDir, {
  headless: true,
  args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
});

// Stealth: hide automation
await context.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
});

const page = await context.newPage();
const today = new Date();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  const url = 'https://weibo.com/u/' + uid;
  
  process.stdout.write('[' + (i+1) + '/19] ' + b.name + '... ');
  
  try {
    // First visit weibo.com to ensure cookies are set
    await page.goto('https://weibo.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    
    // Navigate to the brand page
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(8000);
    
    // Check page content
    const pageText = await page.evaluate(() => document.body.innerText);
    const isBlocked = pageText.includes('前方有点拥堵') || (pageText.includes('登录') && pageText.includes('注册') && !pageText.includes('粉丝'));
    const pageLen = pageText.length;
    
    if (isBlocked) {
      console.log('被拦截 (' + pageLen + ' chars)');
      results[b.name] = { '新品': [], 'IP': [], '营销': [] };
      await page.waitForTimeout(3000);
      continue;
    }
    
    // Scroll for lazy loading
    for (const y of [0, 600, 1200, 1800]) {
      try { await page.evaluate((Y) => window.scrollTo(0, Y), y); } catch(e) {}
      await page.waitForTimeout(2000);
    }
    
    // Extract posts from raw text - weibo.com doesn't have clean selectors in new version
    const posts = await page.evaluate(() => {
      const results = [];
      const allText = document.body.innerText;
      const lines = allText.split('\n').filter(l => l.trim().length > 15);
      
      // Find date patterns and surrounding content
      let currentDate = '';
      for (let j = 0; j < lines.length; j++) {
        const line = lines[j].trim();
        const dateMatch = line.match(/(\d{1,2}[-/]\d{1,2})\s+\d{1,2}:\d{2}/);
        if (dateMatch) {
          currentDate = dateMatch[1];
          // Collect the next lines as content
          let content = '';
          for (let k = j + 1; k < Math.min(j + 8, lines.length); k++) {
            const nextLine = lines[k].trim();
            // Stop at next date marker
            if (nextLine.match(/(\d{1,2}[-/]\d{1,2})\s+\d{1,2}:\d{2}/)) break;
            // Skip noise
            if (nextLine.includes('帮助中心') || nextLine.includes('微博客服') || 
                nextLine.includes('营业执照') || nextLine.includes('Copyright') ||
                nextLine.includes('开放平台') || nextLine.includes('举报')) continue;
            if (nextLine.length > 5) content += (content ? ' ' : '') + nextLine;
          }
          if (content.length > 20) {
            results.push({ date: currentDate, text: content });
          }
        }
      }
      return results;
    });
    
    const filtered = posts.filter(p => isTargetDay(p.date, today)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const cleaned = (p.text || '')
        .replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '').replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '')
        .replace(/展开全文|收起全文/g, '').trim();
      cats[classify(cleaned)].push(cleaned);
    }
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条 (' + pageLen + ' chars)');
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + (e.message || '').slice(0, 40));
  }
  await page.waitForTimeout(5000);
}

await context.close();

// Generate report
const dateStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
const dateDisplay = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';

let report = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：前一日 0:00 - 当日当前\n\n---\n\n';
const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
let tableRows = '';
const activeBrands = [];

for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  const total = r['新品'].length + r['IP'].length + r['营销'].length;
  if (total === 0) continue;
  activeBrands.push(brand);
  totalAll['新品'] += r['新品'].length; totalAll['IP'] += r['IP'].length; totalAll['营销'] += r['营销'].length;
  report += '## ' + brand.name + '\n\n【新品上市】\n';
  if (r['新品'].length) r['新品'].forEach(t => report += '- ' + t.slice(0, 300) + '\n'); else report += '- 暂无新品\n';
  report += '\n【IP联名/艺人宣发】\n';
  if (r['IP'].length) r['IP'].forEach(t => report += '- ' + t.slice(0, 300) + '\n'); else report += '- 暂无IP联名/艺人宣发\n';
  report += '\n【营销活动】\n';
  if (r['营销'].length) r['营销'].forEach(t => report += '- ' + t.slice(0, 300) + '\n'); else report += '- 暂无营销活动\n';
  report += '\n---\n\n';
  tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
}

if (tableRows) {
  report += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n' + tableRows;
  report += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
  const newBrands = activeBrands.filter(b => results[b.name]['新品'].length > 0);
  const ipBrands = activeBrands.filter(b => results[b.name]['IP'].length > 0);
  report += '## 今日行业洞察\n\n';
  if (newBrands.length) report += '1. **新品动态**：' + newBrands.map(b => b.name).join('、') + ' 等品牌有新品发布，共' + totalAll['新品'] + '款。\n\n';
  if (ipBrands.length) report += '2. **IP联名**：' + ipBrands.map(b => b.name).join('、') + ' 等品牌有IP联名/代言人动态。\n\n';
  report += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌今日有更新。\n';
} else {
  report += '今日暂无品牌更新数据。\n';
}

const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
