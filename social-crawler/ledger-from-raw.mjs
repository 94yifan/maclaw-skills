/**
 * 从已抓好的 raw 生成「窗口逐条台账」，用于写日报前的逐条交代与事后审计。
 * 用法：node ledger-from-raw.mjs /tmp/tea-raw-2026-10-22.json [输出路径]
 * 2026-10-22 建立：10-22 日报守恒式「凑数通过」但静默吞掉爷爷不泡茶 2 条帖，
 * 根因是写作阶段靠总数倒推而非逐条点名。台账把「38 条」变成 38 行可打勾的清单。
 */
import { readFileSync, writeFileSync } from 'fs';

const src = process.argv[2];
if (!src) {
  console.error('用法: node ledger-from-raw.mjs <raw.json> [out.md]');
  process.exit(1);
}
const out = process.argv[3] || src.replace(/tea-raw-/, 'tea-ledger-').replace(/\.json$/, '.md');
const d = JSON.parse(readFileSync(src, 'utf8'));

const lines = [
  `# 窗口逐条台账 ${d.date}`,
  `> 窗口 ${d.windowStart || '?'} – ${d.windowEnd || '?'}｜crawlTime ${d.crawlTime || '?'}｜来源 ${src}`,
  ''
];
let n = 0;
for (const b of d.brands || []) {
  const items = b.items || [];
  lines.push(`## ${b.brand}（${items.length} 条）`);
  if (items.length === 0) lines.push(`- 无：latest=${b.latest || 'n/a'} total=${b.total ?? 'n/a'} ok=${b.ok}`);
  for (const it of items) {
    n++;
    const when = (it.d || it.created_at || '').replace(/ \+0800 \d{4}$/, '');
    lines.push(`- [ ] #${n} \`${it.id}\` ${when}｜${String(it.t || it.text || '').slice(0, 60).replace(/\s+/g, ' ')}`);
  }
  lines.push('');
}
lines.push(`合计 ${n} 条。每条必须落到「正文 bullet」或「合并到某条」或「剔除＋原因」，写完后逐行打勾。`);

writeFileSync(out, lines.join('\n'));
console.log(`台账写入 ${out}，共 ${n} 条`);
