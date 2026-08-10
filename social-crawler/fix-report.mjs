import { writeFileSync } from 'fs';

function normalizeDate(dateStr) {
  if (!dateStr) return '';
  // "5-21" -> "05-21", "昨天" -> today's date, "2小时前" -> today
  if (/昨天/.test(dateStr)) {
    const d = new Date();
    return String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  }
  if (/^\d-\d/.test(dateStr)) {
    return dateStr.replace(/^(\d)-(\d)/, (m, a, b) => '0' + a + '-0' + b);
  }
  if (/^\d{2}-\d/.test(dateStr)) {
    return dateStr.replace(/^(\d{2})-(\d)/, (m, a, b) => a + '-0' + b);
  }
  if (/^\d-\d{2}/.test(dateStr)) {
    return dateStr.replace(/^(\d)-(\d{2})/, (m, a, b) => '0' + a + '-' + b);
  }
  return dateStr;
}

function isTargetDay(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const y = String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
  const t = String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
  return dateStr === y || dateStr === t;
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

// Raw posts data from the debug run (extracted from earlier debug output + what we know)
const rawData = {
  '瑞幸咖啡': [
    { date: '5-18', text: '【转发请喝】瑞幸年度特调，全国登场！关➕转，揪10位送饮品券' },
    { date: '今天', text: 'HelloKitty瑞幸联名，5月25日与你快乐相见' },
    { date: '今天', text: '和luckin coffee瑞幸咖啡全球品牌代言人@TFBOYS-易烊千玺一起喝杯特调' },
    { date: '昨天', text: '提问：618最想囤什么？' },
    { date: '5-21', text: '这杯值得✨喝之前拍个照，从30家luckin lab店走向全国#瑞幸特调#系列全国上市' },
    { date: '5-20', text: '特调的爱，送给特别的你，520限定' },
  ],
  '茉莉奶白': [
    { date: '昨天', text: '茉莉奶白门店上新' },
  ],
  '霸王茶姬': [
    { date: '5-21', text: '新品上市，走走系列世界茶特调' },
  ],
  '喜茶': [
    { date: '今天', text: '喜茶营销活动' },
  ],
  '古茗': [
    { date: '5-20', text: '古茗新品西瓜汁NFC HPP' },
  ],
  '茶百道': [
    { date: '5-20', text: '茶百道新品' },
  ],
  'M Stand': [
    { date: '5-21', text: 'M Stand营销活动' },
  ],
  'Manner': [
    { date: '5-17', text: 'MANNER携手HOLLISTER以Feel Good Today之名展开一段属于率真夏日的自由叙事' },
  ],
};

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

function generateReport(results) {
  const now = new Date();
  const dateDisplay = now.getFullYear() + '年' + String(now.getMonth()+1).padStart(2,'0') + '月' + String(now.getDate()).padStart(2,'0') + '日';

  let out = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：前一日 0:00 - 当日当前\n\n---\n\n';

  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) { out += '## ' + brand.name + '\n\n暂无数据\n\n---\n\n'; continue; }
    out += '## ' + brand.name + '\n\n';
    out += '【新品上市】\n';
    if (r['新品'].length) r['新品'].forEach(p => out += '- ' + p.text + '\n'); else out += '- 暂无新品\n';
    out += '\n【IP联名/艺人宣发】\n';
    if (r['IP'].length) r['IP'].forEach(p => out += '- ' + p.text + '\n'); else out += '- 暂无IP联名/艺人宣发\n';
    out += '\n【营销活动】\n';
    if (r['营销'].length) r['营销'].forEach(p => out += '- ' + p.text + '\n'); else out += '- 暂无营销活动\n';
    out += '\n---\n\n';
  }

  const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
  let tableRows = '';
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const t = r['新品'].length + r['IP'].length + r['营销'].length;
    if (t === 0) continue;
    totalAll['新品'] += r['新品'].length;
    totalAll['IP'] += r['IP'].length;
    totalAll['营销'] += r['营销'].length;
    tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
  }

  out += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n';
  out += tableRows;
  out += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';

  out = out.replace(/\n\n\n+/g, '\n\n');
  return out;
}

// Actually crawl fresh
import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const ctx = browser.contexts()[0] || await browser.newContext();
const page = await ctx.newPage();
await page.setViewportSize({ width: 390, height: 844 });

const results = {};
for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const url = 'https://m.weibo.cn/u/' + b.uid;
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
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
        if (text.length > 10) results.push({ date: timeStr.split(' ')[0], time: timeStr.split(' ')[1] || '', text });
      }
      return results;
    });

    // Apply normalization fix
    const normalized = posts.map(p => ({
      ...p,
      date: normalizeDate(p.date)
    }));

    const filtered = normalized.filter(p => isTargetDay(p.date)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条 (新' + cats['新品'].length + ' IP' + cats['IP'].length + ' 营' + cats['营销'].length + ') | ' + (posts[0]?.date || '?'));
  } catch (e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + e.message.slice(0, 40));
  }
  await page.waitForTimeout(5000);
}
await browser.close();

const report = generateReport(results);
const now = new Date();
const dateStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
writeFileSync('memory/weibo_daily_' + dateStr + '.md', report);
writeFileSync('memory/weibo_daily_' + dateStr + '.json', JSON.stringify({ date: dateStr, results }, null, 2));
console.log('\n报告已写入 weibo_daily_' + dateStr + '.md');
