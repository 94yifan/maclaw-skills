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

const NOW = new Date();

// 守卫：旧系统crontab在10:15运行，直接退出（由11:00的OpenClaw cron统一执行）
const hour = NOW.getHours(), min = NOW.getMinutes();
if ((hour === 10 && min <= 45) || (hour < 10)) {
  process.stdout.write('[guard] 旧crontab时段，跳过（由11:00 OpenClaw cron执行）\n');
  process.exit(0);
}

const REPORT_PATH = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_'
  + NOW.getFullYear() + '-' + String(NOW.getMonth()+1).padStart(2,'0') + '-' + String(NOW.getDate()).padStart(2,'0') + '.md';

// ---- 时间解析 ----
// 取昨天0点至今，避免滑动窗口在周末漏数据
const TWO_DAYS_AGO = new Date(NOW);
TWO_DAYS_AGO.setDate(TWO_DAYS_AGO.getDate() - 2);
TWO_DAYS_AGO.setHours(0, 0, 0, 0);
const CUTOFF = TWO_DAYS_AGO.getTime();

function parseWeiboTime(timeStr) {
  if (!timeStr) return null;
  const s = timeStr.trim();
  if (s === '刚刚') return NOW.getTime();
  const m = s.match(/^(\d+)分钟前$/);
  if (m) return NOW.getTime() - parseInt(m[1]) * 60 * 1000;
  const h = s.match(/^(\d+)小时前$/);
  if (h) return NOW.getTime() - parseInt(h[1]) * 60 * 60 * 1000;
  const y = s.match(/^昨天(?:\s+(\d{1,2}):(\d{2}))?$/);
  if (y) {
    const yesterday = new Date(NOW);
    yesterday.setDate(yesterday.getDate() - 1);
    if (y[1] !== undefined) yesterday.setHours(parseInt(y[1]), parseInt(y[2]), 0, 0);
    else yesterday.setHours(23, 59, 59, 0);
    return yesterday.getTime();
  }
  const d = s.match(/^(\d+)天前$/);
  if (d) return NOW.getTime() - parseInt(d[1]) * 24 * 60 * 60 * 1000;
  const abs = s.match(/^(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?$/);
  if (abs) {
    const month = parseInt(abs[1]), day = parseInt(abs[2]);
    const hour = abs[3] !== undefined ? parseInt(abs[3]) : 23;
    const min = abs[4] !== undefined ? parseInt(abs[4]) : 59;
    let year = NOW.getFullYear();
    const dt = new Date(year, month - 1, day, hour, min, 0);
    if (dt.getTime() > NOW.getTime() + 86400000) {
      year -= 1;
      return new Date(year, month - 1, day, hour, min, 0).getTime();
    }
    return dt.getTime();
  }
  return null;
}

function isWithinRecent(timeStr) {
  const ts = parseWeiboTime(timeStr);
  return ts !== null && ts >= CUTOFF && ts <= NOW.getTime();
}

function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) return false;
  if (/加入群|粉丝群\s*\d/.test(text)) return false;
  return true;
}

function classify(text) {
  const t = text || '';
  // IP联名/艺人宣发：跟其他品牌/活动/人物的合作
  const isIP = /联名|代言|×|合作款/.test(t) && !/暂无/.test(t);
  // 新品：产品本身的新品/回归/上新（包括产品介绍、预告）
  const isNew = /新品|上市|首发|新系列|新口味|新作|上新|升级回归|焕新回归|限时回归/.test(t)
    || /\u4E28/.test(t) // 丨成分分隔符（东方美人乌龙茶丨啤酒花风味，产品介绍特征）
    || /限定.*(茶|饮|咖|果|酸奶|特调)/.test(t)
    || /(什么时候.*回归|回归.*预告|即将回归|回归.*明日|回归.*上班)/.test(t)
    // 产品名模式（新品预告、产品介绍）
    || /「.*摇摇沙」|茶特调·摇摇沙/.test(t)
    || /瑰夏之梦/.test(t)
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

function cleanText(text) {
  return text
    .replace(/#[^#]+#/g, '')
    .replace(/@\S+/g, '')
    .replace(/全文/g, '')
    .replace(/关注.*?转发/g, '')
    .replace(/抽\d+/g, '抽')
    .replace(/[🔥💥💕💙🤎💚💜🩷🆘🧊✨🎉✅‼️🙌🥤☕🍵🎁💪⛱️🌊🌹]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// ---- 爬取 ----
async function crawlBrand(page, brand) {
  await page.goto('https://m.weibo.cn/u/' + brand.uid, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(5000);
  for (const y of [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]) {
    await page.evaluate((Y) => window.scrollTo(0, Y), y);
    await page.waitForTimeout(1500);
  }
  const posts = await page.evaluate(() => {
    const cards = document.querySelectorAll('.card');
    const results = [];
    for (const card of cards) {
      const timeEl = card.querySelector('span.time');
      const textEl = card.querySelector('.weibo-text');
      if (!timeEl || !textEl) continue;
      const timeStr = timeEl.innerText.trim();
      const text = textEl.innerText.trim().slice(0, 400);
      if (text.length > 10) results.push({ timeStr, text });
    }
    return results;
  });
  return posts;
}

// ---- 主流程 ----
const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i + 1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    const filtered = posts.filter(p => isWithinRecent(p.timeStr)).filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条 (新' + cats['新品'].length + ' IP' + cats['IP'].length + ' 营' + cats['营销'].length + ')');
  } catch (e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    process.stdout.write('error: ' + e.message.slice(0, 30) + '\n');
  }
  await page.waitForTimeout(5000);
}
await browser.close();

// ---- 生成报告 ----
let out = '';
for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  out += '## ' + brand.name + '\n\n【新品上市】\n';
  if (r['新品'].length) r['新品'].forEach(p => out += '- ' + cleanText(p.text) + '\n');
  else out += '- 暂无新品\n';
  out += '\n【IP联名/艺人宣发】\n';
  if (r['IP'].length) r['IP'].forEach(p => out += '- ' + cleanText(p.text) + '\n');
  else out += '- 暂无IP联名/艺人宣发\n';
  out += '\n【营销活动】\n';
  if (r['营销'].length) r['营销'].forEach(p => out += '- ' + cleanText(p.text) + '\n');
  else out += '- 暂无营销活动\n';
  out += '\n---\n\n';
}

// 汇总表
let totalNew = 0, totalIP = 0, totalMkt = 0;
let tableRows = '';
for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  const n = r['新品'].length, ip = r['IP'].length, m = r['营销'].length;
  if (n + ip + m > 0) {
    totalNew += n; totalIP += ip; totalMkt += m;
    tableRows += '| ' + brand.name + ' | ' + (n || '-') + ' | ' + (ip || '-') + ' | ' + (m || '-') + ' |\n';
  }
}
out += '## 今日概览\n\n| 品牌 | 新品 | IP联名 | 营销 |\n|------|------|--------|------|\n' + tableRows;
out += '\n**汇总：新品 ' + totalNew + ' 条 | IP联名 ' + totalIP + ' 条 | 营销 ' + totalMkt + ' 条**\n\n';

out += '## 今日行业洞察\n\n（洞察待基于数据手动补充）\n';

writeFileSync(REPORT_PATH, out);
console.log('\n=== 报告已写入 ' + REPORT_PATH + ' (新' + totalNew + ' IP' + totalIP + ' 营' + totalMkt + ') ===');
console.log('=== 总计' + (totalNew+totalIP+totalMkt) + '条，覆盖' + tableRows.split('\n').filter(l=>l.startsWith('| ')).length + '个品牌 ===');
