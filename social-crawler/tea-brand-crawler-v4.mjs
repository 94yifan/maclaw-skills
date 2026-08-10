import { chromium } from 'playwright-core';

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
  const lower = text.toLowerCase();
  const isIP = /联名|代言|品牌大使|合作伙伴|ip合作|×|x |合作款|限量/.test(text) ||
    /明星\b|代言人\b|大使\b|官宣\b|签约\b/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|新上市|全新|升级|回归|出道|新鲜/.test(text) &&
    !/暂无/.test(text);
  return { isNew, isIP };
}

function cleanText(post) {
  if (!post) return '';
  let text = post.text || post.content || String(post);
  text = text.replace(/(查看原网页|展开|收起|网页链接|🔗|👈|👉|👆|👇|⬆️|⬇️|🔍|📍|📢|🎉|✅|⏰|💰|🧧|🎁|⬇️|⏳|📱|🎫|📅|🏷️)/g, '').trim();
  text = text.replace(/\s+/g, ' ');
  if (text.length < 10) return '';
  return text.substring(0, 300);
}

async function crawlBrand(page, brand) {
  const url = `https://weibo.com/u/${brand.uid}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);
  
  let articles = [];
  try {
    const nodes = await page.$$('div[class*="vue-recycle-scroller__item-view"] > div > div');
    if (nodes.length > 0) {
      for (const node of nodes.slice(0, 10)) {
        const text = await node.innerText().catch(() => '');
        const time = await node.$eval('span[class*="time"]', el => el.innerText).catch(() => '');
        if (text) articles.push({ text, time });
      }
    }
  } catch (e) {}
  
  if (articles.length === 0) {
    try {
      const cards = await page.$$('[class*="card"]');
      for (const card of cards.slice(0, 10)) {
        const text = await card.innerText().catch(() => '');
        if (text && text.length > 20) {
          articles.push({ text, time: '' });
        }
      }
    } catch (e) {}
  }
  
  if (articles.length === 0) {
    try {
      const feedList = await page.$('#pl_feedlist_index');
      if (feedList) {
        const items = await feedList.$$('div[class*="item"]');
        for (const item of items.slice(0, 10)) {
          const text = await item.innerText().catch(() => '');
          if (text && text.length > 20) {
            articles.push({ text, time: '' });
          }
        }
      }
    } catch (e) {}
  }
  
  return articles;
}

// 生成报告末尾的汇总表
function generateSummary(results) {
  const brandNames = Object.keys(results).filter(k => results[k] && !results[k].error);
  const total = { 新品: 0, IP: 0, 营销: 0 };
  
  let table = '## 今日概览\n\n';
  table += '| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n';
  table += '|------|----------|----------------|----------|\n';
  
  brandNames.forEach(name => {
    const r = results[name];
    total.新品 += r.新品.length;
    total.IP += r.IP.length;
    total.营销 += r.营销.length;
    const 新品 = r.新品.length > 0 ? `${r.新品.length}` : '-';
    const IP = r.IP.length > 0 ? `${r.IP.length}` : '-';
    const 营销 = r.营销.length > 0 ? `${r.营销.length}` : '-';
    table += `| ${name} | ${新品} | ${IP} | ${营销} |\n`;
  });
  
  table += `\n**汇总：新品 ${total.新品} 条 | IP联名 ${total.IP} 条 | 营销活动 ${total.营销} 条**\n`;
  return table;
}

// 生成3条行业洞察
function generateInsights(results) {
  const brandNames = Object.keys(results).filter(k => results[k] && !results[k].error);
  const insights = [];
  
  // 洞察1：新品最密集的品牌
  const newProductBrands = brandNames
    .map(name => ({ name, count: results[name].新品.length }))
    .filter(b => b.count > 0)
    .sort((a, b) => b.count - a.count);
  if (newProductBrands.length > 0) {
    const top = newProductBrands[0];
    insights.push(`**新品密集**：` + top.name + `等${newProductBrands.length}个品牌今日有新品动作，共${newProductBrands.reduce((s, b) => s + b.count, 0)}款新品发布，其中` + top.name + `最活跃（${top.count}款）。`);
  }
  
  // 洞察2：IP联名动态
  const ipBrands = brandNames.filter(name => results[name].IP.length > 0);
  if (ipBrands.length > 0) {
    const detail = ipBrands.slice(0, 3).map(name => {
      const first = results[name].IP[0].substring(0, 40);
      return `${name}（${first}…）`;
    }).join('；');
    insights.push(`**IP联动**：` + ipBrands.length + `个品牌有IP/代言动态——` + detail + `。`);
  }
  
  // 洞察3：时令鲜果信号
  const seasonBrands = [];
  brandNames.forEach(name => {
    const allText = [...results[name].新品, ...results[name].营销].join('');
    if (/(杨梅|蜜瓜|西瓜|桃子|青梅|芭乐|荔枝|柠檬)/.test(allText)) {
      seasonBrands.push(name);
    }
  });
  if (seasonBrands.length > 0) {
    insights.push(`**时令鲜果**：` + seasonBrands.slice(0, 5).join('、') + `等品牌围绕时令鲜果（杨梅/蜜瓜/桃子等）密集布局，夏日争夺战白热化。`);
  }
  
  if (insights.length < 3) {
    insights.push(`**行业动态**：` + brandNames.length + `个品牌今日均有更新，市场活跃。`);
  }
  
  let output = '\n---\n\n## 今日行业洞察\n\n';
  insights.slice(0, 3).forEach((insight, i) => {
    output += `${i + 1}. ${insight}\n\n`;
  });
  
  return output;
}

async function main() {
  const outputFile = process.argv[2] || null;
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const ctx = await browser.contexts()[0];
  const page = (await ctx.pages())[0] || await ctx.newPage();

  const results = {};

  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i + 1}/${brands.length}] ${brand.name}... `);

    try {
      const articles = await crawlBrand(page, brand);

      const categorized = { 新品: [], IP: [], 营销: [] };
      articles.forEach(post => {
        const clean = cleanText(post);
        if (!clean) return;
        const { isNew, isIP } = classifyPost(clean);
        if (isNew) categorized.新品.push(clean);
        else if (isIP) categorized.IP.push(clean);
        else categorized.营销.push(clean);
      });

      results[brand.name] = categorized;
      process.stdout.write(`${articles.length}条\n`);
    } catch (e) {
      results[brand.name] = { 新品: [], IP: [], 营销: [], error: e.message.substring(0, 50) };
      process.stdout.write(`错误: ${e.message.substring(0, 30)}\n`);
    }

    const delay = Math.floor(Math.random() * 8000) + 12000;
    await page.waitForTimeout(delay);
  }

  await browser.close();

  // Generate report
  const today = new Date().toISOString().split('T')[0];
  const dateStr = today.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1年$2月$3日');

  let output = `# ${dateStr} 茶饮品牌热点日报\n\n---\n\n`;

  for (const brand of brands) {
    const r = results[brand.name];
    if (!r || r.error) continue;

    output += `## ${brand.name}\n\n`;
    output += `【新品上市】\n`;
    if (r.新品.length > 0) {
      r.新品.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无新品\n`;
    }
    output += `\n【IP联名/艺人宣发】\n`;
    if (r.IP.length > 0) {
      r.IP.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无IP联名/艺人宣发\n`;
    }
    output += `\n【营销活动】\n`;
    if (r.营销.length > 0) {
      r.营销.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无营销活动\n`;
    }
    output += `\n---\n\n`;
  }

  // 添加汇总表和洞察
  output += generateSummary(results);
  output += generateInsights(results);

  if (outputFile) {
    const fs = await import('fs');
    fs.writeFileSync(outputFile, output);
  }

  process.stdout.write('\n=== 报告生成完毕 ===\n');
  return output;
}

main().catch(console.error);
