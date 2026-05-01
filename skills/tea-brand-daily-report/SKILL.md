---
name: social-content-crawler
description: 通过已登录的Chrome浏览器爬取指定社交媒体账号的公开内容，写入飞书文档。适用场景：(1) 品牌日报自动生成 (2) 竞品监控 (3) 任意品类/品牌的社交媒体内容聚合。触发条件：用户要求爬取品牌内容并生成报告，或每天定时触发。
---

# 社交媒体内容爬取 → 飞书文档写入

## 核心能力
- 使用 playwright 连接用户已登录的 Chrome 浏览器（CDP 端口 9333）
- 按账号 UID 列表逐个爬取内容
- 去除平台特有痕迹词
- 结构化写入飞书文档

## Chrome 连接
- 端口: 9333
- 测试: `node /tmp/pw-test.mjs`
- 连接: `chromium.connectOverCDP('http://127.0.0.1:9333')`

## 品牌列表（19个）
| 序号 | 品牌 | UID/username |
|------|------|-------------|
| 1 | 瑞幸咖啡 | 6349791448 |
| 2 | 库迪 | 7791266545 |
| 3 | 古茗 | 2809775704 |
| 4 | 幸运咖 | 6519396553 |
| 5 | 茉莉奶白 | 7577524421 |
| 6 | 霸王茶姬 | 5652018762 |
| 7 | 喜茶 | 2804387887 |
| 8 | 星巴克 | starbucks（username） |
| 9 | 茶百道 | 6502206666 |
| 10 | 奈雪的茶 | 5884674413 |
| 11 | CoCo | 2030619861 |
| 12 | 爷爷不泡茶 | 7769072120 |
| 13 | 沪上阿姨 | 3921865344 |
| 14 | 乐乐茶 | 6253473981 |
| 15 | 皮爷咖啡 | 6360528436 |
| 16 | M Stand | 6345199298 |
| 17 | Manner | 6808111794 |
| 18 | 茉酸奶 | 5188894132 |
| 19 | 树夏酸奶 | 7144806571 |

## 内容爬取
```javascript
const url = brand.id === 'starbucks'
  ? 'https://weibo.com/starbucks'
  : `https://weibo.com/u/${brand.id}`;

await page.goto(url, { timeout: 20000, waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);

// 滚动加载
for (let s = 0; s < 4; s++) {
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(600);
}

// 文章选择器
const articles = await page.evaluate(() => {
  const arts = document.querySelectorAll('article');
  return Array.from(arts)
    .map(a => a.innerText.trim())
    .filter(t => t.length > 30)
    .slice(0, 10);
});
```

## 去痕迹规则
禁止出现：转发、关注、点赞、评论、抽X位、揪X位、互动送、来自微博网页版、来自超话、来自iPhone、Live
改写示例：转发抽奖送 → 参与互动有机会获得；关注+转发 → 参与互动

## 与前一日内容去重比对
每条内容与前一天同品牌内容进行比对：
- **完全相同或高度雷同**：整条保留但标注"🔄 重复推老内容：[内容简述]"
- **同一活动/产品连续多日重复推广**：标注"🔄 第X天重复推广：[内容简述]"
- **确实为新发布**：按正常格式录入
- **24小时内无新增发布**：注明"无新增发布"

## 报告格式规范
- 每个品牌分【新品上市】【IP联名/艺人宣发】【营销活动】三块，每块内容分条列出
- 同一品牌有多个新品/IP联名/营销活动时各自单独成行，不合并
- 无新增发布的品牌注明"无新增发布"

## 飞书写入规则（固定，不可改）
- 文档Token: `PEJadXoKiorPI2xNFgvcqdOFnHL`
- **写入顺序**：找到文档中最底部的日期块（H1），将其作为参照点，把当日日报整块内容（从H1日期标题到汇总表）append 到该日期块下方空白处
- **永远不修改已有内容**，只在末尾追加
- **格式**（固定）：H1日期标题 → 分割线 → 各品牌H2（新品/IP联名/营销活动三段）→ 汇总表
- **写入前必须先发群里确认**，用户说"写吧"后才执行 `feishu_doc(action="append", ...)`
- 禁止用 `insert`，禁止用 `write`（会叠加旧内容）

## 日报 cron
- 每日 10:05 北京时间触发
- 超时 900s
- 第零步：群里发"🙌 开始跑今天的茶饮日报了，稍后出报告"
- 脚本：`/tmp/tea-brand-crawler-v3.mjs`