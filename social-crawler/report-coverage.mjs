#!/usr/bin/env node
// report-coverage.mjs — 机械核对 raw 每条是否落到日报正文
// 用途：解决「台账全勾 [x] 但正文静默吞帖」的缺口（2026-10-26 实证：header 24 条 / 正文 21 bullet，瑞幸 09:00 转发请喝帖无归属）
// 判据：对每条 raw 文本与日报全文求最长公共子串（LCS，按字符），>=8 字判已覆盖；<8 字列出待人工判定
// 铁律：退出码恒为 0（SKILL 规则 21），判定只看输出数字
// 用法：node report-coverage.mjs --raw /tmp/tea-raw-2026-10-26.json --report memory/weibo_daily_2026-10-26.md
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const getArg = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};

const today = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10);
const rawPath = getArg('--raw', `/tmp/tea-raw-${today}.json`);
const reportPath = getArg('--report', path.join(process.cwd(), 'memory', `weibo_daily_${today}.md`));
const THRESHOLD = Number(getArg('--min', '8'));

function clean(s) {
  return String(s || '')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/网页链接|微博视频|抽奖详情|微博抽奖平台|微博官方唯一抽奖工具/g, '')
    .replace(/[\s\u0000-\u001f]/g, '')
    .replace(/[，。！？、；：""''（）()\[\]【】《》…—\-~·#@+=*%^&|\\/<>,.!?;:'"`]/g, '')
    .trim();
}

function lcs(a, b) {
  if (!a.length || !b.length) return 0;
  const n = a.length, m = b.length;
  // 单行 DP，控制内存
  let prev = new Uint32Array(m + 1);
  let cur = new Uint32Array(m + 1);
  let best = 0;
  for (let i = 1; i <= n; i++) {
    const ca = a.charCodeAt(i - 1);
    for (let j = 1; j <= m; j++) {
      if (ca === b.charCodeAt(j - 1)) {
        cur[j] = prev[j - 1] + 1;
        if (cur[j] > best) best = cur[j];
      } else {
        cur[j] = 0;
      }
    }
    const t = prev; prev = cur; cur = t; cur.fill(0);
  }
  return best;
}

let raw, report;
try {
  raw = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
  report = fs.readFileSync(reportPath, 'utf8');
} catch (e) {
  console.log(`READ_FAIL raw=${rawPath} report=${reportPath} err=${e.message}`);
  console.log('判定：无法核对，需人工确认路径（退出码仍为 0）');
  process.exit(0);
}

const reportClean = clean(report);
const brands = raw.brands || [];
let total = 0, covered = 0;
const pending = [];
const rows = [];

for (const b of brands) {
  for (const it of (b.items || [])) {
    total++;
    const text = clean(it.t || it.text || it.content || '');
    const score = lcs(text, reportClean);
    const ok = score >= THRESHOLD;
    if (ok) covered++;
    else pending.push({ brand: b.brand, time: it.d || it.created_at, score, snippet: (it.t || it.text || '').slice(0, 50) });
    rows.push(`  ${ok ? '[OK]  ' : '[MISS]'} ${b.brand}  ${it.d || ''}  LCS=${score}  ${(it.t || it.text || '').replace(/\s+/g, ' ').slice(0, 40)}`);
  }
}

console.log(`# 覆盖核对 ${raw.date || today}｜raw=${rawPath}`);
console.log(`raw 条数 ${total}｜已覆盖 ${covered}｜待判定 ${pending.length}｜阈值 LCS>=${THRESHOLD}`);
console.log('--- 逐条 ---');
console.log(rows.join('\n'));

if (pending.length) {
  console.log('--- 待判定（正文可能静默吞帖，需在台账写明「合并到哪条」或「剔除＋原因」）---');
  for (const p of pending) {
    console.log(`  ${p.brand}｜${p.time}｜LCS=${p.score}｜${p.snippet.replace(/\s+/g, ' ')}`);
  }
}
console.log('--- 结论 ---');
console.log(pending.length === 0
  ? '全部 raw 条目在正文有对应文本，无静默吞帖'
  : `${pending.length} 条未在正文找到对应文本：逐条给出归属（合并/剔除+原因），否则视为吞帖`);
process.exit(0);
