/**
 * 茶饮品牌微博爬虫 v7.1
 * - 点击「微博」tab获取全部时间线
 * - 模拟人类滚动加载
 * - 提取文章文本+时间戳
 */
import { chromium } from 'playwright-core';

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

// 解析微博时间
function parseTime(timeText) {
  if (!timeText) return null;
  const now = new Date();
  const y = now.getFullYear();
  
  // "刚刚"
  if (timeText === '刚刚') return now;
  
  // "X分钟前"
  let m = timeText.match(/^(\d+)分钟前$/);
  if (m) return new Date(now - parseInt(m[1]) * 60000);
  
  // "X小时前"
  m = timeText.match(/^(\d+)小时前$/);
  if (m) return new Date(now - parseInt(m[1]) * 3600000);
  
  // "MM-DD HH:mm"
  m = timeText.match(/^(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$/);
  if (m) return new Date(y, parseInt(m[1])-1, parseInt(m[2]), parseInt(m[3]), parseInt(m[4]));
  
  return null;
}

function isWithin24h(timeText) {
  const dt = parseTime(timeText);
  if (!dt) return false;
  return (new Date() - dt) < 24 * 3600 * 1000;
}

// 从页面提取文章
async function extractArticles(page) {
  return await page.evaluate(() => {
    const articles = document.querySelectorAll('article');
    return Array.from(articles).map(art => {
      const allText = art.innerText || '';
      
      // 找时间戳
      let timestamp = '';
      const links = art.querySelectorAll('a');
      for (const link of links) {
        const t = link.innerText.trim();
        if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}$/.test(t) || 
            /^\d+分钟前$/.test(t) || /^\d+小时前$/.test(t) || t === '刚刚') {
          timestamp = t;
          break;
        }
      }
      
      return { text: allText, timestamp };
    }).filter(a => a.text.length > 20);
  });
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const ctx = browser.contexts()[0];
  const page = (await ctx.pages())[0] || await ctx.newPage();
  
  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  
  const allData = {};
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i+1}/${brands.length}] ${brand.name}... `);
    
    try {
      // 导航
      const url = `https://weibo.com/u/${brand.uid}`;
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(4000 + Math.random() * 3000);
      
      // 尝试点击「微博」tab - 用多种方式找到它
      let clickedWeibo = false;
      for (const tabText of ['微博', '全部微博']) {
        const found = await page.evaluate((text) => {
          const allEls = document.querySelectorAll('a, span, div');
          for (const el of allEls) {
            if (el.innerText.trim() === text && el.offsetParent !== null) {
              el.click();
              return true;
            }
          }
          return false;
        }, tabText);
        if (found) {
          clickedWeibo = true;
          process.stdout.write(`点击「${tabText}」`);
          await page.waitForTimeout(3000 + Math.random() * 2000);
          break;
        }
      }
      
      if (!clickedWeibo) {
        process.stdout.write('未找到微博tab');
      }
      
      // 滚动加载
      let prevCount = 0;
      let stagnantCount = 0;
      const maxScrolls = 8;
      
      for (let s = 0; s < maxScrolls; s++) {
        const posts = await extractArticles(page);
        
        if (posts.length === prevCount) {
          stagnantCount++;
          if (stagnantCount >= 2) break;
        } else {
          stagnantCount = 0;
          prevCount = posts.length;
        }
        
        // 智能滚动
        await page.evaluate(() => {
          window.scrollBy(0, 600 + Math.random() * 400);
        });
        await page.waitForTimeout(2000 + Math.random() * 2000);
      }
      
      // 最终提取
      const allPosts = await extractArticles(page);
      
      // 去重
      const seen = new Set();
      const unique = allPosts.filter(p => {
        const key = p.text.substring(0, 120);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      
      const recent = unique.filter(p => isWithin24h(p.timestamp));
      
      process.stdout.write(` → ${unique.length}条, ${recent.length}条24h内\n`);
      
      allData[brand.name] = {
        uid: brand.uid,
        total: unique.length,
        recent: recent.length,
        posts: recent
      };
      
      // 人类延时
      const delay = 5000 + Math.random() * 8000;
      await page.waitForTimeout(delay);
      
    } catch (e) {
      process.stdout.write(`错误: ${(e.message||'').substring(0, 60)}\n`);
      allData[brand.name] = { uid: brand.uid, total: 0, recent: 0, posts: [], error: e.message?.substring(0,120) };
      await page.waitForTimeout(3000);
    }
  }
  
  // 输出JSON
  const fs = await import('fs');
  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  fs.writeFileSync(outPath, JSON.stringify(allData, null, 2));
  
  // 输出精简版
  const summary = {};
  for (const brand of brands) {
    const d = allData[brand.name];
    summary[brand.name] = {
      recent: d?.recent || 0,
      total: d?.total || 0,
      error: d?.error
    };
  }
  
  process.stdout.write(`\n=== 完成 ===\n数据已写入 ${outPath}\n`);
  process.stdout.write(JSON.stringify(summary, null, 2) + '\n');
  
  await browser.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});
