#!/usr/bin/env node
// report-structure-check.mjs — 日报结构门禁：查「该有的段有没有、header 数字与正文对不对得上、有没有禁用表述」
// 背景（2026-10-28）：行业层面信号段被误删，连续 3 天（10-26/10-27/10-28 11:00 版）没有，直到逸凡指出。
//   ledger-check 只校验「每条 raw 有归属」，管不了「该有的栏目整体缺失」和「header 条数与正文条数不符」。
//   今日另发现茉酸奶 3 条 raw → 2 条 bullet，两行都写「→ 正文」落在同一条 bullet，ledger-check 判通过（缺归属 0）。
// 铁律：退出码恒为 0（SKILL 规则 21），判定只看打印的数字与「待修 N 项」。
// 用法：node report-structure-check.mjs --report memory/weibo_daily_2026-10-28.md \
//          --ledger /tmp/tea-ledger-2026-10-28.md --brands 23
import fs from 'node:fs';

const args = process.argv.slice(2);
const getArg = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};
const today = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10);
// 2026-10-30 修复：位置参数曾被静默忽略（传旧文件路径仍去读今天文件，打印「结构通过」），
// 属守卫二十第①段「读数读错对象」。现在位置参数按 --report 处理，并在输出首行打印真实读取路径。
const positional = args.find((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
const reportPath = getArg('--report', positional || `memory/weibo_daily_${today}.md`);
const ledgerPath = getArg('--ledger', `/tmp/tea-ledger-${today}.md`);
const expectBrands = Number(getArg('--brands', '24'));

let rep = '';
try {
  rep = fs.readFileSync(reportPath, 'utf8');
} catch (e) {
  console.log(`GATE_FAIL READ_FAIL report=${reportPath} err=${e.message}`);
  console.log('判定：门禁没跑成，等于没门禁。先修路径再发（退出码仍为 0，判定看本行 GATE_FAIL）');
  process.exit(0);
}

const lines = rep.split('\n');
const issues = [];
const info = [];
const advisories = [];

// 2026-10-30 修复：台账与报告可能不是同一天（传旧报告却默认读今天台账），
// 错配会让门禁报出一堆「静默合并」假阳性。只在日期匹配或显式传 --ledger 时做归属交叉核对。
const repDateMatch = (rep.match(/^#\s*茶饮品牌微博日报\s*(\d{4}-\d{2}-\d{2})/m) || [])[1] || '';
const ledgerExplicit = args.includes('--ledger');
const ledgerDateMatch = (ledgerPath.match(/(\d{4}-\d{2}-\d{2})/) || [])[1] || '';
const ledgerPaired = ledgerExplicit || (repDateMatch && repDateMatch === ledgerDateMatch);

// ---------- 1. header ----------
const head = lines.slice(0, 6).filter(l => l.trim());
if (!/^#\s*茶饮品牌微博日报/.test(head[0] || '')) issues.push('header 第 1 行缺标题「# 茶饮品牌微博日报 <日期>」');
if (!/统计区间/.test(head[1] || '')) issues.push('header 第 2 行缺「统计区间」（日期级 + 北京时间）');
else if (/\d{1,2}:\d{2}/.test(head[1])) issues.push('header 第 2 行出现时刻（规则 24：统计区间只到日期级）');
const statLine = head[2] || '';
const mCover = statLine.match(/覆盖\s*(\d+)\s*品牌/);
const mAct = statLine.match(/有动态\s*(\d+)\s*家/);
const mIdle = statLine.match(/无动态\s*(\d+)\s*家/);
const mCount = statLine.match(/共\s*(\d+)\s*条/);
if (!mCover || !mAct || !mIdle || !mCount) issues.push('header 第 3 行要素不全（覆盖N品牌·有动态X家·无动态Y家·共K条）');
if (mCover && Number(mCover[1]) !== expectBrands) issues.push(`header 覆盖数 ${mCover[1]} ≠ ${expectBrands}（规则 5：23 品牌全列）`);

// ---------- 2. 正文结构 ----------
let inBrand = false, inIndustry = false, inIdle = false;
const brandBullets = new Map();
const bulletsOrder = [];
let industryItems = 0;
const idleBrands = [];
const bannedHits = [];
const timeHits = [];
let curBrand = null;

const BANNED = [
  ['对品牌而言', /对品牌而言/],
  ['这意味着', /这意味着/],
  ['待核实', /待核实/],
  ['实质/抽奖拆分', /实质\s*\d|抽奖公示\s*\d/],
  ['互动口径', /互动(量|数|排名)|r\+c\+l/],
  ['互动数字', /转\s*\d|评\s*\d|赞\s*\d/],
];
const SOFT = [
  ['说明/判断类句（人工确认）', /说明|判断|反映出/],
];

for (let i = 0; i < lines.length; i++) {
  const raw = lines[i];
  const line = raw.trim();
  if (!line) continue;
  if (/^\*\*行业层面信号\*\*$/.test(line)) { inIndustry = true; inBrand = false; continue; }
  if (/^\*\*无动态品牌\*\*$/.test(line)) { inIdle = true; inBrand = false; inIndustry = false; continue; }
  const bm = line.match(/^\*\*(.+?)\*\*$/);
  if (bm && !/行业层面信号|无动态品牌/.test(line)) { curBrand = bm[1]; inBrand = true; inIdle = false; continue; }
  if (inIdle && /今日无动态：/.test(line)) {
    line.replace(/^今日无动态：/, '').split(/[、,，]/).map(s => s.trim()).filter(Boolean).forEach(b => idleBrands.push(b));
    continue;
  }
  if (inIndustry && /^\d+\.\s/.test(line)) { industryItems++; continue; }
  if (inBrand && curBrand && /【(新品上市|IP联名\/艺人宣发|营销活动)】/.test(line)) {
    brandBullets.set(curBrand, (brandBullets.get(curBrand) || 0) + 1);
    bulletsOrder.push({ brand: curBrand, text: line });
    for (const [name, re] of BANNED) if (re.test(line)) bannedHits.push(`L${i + 1} ${curBrand}｜${name}｜${line.slice(0, 40)}`);
    for (const [name, re] of SOFT) if (re.test(line)) advisories.push(`L${i + 1} ${curBrand}｜${name}｜${line.slice(0, 40)}`);
    // 2026-10-30 修复（对应 10-29 B4 未落地）：时刻提示要区分「活动时间」与「发帖时间」。
    // 判据：时刻前后 12 字内出现活动语义词即视为活动时间，不提示。10-29 当天 4 条提示全是误报，
    // 提示区长期误报会把真错误训练成背景噪音（门禁精度与召回同样要守）。
    const ACT_CTX = /(月|日|至|起|止|截止|限时|活动|每日|每天|开抽|开奖|营业|时段|上架|上线|前|–|—|~|～)/;
    for (const m of line.matchAll(/\b\d{1,2}:\d{2}\b/g)) {
      const t = m[0];
      const from = Math.max(0, m.index - 12);
      const to = Math.min(line.length, m.index + t.length + 12);
      const ctx = line.slice(from, to);
      if (ACT_CTX.test(ctx)) continue;
      advisories.push(`L${i + 1} ${curBrand}｜出现时刻 ${t}（活动时间可保留，发帖时间必须删）`);
    }
  }
}

const totalBullets = [...brandBullets.values()].reduce((a, b) => a + b, 0);
const activeBrands = brandBullets.size;

if (!/行业层面信号/.test(rep)) issues.push('缺「**行业层面信号**」整段（规则 27：固定结构，3-6 条，不得删）');
else if (industryItems < 3) issues.push(`行业层面信号只有 ${industryItems} 条，规则 27 要求 3-6 条`);
if (!/无动态品牌/.test(rep)) issues.push('缺「**无动态品牌**」清单');
if (mAct && Number(mAct[1]) !== activeBrands) issues.push(`header 有动态 ${mAct[1]} 家 ≠ 正文品牌块 ${activeBrands} 家`);
if (mIdle && Number(mIdle[1]) !== idleBrands.length) issues.push(`header 无动态 ${mIdle[1]} 家 ≠ 清单 ${idleBrands.length} 家`);
if (mCover && mAct && mIdle && Number(mAct[1]) + Number(mIdle[1]) !== Number(mCover[1])) {
  issues.push(`有动态 ${mAct[1]} + 无动态 ${mIdle[1]} ≠ 覆盖 ${mCover[1]}`);
}
if (bannedHits.length) issues.push(...bannedHits.map(h => `禁用表述 ${h}`));
if (timeHits.length) timeHits.length = 0;

// ---------- 3. header 条数 vs 正文条数 ----------
let ledgerStat = '台账未提供';
if (mCount) {
  const K = Number(mCount[1]);
  info.push(`header 共 ${K} 条｜正文 bullet ${totalBullets} 条｜差 ${K - totalBullets}`);
  if (K !== totalBullets) {
    let brk = '';
    try {
      if (!ledgerPaired) throw new Error('ledger date mismatch');
      const led = fs.readFileSync(ledgerPath, 'utf8');
      const cut = (led.match(/→\s*剔除/g) || []).length;
      const mrg = (led.match(/→\s*合并/g) || []).length;
      brk = `（台账：剔除 ${cut}｜合并 ${mrg}）`;
      ledgerStat = `剔除 ${cut}｜合并 ${mrg}`;
    } catch { /* ledger 缺失不阻断 */ }
    issues.push(`header 条数 ${K} ≠ 正文 bullet ${totalBullets}${brk}：header 应写读者看得见的条数，抽奖公示与合并不计数`);
  }
}

// ---------- 4. 台账「一行一 bullet」：抓静默合并 ----------
if (!ledgerPaired) {
  info.push(`台账未配对（报告 ${repDateMatch || '无日期'} vs 台账 ${ledgerDateMatch || '无日期'}），跳过归属交叉核对`);
} else if (fs.existsSync(ledgerPath)) {
  const led = fs.readFileSync(ledgerPath, 'utf8');
  const rows = new Map();
  let cur = null;
  for (const ln of led.split('\n')) {
    const h = ln.match(/^##\s*(.+?)（(\d+)\s*条）/);
    if (h) { cur = h[1]; rows.set(cur, { 正文: 0, 剔除: 0, 合并: 0 }); continue; }
    if (!cur || !ln.startsWith('- [x]')) continue;
    if (/→\s*正文/.test(ln)) rows.get(cur).正文++;
    else if (/→\s*剔除/.test(ln)) rows.get(cur).剔除++;
    else if (/→\s*合并/.test(ln)) rows.get(cur).合并++;
  }
  for (const [brand, r] of rows) {
    const b = brandBullets.get(brand) || 0;
    if (r.正文 > b) {
      issues.push(`静默合并 ${brand}：台账 ${r.正文} 行标「→ 正文」，正文只有 ${b} 条 bullet（规则 25：合并必须写「→ 合并到 #<id>」）`);
    }
  }
}

// ---------- 输出 ----------
console.log(`# 日报结构核对 ${reportPath}`);
console.log(`品牌块 ${activeBrands} 家｜无动态清单 ${idleBrands.length} 家｜正文 bullet ${totalBullets} 条｜行业信号 ${industryItems} 条`);
if (mCount) console.log(info.join('\n'));
if (ledgerStat !== '台账未提供') console.log(`台账归属：${ledgerStat}`);
if (issues.length) {
  console.log(`--- 待修 ${issues.length} 项 ---`);
  console.log(issues.map((s, i) => `${i + 1}. ${s}`).join('\n'));
} else {
  console.log('--- 待修 0 项 ---');
}
if (advisories.length) {
  console.log(`--- 提示 ${advisories.length} 条（不阻断，人工确认）---`);
  console.log(advisories.map((s, i) => `${i + 1}. ${s}`).join('\n'));
}
console.log('判定：' + (issues.length === 0 ? '结构通过，可发' : '先修上面的项再发（禁用表述需人工确认是否为活动名称）'));
process.exit(0);
