import { chromium } from 'playwright-core';

const context = await chromium.launchPersistentContext('/tmp/weibo-modal-login', {
  headless: false,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox']
});
const p = await context.newPage();
await p.setViewportSize({ width: 1280, height: 800 });

// Go to weibo.com
await p.goto('https://weibo.com/', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 5000));

// Click the login/register button
await p.click('text=登录/注册');
console.log('Clicked login button');
await new Promise(r => setTimeout(r, 5000));

// Check what's on the page now
const text = await p.evaluate(() => document.body.innerText);

// See if a modal opened
const modals = await p.evaluate(() => {
  return Array.from(document.querySelectorAll('[class*="modal"], [class*="dialog"], [class*="popup"], [class*="layer"], [class*="overlay"]')).length;
});
console.log('Modals found:', modals);

// Check for login-specific content
if (text.includes('手机') || text.includes('密码') || text.includes('验证码')) {
  console.log('Login form visible!');
} else {
  console.log('No login form found');
}

// Get all input fields
const inputs = await p.evaluate(() => {
  return Array.from(document.querySelectorAll('input')).map(el => ({
    type: el.type, placeholder: el.placeholder, id: el.id, name: el.name
  }));
});
console.log('Inputs:', JSON.stringify(inputs, null, 2));

// Get all elements with text
const loginTexts = await p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('*'));
  return els.filter(el => {
    const t = (el.innerText || '').trim();
    return (t.includes('登录') || t.includes('手机') || t.includes('密码')) && el.children.length === 0;
  }).slice(0, 10).map(el => ({
    tag: el.tagName,
    text: (el.innerText || '').substring(0, 30)
  }));
});
console.log('Login texts:', JSON.stringify(loginTexts, null, 2));

await p.screenshot({ path: '/tmp/weibo-modal.png' });
console.log('Screenshot at /tmp/weibo-modal.png');

await context.close();
