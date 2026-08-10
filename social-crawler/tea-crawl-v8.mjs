/**
 * 茶饮品牌微博爬虫 v8 - 基于 m.weibo.cn 移动版
 * 结构清晰，提取更可靠
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

// 从m.weibo.cn页面提取文章
async function extractMobilePosts(page) {
  return await page.evaluate(() => {
    const posts = [];
    // 找到所有banner元素 - 每个banner包含一个post的头部信息
    const banners = document.querySelectorAll('.card9 .card-list .card9 .banner');
    // 或者找所有文章元素
    const cards = document.querySelectorAll('.card-wrap, .card, .card-list > div');
    
    if (cards.length > 0) {
      cards.forEach(card => {
        const text = card.innerText || '';
        // 找时间
        let timestamp = '';
        const headings = card.querySelectorAll('h4, h3');
        headings.forEach(h => {
          const t = h.innerText.trim();
          if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(t)) timestamp = t;
          else if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(h.textContent || '')) timestamp = h.textContent.trim();
        });
        
        if (text.length > 20) {
          posts.push({ text: text.substring(0, 800), timestamp });
        }
      });
    }
    
    return posts;
  });
}

// 更精确的提取 - 从timeline直接找
async function extractPosts(page) {
  return await page.evaluate(() => {
    const results = [];
    
    // 方法1: 找按钮/链接中包含时间格式的元素，然后取父级内容
    const allElements = document.querySelectorAll('h4, h3, a, span, div');
    
    allElements.forEach(el => {
      const text = el.textContent || '';
      const trimmed = text.trim();
      
      // 匹配时间格式: "6-16 10:00" 或 "6-16 10:00 来自 ..."
      if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(trimmed)) {
        // 找到包含此时间的post容器
        let container = el.closest('[class*="card"]') || el.closest('.card9') || el.parentElement;
        if (!container) container = el;
        
        // 向上找3层找内容
        let content = '';
        let walk = el;
        for (let i = 0; i < 5 && walk; i++) {
          const t = (walk.innerText || walk.textContent || '').trim();
          if (t.length > content.length) content = t;
          walk = walk.parentElement;
        }
        
        results.push({
          timestamp: trimmed.split('来自')[0].trim(),
          text: content.substring(0, 800)
        });
      }
    });
    
    return results;
  });
}

// 解析时间
function parseTime(text) {
  if (!text) return null;
  const now = new Date();
  const y = now.getFullYear();
  
  let m = text.match(/^(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})/);
  if (m) return new Date(y, parseInt(m[1])-1, parseInt(m[2]), parseInt(m[3]), parseInt(m[4]));
  
  m = text.match(/^(\d+)分钟前$/);
  if (m) return new Date(now - parseInt(m[1])*60000);
  
  m = text.match(/^(\d+)小时前$/);
  if (m) return new Date(now - parseInt(m[1])*3600000);
  
  if (text === '刚刚') return now;
  return null;
}

function isWithin24h(text) {
  const dt = parseTime(text);
  if (!dt) return false;
  return (new Date() - dt) < 24*3600*1000;
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  const ctx = browser.contexts()[0];
  
  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  
  const allData = {};
  
  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i+1}/${brands.length}] ${brand.name}... `);
    
    try {
      // 使用新标签页打开m.weibo.cn
      const page = await ctx.newPage();
      await page.goto(`https://m.weibo.cn/u/${brand.uid}`, {
        waitUntil: 'networkidle',
        timeout: 20000
      });
      
      // 等待渲染
      await page.waitForTimeout(3000 + Math.random() * 2000);
      
      // 提取
      let posts = await page.evaluate(() => {
        const results = [];
        const els = document.querySelectorAll('h4');
        els.forEach(h => {
          const t = h.textContent || '';
          if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(t.trim())) {
            // 找父级容器
            let card = h.closest('[class*="card"]') || h.parentElement;
            while (card && !card.querySelector('h4') && card.parentElement) {
              card = card.parentElement;
            }
            // 再向上找内容容器
            let container = card ? card.parentElement : null;
            if (!container) container = h;
            for (let j = 0; j < 3; j++) {
              if (container.parentElement) container = container.parentElement;
            }
            
            const content = container ? (container.innerText || '').trim() : '';
            
            // 提取纯粹的时间部分
            const tsMatch = t.trim().match(/^(\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2})/);
            if (tsMatch) {
              results.push({
                timestamp: tsMatch[1],
                content: content.substring(0, 1000)
              });
            }
          }
        });
        return results;
      });
      
      // 如果没找到，用整个body的innerText
      if (posts.length === 0) {
        const bodyText = await page.evaluate(() => document.body.innerText);
        // 手动找时间戳行
        const lines = bodyText.split('\n');
        let currentTs = '';
        let currentContent = '';
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (/^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(trimmed)) {
            if (currentTs && currentContent) {
              posts.push({ timestamp: currentTs, content: currentContent });
            }
            currentTs = trimmed.replace(/ 来自 .*$/, '').trim();
            currentContent = '';
          } else if (currentTs && trimmed.length > 5) {
            currentContent += trimmed + '\n';
          }
        }
        if (currentTs && currentContent) {
          posts.push({ timestamp: currentTs, content: currentContent });
        }
      }
      
      // 去重
      const seen = new Set();
      const unique = posts.filter(p => {
        const key = p.content?.substring(0, 80) || '';
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      
      const recent = unique.filter(p => isWithin24h(p.timestamp));
      
      process.stdout.write(`${unique.length}条, ${recent.length}条24h内\n`);
      
      // 打印最近的内容概要
      recent.forEach((p, idx) => {
        process.stdout.write(`  #${idx+1} [${p.timestamp}] ${(p.content||'').substring(0, 100)}...\n`);
      });
      
      allData[brand.name] = {
        uid: brand.uid,
        total: unique.length,
        recent: recent.length,
        posts: recent.map(p => ({ ts: p.timestamp, text: p.content }))
      };
      
      await page.close();
      
      // 人类延时
      const delay = 3000 + Math.random() * 5000;
      await page.waitForTimeout(delay);
      
    } catch (e) {
      process.stdout.write(`错误: ${(e.message||'').substring(0, 60)}\n`);
      allData[brand.name] = { uid: brand.uid, total: 0, recent: 0, posts: [], error: e.message?.substring(0,120) };
      
      try {
        const pages = ctx.pages();
        for (const p of pages) {
          if (p.url().includes('m.weibo.cn/u')) await p.close().catch(()=>{});
        }
      } catch(e2) {}
      
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  
  // 输出
  const fs = await import('fs');
  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  fs.writeFileSync(outPath, JSON.stringify(allData, null, 2));
  
  process.stdout.write(`\n=== 完成 ===\n数据已写入 ${outPath}\n`);
  
  // 摘要
  process.stdout.write('\n=== 品牌摘要 ===\n');
  let totalRecent = 0;
  let activeBrands = 0;
  for (const brand of brands) {
    const d = allData[brand.name];
    if (d && d.recent > 0) {
      process.stdout.write(`  ${brand.name}: ${d.recent}条\n`);
      totalRecent += d.recent;
      activeBrands++;
    }
  }
  process.stdout.write(`\n共${activeBrands}个品牌有动态, ${totalRecent}条内容\n`);
  
  await browser.close();
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});
