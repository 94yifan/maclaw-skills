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
  // 2026-10-22：CDP 端口改成有序回退，避免单端口挂掉整轮直接失败（10-17 双端口同时失败属环境问题，重试无意义）
  // 2026-10-26：9333 连续 4 天（10-23~10-26）connectOverCDP 失败，每天固定浪费 60 秒超时；改为 18800 优先、单端口 20 秒
  let browser = null, usedPort = null;
  for (const port of [18800, 9333]) {
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`, { timeout: 20000 });
      usedPort = port;
      break;
    } catch (e) {
      console.log(`CDP ${port} 连接失败：${(e.message || '').slice(0, 80)}`);
    }
  }
  if (!browser) throw new Error('CDP 9333 与 18800 均连接失败，本轮无数据');
  console.log(`Connected CDP ${usedPort}`);
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
  // 2026-10-22：windowEnd 必须带秒。窗口右端冻结到秒，header 只写分钟会让「11:00:07 的帖在 11:00 窗口内」看起来像漂移（10-22 茶百道实例）
  const fmtSec = d => `${fmt(d)}:${String(d.getSeconds()).padStart(2,'0')}`;
  const output = {
    date: dateStr,
    crawlTime,
    windowEnd: fmtSec(windowEndDate),
    windowStart: fmtSec(windowStart),
    source: 'm.weibo.cn API via CDP (per-brand nav)',
    cdpPort: usedPort,
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
        // 2026-10-20 修正：容差从 -5 分钟改为 0。抓取开始后发布（ts > WINDOW_END）的帖子一律不进本窗口，
        // 否则 header 声称的 windowEnd 与实际正文时间不一致（10-19 55 秒漂移、10-20 1 秒漂移同源）。
        // 这些帖子会落在次日窗口左端，不会丢数据。
        const age = WINDOW_END - ts.getTime();
        return age <= WINDOW_MS && age >= 0;
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
  // 2026-10-22：记录抓取起止，用于把「整轮 duration」拆成抓取段和写作段（10-21/10-22 连续两轮 586s→665s，无法归因）
  output.crawlStartedAt = fmtSec(windowEndDate);
  output.crawlFinishedAt = fmtSec(new Date());
  const outPath = `/tmp/tea-raw-${dateStr}.json`;
  writeFileSync(outPath, JSON.stringify(output, null, 2));
  console.log('=== 完成 === 数据已写入', outPath);
  console.log(`窗口：${output.windowStart} – ${output.windowEnd}`);

  // 2026-10-22：输出逐条台账。写报告时按台账逐行交代（bullet / 合并到X / 剔除原因），
  // 禁止用「总数倒推」凑守恒式——10-22 就是这么把 2 条爷爷不泡茶静默吞掉的。
  const ledgerPath = `/tmp/tea-ledger-${dateStr}.md`;
  const lines = [`# 窗口逐条台账 ${dateStr}`, `> 窗口 ${output.windowStart} – ${output.windowEnd}｜来源 ${outPath}`, ''];
  let n = 0;
  for (const b of output.brands) {
    lines.push(`## ${b.brand}（${b.items.length} 条）`);
    if (b.items.length === 0) lines.push(`- 无：latest=${b.latest || 'n/a'} total=${b.total ?? 'n/a'} ok=${b.ok}`);
    for (const it of b.items) {
      n++;
      const when = (it.d || '').replace(/ \+0800 \d{4}$/, '');
      // 2026-10-26：每行带「→ 待归属」占位，写报告时必须替换成 正文/合并到#id/剔除＋原因；ledger-check.mjs 视「待归属」为未闭合
      lines.push(`- [ ] #${n} \`${it.id}\` ${when}｜${(it.t || '').slice(0, 60).replace(/\s+/g, ' ')} → 待归属`);
    }
    lines.push('');
  }
  lines.push(`合计 ${n} 条。每条必须落到「正文 bullet」或「合并到某条」或「剔除＋原因」，写完后逐行打勾。`);
  writeFileSync(ledgerPath, lines.join('\n'));
  console.log('逐条台账已写入', ledgerPath);

  let active = 0, totalPosts = 0, errs = 0, empty = 0;
  for (const b of output.brands) {
    if (b.error) errs++;
    if (b.ok && b.total === 0) empty++;
    if (b.items && b.items.length > 0) { active++; totalPosts += b.items.length; }
  }
  console.log(`${active}/23 个品牌24h窗口内有动态, 共 ${totalPosts} 条, 请求错误 ${errs} 个, 接口无返回(total=0) ${empty} 个`);

  // 2026-10-24：抓取完成后必须显式退出。
  // 走 chromium.connectOverCDP 时 websocket 会一直挂住 Node 事件循环：数据与台账已经写完，
  // 进程却不退出 → exec 超时被 terminate → cron 判 "Process failed" → announce 投递被跳过。
  // 10-18 sharp-harbor、10-24 delta-breeze 是同一签名（报告完整、run error、交付靠兜底补发）。
  // 注意：不要调 browser.close()，那是关掉用户的浏览器；直接退进程即可。
  await new Promise(resolve => process.stdout.write('', resolve));
  console.log('=== 进程退出 ===');
  process.exit(0);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
