import playwright from 'playwright';

async function searchAndGetUID(browserWS, brandName) {
  const browser = await playwright.chromium.connectOverCDP(browserWS);
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    await page.goto(`https://s.weibo.com/user?q=${encodeURIComponent(brandName)}&type=user`, { 
      waitUntil: 'domcontentloaded',
      timeout: 15000 
    });
    
    await page.waitForTimeout(3000);
    
    // Scroll to load results
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(2000);
    
    const result = await page.evaluate(() => {
      // Find user cards with verified accounts (蓝V)
      const cards = document.querySelectorAll('.member .member_info, .user_atten, .W_btn_b');
      const results = [];
      
      // Try finding user list items
      document.querySelectorAll('div[class*="user"], div[class*="card"], div[class*="member"]').forEach(card => {
        const nameEl = card.querySelector('a[class*="name"], a[class*="nickname"], .nickname, [class*="user_name"]');
        const uidMatch = card.innerHTML.match(/uid=(\d+)/) || card.innerHTML.match(/\/(\d+)$/);
        const isVerified = card.innerText.includes('认证') || card.innerHTML.includes('icon-vip-blue');
        
        if (nameEl && uidMatch) {
          results.push({
            name: nameEl.innerText,
            uid: uidMatch[1],
            verified: isVerified
          });
        }
      });
      
      // Get page text as fallback
      if (results.length === 0) {
        const text = document.body.innerText;
        return { text: text.substring(0, 1000), found: false };
      }
      
      return { results, found: true };
    });
    
    await browser.close();
    return { brandName, ...result, error: null };
  } catch (e) {
    await browser.close();
    return { brandName, error: e.message, found: false };
  }
}

async function main() {
  const brands = ['瑞幸咖啡', '库迪咖啡', '古茗茶饮', '茉莉奶白', '霸王茶姬', '喜茶', '乐乐茶', 'T9tea', '奈雪的茶', '一只酸奶牛', '益禾堂', 'CoCo都可', '书亦烧仙草', '悸动烧仙草', '沪上阿姨', '茶百道', '七分甜'];
  const browserWS = 'http://localhost:9333';
  
  const results = [];
  for (const brand of brands) {
    console.log(`Searching ${brand}...`);
    const result = await searchAndGetUID(browserWS, brand);
    results.push(result);
    
    if (result.found) {
      console.log(`  Found: ${JSON.stringify(result.results)}`);
    } else {
      console.log(`  Text: ${(result.text || result.error || 'No content').substring(0, 200)}`);
    }
    
    await new Promise(r => setTimeout(r, 2000));
  }
  
  console.log('\n=== ALL RESULTS ===');
  console.log(JSON.stringify(results, null, 2));
}

main().catch(console.error);