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

// 时间范围：2026-05-25 10:00 到 2026-05-26 11:00
const START = new Date('2026-05-25T10:00:00+08:00').getTime();
const END = new Date('2026-05-26T11:00:00+08:00').getTime();

function parseWeiboTime(timeStr) {
  // 处理 "5-25 10:20" 或 "昨天 10:20" 或 "10分钟前" 等
  const now = new Date('2026-05-26T12:00:00+08:00');
  if (/^\d+-\d+\s+\d+:\d+$/.test(timeStr)) {
    const [md, hm] = timeStr.split(' ');
    const [m, d] = md.split('-').map(Number);
    const [h, min] = hm.split(':').map(Number);
    // 假设是2026年
    return new Date(2026, m-1, d, h, min).getTime();
  }
  if (/^昨天/.test(timeStr)) {
    const [, hm] = timeStr.split(' ');
    const [h, min] = hm.split(':').map(Number);
    return new Date(2026, 4, 25, h, min).getTime(); // 5月25日是昨天
  }
  if (/^\d+分钟前/.test(timeStr)) {
    const mins = parseInt(timeStr);
    return now.getTime() - mins * 60000;
  }
  if (/^\d+小时前/.test(timeStr)) {
    const hrs = parseInt(timeStr);
    return now.getTime() - hrs * 3600000;
  }
  return null;
}

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|×|IP/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归|回归/.test(t) && !/暂无/.test(t);
  return isIP ? 'IP' : (isNew ? '新品' : '营销');
}

async function crawlBrand(page, brand, index, total) {
  const url = `https://m.weibo.cn/u/${brand.uid}`;
  process.stdout.write(`[${index}/${total}] ${brand.name}... `);
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(4000);
    
    // 多次滚动加载更多
    for (let i = 0; i < 4; i++) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2500);
    }
    
    const posts = await page.evaluate(() => {
      const results = [];
      // 尝试多种选择器
      const cards = document.querySelectorAll('.card');
      for (const card of cards) {
        const timeEl = card.querySelector('span.time');
        const textEl = card.querySelector('.weibo-text');
        if (!timeEl || !textEl) continue;
        const timeStr = timeEl.innerText.trim();
        const text = textEl.innerText.trim();
        if (text.length > 10) {
          results.push({ timeStr, text });
        }
      }
      // 备选：直接找所有含时间的元素对
      if (results.length === 0) {
        const items = document.querySelectorAll('[style*="color"]');
        for (const item of items) {
          const t = item.innerText.trim();
          if (/^\d+-\d+/.test(t) || /^昨天/.test(t) || /^\d+分钟前/.test(t) || /^\d+小时前/.test(t)) {
            const parent = item.closest('.card') || item.parentElement;
            if (parent) {
              const textEl = parent.querySelector('.weibo-text');
              if (textEl) {
                const text = textEl.innerText.trim();
                if (text.length > 10) results.push({ timeStr: t, text });
              }
            }
          }
        }
      }
      return results;
    });
    
    // 过滤时间范围内的帖子
    const filtered = posts.filter(p => {
      const ts = parseWeiboTime(p.timeStr);
      return ts !== null && ts >= START && ts <= END;
    });
    
    // 去重+分类
    const seen = new Set();
    const categorized = { '新品': [], 'IP': [], '营销': [] };
    for (const p of filtered) {
      const key = p.text.slice(0, 100);
      if (seen.has(key)) continue;
      seen.add(key);
      const cat = classify(p.text);
      categorized[cat].push(p.text.slice(0, 400));
    }
    
    const newCount = categorized['新品'].length;
    const ipCount = categorized['IP'].length;
    const mktCount = categorized['营销'].length;
    const total2 = newCount + ipCount + mktCount;
    process.stdout.write(`${total2}条 (新${newCount} IP${ipCount} 营${mktCount})\n`);
    
    return { brand: brand.name, ...categorized, raw: filtered };
  } catch(e) {
    process.stdout.write(`错误: ${e.message.slice(0,50)}\n`);
    return { brand: brand.name, '新品': [], 'IP': [], '营销': [] };
  }
}

(async () => {
  const browser = await chromium.connectOverCDP('http://localhost:9333');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  
  const results = [];
  for (let i = 0; i < brands.length; i++) {
    const r = await crawlBrand(page, brands[i], i+1, brands.length);
    results.push(r);
    await page.waitForTimeout(2000);
  }
  
  writeFileSync('/tmp/crawl_may25_may26.json', JSON.stringify(results, null, 2));
  console.log('\n完成，结果已保存');
  
  await browser.close();
})().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
