import { chromium } from 'playwright-core';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
let page;
try { const ctx = browser.contexts()[0]; page = await ctx.newPage(); } catch(e) { page = await browser.newPage(); }

// Track all API requests
const apiCalls = [];
page.on('response', async resp => {
  const url = resp.url();
  if (url.includes('/ajax/profile/') || url.includes('/ajax/statuses/mymblog')) {
    try {
      const json = await resp.json();
      apiCalls.push({
        url: url.substring(0, 150),
        ok: resp.ok(),
        status: resp.status(),
        hasData: !!json.data
      });
    } catch(e) {
      apiCalls.push({ url: url.substring(0, 150), ok: resp.ok(), status: resp.status(), parseError: true });
    }
  }
});

await page.goto('https://weibo.com/starbucks', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(10000);

console.log('API calls made:');
apiCalls.forEach(c => console.log(JSON.stringify(c)));

// Check all URL params
console.log('\nCurrent URL:', page.url());

// Try to get the profile info from the rendered page
const domData = await page.evaluate(() => {
  // Look for user/profile data in the DOM
  const profileCard = document.querySelector('[class*="profile"]');
  const info = {};
  
  // Check all data attributes on the page
  const allEls = document.querySelectorAll('[data-uid]');
  if (allEls.length > 0) {
    info.uidElements = Array.from(allEls).slice(0, 5).map(el => el.getAttribute('data-uid'));
  }
  
  // Check for hidden inputs or data
  const bodyHtml = document.body.innerHTML;
  const uidMatch = bodyHtml.match(/userid["\s:=]+(\d+)/i);
  if (uidMatch) info.uidFromHTML = uidMatch[1];
  
  return info;
});
console.log('DOM data:', JSON.stringify(domData));

await browser.close();
