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

// Time filter: 5月31日 08:00 - 6月2日
function isInWindow(dateStr) {
  if (!dateStr) return false;
  const today = new Date(2026, 5, 2); // June 2, 2026
  const cutoff = new Date(2026, 4, 31, 8, 0, 0); // May 31, 08:00

  // Handle relative dates like "16小时前", "2天前"
  const relativeMatch = dateStr.match(/^(\d+)(小时|分钟|天)(前)?$/);
  if (relativeMatch) {
    const num = parseInt(relativeMatch[1]);
    const unit = relativeMatch[2];
    const postDate = new Date(today);
    if (unit === '小时') postDate.setHours(postDate.getHours() - num);
    else if (unit === '分钟') postDate.setMinutes(postDate.getMinutes() - num);
    else if (unit === '天') postDate.setDate(postDate.getDate() - num);
    return postDate >= cutoff;
  }

  // Handle date like "5-31" or "05-31"
  const dateMatch = dateStr.match(/^(\d{1,2})[-/](\d{1,2})$/);
  if (dateMatch) {
    const m = parseInt(dateMatch[1]), d = parseInt(dateMatch[2]);
    const postDate = new Date(2026, m - 1, d);
    return postDate >= cutoff;
  }

  return false;
}

function classify(text) {
  if (/联名|代言|×|品牌大使/.test(text)) return 'IP';
  if (/新品|上市|首发|新系列|新口味|全新|升级回归/.test(text)) return '新品';
  return '营销';
}

function cleanText(text) {
  return text.replace(/#[^#]+#/g, '').replace(/@\S+/g, '')
    .replace(/展开全文|收起全文/g, '').replace(/关注\s*@\S+/g, '')
    .replace(/\s{3,}/g, ' ').trim();
}

console.log('Connecting to CDP...');
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let ctx = browser.contexts()[0];
if (!ctx) ctx = await browser.newContext();
const page = await ctx.newPage();

const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');

  try {
    await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await new Promise(r => setTimeout(r, 6000));

    // Scroll
    for (const y of [0, 600, 1200]) {
      try { await page.evaluate((Y) => window.scrollTo(0, Y), y); } catch(e) {}
      await new Promise(r => setTimeout(r, 2000));
    }

    // Extract posts from the page
    const posts = await page.evaluate(() => {
      const results = [];
      const allText = document.body.innerText;
      const lines = allText.split('\n').filter(l => l.trim().length > 3);

      let currentDate = '';
      let currentContent = '';

      for (const line of lines) {
        const l = line.trim();
        // Detect date/timestamp
        const relativeDate = l.match(/^(\d+)(小时前|分钟前|天前)$/);
        const absDate = l.match(/^(\d{1,2})[-/](\d{1,2})(?:\s+\d{1,2}:\d{2})?$/);
        const isDate = relativeDate || absDate;

        if (isDate) {
          if (currentContent.length > 20 && currentDate) {
            results.push({ date: currentDate, text: currentContent });
          }
          currentDate = relativeDate ? relativeDate[0] : (absDate[1] + '-' + absDate[2]);
          currentContent = '';
        } else if (l.length > 15 && l.length < 400 && !l.includes('帮助中心') && !l.includes('微博客服') &&
                   !l.includes('营业执照') && !l.includes('Copyright') && !l.includes('开放平台') &&
                   !l.includes('举报') && !l.match(/^\d+[.\d]*$/) && !l.startsWith('IP属地')) {
          currentContent += (currentContent ? ' ' : '') + l;
        }
      }
      if (currentContent.length > 20 && currentDate) {
        results.push({ date: currentDate, text: currentContent });
      }
      return results;
    });

    const filtered = posts.filter(p => isInWindow(p.date));
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
    console.log('err: ' + (e.message || '').slice(0, 30));
  }

  await new Promise(r => setTimeout(r, 8000));
}

await page.close();
if (!browser.isConnected()) process.exit(1);

// Generate report
const dateStr = '2026-06-02';
const dateDisplay = '2026年6月2日';

let report = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：2026年5月31日 08:00 - 6月2日 01:30\n\n---\n\n';
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
  if (r['新品'].length) r['新品'].forEach(t => report += '- ' + t.slice(0, 200) + '\n'); else report += '- 暂无新品\n';
  report += '\n【IP联名/艺人宣发】\n';
  if (r['IP'].length) r['IP'].forEach(t => report += '- ' + t.slice(0, 200) + '\n'); else report += '- 暂无IP联名/艺人宣发\n';
  report += '\n【营销活动】\n';
  if (r['营销'].length) r['营销'].forEach(t => report += '- ' + t.slice(0, 200) + '\n'); else report += '- 暂无营销活动\n';
  report += '\n---\n\n';
  tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
}

if (tableRows) {
  report += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n' + tableRows;
  report += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
  const newB = activeBrands.filter(b => results[b]['新品'].length > 0);
  const ipB = activeBrands.filter(b => results[b]['IP'].length > 0);
  report += '## 今日行业洞察\n\n';
  if (newB.length) report += '1. **新品动态**：' + newB.join('、') + '等' + newB.length + '个品牌有新动作。\n\n';
  if (ipB.length) report += '2. **IP联名**：' + ipB.join('、') + '等品牌有IP联名/代言人动态。\n\n';
  report += '3. **市场活跃度**：' + activeBrands.length + '/' + brands.length + '个品牌在监测时段内有更新。\n';
} else {
  report += '今日暂无品牌更新数据。\n';
}

const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
