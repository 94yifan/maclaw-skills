/**
 * 茶饮品牌微博爬虫 v9 - 基于m.weibo.cn API
 * 速度最快，最可靠
 */
import { chromium } from 'playwright-core';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448', stars: false },
  { name: '库迪', uid: '7791266545', stars: false },
  { name: '古茗', uid: '2809775704', stars: false },
  { name: '幸运咖', uid: '6519396553', stars: false },
  { name: '茉莉奶白', uid: '7577524421', stars: false },
  { name: '霸王茶姬', uid: '5652018762', stars: false },
  { name: '喜茶', uid: '2804387887', stars: false },
  { name: '星巴克', uid: '1741514817', stars: false },
  { name: '茶百道', uid: '6502206666', stars: false },
  { name: '奈雪的茶', uid: '5884674413', stars: false },
  { name: 'CoCo', uid: '2030619861', stars: false },
  { name: '爷爷不泡茶', uid: '7769072120', stars: false },
  { name: '沪上阿姨', uid: '3921865344', stars: false },
  { name: '乐乐茶', uid: '6253473981', stars: false },
  { name: '皮爷咖啡', uid: '6360528436', stars: false },
  { name: 'M Stand', uid: '6345199298', stars: false },
  { name: 'Manner', uid: '6808111794', stars: false },
  { name: '茉酸奶', uid: '5188894132', stars: false },
  { name: '树夏酸奶', uid: '7144806571', stars: false },
];

function parseDate(createdStr) {
  // "Mon Jun 15 10:00:00 +0800 2026"
  const m = createdStr.match(/(\w{3}) (\w{3}) (\d{2}) (\d{2}):(\d{2}):(\d{2}) .+? (\d{4})/);
  if (!m) return null;
  const months = {Jan:0,Feb:1,Mar:2,Apr:3,May:4,Jun:5,Jul:6,Aug:7,Sep:8,Oct:9,Nov:10,Dec:11};
  const month = months[m[2]];
  if (month === undefined) return null;
  return new Date(parseInt(m[7]), month, parseInt(m[3]), parseInt(m[4]), parseInt(m[5]), parseInt(m[6]));
}

function isWithin24h(createdStr) {
  const dt = parseDate(createdStr);
  if (!dt) return false;
  return (new Date() - dt) < 24 * 3600 * 1000;
}

// 清洗HTML标签
function cleanHtml(html) {
  return html.replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

async function fetchBrandPosts(page, uid, maxPages = 2) {
  const containerid = '107603' + uid;
  const baseUrl = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=${containerid}`;
  const allPosts = [];
  let pageNum = 1;
  
  while (pageNum <= maxPages) {
    const url = pageNum === 1 ? baseUrl : `${baseUrl}&page=${pageNum}`;
    
    const result = await page.evaluate(async (fetchUrl) => {
      try {
        const resp = await window.fetch(fetchUrl, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await resp.json();
        const cards = data?.data?.cards || [];
        const posts = cards.filter(c => c.mblog).map(c => ({
          text: c.mblog.text || '',
          created: c.mblog.created_at || '',
          id: c.mblog.id || ''
        }));
        // 还有更多？
        const cardlineInfo = data?.data?.cardlistInfo || {};
        const total = cardlineInfo.total || posts.length;
        return {
          ok: data.ok,
          posts,
          total,
          page: pageNum
        };
      } catch(e) {
        return { ok: 0, posts: [], error: e.message };
      }
    }, url);
    
    if (!result.ok || result.posts.length === 0) break;
    
    allPosts.push(...result.posts);
    
    // 检查是否还有更多且已经是24h外了，停止
    const lastPost = result.posts[result.posts.length - 1];
    if (lastPost && !isWithin24h(lastPost.created)) break;
    
    pageNum++;
    
    // 人类感延时
    await new Promise(r => setTimeout(r, 500 + Math.random() * 1000));
  }
  
  return allPosts;
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const ctx = browser.contexts()[0];
  
  // 用现有页或新建
  let page = (await ctx.pages()).find(p => p.url().includes('m.weibo.cn'));
  if (!page) page = await ctx.newPage();
  
  // 先打开一个品牌页面确保登录态
  await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'networkidle', timeout: 20000 });
  await new Promise(r => setTimeout(r, 2000));
  
  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  
  const allData = {};
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i+1}/${brands.length}] ${brand.name}... `);
    
    try {
      const posts = await fetchBrandPosts(page, brand.uid);
      
      // 过滤24h内
      const recent = posts.filter(p => isWithin24h(p.created));
      
      // 清洗文本
      const cleaned = recent.map(p => ({
        text: cleanHtml(p.text),
        created: p.created,
        id: p.id
      }));
      
      process.stdout.write(`${posts.length}条API, ${cleaned.length}条24h内\n`);
      
      // 输出内容摘要
      cleaned.forEach((p, idx) => {
        process.stdout.write(`  #${idx+1} [${p.created}] ${p.text.substring(0, 120)}...\n`);
      });
      
      allData[brand.name] = {
        uid: brand.uid,
        apiCount: posts.length,
        recentCount: cleaned.length,
        posts: cleaned
      };
      
      // 人类延时
      await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000));
      
    } catch (e) {
      process.stdout.write(`错误: ${(e.message||'').substring(0, 60)}\n`);
      allData[brand.name] = { uid: brand.uid, apiCount: 0, recentCount: 0, posts: [], error: e.message?.substring(0,120) };
      await new Promise(r => setTimeout(r, 2000));
    }
  }
  
  // 输出JSON
  const fs = await import('fs');
  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  fs.writeFileSync(outPath, JSON.stringify(allData, null, 2));
  
  process.stdout.write(`\n=== 完成 ===\n数据已写入 ${outPath}\n`);
  
  // 品牌摘要
  process.stdout.write('\n=== 品牌摘要 ===\n');
  let totalRecent = 0;
  let activeBrands = 0;
  for (const brand of brands) {
    const d = allData[brand.name];
    if (d && d.recentCount > 0) {
      process.stdout.write(`${brand.name}: ${d.recentCount}条\n`);
      totalRecent += d.recentCount;
      activeBrands++;
    }
  }
  process.stdout.write(`\n${activeBrands}个品牌有动态, 共${totalRecent}条24h内内容\n`);
  
  await browser.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});
