import { chromium } from 'playwright-core';

const CDP_URL = 'http://localhost:9333';
const brand = { name: 'Manner', uid: '6808111794' };

async function crawl() {
  const browser = await chromium.connectOverCDP(CDP_URL);
  const page = await browser.newPage();
  
  await page.goto(`https://weibo.com/u/${brand.uid}`, { timeout: 30000 });
  await page.waitForTimeout(3000);
  
  const articles = await page.$$('div.article, div.node-bg, div.content');
  let data = [];
  
  for (let i = 0; i < Math.min(articles.length, 20); i++) {
    const el = articles[i];
    const html = await el.innerHTML();
    const text = await el.innerText();
    
    if (text && text.length > 15 && !/抱歉.*不存在|该昵称|暂无.*内容/.test(text)) {
      const dateMatch = html.match(/(\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2})/);
      const date = dateMatch ? dateMatch[1] : '';
      data.push({ text: text.substring(0, 200), date });
    }
  }
  
  console.log(JSON.stringify({ brand: brand.name, data }, null, 2));
  await browser.close();
}

crawl().catch(console.error);
