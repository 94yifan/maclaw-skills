/**
 * 茶饮日报爬虫 - m.weibo.cn API, 23 brands, 5s间隔
 */
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
  { name: '林里LINLEE', uid: '7608120899' },
  { name: '柠季', uid: '7592401864' },
  { name: '挪瓦咖啡', uid: '7268463229' },
  { name: '东方墨兰', uid: '8005590706' },
];

function parseDate(createdStr) {
  const m = createdStr.match(/(\w{3}) (\w{3}) (\d{2}) (\d{2}):(\d{2}):(\d{2}) .+? (\d{4})/);
  if (!m) return null;
  const months = {Jan:0,Feb:1,Mar:2,Apr:3,May:4,Jun:5,Jul:6,Aug:7,Sep:8,Oct:9,Nov:10,Dec:11};
  const month = months[m[2]];
  if (month === undefined) return null;
  return new Date(parseInt(m[7]), month, parseInt(m[3]), parseInt(m[4]), parseInt(m[5]), parseInt(m[6]));
}

function cleanHtml(html) {
  return (html || '').replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

async function fetchBrandPosts(page, uid, maxPages = 3) {
  const containerid = '107603' + uid;
  const baseUrl = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=${containerid}`;
  const allPosts = [];
  let pageNum = 1;

  while (pageNum <= maxPages) {
    const url = pageNum === 1 ? baseUrl : `${baseUrl}&page=${pageNum}`;
    const result = await page.evaluate(async ({ fetchUrl, pageNum }) => {
      try {
        const resp = await window.fetch(fetchUrl, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await resp.json();
        const cards = data?.data?.cards || [];
        const posts = cards.filter(c => c.mblog).map(c => {
          const mb = c.mblog;
          return {
            id: mb.id || '',
            created: mb.created_at || '',
            text: mb.text || '',
            text_raw: mb.text_raw || '',
            reposts_count: mb.reposts_count || 0,
            comments_count: mb.comments_count || 0,
            attitudes_count: mb.attitudes_count || 0,
            is_repost: !!mb.retweeted_status,
            repost_text: mb.retweeted_status ? (mb.retweeted_status.text || '') : '',
            repost_user: mb.retweeted_status ? (mb.retweeted_status.user?.screen_name || '') : '',
            pics: mb.pics ? mb.pics.length : 0
          };
        });
        const cardlineInfo = data?.data?.cardlistInfo || {};
        return { ok: data.ok, posts, total: cardlineInfo.total || posts.length, page: pageNum };
      } catch(e) {
        return { ok: 0, posts: [], error: e.message };
      }
    }, { fetchUrl: url, pageNum });

    if (!result.ok || result.posts.length === 0) {
      if (result.error) process.stdout.write(`[API err p${pageNum}: ${result.error}] `);
      break;
    }
    allPosts.push(...result.posts);

    const lastPost = result.posts[result.posts.length - 1];
    const lastDate = parseDate(lastPost.created);
    if (lastDate && (Date.now() - lastDate.getTime()) > 30 * 3600 * 1000) break;

    pageNum++;
    await new Promise(r => setTimeout(r, 500 + Math.random() * 800));
  }

  return allPosts;
}

async function main() {
  // Try ports in order
  const PORTS = [9333, 18800];
  let browser = null;
  for (const port of PORTS) {
    try {
      browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
      console.log('Connected to CDP port', port);
      break;
    } catch(e) {
      console.log('Port', port, 'failed:', e.message.slice(0, 60));
    }
  }
  if (!browser) {
    console.log('CDP_CONNECTION_FAILED');
    process.exit(1);
  }

  const ctx = browser.contexts()[0] || await browser.newContext();
  let page = (await ctx.pages()).find(p => p.url().includes('weibo'));
  if (!page) page = await ctx.newPage();

  // Ensure logged-in session on m.weibo.cn
  await page.goto('https://m.weibo.cn/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 3000));

  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const crawlTime = today.toTimeString().slice(0, 5);

  const output = { date: dateStr, crawlTime, brands: [] };

  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i+1}/${brands.length}] ${brand.name}... `);
    try {
      const posts = await fetchBrandPosts(page, brand.uid);
      const cleaned = posts.map(p => ({
        id: p.id,
        created_at: p.created,
        text: cleanHtml(p.text),
        is_repost: p.is_repost,
        repost_user: p.repost_user,
        repost_text: cleanHtml(p.repost_text),
        pics: p.pics,
        reposts_count: p.reposts_count,
        comments_count: p.comments_count,
        attitudes_count: p.attitudes_count
      }));
      const entry = { name: brand.name, uid: brand.uid, total: posts.length ? posts[0] && posts.length : 0, posts: cleaned };
      // capture total from API first call
      output.brands.push(entry);
      process.stdout.write(`${posts.length}条\n`);
    } catch (e) {
      output.brands.push({ name: brand.name, uid: brand.uid, error: (e.message || '').slice(0, 120), posts: [] });
      process.stdout.write(`err: ${(e.message||'').slice(0, 50)}\n`);
    }
    // 每批间隔5秒以上，模拟人类操作
    await new Promise(r => setTimeout(r, 5000 + Math.random() * 2000));
  }

  await browser.close();

  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  writeFileSync(outPath, JSON.stringify(output, null, 2));
  console.log('=== 完成 === 数据已写入', outPath);

  // 摘要
  let active = 0, totalPosts = 0;
  for (const b of output.brands) {
    if (b.posts && b.posts.length > 0) { active++; totalPosts += b.posts.length; }
  }
  console.log(`${active}/23 个品牌有内容, 共 ${totalPosts} 条`);
}

main().catch(e => {
  console.error('FATAL:', e);
  process.exit(1);
});
