import { readFileSync, writeFileSync } from 'fs';

const raw = JSON.parse(readFileSync('/tmp/tea-crawl-0518-v3.json', 'utf8'));

function classifyPost(text) {
  const isIP = /联名|代言|品牌大使|合作伙伴|×|x |合作款|限量/.test(text) ||
    /明星|代言人|大使|官宣|签约/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|新上市|全新|升级|回归|出道|新鲜/.test(text) && !/暂无/.test(text);
  if (isIP) return 'IP';
  if (isNew) return '新品';
  return '营销';
}

function cleanEntry(t) {
  if (!t) return '';
  return t
    .replace(/[#@:：]/g, ' ')
    .replace(/🔥|💥|🎉|✨|💗|⏰|📸|👏|☕|🍷|🌙|🐶|📌|🍎|🧊|🌴|🍃|🍀|🎁|✔|✅|➡|💫|🎊|🧋|🥤|🧃|☀️|🌈/g, '')
    .replace(/\d{2,}\s*\d{3,}\s*\d+/g, '')   // removes "1621 731 743" type engagement numbers
    .replace(/\d+[\u4e00-\u9fa5]\d+[\u4e00-\u9fa5]/g, '') // removes "5万 3.1万" type metrics
    .replace(/\d+\s*[分时天个月年]+前/g, '')
    .replace(/\d{1,2}-\d{1,2}\s*\d{1,2}:\d{2}/g, '')
    .replace(/转发\s*\d+|评论\s*\d+|赞\s*\d+|关注\s*\d+/g, '')
    .replace(/微博|网页版|微博视频|来自\s*[\w]+|已编辑/g, '')
    .replace(/超话\d+|群主.*|加入群.*|关注推荐.*|微博客服.*|合作热线.*|Copyright.*|营业执照/g, '')
    .replace(/展开\s*全文/g, '')
    .replace(/[\u4e00-\u9fa5]\d+万/g, (m) => m.slice(0,-1))  // "4.4万" -> remove number
    .replace(/\s{2,}/g, ' ')
    .trim()
    .slice(0, 150);
}

const brands = [
  '瑞幸咖啡', '库迪', '古茗', '幸运咖', '茉莉奶白', '霸王茶姬',
  '喜茶', '星巴克', '茶百道', '奈雪的茶', 'CoCo', '爷爷不泡茶',
  '沪上阿姨', '乐乐茶', '皮爷咖啡', 'M Stand', 'Manner', '茉酸奶', '树夏酸奶'
];

const valid = brands.filter(b => raw[b] && raw[b].posts && raw[b].posts.length > 0);

let lines = [];
lines.push('# 2026年05月18日 茶饮品牌热点日报\n');
lines.push('> 数据区间：前一日 0:00 - 当日 13:00\n');
lines.push('---\n');

let totalNew = 0, totalIP = 0, totalMkt = 0;

for (const brand of brands) {
  const posts = raw[brand]?.posts || [];
  if (posts.length === 0) {
    lines.push(`## ${brand}\n\n暂无动态\n\n---\n`);
    continue;
  }

  const cats = { '新品上市': [], 'IP联名/艺人宣发': [], '营销活动': [] };
  
  for (const p of posts) {
    const t = p.text || '';
    // Skip obvious navigation/junk
    if (/帮助中心|微博客服|合作热线|Copyright|营业执照|自助服务中心/.test(t)) continue;
    if (t.length < 25) continue;
    
    const cleaned = cleanEntry(t);
    if (cleaned.length < 10) continue;
    
    const type = classifyPost(t);
    if (type === '新品') cats['新品上市'].push(cleaned);
    else if (type === 'IP') cats['IP联名/艺人宣发'].push(cleaned);
    else cats['营销活动'].push(cleaned);
  }

  lines.push(`## ${brand}\n`);
  
  const hasContent = cats['新品上市'].length + cats['IP联名/艺人宣发'].length + cats['营销活动'].length > 0;

  if (cats['新品上市'].length > 0) {
    lines.push('\n【新品上市】');
    cats['新品上市'].slice(0,2).forEach(t => lines.push(`\n- ${t}`));
    totalNew += cats['新品上市'].length;
  }
  if (cats['IP联名/艺人宣发'].length > 0) {
    lines.push('\n\n【IP联名/艺人宣发】');
    cats['IP联名/艺人宣发'].slice(0,2).forEach(t => lines.push(`\n- ${t}`));
    totalIP += cats['IP联名/艺人宣发'].length;
  }
  if (cats['营销活动'].length > 0) {
    lines.push('\n\n【营销活动】');
    cats['营销活动'].slice(0,2).forEach(t => lines.push(`\n- ${t}`));
    totalMkt += cats['营销活动'].length;
  }
  if (!hasContent) {
    lines.push('\n暂无动态');
  }

  lines.push('\n\n---\n');
}

// Summary table
lines.push('\n## 今日概览\n\n');
lines.push('| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n');
lines.push('|------|----------|----------------|----------|\n');
for (const b of brands) {
  const posts = raw[b]?.posts || [];
  const has = posts.length > 0;
  if (!has) { lines.push(`| ${b} | - | - | - |\n`); continue; }
  const typeCount = (type) => posts.filter(p => classifyPost(p.text) === type).length;
  const n = typeCount('新品'), ip = typeCount('IP'), m = typeCount('营销');
  lines.push(`| ${b} | ${n > 0 ? n+' 条' : '-'} | ${ip > 0 ? ip+' 条' : '-'} | ${m > 0 ? m+' 条' : '-'} |\n`);
}
lines.push(`\n**汇总：新品 ${totalNew} 条 | IP联名 ${totalIP} 条 | 营销活动 ${totalMkt} 条**\n`);

// Insights
lines.push('\n## 今日行业洞察\n\n');
lines.push('1. **520节点余热**：瑞幸绯色月光全国登场（首周爆款），库迪×京东外卖联手请客，霸王茶姬早系列连续活动推进会员打卡习惯。\n');
lines.push('2. **夏季鲜果竞争白热化**：瑞幸小青桔首周1029万杯，库迪鲜气杨梅HPP回归，CoCo生椰水系列沁爽回归，果茶品类进入全面火拼。\n');
lines.push('3. **IP联名纵深推进**：古茗×线条小狗联名活动进行中（至5/31），茉酸奶520神秘联动5/22预告，沪上阿姨田曦薇5/20代言人活动上线在即。\n');

writeFileSync('/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-05-18.md', lines.join(''));
console.log('done');
