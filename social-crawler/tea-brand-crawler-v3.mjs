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
  if (!text) return '';
  let t = text;
  const P = '[+\\uff13\\u2795]';
  
  // 按行清理
  const rawLines = t.split('\n').filter(l => l.trim().length > 0);
  const cleanedLines = [];
  
  for (const line of rawLines) {
    let l = line.trim();
    
    // 跳过：仅数字（互动数）
    if (/^\\d+$/.test(l)) continue;
    // 跳过：仅emoji+数字
    if (/^[\\u2600-\\u27bf\\u1f600-\\u1f64f\\u1f300-\\u1f5ff\\u1f680-\\u1f6ff]+$/.test(l)) continue;
    // 跳过：来自微博xxx
    if (/^来自/.test(l)) continue;
    // 跳过：超话标题行
    if (/\\S+超话$/.test(l)) continue;
    // 跳过：用户名+超话+时间（完整前缀行）
    if (l.match(/^[^\\n]{2,30}(?:超话|的微博|微博视频)/)) continue;
    
    // 去掉@mention
    l = l.replace(/@\\S+/g, '');
    // 微博话题
    l = l.replace(/#([^#]+)#/g, '$1');
    l = l.replace(/#/g, '');
    // 去掉播放视频
    l = l.replace(/播放视频$/, '');
    l = l.replace(/微博视频/g, '');
    // 去掉时间戳
    l = l.replace(/^\\d+-\\d+\\s*\\d+:\\d+$/, '');
    l = l.replace(/^\\d+分钟前$/, '');
    l = l.replace(/^\\d+小时前$/, '');
    l = l.replace(/^昨天$/, '');
    l = l.replace(/^今天$/, '');
    l = l.replace(/已编辑/, '');
    
    // 参与语
    l = l.replace(new RegExp(\`关注\${P}转发分享[^\\n]{0,150}\`, 'gi'), '');
    l = l.replace(new RegExp(\`关注\${P}转发[^\\n]{0,100}\`, 'gi'), '');
    l = l.replace(new RegExp(\`关\${P}转[^\\n]{0,100}\`, 'gi'), '');
    l = l.replace(new RegExp(\`关\${P}赞[^\\n]{0,80}\`, 'gi'), '');
    l = l.replace(/[，,]\s*抽\s*\\d+\s*位[^\\n]{0,100}/g, '，');
    l = l.replace(/[，,]\s*揪\s*\\d+\s*位[^\\n]{0,100}/g, '，');
    l = l.replace(/[，,]\s*随机抽\s*\\d+\\s*(?:位|人)[^\\n]{0,100}/g, '，');
    l = l.replace(/[，,]\s*送[^\\n]{0,40}/g, '，');
    l = l.replace(/【转发请喝】【^\\n】*/g, '');
    l = l.replace(/【请喝】【^\\n】*/g, '');
    
    // 去掉截断
    l = l.replace(/[.。]{2,}\\s*展开$/, '');
    l = l.replace(/[.。]{3,}/g, '');
    
    // 去掉互动数字
    l = l.replace(/\\d+万次观看/g, '');
    l = l.replace(/\\d+[.·]\\d+万/g, '');
    l = l.replace(/\\d+万/g, '');
    l = l.replace(/\\d+:\\d+$/, '');
    
    l = l.trim();
    if (l.length > 5 && !/^[，,、\\s\\d]+$/.test(l)) {
      cleanedLines.push(l);
    }
  }
  
  return cleanedLines.join(' ').substring(0, 300);
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
