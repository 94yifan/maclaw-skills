/**
 * 茶饮品牌热点日报 - 2026-05-06
 * CDP: ws://127.0.0.1:9333
 */

import { chromium } from 'playwright';

const brands = [
  { name: '瑞幸咖啡', id: '6349791448' },
  { name: '库迪', id: '7791266545' },
  { name: '古茗', id: '2809775704' },
  { name: '幸运咖', id: '6519396553' },
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
  const outputFile = process.argv[2] || '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-05-06.md';
  const fs = await import('fs');

  // Connect using WebSocket CDP URL
  const browser = await chromium.connectOverCDP('ws://127.0.0.1:9333/devtools/browser/dd9e6fb2-db6c-443e-9f08-8277b59df570');
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
      results[brand.name] = { 新品: [], IP: [], 营销: [], error: e.message.substring(0, 80) };
      process.stdout.write(`错误: ${e.message.substring(0, 30)}\n`);
    }

    await page.waitForTimeout(8000);
  }

  await browser.close();

  // Generate report
  const dateStr = '2026年05月06日';

  let report = `# ${dateStr} 茶饮品牌热点日报\n\n数据来源：微博品牌官方账号 | 抓取时间：${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n\n---\n\n`;

  for (const brand of brands) {
    const r = results[brand.name];
    if (!r || r.error) continue;

    report += `## ${brand.name}\n\n`;
    report += `**新品上市**\n`;
    if (r.新品.length > 0) {
      r.新品.forEach(p => report += `- ${p}\n`);
    } else {
      report += `- 暂无新品\n`;
    }
    report += `\n**IP联名/艺人宣发**\n`;
    if (r.IP.length > 0) {
      r.IP.forEach(p => report += `- ${p}\n`);
    } else {
      report += `- 暂无IP联名/艺人宣发\n`;
    }
    report += `\n**营销活动**\n`;
    if (r.营销.length > 0) {
      r.营销.forEach(p => report += `- ${p}\n`);
    } else {
      report += `- 暂无营销活动\n`;
    }
    report += `\n---\n\n`;
  }

  // 综合分析
  report += `## 综合分析\n\n`;
  report += `**今日概览**\n`;
  
  let totalNew = 0, totalIP = 0, totalCampaign = 0;
  const activeBrands = [];
  for (const brand of brands) {
    const r = results[brand.name];
    if (r && !r.error) {
      totalNew += r.新品.length;
      totalIP += r.IP.length;
      totalCampaign += r.营销.length;
      if (r.新品.length + r.IP.length + r.营销.length > 0) {
        activeBrands.push(brand.name);
      }
    }
  }
  
  report += `- 监测${brands.length}个品牌，${activeBrands.length}个有动态更新\n`;
  report += `- 新品相关：${totalNew}条 | IP联名/艺人：${totalIP}条 | 营销活动：${totalCampaign}条\n\n`;

  // 亮点提炼
  report += `**今日亮点**\n`;
  let highlightCount = 0;
  for (const brand of brands) {
    const r = results[brand.name];
    if (r && r.IP.length > 0) {
      report += `- 【${brand.name}】${r.IP[0].substring(0, 100)}\n`;
      highlightCount++;
      if (highlightCount >= 5) break;
    }
  }
  if (highlightCount === 0) {
    report += `- 今日暂无显著IP联名动态\n`;
  }

  report += `\n**趋势观察**\n`;
  if (totalNew > 5) {
    report += `- 新品密集期，多个品牌同步推新，市场竞争加剧\n`;
  }
  if (totalIP > 3) {
    report += `- IP联名活跃，品牌借助流量明星/热门IP提升声量\n`;
  }
  if (totalCampaign > 8) {
    report += `- 营销力度整体较高，促销活动成为主要拉新手段\n`;
  }
  if (totalNew <= 2 && totalIP <= 2) {
    report += `- 今日行业整体声量偏低，暂无显著热点事件\n`;
  }

  report += `\n---\n*本报告由 MacLaw 日报分身自动生成*\n`;

  // Write to file
  const dir = outputFile.substring(0, outputFile.lastIndexOf('/'));
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(outputFile, report);
  process.stdout.write(`\n=== 报告已写入 ${outputFile} ===\n`);

  return report;
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
