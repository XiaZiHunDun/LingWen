# Phase 71 — Vite Bundle Audit 设计

> **日期**: 2026-08-21
> **范围**: `apps/dashboard/vite.config.js` build config 优化 — 4 处配置改进
> **基础**: Phase 60-70 完整闭环（11 phases 推送完成）
> **版本**: master（Phase 70 收官后）

---

## 1. 背景

Phase 68-70 已 closed 全部 minor follow-up. 剩余 substantive work 是 Performance 优化.

实测（2026-08-21）`apps/dashboard/vite.config.js` 当前状态:
- 已有 `manualChunks` function for 10 大型库 (echarts, mermaid, cytoscape, katex, naive-ui, vue-router, pinia, @vicons, lodash, dayjs)
- `minify: 'esbuild'`, `chunkSizeWarningLimit: 1000`, `assetsInlineLimit: 4096`
- **缺**: `target` (默认 esnext), `reportCompressedSize` (默认 false), `cssCodeSplit` (Vite 5+ 默认 true)
- `manualChunks` 有冗余 `excluded` array 重复 1 次包列表

Phase 71 focus: 4 处 build config 优化, 1 原子 commit, 最低风险.

## 2. 目标 & 非目标

### 目标
1. 增加 `target: 'es2020'` 显式 baseline
2. 增加 `reportCompressedSize: true` 启用 gzip/brotli size 报告
3. 增加 `cssCodeSplit: true` 显式声明
4. `manualChunks` cleanup — 用 NAMED lookup 替代 bare if-chain + 重复 excluded array
5. 1 原子 commit
6. `pnpm test` 1549 PASS

### 非目标
- 不改 manualChunks 的 10 包列表 (现有)
- 不改 server config
- 不改 proxy 配置
- 不动代码本身 (only build config)
- 不动 test files

## 3. 4 处修改 (apps/dashboard/vite.config.js)

### 3.1 `target: 'es2020'`

**Current**: 无 `target` 字段 (默认 `esnext`).

**After**: 增加 `target: 'es2020'` 到 `build` 对象.

```js
build: {
  target: 'es2020',
  // ... existing
}
```

**Rationale**: 显式 ES2020 baseline 让 build 知道转译目标. 现代浏览器覆盖范围已足够 (Chrome 90+, Firefox 88+, Safari 14+).

### 3.2 `reportCompressedSize: true`

**Current**: 无 `reportCompressedSize` 字段 (默认 false).

**After**: 增加 `reportCompressedSize: true`.

```js
build: {
  // ...
  reportCompressedSize: true,
}
```

**Rationale**: build output 同时显示 uncompressed + gzip/brotli compressed sizes. 利于后续 perf audit.

### 3.3 `cssCodeSplit: true`

**Current**: 无 `cssCodeSplit` 字段 (Vite 5+ 默认 true).

**After**: 增加 `cssCodeSplit: true` 显式声明.

```js
build: {
  // ...
  cssCodeSplit: true,
}
```

**Rationale**: Vite 5+ 默认 true, 但显式声明 best practice, 防止 Vite 升级或 config 漂移意外改变行为.

### 3.4 `manualChunks` cleanup

**Current** (lines 13-32):
```js
manualChunks(id) {
  // 将大型图表库拆分为独立 chunks
  if (id.includes('node_modules/echarts')) {
    return 'echarts';
  }
  if (id.includes('node_modules/mermaid')) {
    return 'mermaid';
  }
  if (id.includes('node_modules/cytoscape')) {
    return 'cytoscape';
  }
  if (id.includes('node_modules/katex')) {
    return 'katex';
  }
  if (id.includes('node_modules/naive-ui')) {
    return 'naive-ui';
  }
  if (id.includes('node_modules/vue-router')) {
    return 'vue-router';
  }
  if (id.includes('node_modules/pinia')) {
    return 'pinia';
  }
  if (id.includes('node_modules/@vicons')) {
    return 'vicons';
  }
  if (id.includes('node_modules/lodash')) {
    return 'lodash';
  }
  if (id.includes('node_modules/dayjs')) {
    return 'dayjs';
  }
  // 将其他第三方依赖合并到 vendor chunk
  // 排除可能导致循环依赖的包
  const excluded = ['mermaid', 'echarts', 'cytoscape', 'katex', 'naive-ui', 'vue-router', 'pinia', '@vicons', 'lodash', 'dayjs'];
  if (id.includes('node_modules/') && !excluded.some(e => id.includes(`node_modules/${e}`))) {
    return 'vendor';
  }
}
```

