import { chromium } from 'playwright';

async function main() {
  // Try with existing Chrome profile
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333', {
    headers: {
      'Accept-Language': 'zh-CN,zh'
    }
  });
  
  // Get existing targets
  const targets = await browser.targets();
  console.log('Available targets:', targets.map(t => t.url()).filter(Boolean));
  
  // Try to create a new page with existing context
  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();
  
  // Navigate to a brand page
  await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);
  
  const content = await page.content();
  console.log('Page length:', content.length);
  
  // Check if logged in
  const isLoggedIn = content.includes('登录') && !content.includes('前方有点拥堵');
  console.log('Logged in:', isLoggedIn);
  
  // Get text content
  const text = await page.evaluate(() => document.body.innerText.slice(0, 2000));
  console.log('Content preview:', text.slice(0, 500));
}

main().catch(console.error);
