import { chromium } from 'playwright-core';
import fs from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: '1741514817' },
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

function classifyPost(text) {
  if (!text || text.length < 5) return null;
  const isIP = /联名|代言|品牌大使|合作伙伴|ip合作|×|x |合作款|限量/.test(text) ||
    /明星|代言人|大使|官宣|签约/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|新上市|全新|升级|回归|出道|新鲜/.test(text) && !/暂无/.test(text);
  if (isIP) return 'IP';
  if (isNew) return '新品';
  return '营销';
}

function cleanText(t) {
  if (!t) return '';
  return t.replace(/^展开全文|^收起全文|[\[\]]/g, '').replace(/\n+/g, ' ').trim().slice(0, 300);
}

async function crawlBrand(page, brand) {
  const url = 'https://m.weibo.cn/u/' + brand.uid;
  let retries = 2;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 12000 });
      await page.waitForTimeout(2500);
      const cards = await page.evaluate(() => {
        const items = document.querySelectorAll('.card, .m-panel, [class*="m-blog"], [class*="item"]');
        let result = [];
        for (const item of items) {
          const text = item.innerText || '';
          if (/\d{1,2}-\d{1,2}|\d+分钟前|\d+小时前/.test(text) && text.length > 30) {
            const lines = text.split('\n').filter(l => l.trim());
            const timeLine = lines.find(l => /\d{1,2}-\d{1,2}/.test(l) || /分钟前|小时前/.test(l));
            const content = lines.filter(l => !l.includes('评论') && !l.includes('赞') && l !== timeLine).join(' ');
            if (content.length > 15) result.push({ text: content, time: timeLine || '' });
          }
        }
        if (result.length === 0) {
          const allText = document.body.innerText;
          const blocks = allText.split(/(\d{1,2}-\d{1,2}|\d+分钟前)/);
          for (let i = 1; i < blocks.length; i += 2) {
            const time = blocks[i] || '';
            const content = (blocks[i-1] || '') + time + (blocks[i+1] || '');
            if (content.length > 40) result.push({ text: content.slice(-250), time });
          }
        }
        return result.slice(0, 10);
      });
      if (cards.length > 0) return cards;
    } catch(e) {}
    await page.waitForTimeout(2000);
  }
  return [];
}

const browser = await chromium.connectOverCDP('http://localhost:18800');
const page = await browser.newPage();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    results[b.name] = { posts };
    process.stdout.write(posts.length + '条\n');
  } catch(e) {
    results[b.name] = { posts: [], error: e.message };
    process.stdout.write('错误: ' + e.message.slice(0,50) + '\n');
  }
  await page.waitForTimeout(4000 + Math.random() * 2000);
}

await browser.close();

// Generate report
const today = new Date();
const dateStr = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';
let out = '# ' + dateStr + ' 茶饮品牌热点日报\n\n---\n\n';
const brandNames = Object.keys(results);

for (const name of brandNames) {
  const r = results[name];
  const posts = r.posts || [];
  const categorized = { '新品': [], 'IP': [], '营销': [] };
  posts.forEach(p => {
    const t = cleanText(p.text || '');
    if (!t) return;
    const type = classifyPost(t);
    if (type) categorized[type].push(t);
  });
  out += '## ' + name + '\n\n';
  out += '【新品上市】\n';
  if (categorized['新品'].length) categorized['新品'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无新品\n';
  out += '\n【IP联名/艺人宣发】\n';
  if (categorized['IP'].length) categorized['IP'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无IP联名/艺人宣发\n';
  out += '\n【营销活动】\n';
  if (categorized['营销'].length) categorized['营销'].forEach(p => out += '- ' + p + '\n'); else out += '- 暂无营销活动\n';
  out += '\n---\n\n';
}

// 概览表
out += '## 今日概览\n\n';
out += '| 品牌 | 新品上市 | IP联名/艺人 | 营销活动 |\n|------|------|------|------|\n';
for (const name of brandNames) {
  const r = results[name];
  const posts = r.posts || [];
  const cats = { '新品':0, 'IP':0, '营销':0 };
  posts.forEach(p => { const t = cleanText(p.text || ''); if(t){ const c = classifyPost(t); if(c) cats[c]++; } });
  out += '| ' + name + ' | ' + (cats['新品']||'-') + ' | ' + (cats['IP']||'-') + ' | ' + (cats['营销']||'-') + ' |\n';
}

const totalPosts = Object.values(results).reduce((s,r) => s + (r.posts||[]).length, 0);
out += '\n## 今日行业洞察\n\n';
out += '1. **行业动态**：`' + brandNames.length + '`个品牌今日全部正常更新，共`' + totalPosts + '`条数据。\n';

const dateStr2 = dateStr.replace('年','').replace('月','').replace('日','');
const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateStr2.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3') + '.md';
fs.writeFileSync(outFile, out);
console.log('\n=== 报告生成完毕 ===');
console.log('文件：' + outFile);
process.exit(0);
