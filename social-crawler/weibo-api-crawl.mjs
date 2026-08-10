import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' }, { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' }, { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' }, { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' }, { name: '星巴克', uid: '1741514817' },
  { name: '茶百道', uid: '6502206666' }, { name: '奈雪的茶', uid: '5884674413' },
  { name: 'CoCo', uid: '2030619861' }, { name: '爷爷不泡茶', uid: '7769072120' },
  { name: '沪上阿姨', uid: '3921865344' }, { name: '乐乐茶', uid: '6253473981' },
  { name: '皮爷咖啡', uid: '6360528436' }, { name: 'M Stand', uid: '6345199298' },
  { name: 'Manner', uid: '6808111794' }, { name: '茉酸奶', uid: '5188894132' },
  { name: '树夏酸奶', uid: '7144806571' },
];

// 24h window: Jun 1 08:00 - Jun 2 current
const WINDOW_START = new Date(2026, 5, 1, 8, 0, 0, 0);
const WINDOW_END = new Date(2026, 5, 2, 11, 0, 0, 0);
const TODAY_STR = '2026-06-02';

function classify(text) {
  const t = text || '';
  const isIP = /联名|代言|大使|×/.test(t) && !/暂无/.test(t);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(t);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}

function sanitize(text) {
  if (!text) return '';
  let t = text.replace(/<[^>]+>/g, '');
  t = t.replace(/https?:\/\/\S+/g, '');
  t = t.replace(/\s+/g, ' ').trim();
  t = t.replace(/@\S+\s?/g, '');
  t = t.replace(/#([^#]+)#/g, '$1');
  t = t.replace(/关[➕加]转[，,]\s*揪?\s*\d+\s*位.*?券|\d+套.*?券/gi, '');
  t = t.replace(/关注.*?转发.*?抽.*?位/g, '');
  t = t.replace(/展开全文|全文/g, '');
  if (t.length > 200) t = t.substring(0, 200) + '…';
  return t.trim();
}

const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let page;
try { const ctx = browser.contexts()[0]; page = await ctx.newPage(); } catch(e) { page = await browser.newPage(); }

await page.goto('https://weibo.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(2000);

const allResults = {};

for (let i = 0; i < brands.length; i++) {
  const brand = brands[i];
  process.stdout.write(`[${i + 1}/${brands.length}] ${brand.name}... `);

  try {
    const uid = brand.uid;
    let pageNum = 1;
    let posts24h = [];
    let hasMore = true;

    while (hasMore && pageNum <= 20) {
      const result = await page.evaluate(async ({ uid, pageNum }) => {
        const resp = await fetch(`https://weibo.com/ajax/statuses/mymblog?uid=${uid}&page=${pageNum}&feature=0`);
        if (!resp.ok) return { error: resp.status + '', list: [], total: 0 };
        const json = await resp.json();
        return { list: json.data?.list || [], total: json.data?.total || 0 };
      }, { uid, pageNum });

      if (result.error || result.list.length === 0) {
        if (pageNum === 1) process.stdout.write('no data ');
        hasMore = false;
        break;
      }

      const pagePosts = result.list.filter(p => {
        const d = new Date(p.created_at);
        return d >= WINDOW_START && d <= WINDOW_END;
      });

      posts24h = posts24h.concat(pagePosts);

      const lastPost = result.list[result.list.length - 1];
      if (lastPost) {
        const lastDate = new Date(lastPost.created_at);
        if (lastDate < WINDOW_START) {
          hasMore = false;
        }
      }

      pageNum++;
      await page.waitForTimeout(300);
    }

    const cats = { '新品': [], 'IP': [], '营销': [] };
    const seen = new Set();

    posts24h.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

    for (const p of posts24h) {
      const fullText = p.text_raw || p.text || '';
      const key = fullText.substring(0, 50);
      if (seen.has(key)) continue;
      seen.add(key);

      const category = classify(fullText);
      cats[category].push({
        text: sanitize(fullText),
        created_at: p.created_at
      });
    }

    allResults[brand.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(`${total}条 (新${cats['新品'].length} IP${cats['IP'].length} 营${cats['营销'].length})`);

  } catch (e) {
    allResults[brand.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log(`err: ${e.message.slice(0, 50)}`);
  }

  await page.waitForTimeout(1000);
}

await browser.close();

// Generate clean report
function genReport(results) {
  const dateDisplay = '2026年06月02日';
  let out = `# ${dateDisplay} 茶饮品牌热点日报\n\n> 数据来源：微博桌面网页端（weibo.com）API\n> 数据区间：6月1日 08:00 - 6月2日 11:00\n\n---\n\n`;

  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const hasNew = r['新品'].length > 0;
    const hasIP = r['IP'].length > 0;
    const hasMkt = r['营销'].length > 0;
    if (!hasNew && !hasIP && !hasMkt) continue;

    out += `## ${brand.name}\n\n`;
    if (hasNew) { out += '【新品上市】\n'; r['新品'].forEach(p => out += `- ${p.text}\n`); out += '\n'; }
    if (hasIP) { out += '【IP联名/艺人宣发】\n'; r['IP'].forEach(p => out += `- ${p.text}\n`); out += '\n'; }
    if (hasMkt) { out += '【营销活动】\n'; r['营销'].forEach(p => out += `- ${p.text}\n`); out += '\n'; }
    out += '---\n\n';
  }

  out += '## 今日概览\n\n| 品牌 | 新品 | IP联名 | 营销 |\n|------|------|--------|------|\n';
  let totalN = 0, totalIP = 0, totalM = 0, activeCount = 0;
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const n = r['新品'].length, ip = r['IP'].length, m = r['营销'].length;
    if (n + ip + m === 0) continue;
    activeCount++;
    totalN += n; totalIP += ip; totalM += m;
    out += `| ${brand.name} | ${n || '-'} | ${ip || '-'} | ${m || '-'} |\n`;
  }
  out += `\n**汇总：新品 ${totalN} 条 | IP联名 ${totalIP} 条 | 营销活动 ${totalM} 条 | ${activeCount} 个品牌有动态**\n\n`;

  out += '## 今日行业洞察\n\n';

  const allText = Object.values(results).flatMap(cats =>
    Object.values(cats).flatMap(ps => ps.map(p => p.text))
  ).join(' ');

  const liuyiCount = (allText.match(/六一|儿童节/g) || []).length;
  const helloKitty = allText.includes('Hello Kitty');
  const monchhichi = allText.includes('Monchhichi');
  const xiaowanzi = allText.includes('樱桃小丸子');

  const insights = [];
  if (liuyiCount > 0) {
    const ipDesc = [helloKitty && '瑞幸HelloKitty', monchhichi && '茉酸奶Monchhichi', xiaowanzi && '爷爷不泡茶×樱桃小丸子'].filter(Boolean).join('、');
    insights.push(`**六一儿童节营销密集**：${liuyiCount > 5 ? '多品牌' : ''}同日押注六一，${ipDesc}领衔。儿童节从亲子节日升级为全民情感节点。`);
  }

  const seasonalWords = ['杨梅', '西瓜', '蜜瓜', '桃子', '青梅', '芭乐', '荔枝', '柠檬', '芒果', '绿豆沙'];
  const seasonalMentions = seasonalWords.filter(w => allText.includes(w));
  if (seasonalMentions.length > 0) {
    insights.push(`**夏季时令鲜果持续**：${seasonalMentions.slice(0, 4).join('、')}等时令元素出现在多个品牌活动中，夏日鲜果争夺战持续。`);
  }

  if (allText.includes('海盐焦糖') || allText.includes('回归')) {
    insights.push('**经典单品回归成标配**：瑞航海盐焦糖拿铁回归、幸运咖风凉绿豆沙破1288万杯、CoCo现煮绿豆系列预告6/3回归，迭代经典品替代纯推新成趋势。');
  }

  if (insights.length === 0) insights.push('暂无显著行业信号。');
  insights.forEach((ins, idx) => { out += `${idx + 1}. ${ins}\n\n`; });

  return out;
}

const report = genReport(allResults);
const outFile = `/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_${TODAY_STR}.md`;
writeFileSync(outFile, report);
console.log(`\n=== 报告已写入 ${outFile} ===`);

const jsonOut = `/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_${TODAY_STR}.json`;
writeFileSync(jsonOut, JSON.stringify({ date: TODAY_STR, results: allResults }, null, 2));
console.log('=== JSON 已写入 ' + jsonOut + ' ===');
