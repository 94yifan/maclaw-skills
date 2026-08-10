import { chromium } from 'playwright-core';
import { writeFileSync } from 'fs';

const profileDir = '/Users/yifansmacmini/Library/Application Support/Google/Chrome';
const context = await chromium.launchPersistentContext(profileDir, {
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});
const page = await context.newPage();

// Check weibo login status
await page.goto('https://weibo.com/u/6349791448', { waitUntil: 'domcontentloaded', timeout: 20000 });
await page.waitForTimeout(6000);
console.log('URL:', page.url());
const text = await page.evaluate(() => document.body.innerText.substring(0, 500));
console.log('PAGE TEXT:', text);

// Check cookies
const cookies = await context.cookies();
const weiboCookies = cookies.filter(c => c.domain.includes('weibo'));
console.log('Weibo cookies:', weiboCookies.length);
for (const c of weiboCookies.slice(0, 5)) {
  console.log(`  ${c.name}=${c.value.substring(0, 30)}...`);
}

await context.close();
