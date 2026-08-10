import { chromium } from 'playwright';
import { execSync } from 'child_process';
import fs from 'fs';

async function main() {
  // First check what CDP ports are available
  try {
    execSync('lsof -i :9333 -i :9222 -i :9500 2>/dev/null | grep LISTEN', {encoding:'utf8'});
  } catch(e) {}
  
  // Try to launch Chrome with user data dir
  const userDataDir = process.env.HOME + '/Library/Application Support/Google/Chrome';
  
  // Check if profile has cookies
  const cookieDB = userDataDir + '/Default/Cookies';
  const exists = fs.existsSync(cookieDB);
  console.log('Cookies DB exists:', exists);
  console.log('User data dir:', userDataDir);
  
  // Try to launch new browser with existing profile
  let browser;
  try {
    browser = await chromium.launch({
      headless: false,
      userDataDir: userDataDir,
      args: ['--remote-debugging-port=9334']
    });
    console.log('Launched Chrome with profile');
    
    const page = await browser.newPage();
    await page.goto('https://weibo.com/u/6349791448', {waitUntil: 'networkidle', timeout: 30000});
    
    const text = await page.evaluate(() => document.body.innerText.slice(0, 2000));
    console.log('Weibo content:', text.slice(0, 500));
    
    await browser.close();
  } catch(err) {
    console.log('Launch error:', err.message);
  }
}

main().catch(console.error);
