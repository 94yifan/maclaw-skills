import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const profileDir = '/Users/yifansmacmini/Library/Application Support/Google/Chrome';
console.log('Launching browser with real profile...');
const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  args: ['--no-sandbox', '--start-minimized']
});
const page = await context.newPage();

// Test 1: Check if we're logged in on weibo.com
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 25000 });
await page.waitForTimeout(8000);

console.log('URL:', page.url());
const bodyText = await page.evaluate(() => document.body.innerText);
console.log('--- BODY TEXT (first 3000 chars) ---');
console.log(bodyText.substring(0, 3000));
console.log('--- BODY TEXT LENGTH:', bodyText.length, '---');

// Save raw HTML for analysis
const html = await page.evaluate(() => document.documentElement.outerHTML);
writeFileSync('/tmp/weibo-diagnostic.html', html);
console.log('HTML saved to /tmp/weibo-diagnostic.html');

// Test 2: Try all selectors
const selectors = ['.WB_cardwrap', '.WB_feed', '.card', '.weibo-list .item', '[class*="feed"]', '.wbpro-feed', '.WB_feed_record'];
for (const sel of selectors) {
  const count = await page.evaluate((s) => document.querySelectorAll(s).length, sel);
  console.log(`Selector "${sel}": ${count} elements`);
}

await context.close();
