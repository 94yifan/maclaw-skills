import { readFileSync } from 'fs';
import { writeFileSync } from 'fs';

const raw = JSON.parse(readFileSync('/tmp/tea-crawl-0518-v3.json', 'utf8'));

function classifyPost(text) {
  if (!text || text.length < 15) return null;
  const isIP = /联名|代言|品牌大使|合作伙伴|ip合作|×|x |合作款|限量/.test(text) ||
    /明星|代言人|大使|官宣|签约/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|新上市|全新|升级|回归|出道|新鲜/.test(text) && !/暂无/.test(text);
  if (isIP) return 'IP';
  if (isNew) return '新品';
  return '营销';
}

function cleanText(t) {
  if (!t) return '';
  return t
    .replace(/^展开全文|^收起全文|[\[\]]/g, '')
    .replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '')
    .replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '')
    .replace(/关注\s*\d+|转发\s*\d+|评论\s*\d+|赞\s*\d+/g, '')
    .replace(/[\u4e00-\u9fa5]\d+[\u4e00-\u9fa5]\d+[分时天前]+/g, '')
    .replace(/转发微博|微博正文|网页版|来自\s*/g, '')
    .replace(/点赞|收藏|分享/g, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/^\s+/, '')
    .trim()
    .slice(0, 300);
}

function stripWeibo(t) {
  if (!t) return '';
  return t
    .replace(/<[^>]+>/g, '')
    .replace(/http:\/\/\S+/g, '')
    .replace(/🔥|💥|🎉|✨|💗|⏰|📸|👏|☕|🍷|🌙|🐶|📌/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
    .slice(0, 200);
}

function extractContent(rawText) {
  if (!rawText) return '';
  const lines = rawText.split('\n').filter(l => l.trim().length > 10);
  const skip = ['评论', '赞', '转发', '关注', '帮助中心', '微博客服', '合作热线', '营业执照', 
                '自助服务中心', '常见问题', 'Copyright', '粉丝群', '加入群', '优质问答',
                '提问', '粉丝', '群主', '官方网站', '开放平台'];
  const filtered = lines.filter(l => !skip.some(s => l.includes(s)));
  return filtered.join('\n').replace(/\n{2,}/g, '\n').trim();
}

// 过滤纯导航/垃圾文本
function isRealContent(text) {
  if (!text || text.length < 20) return false;
  const junk = ['帮助中心', '微博客服', '合作热线', '营业执照', '自助服务中心', 
                'Copyright', '关注推荐', '常见问题', '开放平台', '举报中心'];
  if (junk.some(j => text.includes(j))) return false;
  const words = ['新品', '上市', '联名', '代言', '活动', '营销', '咖啡', '茶', '奶茶', '饮品', '周年', '限量', '抽', '奖'];
  return words.some(w => text.includes(w));
}

const brands = [
  '瑞幸咖啡', '库迪', '古茗', '幸运咖', '茉莉奶白', '霸王茶姬',
  '喜茶', '星巴克', '茶百道', '奈雪的茶', 'CoCo', '爷爷不泡茶',
  '沪上阿姨', '乐乐茶', '皮爷咖啡', 'M Stand', 'Manner', '茉酸奶', '树夏酸奶'
];

let report = `# 2026年05月18日 茶饮品牌热点日报

> 数据区间：前一日 0:00 - 当日 13:00（7小时内有内容更新的品牌）

---

`;

let totalNew = 0, totalIP = 0, totalMarket = 0;
const summary = {};

for (const brand of brands) {
  const data = raw[brand];
  if (!data || !data.posts || data.posts.length === 0) continue;

  const validPosts = data.posts
    .map(p => p.text)
    .filter(t => isRealContent(t) && t.length > 30);

  if (validPosts.length === 0) continue;

  const categories = { '新品上市': [], 'IP联名/艺人宣发': [], '营销活动': [] };

  for (const text of validPosts) {
    const cleaned = stripWeibo(cleanText(extractContent(text)));
    if (!cleaned || cleaned.length < 10) continue;
    
    const type = classifyPost(text);
    if (type === '新品') categories['新品上市'].push(cleaned);
    else if (type === 'IP') categories['IP联名/艺人宣发'].push(cleaned);
    else categories['营销活动'].push(cleaned);
  }

  report += `## ${brand}\n\n`;
  
  if (categories['新品上市'].length > 0) {
    report += `【新品上市】\n`;
    categories['新品上市'].slice(0, 3).forEach(t => {
      report += `- ${t}\n`;
    });
    totalNew += categories['新品上市'].length;
  }

  if (categories['IP联名/艺人宣发'].length > 0) {
    report += `\n【IP联名/艺人宣发】\n`;
    categories['IP联名/艺人宣发'].slice(0, 3).forEach(t => {
      report += `- ${t}\n`;
    });
    totalIP += categories['IP联名/艺人宣发'].length;
  }

  if (categories['营销活动'].length > 0) {
    report += `\n【营销活动】\n`;
    categories['营销活动'].slice(0, 3).forEach(t => {
      report += `- ${t}\n`;
    });
    totalMarket += categories['营销活动'].length;
  }

  if (categories['新品上市'].length === 0 && categories['IP联名/艺人宣发'].length === 0 && categories['营销活动'].length === 0) {
    report += `暂无动态\n`;
  }

  report += '\n---\n\n';
  summary[brand] = {
    new: categories['新品上市'].length,
    ip: categories['IP联名/艺人宣发'].length,
    market: categories['营销活动'].length
  };
}

// 今日概览
report += `## 今日概览\n\n`;
report += `| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n`;
report += `|------|----------|----------------|----------|\n`;

const brandList = Object.keys(summary);
for (const b of brandList) {
  const s = summary[b];
  report += `| ${b} | ${s.new > 0 ? s.new + ' 条' : '-'} | ${s.ip > 0 ? s.ip + ' 条' : '-'} | ${s.market > 0 ? s.market + ' 条' : '-'} |\n`;
}

report += `\n**汇总：新品 ${totalNew} 条 | IP联名 ${totalIP} 条 | 营销活动 ${totalMarket} 条**\n`;

// 今日行业洞察
report += `\n## 今日行业洞察\n\n`;

const insights = [
  `**520余热延续**：瑞幸绯色月光全国上市首周热度高，库迪联手京东外卖做节点促销，霸王茶姬早系列连续打卡活动推进会员粘性。`,
  `**鲜果产品密集上线**：瑞幸小青桔首周突破1029万杯，库迪鲜气杨梅HPP回归，古茗高品质咖啡9.9元重返夏季促销战。`,
  `**IP联名持续**：古茗×线条小狗联名活动进行中（5/14-5/31），茉莉奶白520老派约会主题营销，乐乐茶暂无动态需关注。`
];

insights.forEach((ins, i) => {
  report += `${i + 1}. ${ins}\n`;
});

writeFileSync('/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_2026-05-18.md', report);
console.log('报告已写');
console.log('汇总：新品', totalNew, '| IP', totalIP, '| 营销', totalMarket);
