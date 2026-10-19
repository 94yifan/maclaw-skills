/**
 * 茶饮日报爬虫（canonical，唯一维护版本）
 * 用法：node tea-daily-crawl.mjs   → 输出 /tmp/tea-raw-<运行日>.json
 *
 * 2026-10-19 修复（对应当日 dreaming）：
 * 1. 窗口右端 WINDOW_END 在抓取开始前冻结一次，所有品牌用同一时间点过滤。
 *    旧版用 Date.now() 逐品牌比较，crawlTime=脚本启动时刻，导致窗口内混入
 *    crawlTime 之后发布的帖子（10-19 霸王茶姬 11:00:55），header 与数据不一致。
 * 2. 每品牌写回 ok / total / fetched / error，采集说明只允许引用这些字段。
 *    旧版不落盘 ok 和 total，报告却写「接口 ok=1」，无法溯源；
 *    也无法按 10-18 的规则用 total=0 判断是否为接口无返回。
 * 3. items 保留微博 id，便于跨天去重与守恒式核对。
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
  const m = (createdStr || '').match(/(\w{3}) (\w{3}) (\d{2}) (\d{2}):(\d{2}):(\d{2}) .+? (\d{4})/);
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

async function fetchPage(page, uid, pageNum) {
  const containerid = '107603' + uid;
  const url = `https://m.weibo.cn/api/container/getIndex?type=uid&value=${uid}&containerid=${containerid}` + (pageNum > 1 ? `&page=${pageNum}` : '');
  return await page.evaluate(async ({ fetchUrl }) => {
    try {
      const resp = await window.fetch(fetchUrl, { credentials: 'include', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const txt = await resp.text();
      if (resp.status !== 200) return { ok: 0, status: resp.status, posts: [], total: 0, error: 'HTTP ' + resp.status };
      let data;
      try { data = JSON.parse(txt); } catch (e) { return { ok: 0, status: resp.status, posts: [], total: 0, error: 'badjson len=' + txt.length }; }
      const cards = data?.data?.cards || [];
      const posts = cards.filter(c => c.mblog).map(c => {
        const mb = c.mblog;
        return {
          id: mb.id || '', created: mb.created_at || '', text: mb.text || '',
          reposts_count: mb.reposts_count || 0, comments_count: mb.comments_count || 0,
          attitudes_count: mb.attitudes_count || 0
        };
      });
      return { ok: data.ok, status: resp.status, posts, total: data?.data?.cardlistInfo?.total ?? posts.length };
    } catch (e) { return { ok: 0, status: 0, posts: [], total: 0, error: e.message }; }
  }, { fetchUrl: url });
}

async function fetchBrandPosts(page, uid, windowEnd, maxPages = 4) {
  await page.goto(`https://m.weibo.cn/u/${uid}`, { waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2500 + Math.random() * 1500));

  const allPosts = [];
  let last = { ok: 0, total: 0, error: 'no request' };
  for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
    let result = await fetchPage(page, uid, pageNum);
    if (!result.ok && (result.status === 432 || result.status === 0 || (result.error || '').includes('badjson'))) {
      await page.goto(`https://m.weibo.cn/u/${uid}`, { waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => {});
      await new Promise(r => setTimeout(r, 4000 + Math.random() * 2000));
      result = await fetchPage(page, uid, pageNum);
    }
    last = result;
    if (!result.ok || result.posts.length === 0) {
      if (result.error) process.stdout.write(`[p${pageNum}:${result.error}] `);
      break;
    }
    allPosts.push(...result.posts);
    const lastPost = result.posts[result.posts.length - 1];
    const lastDate = parseDate(lastPost.created);
    if (lastDate && (windowEnd - lastDate.getTime()) > 36 * 3600 * 1000) break;
    await new Promise(r => setTimeout(r, 800 + Math.random() * 900));
  }
  return { posts: allPosts, ok: last.ok, total: last.ok ? (last.total ?? null) : null, fetched: allPosts.length, error: last.error || null };
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  console.log('Connected CDP 9333');
  const ctx = browser.contexts()[0] || await browser.newContext();
  let page = (await ctx.pages()).find(p => p.url().includes('m.weibo.cn')) || await ctx.newPage();

  // 窗口右端只冻结一次：所有品牌、所有分页都以这个时间点为准
  const WINDOW_END = Date.now();
  const windowEndDate = new Date(WINDOW_END);
  const dateStr = `${windowEndDate.getFullYear()}-${String(windowEndDate.getMonth()+1).padStart(2,'0')}-${String(windowEndDate.getDate()).padStart(2,'0')}`;
  const crawlTime = windowEndDate.toTimeString().slice(0, 5);
  const windowStart = new Date(WINDOW_END - 24 * 3600 * 1000);
  const WINDOW_MS = 24 * 3600 * 1000;
  const fmt = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  const output = {
    date: dateStr,
    crawlTime,
    windowEnd: fmt(windowEndDate),
    windowStart: fmt(windowStart),
    source: 'm.weibo.cn API via CDP (per-brand nav)',
    brands: []
  };

  for (let i = 0; i < brands.length; i++) {
    const brand = brands[i];
    process.stdout.write(`[${i+1}/${brands.length}] ${brand.name}... `);
    try {
      const result = await fetchBrandPosts(page, brand.uid, WINDOW_END);
      const posts = result.posts;
      let latest = null, latestTs = 0;
      for (const p of posts) {
        const ts = parseDate(p.created);
        if (ts && ts.getTime() > latestTs) { latestTs = ts.getTime(); latest = p.created; }
      }
      const inWindow = posts.filter(p => {
        const ts = parseDate(p.created);
        if (!ts) return false;
        const age = WINDOW_END - ts.getTime();
        return age <= WINDOW_MS && age >= -5 * 60 * 1000;
      });
      inWindow.sort((a, b) => parseDate(b.created) - parseDate(a.created));
      const items = inWindow.map(p => ({ id: p.id, t: cleanHtml(p.text), d: p.created, r: p.reposts_count, c: p.comments_count, l: p.attitudes_count }));
      output.brands.push({
        brand: brand.name,
        uid: brand.uid,
        ok: result.ok,
        total: result.total,
        fetched: result.fetched,
        error: result.error,
        latest,
        items
      });
      process.stdout.write(`抓${posts.length}条/窗口内${items.length}条 ok=${result.ok} total=${result.total} latest=${latest}\n`);
    } catch (e) {
      output.brands.push({ brand: brand.name, uid: brand.uid, ok: 0, total: null, fetched: 0, error: (e.message || '').slice(0, 120), items: [], latest: null });
      process.stdout.write(`err: ${(e.message||'').slice(0, 60)}\n`);
    }
    await new Promise(r => setTimeout(r, 5000 + Math.random() * 2500));
  }

  await page.close().catch(() => {});
  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  writeFileSync(outPath, JSON.stringify(output, null, 2));
  console.log('=== 完成 === 数据已写入', outPath);
  console.log(`窗口：${output.windowStart} – ${output.windowEnd}`);
  let active = 0, totalPosts = 0, errs = 0, empty = 0;
  for (const b of output.brands) {
    if (b.error) errs++;
    if (b.ok && b.total === 0) empty++;
    if (b.items && b.items.length > 0) { active++; totalPosts += b.items.length; }
  }
  console.log(`${active}/23 个品牌24h窗口内有动态, 共 ${totalPosts} 条, 请求错误 ${errs} 个, 接口无返回(total=0) ${empty} 个`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
