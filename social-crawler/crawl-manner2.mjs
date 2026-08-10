import { chromium } from 'playwright-core';

const CDP_URL = 'http://localhost:9333';
const brand = { name: 'Manner', uid: '6808111794' };

async function crawl() {
  const browser = await chromium.connectOverCDP(CDP_URL);
  const page = await browser.newPage();
  page.setDefaultTimeout(20000);
  
  await page.goto(`https://weibo.com/u/${brand.uid}`, { timeout: 20000 });
  await page.waitForTimeout(5000);
  
  // Get page text content
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('=== PAGE TEXT (first 2000 chars) ===');
  console.log(bodyText.substring(0, 2000));
  
  await browser.close();
}

crawl().catch(console.error);
