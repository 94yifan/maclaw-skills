import { chromium } from 'playwright-core';

const browser = await chromium.connectOverCDP('http://localhost:9333');
const pages = await browser.pages();

console.log('Total pages:', pages.length);
for (const p of pages) {
  console.log(`  URL: ${p.url().slice(0,100)}`);
}

await browser.close();
