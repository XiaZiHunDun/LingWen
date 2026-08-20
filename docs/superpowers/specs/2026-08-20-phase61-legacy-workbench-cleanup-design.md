# Phase 61 — Legacy Workbench Placeholder 清理

> **日期**: 2026-08-20
> **范围**: 删除 Phase 19-20 遗留的 5 个 `useWorkbench*.ts` 占位源文件 + 2 个对应测试 + 清理 `composables/index.ts` re-export + 新增防回潮架构守卫
> **基础**: Phase 60 已把 4 个新 submodule 全部落地，`useCreatorWriteWorkbench.js` facade 已切换到新 submodule，legacy 文件 0 调用方
> **版本**: master（Phase 60 收官后）

---

## 1. 背景

Phase 60 把 `useCreatorWriteWorkbench.js` (529L) 拆为 facade (178L) + 4 个新 submodule（`useWorkbenchLayout/Selection/Checkpoints/Quality`），全部位于 `apps/dashboard/src/composables/useCreatorWriteWorkbench/`。

但 `apps/dashboard/src/composables/` 根目录仍残留 Phase 19-20 时期的 5 个 legacy 占位源文件（717L）：

| 文件 | 行数 | 内容 | 状态 |
|------|------|------|------|
| `useWorkbenchCheckpoint.ts` | 107 | 检查点 + diff 视图（singular） | 0 调用 |
| `useWorkbenchValidation.ts` | 333 | 轻量校验 + 冲突标记 | 0 调用 |
| `useWorkbenchAgent.ts` | 161 | Agent 控制 + 生成 | 0 调用 |
| `useWorkbenchSelection.ts` | 102 | 选区 + Intent（legacy colocation） | 0 调用 |
| `useWorkbenchIndex.ts` | 14 | 上面 4 个的 re-export 聚合器 | 0 调用 |

这 5 个文件是「Phase 18 拆分到 Phase 19 接管期间的中间存档」。Phase 60 把功能以新名字（多数为复数 or 位于子目录）迁到 `useCreatorWriteWorkbench/*`，并通过 `useCreatorWorkbenchSelection` alias 规避根目录 `useWorkbenchSelection.ts` 与子目录 `useWorkbenchSelection.ts` 的命名冲突。

最新实测（grep 2026-08-20）：
- 5 个 legacy 源文件 **0 调用方**（除 `useWorkbenchIndex.ts` 互相 re-export 外）
- `useCreatorWorkbenchSelection` alias **0 引用方**（仅 `index.ts:135` 定义）
- `useWorkbenchIndex` **0 引用方**（仅 `index.ts:83` re-export）
- 新 4 个 submodule 已被 facade 全部采用，作为唯一实作

## 2. 目标 & 非目标

### 目标
1. 删除 5 个 legacy 源文件 + 2 个对应测试（总 717L + 测试）
2. 清理 `composables/index.ts` 中的 re-export (line 83) 与 alias 出口 (line 135)
3. 新增架构守卫（6 项断言）防止 legacy 文件再次被 commit 回来
4. 单原子 commit；`vue-tsc` 0 errors；test 1343 → 1341 PASS

### 非目标
- **不**动 `useCreatorWriteWorkbench/*` 4 个新 submodule
- **不**动 `useCreatorWriteWorkbench.js` facade
- **不**修 Phase 60 收尾声明的字段数不一致（51/56/55→59）—— 留给后续 doc cleanup phase
- **不**修 trailing newline 项目-wide 缺陷 —— 留给后续 doc cleanup phase
- **不**新加 re-export shim（YAGNI：0 调用方无需兜底）

## 3. 文件操作清单

### 3.1 删除源文件

```
apps/dashboard/src/composables/useWorkbenchCheckpoint.ts        (107L)
apps/dashboard/src/composables/useWorkbenchValidation.ts        (333L)
apps/dashboard/src/composables/useWorkbenchAgent.ts             (161L)
apps/dashboard/src/composables/useWorkbenchSelection.ts         (102L, legacy)
apps/dashboard/src/composables/useWorkbenchIndex.ts             (14L)
```

### 3.2 删除对应测试

```
apps/dashboard/tests/unit/use-workbench-checkpoint.spec.ts        (Phase 38)
apps/dashboard/tests/unit/use-workbench-selection-intent.spec.ts  (Phase 18.9)
```

### 3.3 编辑 `apps/dashboard/src/composables/index.ts`

