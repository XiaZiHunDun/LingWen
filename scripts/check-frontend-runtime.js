const http = require('http');
const fs = require('fs');

const DEV_SERVER_URL = 'http://localhost:5173';
const ERROR_LOG_FILE = '/tmp/frontend-errors.log';

async function fetchPage(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`请求超时: ${url}`));
    }, timeout);

    http.get(url, (res) => {
      clearTimeout(timer);
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, body: data, headers: res.headers });
      });
    }).on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

async function waitForServer(maxRetries = 10, delay = 1000) {
  for (let i = 1; i <= maxRetries; i++) {
    try {
      const response = await fetchPage(DEV_SERVER_URL, 2000);
      if (response.statusCode === 200) {
        return true;
      }
    } catch (err) {
      console.log(`[*] 等待服务器启动... (第 ${i}/${maxRetries} 次尝试)`);
    }
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  return false;
}

async function runCheck() {
  const errors = [];
  const results = {};
  const warnings = [];

  try {
    console.log('[*] 等待开发服务器启动...');
    if (!await waitForServer()) {
      errors.push({ type: 'server_not_ready', message: '开发服务器未在预期时间内启动' });
      results.serverReady = 'FAIL';
      console.log('[✗] 开发服务器启动失败');
      fs.writeFileSync(ERROR_LOG_FILE, JSON.stringify({ errors, warnings }, null, 2));
      console.log('\n[✗] 验证失败');
      process.exit(1);
    }
    results.serverReady = 'PASS';
    console.log('[✓] 开发服务器已启动');

    console.log('[*] 步骤1: 检查页面响应');
    const pageResponse = await fetchPage(DEV_SERVER_URL);
    
    if (pageResponse.statusCode !== 200) {
      errors.push({ type: 'http_error', message: `页面返回状态码 ${pageResponse.statusCode}` });
      results.httpStatus = 'FAIL';
    } else {
      results.httpStatus = 'PASS';
      console.log('[✓] HTTP状态码: 200');
    }

    console.log('[*] 步骤2: 检查页面基本结构');
    
    if (!pageResponse.body.includes('墨灵') && !pageResponse.body.includes('灵文')) {
      errors.push({ type: 'content_missing', message: '页面标题"墨灵"或"灵文"缺失' });
      results.pageContent = 'FAIL';
    } else {
      results.pageContent = 'PASS';
      console.log('[✓] 页面标题正确');
    }

    if (!pageResponse.body.includes('<div') && !pageResponse.body.includes('data-testid')) {
      errors.push({ type: 'app_container_missing', message: '页面缺少基本HTML结构或测试标识' });
      results.appContainer = 'FAIL';
    } else {
      results.appContainer = 'PASS';
      console.log('[✓] 页面结构正常');
    }

    const scriptCount = (pageResponse.body.match(/<script/g) || []).length;
    if (scriptCount < 1) {
      errors.push({ type: 'scripts_missing', message: `页面script标签过少 (${scriptCount})，可能缺少入口文件` });
      results.scripts = 'FAIL';
    } else {
      results.scripts = 'PASS';
      console.log(`[✓] 页面script标签数量: ${scriptCount}`);
    }

    const bodyLength = pageResponse.body.length;
    if (bodyLength < 300) {
      errors.push({ type: 'content_empty', message: `页面内容过短 (${bodyLength}字节)，可能为空白页` });
      results.contentLength = 'FAIL';
    } else {
      results.contentLength = 'PASS';
      console.log(`[✓] 页面内容长度: ${bodyLength} 字节`);
    }

    console.log('[*] 步骤3: 检查静态资源');
    const mainJsResponse = await fetchPage(`${DEV_SERVER_URL}/src/main.js`);
    if (mainJsResponse.statusCode !== 200 && mainJsResponse.statusCode !== 304) {
      errors.push({ type: 'asset_error', message: `主入口文件访问失败 (HTTP ${mainJsResponse.statusCode})` });
      results.staticAssets = 'FAIL';
    } else {
      results.staticAssets = 'PASS';
      console.log('[✓] 主入口文件可访问');
    }

    console.log('[*] 步骤4: 检查main.js内容');
    if (!mainJsResponse.body.includes('createApp')) {
      errors.push({ type: 'main_js_invalid', message: 'main.js中未找到createApp，可能入口文件被修改' });
      results.mainJsContent = 'FAIL';
    } else {
      results.mainJsContent = 'PASS';
      console.log('[✓] main.js内容正确');
    }

    console.log('[*] 步骤5: 检查CSS资源');
    const styleCssResponse = await fetchPage(`${DEV_SERVER_URL}/src/assets/style.css`);
    if (styleCssResponse.statusCode !== 200 && styleCssResponse.statusCode !== 304) {
      errors.push({ type: 'css_error', message: `样式文件访问失败 (HTTP ${styleCssResponse.statusCode})` });
      results.cssAssets = 'FAIL';
    } else {
      results.cssAssets = 'PASS';
      console.log('[✓] 样式文件可访问');
    }

    console.log('[*] 步骤6: 检查页面是否有明显的错误提示');
    const errorKeywords = [
      'is not defined',
      'ReferenceError',
      'TypeError',
      'SyntaxError',
      'Cannot read properties',
      'Cannot set properties',
      'Uncaught',
      'Error:',
    ];

    let foundErrors = [];
    errorKeywords.forEach(keyword => {
      if (pageResponse.body.includes(keyword)) {
        foundErrors.push(keyword);
      }
    });

    if (foundErrors.length > 0) {
      errors.push({ type: 'runtime_error', message: `页面中包含运行时错误: ${foundErrors.join(', ')}` });
      results.runtimeError = 'FAIL';
    } else {
      results.runtimeError = 'PASS';
      console.log('[✓] 未检测到运行时错误');
    }

    console.log('[*] 步骤7: 检查关键组件是否存在');
    const criticalComponents = ['App.vue', 'AskPage.vue', 'LibraryPage.vue', 'CreatorPage.vue'];
    for (const component of criticalComponents) {
      const componentPath = `${DEV_SERVER_URL}/src/${component.includes('Page') ? 'pages/' : 'components/'}${component}`;
      try {
        const response = await fetchPage(componentPath);
        if (response.statusCode !== 200 && response.statusCode !== 304) {
          warnings.push({ type: 'component_missing', message: `关键组件 ${component} 可能缺失或不可访问` });
        } else {
          console.log(`[✓] 关键组件 ${component} 可访问`);
        }
      } catch (err) {
        warnings.push({ type: 'component_access_error', message: `访问关键组件 ${component} 失败: ${err.message}` });
      }
    }

    console.log('[*] 步骤8: 检查Vite构建状态');
    if (pageResponse.body.includes('[plugin:vite:import-analysis]')) {
      errors.push({ type: 'vite_import_error', message: 'Vite构建存在import分析错误' });
      results.viteBuild = 'FAIL';
    } else {
      results.viteBuild = 'PASS';
      console.log('[✓] Vite构建状态正常');
    }

    console.log('[*] 步骤9: 检查响应头');
    if (!pageResponse.headers['content-type']?.includes('text/html')) {
      warnings.push({ type: 'content_type_warning', message: `响应内容类型异常: ${pageResponse.headers['content-type']}` });
    } else {
      console.log('[✓] 响应内容类型正确');
    }

  } catch (err) {
    errors.push({ type: 'network_error', message: `网络请求失败: ${err.message}` });
    results.network = 'FAIL';
  }

  fs.writeFileSync(ERROR_LOG_FILE, JSON.stringify({ errors, warnings }, null, 2));

  console.log('\n[*] 验证结果汇总:');
  for (const [key, value] of Object.entries(results)) {
    const status = value === 'PASS' ? '✓' : (value === 'WARN' ? '!' : '✗');
    console.log(`  ${status} ${key}: ${value}`);
  }

  if (warnings.length > 0) {
    console.log('\n[*] 警告详情:');
    warnings.forEach((w, i) => {
      console.log(`  [!] ${w.message}`);
    });
  }

  if (errors.length > 0) {
    console.log('\n[*] 错误详情:');
    errors.forEach((e, i) => {
      console.log(`  [✗] ${e.message}`);
    });
  }

  const hasErrors = errors.length > 0;
  
  if (hasErrors) {
    console.log('\n[✗] 验证失败');
    process.exit(1);
  } else if (warnings.length > 0) {
    console.log('\n[!] 验证通过，但存在警告');
    process.exit(0);
  } else {
    console.log('\n[✓] 所有验证通过');
    process.exit(0);
  }
}

runCheck().catch(err => {
  console.error('[✗] 验证脚本执行失败:', err.message);
  fs.writeFileSync(ERROR_LOG_FILE, JSON.stringify([{ type: 'script_error', message: err.message }], null, 2));
  process.exit(1);
});