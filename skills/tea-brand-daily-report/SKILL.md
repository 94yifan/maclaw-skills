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

## 写入规则
- 文档Token: `PEJadXoKiorPI2xNFgvcqdOFnHL`
- 使用 `feishu_doc(action="write", doc_token="...", content="...")`
- **新增内容时：将当日从日期标题到汇总表的整块内容作为 H1 block，插入到文档标题（"茶饮品牌热点日报"）下方的第一个位置，旧内容一个字都不修改**
- **顺序固定不可改，除非用户明确要求调整**
- 文档结构由调用方指定
