import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
  
  // Check browser contexts
  console.log('Contexts:', browser.contexts().length);
  
  // Check what page we're on  
  const contexts = browser.contexts();
  for (const ctx of contexts) {
    console.log('Context:', ctx.pages().length, 'pages');
    for (const page of ctx.pages()) {
      console.log('  Page URL:', page.url());
    }
  }
  
  // Try to navigate to weibo and see what's there
  const page = await contexts[0].newPage();
  await page.goto('https://weibo.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(3000);
  
  const url = page.url();
  console.log('Current URL:', url);
  
  // Check cookies for weibo
  const cookies = await page.context().cookies(['https://weibo.com']);
  console.log('Weibo cookies:', cookies.length);
  for (const c of cookies) {
    console.log('  ', c.name, '=', c.value.slice(0,20), 'domain:', c.domain);
  }
  
  await browser.disconnect();
}

main().catch(console.error);
