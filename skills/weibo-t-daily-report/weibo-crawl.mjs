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
  { name: '树夏酸奶', uid: '7144806571' }
];

const today = new Date();
const dateStr = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';
const dateFile = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
const crawlTime = today.toTimeString().slice(0,5);

// 时间窗口：前一天10:00 到 爬取时间
function isTargetDay(dateStr, todayDate) {
  // dateStr 格式如 "5-18 10:05" 或 "5-17 14:30"
  const parts = dateStr.trim().split(/\s+/);
  const datePart = parts[0]; // "5-18"
  const timePart = parts[1] || '00:00'; // "10:05"

  // 前一天10:00 起点
  const yesterday = new Date(todayDate);
  yesterday.setDate(todayDate.getDate() - 1);
  yesterday.setHours(10, 0, 0, 0);

  // 当天爬取时间终点
  const end = new Date(todayDate);
  end.setHours(todayDate.getHours(), todayDate.getMinutes(), 0, 0);

  const [mDay, dDay] = datePart.split('-').map(p => parseInt(p));
  const [tH, tM] = timePart.split(':').map(p => parseInt(p));

  const postDate = new Date(todayDate.getFullYear(), mDay - 1, mDay, tH, tM);
  // 纠正月份计算
  // dateStr "5-17" = 5月17日 = month=4 (0-indexed)
  const actualDate = new Date(todayDate.getFullYear(), mDay - 1, mDay, tH, tM);

  return actualDate >= yesterday && actualDate <= end;
}

function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容|登录注册/.test(text)) return false;
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
  const uid = brand.uid === 'starbucks' ? 'starbucks' : brand.uid;
  await page.goto('https://weibo.com/u/' + uid, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(5000);

  for (const y of [0, 800, 1600, 2400]) {
    await page.evaluate((Y) => window.scrollTo(0, Y), y);
    await page.waitForTimeout(2000);
  }

  const posts = await page.evaluate(() => {
    const results = [];
    const items = document.querySelectorAll('.WB_cardwrap, .WB_feed_record');

    for (const item of items) {
      const timeEl = item.querySelector('.WB_info .WB_time, .WB_func .WB_time, [node-type="feed_list_time"], .time');
      const textEl = item.querySelector('.WB_detail, .WB_text, [node-type="feed_list_content"]');

      let timeStr = '';
      let text = '';

      if (timeEl) timeStr = timeEl.innerText.trim();
      if (textEl) text = textEl.innerText.trim().slice(0, 400);

      if (!timeStr || !text) {
        const allText = item.innerText || '';
        const timeMatch = allText.match(/(\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2})/);
        const contentMatch = allText.match(/(.{20,})/);
        if (timeMatch) timeStr = timeMatch[1];
        if (contentMatch) text = contentMatch[1].slice(0, 400);
      }

      if (text && text.length > 10) {
        results.push({ date: timeStr, text });
      }
    }
    return results;
  });

  return posts;
}

// CDP 连接
const ports = [9333, 9222, 9500];
let browser;
for (const port of ports) {
  try {
    browser = await chromium.connectOverCDP('http://localhost:' + port);
    console.log('CDP connected on port ' + port);
    break;
  } catch(e) {
    if (port === ports[ports.length-1]) {
      console.log('CDP_CONNECTION_FAILED');
      process.exit(1);
    }
  }
}

const page = await browser.newPage();
const results = {};
const todayDate = new Date();

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/19] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    const filtered = posts
      .filter(p => isTargetDay(p.date, todayDate))
      .filter(p => isValid(p.text));
    const cats = { '新品': [], 'IP': [], '营销': [] };
    filtered.forEach(p => { cats[classify(p.text)].push(p); });
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条 (新' + cats['新品'].length + ' IP' + cats['IP'].length + ' 营' + cats['营销'].length + ')');
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + e.message.slice(0,40));
  }
  await page.waitForTimeout(10000);
}

await browser.close();

const output = {
  date: dateFile,
  dateDisplay: dateStr,
  crawlTime,
  windowStart: (() => {
    const y = new Date(todayDate); y.setDate(y.getDate()-1); y.setHours(10,0,0,0);
    return (y.getMonth()+1) + '-' + y.getDate() + ' 10:00';
  })(),
  windowEnd: crawlTime,
  results,
  brands
};

const jsonFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateFile + '.json';
writeFileSync(jsonFile, JSON.stringify(output, null, 2));
console.log('\n=== JSON 已写入 ' + jsonFile + ' ===');