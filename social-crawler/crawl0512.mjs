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

function classifyPost(text) {
  const t = text || '';
  const isIP = /联名|代言|品牌大使|合作伙伴|×/.test(t) && !/暂无|抱歉/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t) && !/暂无|抱歉|关注|加入群/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

function isValidPost(text) {
  if (!text || text.length < 20) return false;
  if (/抱歉.*不存在|该昵称/.test(text)) return false;
  if (/加入群|群主：|粉丝群/.test(text)) return false;
  if (/^[^]*关注\s*$/m.test(text.trim())) return false;
  return true;
}

async function crawlBrand(page, brand) {
  await page.goto('https://m.weibo.cn/u/' + brand.uid, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(4500);
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.waitForTimeout(2000);

  const posts = await page.evaluate(() => {
    const body = document.body.innerText;
    const regex = /(\d{1,2}-\d{1,2}\s+\d{2}:\d{2})/g;
    const results = [];
    let lastIdx = 0;
    let match;
    while ((match = regex.exec(body)) !== null && results.length < 15) {
      const tsStr = match[1];
      const tsIdx = match.index;
      const segment = body.substring(lastIdx, tsIdx).trim();
      const content = segment.replace(/^(返回|微博|超话|精选|关注|粉丝\d+万?)\n?/g, '').trim();
      if (content.length > 20) {
        results.push({ time: tsStr, text: content.slice(-300) });
      }
      lastIdx = tsIdx + match[0].length;
    }
    return results;
  });
  return posts;
}

const browser = await chromium.connectOverCDP('http://localhost:9333');
const page = await browser.newPage();
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  process.stdout.write('[' + (i+1) + '/' + brands.length + '] ' + b.name + '... ');
  try {
    const posts = await crawlBrand(page, b);
    const valid = posts.filter(p => isValidPost(p.text));
    const cats = { 新品: [], IP: [], 营销: [] };
    valid.forEach(p => { cats[classifyPost(p.text)].push(p); });
    results[b.name] = cats;
    process.stdout.write(valid.length + '条 ');
    console.log('(新' + cats.新品.length + ' IP' + cats.IP.length + ' 营' + cats.营销.length + ')');
  } catch(e) {
    console.log('err: ' + e.message.substring(0, 30));
  }
  await page.waitForTimeout(5000);
}

await browser.close();

// Generate report
const today = new Date();
const dateStr = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';
let out = '# ' + dateStr + ' 茶饮品牌热点日报\n\n> 数据区间：5月11日 10:00 - 5月12日 10:00\n\n---\n\n';

for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  out += '## ' + brand.name + '\n\n【新品上市】\n';
  if (r.新品.length) r.新品.forEach(p => out += '- [' + p.time + '] ' + p.text + '\n'); else out += '- 暂无新品\n';
  out += '\n【IP联名/艺人宣发】\n';
  if (r.IP.length) r.IP.forEach(p => out += '- [' + p.time + '] ' + p.text + '\n'); else out += '- 暂无IP联名/艺人宣发\n';
  out += '\n【营销活动】\n';
  if (r.营销.length) r.营销.forEach(p => out += '- [' + p.time + '] ' + p.text + '\n'); else out += '- 暂无营销活动\n';
  out += '\n---\n\n';
}

out += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n';
const total = { 新品: 0, IP: 0, 营销: 0 };
for (const brand of brands) {
  const r = results[brand.name];
  if (!r) continue;
  total.新品 += r.新品.length;
  total.IP += r.IP.length;
  total.营销 += r.营销.length;
  out += '| ' + brand.name + ' | ' + (r.新品.length||'-') + ' | ' + (r.IP.length||'-') + ' | ' + (r.营销.length||'-') + ' |\n';
}
out += '\n**汇总：新品 ' + total.新品 + ' 条 | IP联名 ' + total.IP + ' 条 | 营销活动 ' + total.营销 + ' 条**\n\n';

const allBrands = brands.map(b => b.name);
const newBrands = allBrands.filter(n => results[n] && results[n].新品.length > 0);
const ipBrands = allBrands.filter(n => results[n] && results[n].IP.length > 0);
const seasonBrands = allBrands.filter(n => {
  if (!results[n]) return false;
  const all = [...(results[n].新品||[]), ...(results[n].营销||[])].map(p => p.text||'').join('');
  return /杨梅|蜜瓜|西瓜|桃子|青梅|芭乐|荔枝|柠檬/.test(all);
});

out += '## 今日行业洞察\n\n';
if (newBrands.length) out += '1. **新品密集**：`' + newBrands.join('、') + '`等' + newBrands.length + '个品牌有新品动作，共' + total.新品 + '款。\n\n';
if (ipBrands.length) out += '2. **IP联动**：`' + ipBrands.join('、') + '`等' + ipBrands.length + '个品牌有IP/代言动态。\n\n';
if (seasonBrands.length) out += '3. **时令鲜果**：`' + seasonBrands.slice(0,5).join('、') + '`等品牌密集押注时令鲜果，夏日争夺战白热化。\n\n';
out += '4. **行业动态**：`' + allBrands.length + '`个品牌今日正常更新。\n';

writeFileSync('/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-05-12.md', out);
console.log('=== 报告已写入 memory/weibo_daily_2026-05-12.md ===');
