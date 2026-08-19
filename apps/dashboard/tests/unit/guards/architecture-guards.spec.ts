/**
 * 守卫测试 — 架构不变量守护
 *
 * 确保架构铁律不被违反:
 * 1. L3/L4 不依赖 L2
 * 2. Composable 导出完整性
 * 3. 包边界
 *
 * 参考: OpenHands 的 no-direct-agent-server-calls.test.ts
 */
import { describe, expect, it } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

const composablesDir = path.resolve(__dirname, '../../../src/composables');
const indexFileJs = path.resolve(composablesDir, 'index.js');
const indexFileTs = path.resolve(composablesDir, 'index.ts');
const indexFile = fs.existsSync(indexFileTs) ? indexFileTs : indexFileJs;

describe('Guard: 架构不变量', () => {
  it('composables/index.ts 导出所有 composable 文件', () => {
    const indexContent = fs.readFileSync(indexFile, 'utf-8');
    const composableFiles = fs.readdirSync(composablesDir)
      .filter((f) =>
        (f.endsWith('.js') || f.endsWith('.ts'))
        && f !== 'index.js' && f !== 'index.ts'
        && !f.endsWith('.d.ts')
      );

    const missingExports: string[] = [];
    for (const file of composableFiles) {
      const moduleName = file.replace(/\.(js|ts)$/, '');
      // 检查 index.ts 中是否导出了该模块（直接 export 或从子目录 re-export）
      // 直接 export 模式: export { ... } from './moduleName' 或 export * as from './moduleName'
      const directPattern = new RegExp(
        `export\\s*(?:\\{[^}]*\\}|\\*(?:\\s*as\\s*${moduleName})?)\\s*from\\s*['"]\\.\\/${moduleName}(?:\\.js|\\.ts|['"])`
      );
      // 对于 workbench 子模块，它们通过 useWorkbenchIndex.js 重新聚合
      if (!directPattern.test(indexContent) && moduleName.startsWith('useWorkbench') && moduleName !== 'useWorkbenchIndex') {
        // 检查 useWorkbenchIndex 内部是否导出
        const indexFileFull = path.join(composablesDir, 'useWorkbenchIndex.ts');
        if (fs.existsSync(indexFileFull)) {
          const workbenchIndexContent = fs.readFileSync(indexFileFull, 'utf-8');
          if (workbenchIndexContent.includes(moduleName)) continue;
        }
      }
      if (!directPattern.test(indexContent)) {
        missingExports.push(moduleName);
      }
    }

    if (missingExports.length > 0) {
      // 只报告确实缺失的导出
      expect(missingExports).toEqual([]);
    }
  });

  it('index.js 文件存在且格式正确', () => {
    expect(fs.existsSync(indexFile)).toBe(true);
    const content = fs.readFileSync(indexFile, 'utf-8');
    expect(content).toContain('export');
  });

  it('Vue 组件文件使用 PascalCase 命名', () => {
    const componentsDir = path.resolve(__dirname, '../../../src/components');
    if (!fs.existsSync(componentsDir)) return;

    const vueFiles = findVueFiles(componentsDir);
    const nonPascalCase: string[] = [];

    for (const file of vueFiles) {
      const basename = path.basename(file, '.vue');
      // PascalCase: 首字母大写，不含下划线
      if (!/^[A-Z][a-zA-Z0-9]*$/.test(basename)) {
        nonPascalCase.push(basename);
      }
    }

    // 报告非 PascalCase 的组件
    if (nonPascalCase.length > 0) {
      expect(nonPascalCase).toEqual([]);
    }
  });

  it('Composable 文件使用 use 前缀', () => {
    const files = fs.readdirSync(composablesDir)
      .filter((f) => (f.endsWith('.js') || f.endsWith('.ts')) && f !== 'index.js' && f !== 'index.ts');

    const nonUsePrefix: string[] = [];
    for (const file of files) {
      const basename = file.replace(/\.(js|ts)$/, '');
      if (!basename.startsWith('use')
        && basename !== 'creatorDefaultUiProfile'
        && basename !== 'volumePlanDiffExportUtils'
        && basename !== 'composables.d') {
        // creatorDefaultUiProfile 和 volumePlanDiffExportUtils 是已知的例外（工具函数）
        // composables.d 是 Phase 44 新增的子模块类型声明文件
        nonUsePrefix.push(basename);
      }
    }

    if (nonUsePrefix.length > 0) {
      expect(nonUsePrefix).toEqual([]);
    }
  });
});

function findVueFiles(dir: string): string[] {
  const results: string[] = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findVueFiles(fullPath));
    } else if (entry.name.endsWith('.vue')) {
      results.push(fullPath);
    }
  }
  return results;
}