import { chromium } from 'playwright-core';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let page;
try { const ctx = browser.contexts()[0]; page = await ctx.newPage(); } catch(e) { page = await browser.newPage(); }

await page.goto('https://weibo.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(3000);

// Go to starbucks profile
await page.goto('https://weibo.com/starbucks', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(8000);

const actualUrl = page.url();
console.log('Actual URL:', actualUrl);

const uidFromUrl = actualUrl.match(/\/u\/(\d+)/);
console.log('UID from URL:', uidFromUrl ? uidFromUrl[1] : null);

const title = await page.title();
console.log('Page title:', title);

// Try to find the profile info in the DOM
const profileData = await page.evaluate(() => {
  // Check if there's a profile info component
  const scripts = document.querySelectorAll('script');
  for (const s of scripts) {
    const t = s.textContent || '';
    const idx = t.indexOf('starbucks');
    if (idx >= 0 && t.includes('uid')) {
      const chunk = t.substring(Math.max(0, idx - 200), idx + 200);
      const uidMatch = chunk.match(/"uid":\s*"(\d+)"/);
      return uidMatch ? uidMatch[1] : chunk.substring(0, 300);
    }
  }
  return null;
});
console.log('Profile data:', profileData);

// Try different API endpoint
const apiResult = await page.evaluate(async () => {
  const resp = await fetch('https://weibo.com/ajax/profile/info?customDomain=starbucks');
  if (resp.ok) return await resp.json();
  return { error: resp.status };
});
console.log('API result by domain:', JSON.stringify(apiResult).substring(0, 300));

await browser.close();
