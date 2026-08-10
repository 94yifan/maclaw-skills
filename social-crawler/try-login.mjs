import { chromium } from 'playwright-core';
const context = await chromium.launchPersistentContext('/tmp/weibo-login2', {
  headless: false,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox']
});
const p = await context.newPage();

// Go to weibo.com
await p.goto('https://weibo.com/', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 5000));

// Click login button
await p.click('text=登录/注册');
console.log('Clicked login button');
await new Promise(r => setTimeout(r, 5000));

const text = await p.evaluate(() => document.body.innerText.substring(0, 1500));
console.log('After login click:', text);

// Find all inputs
const inputs = await p.evaluate(() => {
  return Array.from(document.querySelectorAll('input')).map(el => ({
    type: el.type, placeholder: el.placeholder, id: el.id, name: el.name
  }));
});
console.log('INPUTS:', JSON.stringify(inputs, null, 2));

// Find all buttons
const buttons = await p.evaluate(() => {
  return Array.from(document.querySelectorAll('button, a')).map(el => ({
    text: (el.innerText || '').substring(0, 20), type: el.type
  })).filter(b => b.text);
});
console.log('BUTTONS:', JSON.stringify(buttons, null, 2));

await p.screenshot({ path: '/tmp/weibo-login-dialog.png' });
console.log('Screenshot saved');

await context.close();
