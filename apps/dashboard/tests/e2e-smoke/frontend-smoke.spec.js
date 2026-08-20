const { test, expect } = require('@playwright/test');

test('frontend smoke test - page loads without errors', async ({ page }) => {
  const consoleErrors = [];
  const consoleWarnings = [];
  
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    } else if (msg.type() === 'warning') {
      consoleWarnings.push(msg.text());
    }
  });
  
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  
  await page.waitForTimeout(3000);
  
  const pageTitle = await page.title();
  expect(pageTitle).toBe('灵文 · 网文写作伴侣');
  
  const bodyHtml = await page.evaluate(() => document.body.innerHTML);
  const divCount = (bodyHtml.match(/<div[^>]*>/g) || []).length;
  
  if (divCount < 10) {
    throw new Error(`页面div数量过少 (${divCount})，可能为空白页或渲染失败`);
  }
  
  const dashboardElement = await page.$('.dashboard');
  if (!dashboardElement) {
    throw new Error('未找到dashboard元素，页面结构异常');
  }
  
  const sidebarElement = await page.$('.sidebar');
  if (!sidebarElement) {
    throw new Error('未找到sidebar元素，页面结构异常');
  }
  
  if (consoleErrors.length > 0) {
    console.error('\n=== 页面控制台错误 ===');
    consoleErrors.forEach((err, i) => {
      console.error(`${i + 1}. ${err}`);
    });
    throw new Error(`检测到 ${consoleErrors.length} 个控制台错误`);
  }
  
  if (consoleWarnings.length > 0) {
    console.warn('\n=== 页面控制台警告 ===');
    consoleWarnings.forEach((warn, i) => {
      console.warn(`${i + 1}. ${warn}`);
    });
  }
  
  console.log('\n=== Smoke Test 结果 ===');
  console.log(`页面标题: ${pageTitle}`);
  console.log(`页面div数量: ${divCount}`);
  console.log(`控制台错误: ${consoleErrors.length} 个`);
  console.log(`控制台警告: ${consoleWarnings.length} 个`);
  console.log('页面渲染正常！');
});