**After**:
```js
manualChunks(id) {
  // Named chunks: package → chunk name
  const NAMED = {
    echarts: 'echarts',
    mermaid: 'mermaid',
    cytoscape: 'cytoscape',
    katex: 'katex',
    'naive-ui': 'naive-ui',
    'vue-router': 'vue-router',
    pinia: 'pinia',
    '@vicons': 'vicons',
    lodash: 'lodash',
    dayjs: 'dayjs',
  };
  for (const [pkg, chunk] of Object.entries(NAMED)) {
    if (id.includes(`node_modules/${pkg}`)) return chunk;
  }
  // 剩余 node_modules 合并到 vendor chunk
  if (id.includes('node_modules/')) return 'vendor';
}
```

**Rationale**: 
- 用 NAMED lookup 替代 10 lines if-chain
- 消除重复 `excluded` array (single source of truth)
- 行为 identical: 10 named chunks + vendor catch-all

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify current state
grep -nE "target|reportCompressedSize|cssCodeSplit|manualChunks" apps/dashboard/vite.config.js | head -10

# 2. Implementer makes 4 edits to vite.config.js:
#    - Add target: 'es2020' to build
#    - Add reportCompressedSize: true
#    - Add cssCodeSplit: true
#    - Refactor manualChunks to use NAMED lookup

# 3. Verify
grep -c "target.*es2020" apps/dashboard/vite.config.js
echo "---should be 1---"
grep -c "reportCompressedSize" apps/dashboard/vite.config.js
echo "---should be 1---"
grep -c "cssCodeSplit" apps/dashboard/vite.config.js
echo "---should be 1---"
grep -c "NAMED" apps/dashboard/vite.config.js
echo "---should be 1---"

# 4. 1 atomic commit
git add apps/dashboard/vite.config.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "build(vite): target es2020 + reportCompressedSize + cssCodeSplit + manualChunks cleanup" \
    -m "4 处 build config 优化: target 'es2020' (modern baseline); reportCompressedSize (gzip size 报告); cssCodeSplit (explicit); manualChunks 改用 NAMED lookup (消除重复 excluded array)."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 1 (vite.config.js)
- **Lines**: +20 / -20 (估算)
- **Method**: 4 surgical edits

## 5. 测试策略

### 5.1 无 test 改动

Build config 改动, 不动 test logic.

### 5.2 验证

- grep 4 config keys 全部 1 hit
- `pnpm test` 1549 PASS
- `pnpm run build` (optional) 0 errors

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -c 'target.*es2020' apps/dashboard/vite.config.js` | 1 |
| `grep -c 'reportCompressedSize' apps/dashboard/vite.config.js` | 1 |
| `grep -c 'cssCodeSplit' apps/dashboard/vite.config.js` | 1 |
| `grep -c 'NAMED' apps/dashboard/vite.config.js` | 1 |
| `pnpm test` | 1549 tests PASS |
| `git show --stat HEAD` | 1 file changed |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `target: 'es2020'` 排除旧浏览器 | 中 | 旧浏览器不再 supported | 现代浏览器覆盖范围已足够 |
| `cssCodeSplit` 改变 chunk 路径 | 极低 | 生产 hash 变 | OK，新 build 后即可 |
| `manualChunks` 改写破坏 vendor | 极低 | 缺 chunk | 比对 before/after chunk sizes |

## 8. 后续 Phase 72+ 候选

- Lazy-loaded route 组件 (e.g., StudioPage 971L → 异步 import)
- Memoize 优化 (`markRaw` / `shallowRef` / `v-memo`)
- 真实 profiling (e.g., Lighthouse / WebPageTest)
