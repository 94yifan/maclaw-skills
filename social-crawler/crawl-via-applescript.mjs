import { execSync } from 'child_process';
import { writeFileSync } from 'fs';

const brands = [
  { name: '瑞幸咖啡', uid: '6349791448' },
  { name: '库迪', uid: '7791266545' },
  { name: '古茗', uid: '2809775704' },
  { name: '幸运咖', uid: '6519396553' },
  { name: '茉莉奶白', uid: '7577524421' },
  { name: '霸王茶姬', uid: '5652018762' },
  { name: '喜茶', uid: '2804387887' },
  { name: '星巴克', uid: 'starbucks' },
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
];

function shell(script) {
  return execSync(script, { encoding: 'utf-8', timeout: 30000 }).trim();
}

function appleScriptGetPageContent(url) {
  const escapedUrl = url.replace(/"/g, '\\"');
  const result = shell(`osascript -e '
tell application "Google Chrome"
  tell window 1
    set newTab to make new tab with properties {URL:"${escapedUrl}"}
    delay 6
    -- scroll a bit to trigger lazy loading
    tell active tab of window 1
      set loading to true
      repeat while loading
        try
          set loading to (loading of active tab of window 1)
        on error
          set loading to false
        end try
      end repeat
    end tell
  end tell
  delay 2
  -- get the page text
  set pageText to execute active tab of window 1 javascript "document.body.innerText"
  -- close the tab
  set tabIndex to 0
  repeat with t in tabs of window 1
    set tabIndex to tabIndex + 1
    if t = active tab of window 1 then
      close tab tabIndex of window 1
      exit repeat
    end if
  end repeat
  return pageText
end tell
' 2>&1`);
  return result;
}

const today = new Date();
const dateFile = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
const results = {};

for (let i = 0; i < brands.length; i++) {
  const b = brands[i];
  const uid = b.uid === 'starbucks' ? 'starbucks' : b.uid;
  const url = 'https://weibo.com/u/' + uid;
  process.stdout.write('[' + (i+1) + '/19] ' + b.name + '... ');
  
  try {
    const pageText = appleScriptGetPageContent(url);
    
    // Parse posts from page text
    // Look for date patterns like "5-29" or "15分钟前" and extract surrounding content
    const lines = pageText.split('\n').filter(l => l.trim());
    
    // Find posts: look for lines with date patterns and following content
    const posts = [];
    let currentDate = '';
    let currentContent = '';
    
    for (let j = 0; j < lines.length; j++) {
      const line = lines[j].trim();
      // Match date patterns: "5-29", "05-29", "5-29 10:30", "15分钟前", "2小时前"
      const dateMatch = line.match(/^(\d{1,2}[-/]\d{1,2})(?:\s+\d{1,2}:\d{2})?$/);
      const relativeMatch = line.match(/^(\d+)(分钟前|小时前|秒前|天前)$/);
      
      if (dateMatch || relativeMatch) {
        if (currentContent && currentContent.length > 20) {
          posts.push({ date: currentDate, text: currentContent });
        }
        currentDate = dateMatch ? dateMatch[1] : 'today';
        currentContent = '';
      } else if (line.length > 10 && !line.includes('关注') && !line.includes('粉丝') && 
                 !line.includes('评论') && !line.includes('赞') && !line.includes('帮助中心') &&
                 !line.includes('微博客服') && !line.includes('营业执照') && !line.includes('Copyright') &&
                 !line.includes('登录') && !line.includes('注册') && !line.includes('开放平台') &&
                 !line.includes('热搜') && !line.includes('推荐') && !line.includes('超话') &&
                 !line.includes('举报')) {
        if (currentContent) currentContent += ' ' + line;
        else currentContent = line;
      }
    }
    if (currentContent && currentContent.length > 20) {
      posts.push({ date: currentDate, text: currentContent });
    }
    
    // Filter for today/yesterday posts
    const todayMonth = String(today.getMonth() + 1);
    const todayDay = String(today.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    const yMonth = String(yesterday.getMonth() + 1);
    const yDay = String(yesterday.getDate());
    
    const validPosts = posts.filter(p => {
      if (p.date === 'today') return true;
      const parts = p.date.split(/[-/]/);
      if (parts.length === 2) {
        const m = parts[0].replace(/^0/, '');
        const d = parts[1].replace(/^0/, '');
        return (m === todayMonth && d === todayDay) || (m === yMonth && d === yDay);
      }
      return false;
    });
    
    // Categorize
    const cats = { '新品': [], 'IP': [], '营销': [] };
    for (const p of validPosts) {
      const text = p.text;
      if (text.length < 15) continue;
      const cleaned = text.replace(/#[\u4e00-\u9fa5A-Za-z0-9]+#/g, '')
        .replace(/@[\u4e00-\u9fa5A-Za-z0-9]+/g, '')
        .replace(/展开全文|收起全文/g, '').trim();
      
      const isIP = /联名|代言|×|品牌大使/.test(cleaned);
      const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(cleaned);
      if (isIP) cats['IP'].push(cleaned);
      else if (isNew) cats['新品'].push(cleaned);
      else if (cleaned.length > 20) cats['营销'].push(cleaned);
    }
    
    results[b.name] = cats;
    const total = cats['新品'].length + cats['IP'].length + cats['营销'].length;
    console.log(total + '条');
    
  } catch(e) {
    results[b.name] = { '新品': [], 'IP': [], '营销': [] };
    console.log('err: ' + (e.message || '').slice(0, 60));
  }
}

// Generate report
function generateReport(results) {
  const dateDisplay = today.getFullYear() + '年' + String(today.getMonth()+1).padStart(2,'0') + '月' + String(today.getDate()).padStart(2,'0') + '日';
  let out = '# ' + dateDisplay + ' 茶饮品牌热点日报\n\n> 数据区间：前一日 0:00 - 当日当前\n\n---\n\n`;
  
  const totalAll = { '新品': 0, 'IP': 0, '营销': 0 };
  let tableRows = '';
  const allActive = [];
  
  for (const brand of brands) {
    const r = results[brand.name];
    if (!r) continue;
    const total = r['新品'].length + r['IP'].length + r['营销'].length;
    if (total === 0) continue;
    allActive.push(brand);
    
    totalAll['新品'] += r['新品'].length;
    totalAll['IP'] += r['IP'].length;
    totalAll['营销'] += r['营销'].length;
    
    out += '## ' + brand.name + '\n\n';
    out += '【新品上市】\n';
    if (r['新品'].length) r['新品'].forEach(t => out += '- ' + t.slice(0, 300) + '\n');
    else out += '- 暂无新品\n';
    out += '\n【IP联名/艺人宣发】\n';
    if (r['IP'].length) r['IP'].forEach(t => out += '- ' + t.slice(0, 300) + '\n');
    else out += '- 暂无IP联名/艺人宣发\n';
    out += '\n【营销活动】\n';
    if (r['营销'].length) r['营销'].forEach(t => out += '- ' + t.slice(0, 300) + '\n');
    else out += '- 暂无营销活动\n';
    out += '\n---\n\n';
    
    tableRows += '| ' + brand.name + ' | ' + (r['新品'].length || '-') + ' | ' + (r['IP'].length || '-') + ' | ' + (r['营销'].length || '-') + ' |\n';
  }
  
  if (tableRows) {
    out += '## 今日概览\n\n| 品牌 | 新品上市 | IP联名/艺人宣发 | 营销活动 |\n|------|----------|----------------|----------|\n';
    out += tableRows;
    out += '\n**汇总：新品 ' + totalAll['新品'] + ' 条 | IP联名 ' + totalAll['IP'] + ' 条 | 营销活动 ' + totalAll['营销'] + ' 条**\n\n';
    
    const newBrands = allActive.filter(b => results[b.name]['新品'].length > 0);
    const ipBrands = allActive.filter(b => results[b.name]['IP'].length > 0);
    
    out += '## 今日行业洞察\n\n';
    if (newBrands.length) out += '1. **新品动态**：' + newBrands.map(b => b.name).join('、') + ' 等品牌有新品发布，共' + totalAll['新品'] + '款。\n\n';
    if (ipBrands.length) out += '2. **IP联名**：' + ipBrands.map(b => b.name).join('、') + ' 等品牌有IP联名/代言人动态。\n\n';
    out += '3. **市场活跃度**：' + allActive.length + '/' + brands.length + '个品牌今日有更新。\n';
  } else {
    out += '今日暂无品牌更新数据。\n';
  }
  out = out.replace(/\n\n\n+/g, '\n\n');
  return out;
}

const report = generateReport(results);
const outFile = '/Users/yifansmacmini/.openclaw/workspace/social-crawler/memory/weibo_daily_' + dateFile + '.md';
writeFileSync(outFile, report);
console.log('\n=== 报告已写入 ' + outFile + ' ===');
