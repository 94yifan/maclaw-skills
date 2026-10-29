#!/usr/bin/env node
// ledger-check.mjs — 台账归属门禁：每条 raw 必须写清「落到正文哪一条 / 合并到哪条 / 剔除原因」
// 背景（2026-10-26）：台账只有 [x] 打勾，打勾只证明「看过」，不证明「落到正文」。
// 今日实证：header 写「共 24 条动态」，正文 21 个 bullet，瑞幸 09:00 帖的「揪10位送饮品券、转发过2000加抽」整段无归属也没人发现。
// 判据：每条 id 的台账行必须含 `→` 且 `→` 后有内容，三种合法归属：
//   → 正文  <可直接辨认的正文片段>
//   → 合并到 #<id>
//   → 剔除：<原因>
// 铁律：退出码恒为 0（SKILL 规则 21），判定只看打印的「缺归属 N 条」。
// 用法：node ledger-check.mjs --raw /tmp/tea-raw-2026-10-26.json --ledger /tmp/tea-ledger-2026-10-26.md
import fs from 'node:fs';

const args = process.argv.slice(2);
const getArg = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};
const today = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10);
const rawPath = getArg('--raw', `/tmp/tea-raw-${today}.json`);
const ledgerPath = getArg('--ledger', `/tmp/tea-ledger-${today}.md`);

let raw, ledger;
try {
  raw = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
  ledger = fs.readFileSync(ledgerPath, 'utf8');
} catch (e) {
  console.log(`READ_FAIL raw=${rawPath} ledger=${ledgerPath} err=${e.message}`);
  console.log('判定：无法核对，需人工确认路径（退出码仍为 0）');
  process.exit(0);
}

const lines = ledger.split('\n');
const lineById = new Map();
for (const ln of lines) {
  const m = ln.match(/`(\d{10,})`/);
  if (m) lineById.set(m[1], ln);
}

// 先按 raw 顺序解析全部台账行，得到 id → {kind, target, brand}
const kindById = new Map();
const targetById = new Map();
const brandById = new Map();
for (const b of (raw.brands || [])) {
  for (const it of (b.items || [])) {
    brandById.set(String(it.id), b.brand);
    const ln = lineById.get(String(it.id));
    if (!ln) continue;
    const arrow = ln.split('→')[1] || '';
    const mTarget = arrow.match(/合并到\s*#?(\d{10,})/);
    if (mTarget) {
      kindById.set(String(it.id), '合并');
      targetById.set(String(it.id), mTarget[1]);
    } else if (/剔除/.test(arrow)) {
      kindById.set(String(it.id), '剔除');
    } else if (arrow.trim()) {
      kindById.set(String(it.id), '正文');
    }
  }
}

let total = 0, missingLine = 0, missingDisposition = 0, badMerge = 0;
const problems = [];
const reasons = { 正文: 0, 合并: 0, 剔除: 0, 无: 0 };

for (const b of (raw.brands || [])) {
  for (const it of (b.items || [])) {
    total++;
    const id = String(it.id);
    const ln = lineById.get(id);
    if (!ln) {
      missingLine++;
      problems.push(`  缺台账行　${b.brand}｜${it.id}｜${(it.t || '').slice(0, 30)}`);
      continue;
    }
    const arrow = ln.split('→')[1];
    if (!arrow || !arrow.trim() || /待归属/.test(arrow)) {
      missingDisposition++;
      problems.push(`  缺归属　　${b.brand}｜${it.id}｜${(it.t || '').slice(0, 30)}`);
      continue;
    }
    if (kindById.get(id) === '合并') {
      reasons.合并++;
      const tgt = targetById.get(id);
      const tgtKind = kindById.get(tgt);
      if (!tgtKind) {
        badMerge++;
        problems.push(`  合并目标不存在　${b.brand}｜${it.id} → ${tgt}`);
      } else if (tgtKind === '合并') {
        badMerge++;
        problems.push(`  合并目标也是合并（互指/链式）　${b.brand}｜${it.id} → ${tgt}（对方也标合并）`);
      } else if (tgtKind === '剔除') {
        badMerge++;
        problems.push(`  合并进了一条被剔除的帖　${b.brand}｜${it.id} → ${tgt}`);
      } else if (brandById.get(tgt) && brandById.get(tgt) !== b.brand) {
        badMerge++;
        problems.push(`  跨品牌合并　${b.brand}｜${it.id} → ${tgt}（属 ${brandById.get(tgt)}）`);
      }
    } else if (kindById.get(id) === '剔除') reasons.剔除++;
    else reasons.正文++;
  }
}

// bullet 数应为「正文」标签数（合并项不得自己长出新 bullet）
const expectedBullets = reasons.正文;

console.log(`# 台账归属核对 ${raw.date || today}`);
console.log(`raw 条数 ${total}｜缺台账行 ${missingLine}｜缺归属 ${missingDisposition}｜非法合并 ${badMerge}`);
console.log(`归属分布：正文 ${reasons.正文}｜合并 ${reasons.合并}｜剔除 ${reasons.剔除}`);
console.log(`应得 bullet 数 ${expectedBullets}（= 正文标签数；实际 bullet 数请用 report-structure-check 对照）`);
if (problems.length) {
  console.log('--- 待补 ---');
  console.log(problems.join('\n'));
}
console.log('--- 结论 ---');
console.log(missingLine + missingDisposition + badMerge === 0
  ? `逐条闭合：${total} 条全部有归属，合并链合法`
  : `${missingLine + missingDisposition + badMerge} 项未闭合：先补归属/修合并目标再发日报（禁止用总数倒推）`);
process.exit(0);
