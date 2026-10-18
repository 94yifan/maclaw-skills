/**
 * 茶饮日报爬虫 2026-10-18 - m.weibo.cn API via per-brand navigation
 * 关键修复：每品牌先导航到其主页（重置 432 限流/建立会话），再 fetch API
 * 按 skill 铁律：脚本内完成 24h 窗口过滤，latest 用 max(created_at) 计算
 */
import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const brands = [
  { name: 'Manner', uid: '6808111794' },
  { name: '树夏酸奶', uid: '7144806571' },
  { name: '挪瓦咖啡', uid: '7268463229' },
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
      if (resp.status !== 200) return { ok: 0, status: resp.status, posts: [], error: 'HTTP ' + resp.status };
      let data;
      try { data = JSON.parse(txt); } catch (e) { return { ok: 0, status: resp.status, posts: [], error: 'badjson len=' + txt.length }; }
      const cards = data?.data?.cards || [];
      const posts = cards.filter(c => c.mblog).map(c => {
        const mb = c.mblog;
        return {
          id: mb.id || '', created: mb.created_at || '', text: mb.text || '',
          reposts_count: mb.reposts_count || 0, comments_count: mb.comments_count || 0,
          attitudes_count: mb.attitudes_count || 0
        };
      });
      return { ok: data.ok, status: resp.status, posts, total: data?.data?.cardlistInfo?.total || posts.length };
    } catch (e) { return { ok: 0, status: 0, posts: [], error: e.message }; }
  }, { fetchUrl: url });
}

async function fetchBrandPosts(page, uid, maxPages = 4) {
  await page.goto(`https://m.weibo.cn/u/${uid}`, { waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2500 + Math.random() * 1500));

  const allPosts = [];
  for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
    let result = await fetchPage(page, uid, pageNum);
    if (!result.ok && (result.status === 432 || result.status === 0 || (result.error || '').includes('badjson'))) {
      await page.goto(`https://m.weibo.cn/u/${uid}`, { waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => {});
      await new Promise(r => setTimeout(r, 4000 + Math.random() * 2000));
      result = await fetchPage(page, uid, pageNum);
    }
    if (!result.ok || result.posts.length === 0) {
      if (result.error) process.stdout.write(`[p${pageNum}:${result.error}] `);
      break;
    }
    allPosts.push(...result.posts);
    const lastPost = result.posts[result.posts.length - 1];
    const lastDate = parseDate(lastPost.created);
    if (lastDate && (Date.now() - lastDate.getTime()) > 36 * 3600 * 1000) break;
    await new Promise(r => setTimeout(r, 800 + Math.random() * 900));
  }
  return allPosts;
}

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  console.log('Connected CDP 9333 (retry)');
  const ctx = browser.contexts()[0] || await browser.newContext();
  const page = (await ctx.pages()).find(p => p.url().includes('m.weibo.cn')) || await ctx.newPage();

  const today = new Date();
  const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const WINDOW_MS = 24 * 3600 * 1000;
  const output = { date: dateStr, crawlTime: today.toTimeString().slice(0,5), brands: [] };

  for (const brand of brands) {
    process.stdout.write(`[retry] ${brand.name}... `);
    let posts = [];
    for (let attempt = 0; attempt < 3; attempt++) {
      await new Promise(r => setTimeout(r, 4000 + Math.random() * 2000));
      posts = await fetchBrandPosts(page, brand.uid, 3);
      if (posts.length > 0) break;
      process.stdout.write(`(attempt ${attempt+1} empty) `);
    }
    let latest = null, latestTs = 0;
    for (const p of posts) {
      const ts = parseDate(p.created);
      if (ts && ts.getTime() > latestTs) { latestTs = ts.getTime(); latest = p.created; }
    }
    const items = posts.filter(p => { const ts = parseDate(p.created); return ts && (Date.now()-ts.getTime()) <= WINDOW_MS && (Date.now()-ts.getTime()) >= -5*60*1000; })
      .sort((a,b)=>parseDate(b.created)-parseDate(a.created))
      .map(p => ({ t: cleanHtml(p.text), d: p.created, r: p.reposts_count, c: p.comments_count, l: p.attitudes_count }));
    output.brands.push({ brand: brand.name, uid: brand.uid, latest, items });
    process.stdout.write(`抓${posts.length}条/窗口内${items.length}条 latest=${latest}\n`);
  }

  await page.close().catch(() => {});
  writeFileSync('/tmp/tea-raw-retry-2026-10-18.json', JSON.stringify(output, null, 2));
  console.log('retry done');
}
main().catch(e => { console.error('FATAL:', e); process.exit(1); });
