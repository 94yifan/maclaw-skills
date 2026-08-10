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

// 时间范围：2026-05-25 10:00 到 2026-05-26 11:00 北京时间
const START = new Date('2026-05-25T10:00:00+08:00').getTime();
const END = new Date('2026-05-26T11:00:00+08:00').getTime();

function parseTime(timeStr) {
  if (!timeStr) return null;
  const now = new Date('2026-05-26T12:00:00+08:00');
  // "昨天 HH:mm"
  let m = timeStr.match(/^昨天\s+(\d+):(\d+)$/);
  if (m) return new Date(2026, 4, 25, parseInt(m[1]), parseInt(m[2])).getTime();
  // "5-25 10:20"
  m = timeStr.match(/^(\d+)-(\d+)\s+(\d+):(\d+)$/);
  if (m) {
    const [, mo, day, h, min] = m;
    return new Date(2026, parseInt(mo)-1, parseInt(day), parseInt(h), parseInt(min)).getTime();
  }
  // "X分钟前"
  m = timeStr.match(/^(\d+)分钟前$/);
  if (m) return now.getTime() - parseInt(m[1]) * 60000;
  // "X小时前"
  m = timeStr.match(/^(\d+)小时前$/);
  if (m) return now.getTime() - parseInt(m[1]) * 3600000;
  return null;
}

function classify(text) {
  if (!text) return '营销';
  const t = text;
  if (/联名|代言|×|IP\s/i.test(t) && !/暂无/.test(t)) return 'IP';
  if (/新品|上市|首发|新系列|新口味|全新|回归|[再次重新]上市/.test(t) && !/暂无/.test(t)) return '新品';
  return '营销';
}

async function crawlBrand(page, brand, idx, total) {
  const url = `https://weibo.com/${brand.uid}`;
  process.stdout.write(`[${idx}/${total}] ${brand.name}... `);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(5000);
    // 滚动加载3次
    for (let i = 0; i < 3; i++) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2500);
    }
    const posts = await page.evaluate(() => {
      const results = [];
      const feeds = document.querySelectorAll('.wbpro-feed-content');
      for (const f of feeds) {
        const text = f.innerText.trim();
        if (text.length < 15) continue;
        // 向上找时间
        let parent = f.parentElement;
        let timeStr = '';
        for (let i = 0; i < 6 && parent; i++) {
          const t = parent.innerText || '';
          const match = t.match(/(\d+-\d+\s+\d+:\d+|昨天\s+\d+:\d+|\d+分钟前|\d+小时前)/);
          if (match) { timeStr = match[1]; break; }
          parent = parent.parentElement;
        }
        results.push({ timeStr, text: text.slice(0, 400) });
      }
      return results;
    });
    // 过滤时间范围
    const filtered = posts.filter(p => {
      const ts = parseTime(p.timeStr);
      return ts !== null && ts >= START && ts <= END;
    });
    const seen = new Set();
    const categorized = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const key = p.text.slice(0, 80);
      if (seen.has(key)) continue;
      seen.add(key);
      const cat = classify(p.text);
      categorized[cat].push(p.text);
    }
    const nc = categorized['新品'].length;
    const ic = categorized['IP'].length;
    const mc = categorized['营销'].length;
    process.stdout.write(`${nc+ic+mc}条(新${nc} IP${ic} 营${mc})\n`);
    return { brand: brand.name, ...categorized };
  } catch(e) {
    process.stdout.write(`错误:${e.message.slice(0,40)}\n`);
    return { brand: brand.name, '新品': [], 'IP': [], '营销': [] };
  }
}

(async () => {
  const browser = await chromium.connectOverCDP('http://localhost:9333');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();
  page.setDefaultTimeout(30000);
  const results = [];
  for (let i = 0; i < brands.length; i++) {
    const r = await crawlBrand(page, brands[i], i+1, brands.length);
    results.push(r);
    await page.waitForTimeout(2000);
  }
  writeFileSync('/tmp/ws_crawl_0526.json', JSON.stringify(results, null, 2));
  console.log('\n=== 完成 ===');
  const totalFiltered = results.reduce((s,r) => s + r['新品'].length + r['IP'].length + r['营销'].length, 0);
  console.log(`总计采集条目(时间范围内): ${totalFiltered}`);
  await browser.close();
})().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
