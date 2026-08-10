import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  console.log('Browser connected');
  console.log('Browser type:', browser.constructor.name);
  console.log('Browser channels:', Object.keys(browser));
  
  // Get pages from the first context
  const ctx = browser.contexts()[0];
  const pages = ctx.pages();
  console.log('Pages in context:', pages.length);
  
  // Try to navigate a new page in this context
  const newPage = await ctx.newPage();
  console.log('Created new page');
  
  await newPage.goto('https://weibo.com/u/6349791448', {waitUntil: 'domcontentloaded', timeout: 20000});
  console.log('Navigated');
  
  await newPage.waitForTimeout(3000);
  
  const text = await newPage.evaluate(() => {
    return document.body.innerText.slice(0, 2000);
  });
  console.log('Body text length:', text.length);
  console.log('Preview:', text.slice(0, 300));
  
  await ctx.close();
  console.log('Done');
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(0);
});
