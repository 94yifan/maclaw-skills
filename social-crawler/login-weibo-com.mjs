import { chromium } from 'playwright-core';

const context = await chromium.launchPersistentContext('/tmp/weibo-direct-login', {
  headless: false,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox']
});
const p = await context.newPage();

// Set viewport to desktop size
await p.setViewportSize({ width: 1280, height: 800 });

// Go to weibo.com login page
await p.goto('https://weibo.com/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 5000));

console.log('URL:', p.url());
const body = await p.evaluate(() => document.body.innerText.substring(0, 2000));
console.log('PAGE:', body);

// Find all input fields
const info = await p.evaluate(() => {
  const inputs = Array.from(document.querySelectorAll('input')).map(el => ({
    type: el.type,
    id: el.id,
    name: el.name,
    placeholder: el.placeholder,
    className: (el.className || '').substring(0, 40)
  }));
  const buttons = Array.from(document.querySelectorAll('button, a.WB_btn_login, a[node-type="loginbtn"]')).map(el => ({
    tag: el.tagName,
    text: (el.innerText || '').substring(0, 20),
    id: el.id,
    className: (el.className || '').substring(0, 40),
    nodeType: el.getAttribute('node-type') || ''
  }));
  return { inputs, buttons };
});
console.log('INPUTS:', JSON.stringify(info.inputs, null, 2));
console.log('BUTTONS:', JSON.stringify(info.buttons, null, 2));

// Try filling login form
const usernameInput = await p.$('#loginname, input[name="username"], input[type="text"]');
if (usernameInput) {
  await usernameInput.fill('15364917418');
  console.log('Filled username');
}

const passwordInput = await p.$('input[type="password"]');
if (passwordInput) {
  await passwordInput.fill('940904');
  console.log('Filled password');
}

// Try clicking login
const loginButton = await p.$('#login_btn, a.WB_btn_login, button[node-type="submit"], .login_btn');
if (loginButton) {
  await loginButton.click();
  console.log('Clicked login');
} else {
  console.log('No login button found, trying form submit');
  await p.evaluate(() => {
    const form = document.querySelector('form');
    if (form) form.submit();
  });
}

// Wait for login
await new Promise(r => setTimeout(r, 10000));
console.log('After login URL:', p.url());

// Try brand page
await p.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 15000 });
await new Promise(r => setTimeout(r, 6000));
const result = await p.evaluate(() => document.body.innerText);
const ok = !result.includes('前方有点拥堵') && result.includes('粉丝');
console.log('LOGGED_IN:', ok, 'LEN:', result.length);
if (!ok) {
  await p.screenshot({ path: '/tmp/weibo-login-result.png' });
  console.log('Screenshot saved');
  console.log('TEXT:', result.substring(0, 500));
} else {
  console.log('LOGIN SUCCESS!');
  await p.screenshot({ path: '/tmp/weibo-success.png' });
}

await context.close();
