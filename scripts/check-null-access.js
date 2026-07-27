#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const SRC_DIR = '/home/ailearn/projects/LingWen/dashboard/frontend/src';

const patterns = [
  {
    regex: /wb\.agent(\.(generating|chat|ask))/g,
    message: 'wb.agent 可能为 null，应使用 wb.agent?.xxx',
    severity: 'high',
  },
  {
    regex: /wb\.startQuickWrite\(/g,
    message: 'wb.startQuickWrite 可能为 null，应使用 wb.startQuickWrite?.()',
    severity: 'high',
  },
  {
    regex: /w\.wb\.draft/g,
    message: 'w.wb.draft 不存在，应使用 w.chapterBodyDraft?.value',
    severity: 'high',
  },
  {
    regex: /\.value\s*=/g,
    message: '检测到可能的可选链赋值语法，这是实验性语法',
    severity: 'medium',
  },
  {
    regex: /wb\.creationMode(\.value)?/g,
    message: 'wb.creationMode 是 computed，模板中直接使用，脚本中需要 .value',
    severity: 'medium',
  },
];

function findVueFiles(dir) {
  const files = [];
  function traverse(currentDir) {
    const entries = fs.readdirSync(currentDir);
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory()) {
        traverse(fullPath);
      } else if (entry.endsWith('.vue') || entry.endsWith('.js')) {
        files.push(fullPath);
      }
    }
  }
  traverse(dir);
  return files;
}

function checkFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const errors = [];
  
  for (const pattern of patterns) {
    let match;
    const regex = new RegExp(pattern.regex);
    while ((match = regex.exec(content)) !== null) {
      const line = content.substring(0, match.index).split('\n').length;
      errors.push({
        file: filePath,
        line,
        match: match[0],
        message: pattern.message,
        severity: pattern.severity,
      });
    }
  }
  
  return errors;
}

function main() {
  console.log('========================================');
  console.log('  Null Access Detection Check');
  console.log('========================================\n');
  
  const files = findVueFiles(SRC_DIR);
  const allErrors = [];
  
  for (const file of files) {
    const errors = checkFile(file);
    allErrors.push(...errors);
  }
  
  if (allErrors.length === 0) {
    console.log('✓ 未发现潜在的 null 访问问题');
    process.exit(0);
  }
  
  console.log(`✗ 发现 ${allErrors.length} 个潜在问题:\n`);
  
  const sortedErrors = allErrors.sort((a, b) => {
    const severityOrder = { high: 0, medium: 1, low: 2 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });
  
  for (const error of sortedErrors) {
    const severityColor = error.severity === 'high' ? '\x1b[31m' : '\x1b[33m';
    const resetColor = '\x1b[0m';
    console.log(`${severityColor}[${error.severity.toUpperCase()}]${resetColor} ${error.file}:${error.line}`);
    console.log(`  匹配: ${error.match}`);
    console.log(`  问题: ${error.message}\n`);
  }
  
  process.exit(1);
}

main();
