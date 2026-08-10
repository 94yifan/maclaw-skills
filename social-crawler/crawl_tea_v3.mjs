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

// 判断时间戳是否在目标日期范围内（今天或昨天）
function isTargetDay(timeStr) {
  // 匹配 "5-13 10:01" 这种格式
  const fullMatch = timeStr.match(/^(\d+)-(\d+)\s+\d+:\d+$/);
  if (fullMatch) {
    const month = parseInt(fullMatch[1]);
    const day = parseInt(fullMatch[2]);
    const today = new Date().getDate();
    return day === today || day === today - 1;
  }
  // 匹配 "1小时前" "刚刚" "3分钟前" 等相对时间 → 算今天
  if (/小时前|分钟前|刚刚/.test(timeStr)) {
    return true;
  }
  // 其他格式（今天、昨天）默认放过
  return true;
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
  await page.goto('https://m.weibo.cn/u/' + brand.uid, { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForTimeout(4000);
  await page.evaluate(() => window.scrollTo(0, 800));
  await page.waitForTimeout(2000);

  const posts = await page.evaluate(() => {
    const cards = document.querySelectorAll('.card');
    const results = [];
    for (const card of cards) {
      const timeEl = card.querySelector('span.time');
      const textEl = card.querySelector('.weibo-text');
      if (!timeEl || !textEl) continue;
      const timeStr = timeEl.innerText.trim();
      const text = textEl.innerText.trim().slice(0, 350);
      if (text.length > 10) {
        results.push({ date: timeStr, time: '', text });
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
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const total = r['新品'].length + r['IP'].length + r['营销'].length;
    if (total === 0) continue;
    out += '## ' + brand.name + '\n\n';
    out += '【新品上市】\n';
    out += r['新品'].length ? r['新品'].map(p => '- [' + p.date + '] ' + p.text).join('\n') + '\n' : '- 暂无新品\n';
    out += '\n【IP联名/艺人宣发】\n';
    out += r['IP'].length ? r['IP'].map(p => '- [' + p.date + '] ' + p.text).join('\n') + '\n' : '- 暂无IP联名/艺人宣发\n';
    out += '\n【营销活动】\n';
    out += r['营销'].length ? r['营销'].map(p => '- [' + p.date + '] ' + p.text).join('\n') + '\n' : '- 暂无营销活动\n';
    out += '\n---\n\n';
  }
  const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    totalAll['新品'] += r['新品'].length;
    totalAll['IP'] += r['IP'].length;
    totalAll['营销'] += r['营销'].length;
  }
  out += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n';
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const total = r['新品'].length + r['IP'].length + r['营销'].length;
    if (total === 0) continue;
    out += '| ' + brand.name + ' | ' + r['新品'].length + ' | ' + r['IP'].length + ' | ' + r['营销'].length + ' |\n';
  }
  out += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
  out += '## 今日行业洞察\n\n';
  const newBrands = brands.filter(b => { const r = results[b.name]; return r && r['新品'].length > 0; });
  const activeBrands = brands.filter(b => { const r = results[b.name]; return r && (r['新品'].length + r['IP'].length + r['营销'].length) > 0; });
  const ipBrands = brands.filter(b => { const r = results[b.name]; return r && r['IP'].length > 0; });
  out += '1. **新品密集**：`' + (newBrands.map(b=>b.name).join('、') || '暂无') + '`等' + newBrands.length + '个品牌有新品动作，共' + totalAll['新品'] + '款。\n\n';
  out += '2. **行业动态**：`' + activeBrands.length + '`个品牌今日有更新，市场活跃。\n\n';
  out += '3. **IP联名**：`' + (ipBrands.map(b=>b.name).join('、') || '暂无') + '`等' + ipBrands.length + '个品牌有IP/代言动态。\n';
  return out;
}

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9333');
  const results = {};
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    try {
      const page = await browser.newPage();
      const posts = await crawlBrand(page, brand);
      const filtered = posts.filter(p => isTargetDay(p.date) && isValid(p.text));
      const categorized = { '新品': [], 'IP': [], '营销': [] };
      filtered.forEach(p => { categorized[classify(p.text)].push(p); });
      results[brand.name] = categorized;
      const total = filtered.length;
      console.log('[' + (i+1) + '/19] ' + brand.name + ': ' + total + '条 (新' + categorized['新品'].length + ' IP' + categorized['IP'].length + ' 营' + categorized['营销'].length + ')');
      await page.close();
    } catch(e) {
      console.log('[' + (i+1) + '/19] ' + brand.name + ': 错误 ' + e.message);
      results[brand.name] = { '新品': [], 'IP': [], '营销': [] };
    }
    await new Promise(r => setTimeout(r, 5000));
  }
  await browser.close();
  const report = generateReport(results);
  const targetDate = new Date().toISOString().slice(0,10);
  writeFileSync('./memory/weibo_daily_' + targetDate + '.md', report);
  console.log('\n=== 完成，报告已写入 memory/weibo_daily_' + targetDate + '.md ===');
}
main().catch(e => { console.error(e); process.exit(1); });
