# tea-brand-daily-report

每天自动拉取 19 个茶饮品牌微博动态，生成结构化日报，写入 memory 存档。

## 做什么

输入：无（定时触发或手动调用）
输出：`memory/weibo_daily_YYYY-MM-DD.md`，结构如下：
- 19 个品牌分三块：新品上市 / IP联名/艺人宣发 / 营销活动
- 末尾：今日概览汇总表 + 今日行业洞察（3条）

## 关键 SOP

### 核心脚本
```
node skills/tea-brand-daily-report/crawl.mjs [YYYY-MM-DD]
```
不传参数默认今天。

### 爬取逻辑（重要）

**用移动版微博 `m.weibo.cn`，不用 PC 版 `weibo.com`。**

PC 版 DOM 结构多次变化，CSS selector 全部失效。移动版 text content + DOM 结合更稳定。

**关键：DOM 解析代替 text content 分割。**

```javascript
// 正确：用 DOM 结构获取真实时间戳
const posts = await page.evaluate(() => {
  const cards = document.querySelectorAll('.card');
  const results = [];
  for (const card of cards) {
    const timeEl = card.querySelector('span.time');     // 真实时间戳在 DOM 里
    const textEl = card.querySelector('.weibo-text');  // 真实内容在 DOM 里
    if (!timeEl || !textEl) continue;
    const timeStr = timeEl.innerText.trim(); // e.g. "5-11 10:01"
    const text = textEl.innerText.trim().slice(0, 350);
    results.push({ date: timeStr.split(' ')[0], time: timeStr.split(' ')[1], text });
  }
  return results;
});
```

**错误做法（已废弃）：**
- 用 `body.innerText.split(/日期正则/)` 分割 → 时间戳错位，胡先煦那条会被挂到5-10而非5-11
- 用 `pl_feedlist_index` 等 PC 版 selector → 早已失效

### 品牌列表（固定 19 个）

```javascript
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
```

### 时间过滤

日报数据窗口：前一天 0:00 至当天当前时间。

```javascript
function isTargetDay(dateStr) {
  const day = parseInt(dateStr.split('-')[1]);
  const today = new Date().getDate();
  return day === today || day === today - 1;
}
```

### 内容过滤

```javascript
function isValid(text) {
  if (!text || text.length < 15) return false;
  if (/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) return false;
  if (/加入群|粉丝群\s*\d/.test(text)) return false;
  return true;
}
```

### 分类逻辑

```javascript
function classify(text) {
  const isIP = /联名|代言|×/.test(text) && !/暂无/.test(text);
  const isNew = /新品|上市|首发|新系列|新口味|全新|升级回归/.test(text) && !/暂无/.test(text);
  return isIP ? 'IP' : isNew ? '新品' : '营销';
}
```

### 报告格式

末尾必须有：
1. 今日概览汇总表
2. 今日行业洞察（3条，基于当日数据提炼）

## 环境依赖

- playwright-core（已在 workspace node_modules）
- CDP 端口 9333（yifan 的 Chrome remote debugging）
- 等待时间：每品牌间隔 5 秒，模拟人类操作

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 时间戳全错 | 用 text content 分割日期 | 改用 DOM span.time |
| 抓到关注列表 | 没有过滤噪音 | isValid() 函数 |
| 胡先煦那条丢了 | 5-11 10:01 在 DOM 里但被错误匹配 | span.time 是 5-11 10:01，内容在 .weibo-text |
| 星巴克/Manner 全空 | 品牌 uid 变更或内容少 | 正常，这些品牌发得少 |

## 调用方式

```bash
# 手动触发今天
node skills/tea-brand-daily-report/crawl.mjs

# 触发指定日期
node skills/tea-brand-daily-report/crawl.mjs 2026-05-11
```

## 飞书发群

webhook 逻辑待接通（需逸凡提供 webhook URL）。


### 报告格式规范（必读）

**三条铁规：**
1. **不要微博原文** - 不能直接复制粘贴微博文案，要提炼核心信息重新表达，只保留活动核心信息（时间/规则/产品/奖品）
2. **不需要出现时间** - 不显示"[1小时前]""[5-12 10:55]""[昨天]"等任何时间标记
3. **去微博化** - 删除所有微博语境词汇：#话题#、@用户名、关注+转发、抽X位、全文…等

**内容提炼原则：**
- 标题用品牌自己的话说，不照抄微博原话
- 提炼活动规则要点（怎么参与、奖什么），不抄抽奖话术
- 不保留任何微博特征符号（#、@、🔥、💥等 emoji 尽量少用）
- 每条营销活动不超过80字，聚焦"是什么+为什么值得知道"

**错误示例：**
❌ [2小时前] 救命🆘库迪小黄油美式 💥爆款喝法藏不住了！🧊全冰去水=风味焊死！关注迪迪并转发此条微博，抽5位粉丝送出【全场任饮券】1张！

✅ 库迪小黄油美式/拿铁/椰椰三兄弟全员就位，全冰去水"风味焊死"爆款喝法小红书已发酵，关注+转发抽5位送全场任饮券

**正确示例：**
✅ 古茗椰椰冰淇淋拿铁明日上市 | 泰国丹嫩沙多香椰+生椰乳+IIAC金奖豆，明日起全国门店上新
