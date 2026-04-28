/**
 * 茶饮品牌热点日报 - 爬虫核心脚本
 * 使用方法: node crawler.mjs [output-file]
 * 输出: 结构化日报文本，默认输出到 stdout
 */

import { chromium } from 'playwright';

const brands = [
  { name: '瑞幸咖啡', id: '6349791448' },
  { name: '库迪', id: '7791266545' },
  { name: '古茗', id: '2809775704' },
  { name: '茉莉奶白', id: '7577524421' },
  { name: '霸王茶姬', id: '5652018762' },
  { name: '喜茶', id: '2804387887' },
  { name: '星巴克', id: 'starbucks' },
  { name: '茶百道', id: '6502206666' },
  { name: '奈雪的茶', id: '5884674413' },
  { name: 'CoCo', id: '2030619861' },
  { name: '爷爷不泡茶', id: '7769072120' },
  { name: '沪上阿姨', id: '3921865344' },
  { name: '乐乐茶', id: '6253473981' },
  { name: '皮爷咖啡', id: '6360528436' },
  { name: 'M Stand', id: '6345199298' },
  { name: 'Manner', id: '6808111794' },
  { name: '茉酸奶', id: '5188894132' },
  { name: '树夏酸奶', id: '7144806571' }
];

// 关键词分类
const NEW_PRODUCT_KEYWORDS = ['新品', '上新', '上市', '首发', '推出', '回归', '升级', '登场', '全新', '系列'];
const IP_KEYWORDS = ['联名', '合作', '代言', 'IP', '艺人', '品牌联动', '×'];
const CAMPAIGN_KEYWORDS = ['抽奖', '活动', '福利', '节日', '主题店', '买一送一', '折扣', '礼包', '限定'];

function classifyPost(text) {
  const t = text.toLowerCase();
  const isNew = NEW_PRODUCT_KEYWORDS.some(k => t.includes(k));
  const isIP = IP_KEYWORDS.some(k => t.includes(k));
  return { isNew, isIP, isCampaign: !isNew && !isIP };
}

function cleanText(text) {
  return text
    .replace(/转发评论赞/g, '')
    .replace(/转发/g, '')
    .replace(/评论/g, '')
    .replace(/赞/g, '')
    .replace(/已编辑/g, '')
    .replace(/来自.*?(?=\n|$)/g, '')
    .replace(/Live/g, '')
    .replace(/^\d+$/gm, '')
    .replace(/\.{3,}\d+/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 300);
}

async function crawlBrand(page, brand) {
  const url = brand.id === 'starbucks' ? 'https://weibo.com/starbucks' : `https://weibo.com/u/${brand.id}`;
  await page.goto(url, { timeout: 20000, waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  for (let s = 0; s < 4; s++) {
    await page.evaluate(() => window.scrollBy(0, 600));
    await page.waitForTimeout(600);
  }

  const articles = await page.evaluate(() => {
    const arts = document.querySelectorAll('article');
    return Array.from(arts)
      .map(a => a.innerText.trim())
      .filter(t => t.length > 30)
      .slice(0, 10);
  });

  return articles;
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
    output += `**新品上市**\n`;
    if (r.新品.length > 0) {
      r.新品.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无新品\n`;
    }
    output += `\n**IP联名/艺人宣发**\n`;
    if (r.IP.length > 0) {
      r.IP.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无IP联名/艺人宣发\n`;
    }
    output += `\n**营销活动**\n`;
    if (r.营销.length > 0) {
      r.营销.forEach(p => output += `- ${p}\n`);
    } else {
      output += `- 暂无营销活动\n`;
    }
    output += `\n---\n\n`;
  }

  if (outputFile) {
    const fs = await import('fs');
    fs.writeFileSync(outputFile, output);
  }

  process.stdout.write('\n=== 报告生成完毕 ===\n');
  return output;
}

main().catch(console.error);
