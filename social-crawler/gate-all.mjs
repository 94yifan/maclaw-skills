#!/usr/bin/env node
// gate-all.mjs — 发报前一次性跑两个门禁，并把输出留痕到 /tmp/tea-gate-<日期>.txt
// 背景（2026-10-30）：ledger-check 与 report-structure-check 都已存在，但 cron prompt 里没有这一步，
// 10-29 的 D4 挂了 1 天没落地；两个门禁当天还各自「误判通过」一次。把调用压成一条命令，
// 主 session 只需在 prompt 里加一行，不必记住两个参数串。
// 用法：node gate-all.mjs [--date 2026-10-30]
// 判据：两个门禁的「缺归属 0／非法合并 0」与「待修 0 项」同时成立才算过；退出码恒为 0（SKILL 规则 21）。
import { execFileSync } from 'node:child_process';
import { writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const di = args.indexOf('--date');
const date = di >= 0 && args[di + 1]
  ? args[di + 1]
  : new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10);

const raw = `/tmp/tea-raw-${date}.json`;
const ledger = `/tmp/tea-ledger-${date}.md`;
const report = path.join(here, 'memory', `weibo_daily_${date}.md`);

const run = (script, argv) => {
  try {
    return execFileSync('node', [path.join(here, script), ...argv], { encoding: 'utf8' });
  } catch (e) {
    return `GATE_FAIL ${script} 执行异常：${e.message}`;
  }
};

// 覆盖数按「本次 raw 实际抓了几个品牌」校验，不按当前品牌表校验：
// 今日 11:00 抓 23 家、19:10 才加第 24 家，按 24 判会把已交付的合格日报判错（假阳性）。
// 抓取端是否漏品牌属于另一层：raw 品牌数与 canonical 数组不等时只提示，不阻断。
let rawBrandCount = 0;
let canonicalCount = 0;
try {
  const d = JSON.parse(readFileSync(raw, 'utf8'));
  rawBrandCount = (d.brands || []).length;
} catch { /* 缺 raw 由 ledger-check 报 READ_FAIL */ }
try {
  const c = readFileSync(path.join(here, 'tea-daily-crawl.mjs'), 'utf8');
  canonicalCount = (c.match(/\{ name: '/g) || []).length;
} catch { /* ignore */ }

const out1 = run('ledger-check.mjs', ['--raw', raw, '--ledger', ledger]);
const out2 = run('report-structure-check.mjs', ['--report', report, '--ledger', ledger, ...(rawBrandCount ? ['--brands', String(rawBrandCount)] : [])]);

const body = [
  `# 发报前门禁 ${date}`,
  `对象：raw=${raw}｜ledger=${ledger}｜report=${report}`,
  `覆盖：raw 品牌 ${rawBrandCount} 家｜canonical 品牌表 ${canonicalCount} 家${rawBrandCount && canonicalCount && rawBrandCount !== canonicalCount ? '（不一致：先确认是当日新增品牌还是抓取漏品牌）' : ''}`,
  '',
  '## 1. 台账归属门禁',
  out1.trim(),
  '',
  '## 2. 结构门禁',
  out2.trim(),
].join('\n');

const ok1 = /缺台账行 0.*缺归属 0.*非法合并 0/s.test(out1) && /逐条闭合/.test(out1);
const ok2 = /待修 0 项/.test(out2);
const verdict = ok1 && ok2 ? 'PASS 两项门禁全过，可发' : `BLOCK 未过：台账${ok1 ? '过' : '未过'}｜结构${ok2 ? '过' : '未过'}（先修再发，禁止带病交付）`;

writeFileSync(`/tmp/tea-gate-${date}.txt`, `${body}\n\n## 结论\n${verdict}\n`, 'utf8');
console.log(body);
console.log('\n## 结论');
console.log(verdict);
console.log(`留痕：/tmp/tea-gate-${date}.txt`);
process.exit(0);
