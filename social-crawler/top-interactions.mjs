#!/usr/bin/env node
/**
 * top-interactions.mjs — 互动排行核验器
 *
 * 用途：日报里任何「互动最高 / 转发最高 / 评论最高」的断言，必须由本脚本输出背书。
 * 报告写作前跑一次，把 topN 表贴进上下文，排名句只能引用该表里的数字与口径。
 *
 * 用法：
 *   node top-interactions.mjs /tmp/tea-raw-2026-10-23.json [topN]
 *
 * 输出：三个口径各 topN —— 总互动(r+c+l)、转发(r)、评论(c)，并标出每条是否疑似抽奖帖。
 * 抽奖识别：文本含「转发+关注」「抽」「揪」「揪N位」「免单券」「@微博抽奖平台」。
 */
import fs from 'node:fs';

const file = process.argv[2];
const N = Number(process.argv[3] || 5);
if (!file) {
  console.error('usage: node top-interactions.mjs <raw.json> [topN]');
  process.exit(2);
}

const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
const brands = Array.isArray(raw) ? raw : raw.brands || [];

const rows = [];
for (const b of brands) {
  for (const it of b.items || []) {
    const r = it.r || 0, c = it.c || 0, l = it.l || 0;
    const t = (it.t || '').replace(/\s+/g, ' ');
    const lottery = /转发\+关注|关注\+转发|抽\d*位|抽奖|揪\d*位|揪\d+|免单券|微博抽奖平台/.test(t);
    rows.push({ brand: b.brand, id: it.id, d: it.d, r, c, l, total: r + c + l, lottery, t: t.slice(0, 34) });
  }
}

if (!rows.length) {
  console.error('no items found — check raw file shape (expect brands[].items[] with r/c/l)');
  process.exit(1);
}

const pad = (s, n) => String(s).padEnd(n);
function table(title, key) {
  const sorted = [...rows].sort((a, b) => b[key] - a[key]).slice(0, N);
  console.log(`\n## ${title}`);
  console.log(pad('rank', 5) + pad('brand', 12) + pad('count', 8) + pad('抽奖?', 7) + 'time / text');
  sorted.forEach((x, i) => {
    console.log(
      pad(i + 1, 5) +
        pad(x.brand, 12) +
        pad(x[key], 8) +
        pad(x.lottery ? 'Y' : 'n', 7) +
        `${x.d} | ${x.t}`
    );
  });
}

console.log(`# ${file} | items ${rows.length} | brands ${brands.length}`);
table('总互动 top (r+c+l) — 「互动最高」只能引这张表', 'total');
table('转发 top (r) — 「转发最高」只能引这张表', 'r');
table('评论 top (c) — 「评论最高」只能引这张表', 'c');

const lotteryRows = rows.filter((x) => x.lottery);
console.log(`\n## 抽奖疑似 ${lotteryRows.length}/${rows.length} 条（写「非抽奖类最高」前先确认目标帖不在其中）`);
