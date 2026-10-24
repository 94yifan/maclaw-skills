/**
 * 日报切片器（2026-10-24 新增）
 * 用法：node chunk-report.mjs memory/weibo_daily_<日期>.md [maxChars]
 * 输出：JSON 数组，每个元素是一条待发消息，可直接用 message 工具原样发送。
 *
 * 为什么要有这个脚本：
 * 10-23、10-24 连续两天「存档 ≠ 交付」——手抄分片时顺手删了 header 里的跨天比对句、
 * 「窗口内转发第三」等定语，交付版比存档少 153 字。规则写在 SKILL 里没人执行，
 * 就把动作换成脚本：切片由文件机械生成，发送时不许再改一个字。
 */
import { readFileSync } from 'fs';

const file = process.argv[2];
const maxChars = Number(process.argv[3] || 2000);
if (!file) {
  console.error('用法: node chunk-report.mjs <报告文件> [maxChars]');
  process.exit(1);
}
const lines = readFileSync(file, 'utf8').split('\n');

// 以「**品牌名**」独占一行为块边界，header 与行业信号各自成块
const blocks = [];
let cur = [];
for (const line of lines) {
  const isBrand = /^\*\*[^*]+\*\*\s*$/.test(line);
  if (isBrand && cur.length) {
    blocks.push(cur.join('\n').trim());
    cur = [];
  }
  cur.push(line);
}
if (cur.length) blocks.push(cur.join('\n').trim());

const chunks = [];
for (const b of blocks) {
  if (!b) continue;
  const last = chunks[chunks.length - 1];
  if (last && (last.length + 2 + b.length) <= maxChars) {
    chunks[chunks.length - 1] = last + '\n\n' + b;
  } else {
    chunks.push(b);
  }
}

process.stdout.write(JSON.stringify(chunks, null, 2) + '\n');