| 行号 | 现状 | 改动 |
|------|------|------|
| 17 | `* - 工作台: useCreatorWriteWorkbench, useWorkbenchIndex` | 改为 `* - 工作台: useCreatorWriteWorkbench` |
| 83 | `export { useWorkbenchSelection, useWorkbenchCheckpoint, useWorkbenchValidation, useWorkbenchAgent } from './useWorkbenchIndex.js';` | 删整行 |
| 130 | `// Phase 60: useWorkbenchSelection aliased to avoid conflict with legacy` | 删 |
| 131 | `// useWorkbenchIndex.js re-export (Phase 19-20 placeholders, superseded by` | 删 |
| 132 | `// useCreatorWriteWorkbench/{useWorkbench*} submodules).` | 删 |
| 135 | `useWorkbenchSelection as useCreatorWorkbenchSelection,` | 改为 `useWorkbenchSelection,` |

### 3.4 扩展架构守卫

`apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 追加 6 项守卫：

```ts
// Phase 61: 5 legacy placeholders from Phase 19-20 must NOT come back
const BANNED_LEGACY = [
  'useWorkbenchCheckpoint.ts',
  'useWorkbenchValidation.ts',
  'useWorkbenchAgent.ts',
  'useWorkbenchSelection.ts', // legacy colocation; new is under useCreatorWriteWorkbench/
  'useWorkbenchIndex.ts',
];
for (const f of BANNED_LEGACY) {
  it(`legacy ${f} 不应复活 (Phase 61)`, () => {
    expect(fs.existsSync(path.join(composablesDir, f))).toBe(false);
  });
}

it('composables/index.ts 不再 re-export useWorkbenchIndex (Phase 61)', () => {
  const indexTs = fs.readFileSync(path.join(composablesDir, 'index.ts'), 'utf-8');
  expect(indexTs).not.toMatch(/useWorkbenchIndex/);
});
```

新守卫位于 `describe('Phase 61 — Legacy Workbench Cleanup Guards', ...)` block 内，遵循既有 `architecture-guards.spec.ts` 风格（嵌套 fs 读 + expect + 注释）。

## 4. 验证清单

| 检查 | 期望结果 |
|------|----------|
| `pnpm exec vue-tsc --noEmit --pretty false` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json --noEmit` | 0 errors |
| `pnpm test` | 1343 → 1322 tests PASS（-21 tests；2 个 legacy spec 共含 14+8=22 tests，留 1 个 skip/未跑） |
| `pnpm exec vitest run tests/unit/guards/` | 现有 5 tests + 新 6 tests = 11 tests PASS |
| `grep -r "useWorkbenchIndex" apps/dashboard/src` | 0 hits |
| `grep -r "useCreatorWorkbenchSelection" apps/dashboard/src` | 0 hits |
| `grep -r "useWorkbenchCheckpoint(\|useWorkbenchValidation(\|useWorkbenchAgent(\|useWorkbenchSelection(\|useWorkbenchIndex(" apps/dashboard/src` | 0 hits（call site） |
| `git show HEAD --stat` | 7 deletes + 2 edits，单 commit |

## 5. 架构原则

- **YAGNI**：0 调用方不留 shim
- **Reversibility**：单 commit；`git revert <hash>` 完整恢复
- **Guard before trust**：删后加 guard 防回潮（与 Phase 60.6 加 `useCreatorWriteWorkbench.js ≤ 200L` 守卫同模式）
- **Boundary 清晰**：legacy 占位与新 submodule 共存 → legacy 必须全删，无 partial cleanup

## 6. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 隐藏的间接引用（动态 import / string ref） | 极低 | 编译失败 | grep + vue-tsc 双验证 |
| 测试 import 旁路（动态 require） | 极低 | 运行时失败 | `pnpm test` 全跑 |
| 外部仓库依赖（dashboard 之外） | 0 | N/A | 5 文件均在 `apps/dashboard/src/composables/`，无外部引用 |
| 未来重新引入 legacy | 中 | 死代码回潮 | 6 项架构守卫阻断 |

## 7. 后续 Phase 62+ 候选

- `api/creator.js` (686L, 114 functions) 拆分
- `useCreatorSettings.js` (650L) approval 流程独立
- `useNavStore.js` (497L) 拆分
- E2E Playwright 集成测试
- Performance 优化
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）

## 8. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase61-final-state.md`，遵循 Phase 60 收官模板：累积指标 + commits + 验证 + 架构守卫。
