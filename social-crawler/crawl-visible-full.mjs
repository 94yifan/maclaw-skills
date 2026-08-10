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
  if (/抱歉.*不存在|该昵称|暂无.*内容|登录注册/.test(text)) return false;
  if (/加入群|粉丝群\s*\d/.test(text)) return false;
  return true;
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×|品牌大使/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

const profileDir = '/Users/yifansmacmini/Library/Application Support/Google/Chrome';
console.log('Launching visible browser...');
const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
});

// Stealth: override webdriver detection
await context.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
});

const page = await context.newPage();
const today = new Date();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  process.stdout.write('[' + (i+1) + '/19] ' + b.name + '... ');
  
  try {
    await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(8000);
    
    // Check if we got content
    const pageInfo = await page.evaluate(() => {
      const text = document.body.innerText;
      return {
        length: text.length,
        hasContent: text.includes('粉丝') && text.length > 500,
        isBlocked: text.includes('前方有点拥堵'),
        preview: text.substring(0, 300)
      };
    });
    
    console.log(`(${pageInfo.length} chars, blocked: ${pageInfo.isBlocked})`);
    
    if (pageInfo.isBlocked || !pageInfo.hasContent) {
      results[b.name] = { '新品': [], 'IP': [], '营销': [] };
      await page.waitForTimeout(3000);
      continue;
    }
    
    // Scroll
    for (const y of [0, 800, 1600]) {
      try { await page.evaluate((Y) => window.scrollTo(0, Y), y); } catch(e) {}
      await page.waitForTimeout(2000);
    }

    const posts = await page.evaluate(() => {
      const results = [];
      const items = document.querySelectorAll('.WB_cardwrap, .WB_feed, [class*="feed"]');
      for (const item of items) {
        const text = (item.innerText || '').trim();
        const timeMatch = text.match(/(\d{1,2}[-/]\d{1,2})\s+\d{1,2}:\d{2}/);
        const date = timeMatch ? timeMatch[1] : '';
        if (text.length > 20) results.push({ date, text: text.slice(0, 500) });
      }
      return results;
    });
    
    // Fallback: parse raw text
    if (posts.length === 0) {
      const allText = await page.evaluate(() => document.body.innerText);
      const lines = allText.split('\n').filter(l => l.trim().length > 20);
      let currentDate = '';
      for (const line of lines) {
        const dateMatch = line.match(/(\d{1,2})[-/](\d{1,2})\s+\d{1,2}:\d{2}/);
        if (dateMatch) {
          currentDate = dateMatch[1] + '-' + dateMatch[2];
          posts.push({ date: currentDate, text: '' });
        } else if (posts.length > 0 && posts[posts.length-1].text === '') {
          posts[posts.length-1].text = line;
        }
      }
    }
    
    const filtered = posts.filter(p => isTargetDay(p.date, today)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const cleaned = (p.text || '').replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '').replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '').replace(/展开全文|收起全文/g, '').trim();
      cats[classify(cleaned)].push(cleaned);
    }
    results[b.name] = cats;
    console.log('  => ' + (cats['新品'].length + cats['IP'].length + cats['营销'].length) + '条');
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + (e.message || '').slice(0, 40));
  }
  await page.waitForTimeout(8000);
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
