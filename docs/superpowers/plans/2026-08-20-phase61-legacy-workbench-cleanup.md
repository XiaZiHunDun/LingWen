# Phase 61 — Legacy Workbench Placeholder 清理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除 Phase 19-20 遗留的 5 个 `useWorkbench*.ts` legacy 占位源文件 + 2 个对应测试 + 清理 `composables/index.ts` re-export 与 alias + 新增 6 项架构守卫；单原子 commit，vue-tsc 0 errors，pnpm test 1343 → 1341 PASS。

**Architecture:** 纯删除 + 出口清理 + 防回潮守卫。0 调用方已 grep 验证（Phase 60 已把对应功能迁到 `useCreatorWriteWorkbench/*` 4 个新 submodule）。沿用 Phase 60.6 守卫模式（`fs.existsSync` + `readFileSync` + `toMatch`）追加 6 个新断言。

**Tech Stack:** Vue 3 + TypeScript + Vitest + vue-tsc。删除 + 路径断言，无新依赖。

**Spec:** `docs/superpowers/specs/2026-08-20-phase61-legacy-workbench-cleanup-design.md`

> **PATCH (2026-08-20, after BLOCKED on Task 1 attempt #1)**: Task 1 ↔ Task 2 必须先清理 `index.ts:83` 的 hard import 再删源文件。原顺序导致 `Cannot find module './useWorkbenchIndex.js'` 编译失败。修正后的顺序：先 Task 1 改 index.ts → 再 Task 2 删文件 → Task 3 加守卫 → Task 4 验证+commit。

---

## 文件结构

```
改 1 源
  apps/dashboard/src/composables/index.ts                          (4 处编辑，必须先做)

删 5 源（717L）
  apps/dashboard/src/composables/useWorkbenchCheckpoint.ts        (107L)
  apps/dashboard/src/composables/useWorkbenchValidation.ts        (333L)
  apps/dashboard/src/composables/useWorkbenchAgent.ts             (161L)
  apps/dashboard/src/composables/useWorkbenchSelection.ts         (102L, legacy)
  apps/dashboard/src/composables/useWorkbenchIndex.ts             (14L)

删 2 测
  apps/dashboard/tests/unit/use-workbench-checkpoint.spec.ts        (Phase 38)
  apps/dashboard/tests/unit/use-workbench-selection-intent.spec.ts  (Phase 18.9)

加 1 守卫
  apps/dashboard/tests/unit/guards/architecture-guards.spec.ts    (新增 6 守卫)

新建 1 文档
  docs/superpowers/specs/2026-08-20-phase61-final-state.md
```

---

## Task 1: 清理 `composables/index.ts` 的 re-export 与 alias（必须先做）

**Files:**
- Modify: `apps/dashboard/src/composables/index.ts:17, 83, 130-132, 135`

**Why first:** `index.ts:83` 包含 `export { ... } from './useWorkbenchIndex.js'` 这条 hard TypeScript import。如果**先删源文件**而**未先改 index.ts**，vue-tsc 会报 `Cannot find module './useWorkbenchIndex.js'` 错误（Task 1 attempt #1 即因此 BLOCKED）。所以本任务必须先于源文件删除。

- [ ] **Step 1.1: 编辑 header 注释 (line 17)**

文件 `apps/dashboard/src/composables/index.ts` 第 17 行：

原文：
```
 * - 工作台: useCreatorWriteWorkbench, useWorkbenchIndex
```

改为：
```
 * - 工作台: useCreatorWriteWorkbench
```

- [ ] **Step 1.2: 删除 line 83 re-export 整行**

文件 `apps/dashboard/src/composables/index.ts` 删除 line 83 整行：

原文：
```
export { useWorkbenchSelection, useWorkbenchCheckpoint, useWorkbenchValidation, useWorkbenchAgent } from './useWorkbenchIndex.js';
```

**整行删除**（不要留空行）。

- [ ] **Step 1.3: 删除 lines 130-132 alias 解释注释**

文件 `apps/dashboard/src/composables/index.ts` 删除 lines 130-132 整 3 行：

原文：
```
// Phase 60: useWorkbenchSelection aliased to avoid conflict with legacy
// useWorkbenchIndex.js re-export (Phase 19-20 placeholders, superseded by
// useCreatorWriteWorkbench/{useWorkbench*} submodules).
```

**整 3 行删除**（不要留空行）。

- [ ] **Step 1.4: 去掉 line 135 alias 还原直接名**

文件 `apps/dashboard/src/composables/index.ts` 把 line 135：

原文：
```
  useWorkbenchSelection as useCreatorWorkbenchSelection,
```

改为：
```
  useWorkbenchSelection,
```

- [ ] **Step 1.5: 验证 index.ts 改动正确**

```bash
cd apps/dashboard
grep -n "useWorkbenchIndex\|useCreatorWorkbenchSelection" src/composables/index.ts
```

Expected: 0 行输出（命令退出码 1）。

- [ ] **Step 1.6: 验证 typescript 编译**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -20
```

Expected: 0 errors（退出码 0）。**这步必须通过**——如果出现 `useWorkbenchIndex` 任何剩余引用，要回退 Step 1.1-1.4 检查。

- [ ] **Step 1.7: 验证两套 tsconfig 编译**

```bash
cd apps/dashboard
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -20
```

Expected: 0 errors（退出码 0）。

**重要：到此步骤不要 commit。** 4 处编辑只是工作树变更，最终单一 commit 在 Task 4 一并完成。

---

## Task 2: 删除 5 个 legacy 源文件 + 2 个对应测试

**Files:**
- Delete: `apps/dashboard/src/composables/useWorkbenchCheckpoint.ts`
- Delete: `apps/dashboard/src/composables/useWorkbenchValidation.ts`
- Delete: `apps/dashboard/src/composables/useWorkbenchAgent.ts`
- Delete: `apps/dashboard/src/composables/useWorkbenchSelection.ts`
- Delete: `apps/dashboard/src/composables/useWorkbenchIndex.ts`
- Delete: `apps/dashboard/tests/unit/use-workbench-checkpoint.spec.ts`
- Delete: `apps/dashboard/tests/unit/use-workbench-selection-intent.spec.ts`

**Why second:** Task 1 已清理 `index.ts:83` 的 hard import，删除源文件不再触发 vue-tsc 编译错误。

- [ ] **Step 2.1: 删除 5 个 legacy 源文件**

```bash
cd apps/dashboard/src/composables
rm useWorkbenchCheckpoint.ts \
   useWorkbenchValidation.ts \
   useWorkbenchAgent.ts \
   useWorkbenchSelection.ts \
   useWorkbenchIndex.ts
ls -la useWorkbench*.ts 2>/dev/null
```

Expected: `ls` 输出为空（命令退出码 2）。`useCreatorWriteWorkbench/` 子目录的 submodule 不受影响。

- [ ] **Step 2.2: 删除 2 个 legacy 测试文件**

```bash
cd apps/dashboard/tests/unit
rm use-workbench-checkpoint.spec.ts \
   use-workbench-selection-intent.spec.ts
ls -la use-workbench-checkpoint.spec.ts use-workbench-selection-intent.spec.ts 2>/dev/null
```

Expected: `ls` 命令每个文件报 `No such file or directory`（退出码 2）。

- [ ] **Step 2.3: 验证 typescript 编译（Task 1 hard import 清理后不会再失败）**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -20
```

Expected: 0 errors（退出码 0）。

- [ ] **Step 2.4: 验证测试通过数**

```bash
cd apps/dashboard
pnpm test 2>&1 | tail -10
```

Expected: `Test Files  182 passed (182)` 与 `Tests  1341 passed (1341)`。**注意**：`1343 → 1341`，因为删了 2 个 legacy spec 文件。如果出现 1343 或其他数值，说明有未发现的引用测试。

**重要：到此步骤不要 commit。** 删除只是工作树变更，最终单一 commit 在 Task 4 一并完成。

---

## Task 3: 扩展架构守卫（防回潮）

**Files:**
- Modify: `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` (在文件末尾追加 6 守卫)

**Why third:** 删 + 改完后再加守卫，是「删除 → 验证 → 加防」的标准顺序——只有删干净后，守卫才有意义。

> **关于既有 workbench-special-case（lines 38-46）**：该段位于「composables/index.ts 导出所有 composable 文件」测试内，**已被 `fs.existsSync` 包裹**（`if (fs.existsSync(indexFileFull))`），删除 `useWorkbenchIndex.ts` 后会安全 no-op（落入直接 `missingExports` 判空分支）。**无需修改**，但 Task 3 加 6 项新守卫直接 BLOCK 路径，杜绝回潮。

- [ ] **Step 3.1: 读取现有 guards 文件**

```bash
cd apps/dashboard
wc -l tests/unit/guards/architecture-guards.spec.ts
tail -30 tests/unit/guards/architecture-guards.spec.ts
```

读取后定位文件末尾，确认 `fs` / `path` / `composablesDir` 等已存在的模块级变量名（避免命名冲突）。

- [ ] **Step 3.2: 在文件末尾追加 6 项守卫**

文件 `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 在文件最后追加如下代码块（保持现有 `describe` 风格）：

```ts
// Phase 61: 5 legacy placeholders from Phase 19-20 must NOT come back
describe('Phase 61 — Legacy Workbench Cleanup Guards', () => {
  const BANNED_LEGACY = [
    'useWorkbenchCheckpoint.ts',
    'useWorkbenchValidation.ts',
    'useWorkbenchAgent.ts',
    'useWorkbenchSelection.ts', // legacy colocation; new is under useCreatorWriteWorkbench/
    'useWorkbenchIndex.ts',
  ];

  for (const banned of BANNED_LEGACY) {
    it(`legacy ${banned} 不应复活 (Phase 61)`, () => {
      expect(fs.existsSync(path.join(composablesDir, banned))).toBe(false);
    });
  }

  it('composables/index.ts 不再 re-export useWorkbenchIndex (Phase 61)', () => {
    const indexTs = fs.readFileSync(path.join(composablesDir, 'index.ts'), 'utf-8');
    expect(indexTs).not.toMatch(/useWorkbenchIndex/);
  });
});
```

**注意**：文件中已有的 Phase 60.6 守卫（`useCreatorWriteWorkbench.js ≤ 200L`，第 107-112 行）所属 `describe('Guard: 架构不变量', ...)` 块在 line 113 关闭。新 `describe` 应在文件最末另起，**不要**嵌套到其他 `describe` 里。

- [ ] **Step 3.3: 验证 6 项新守卫通过**

```bash
cd apps/dashboard
pnpm exec vitest run tests/unit/guards/architecture-guards.spec.ts 2>&1 | tail -30
```

Expected: `Test Files  1 passed (1)` 与 `Tests  11 passed (11)`（既有 5 个 + 新 6 个）。如果失败：
- 某 BANNED_LEGACY 文件被错误建回来 → 检查 `apps/dashboard/src/composables/` 目录
- `useWorkbenchIndex` grep 命中 → 检查 Task 1 的 Step 1.1-1.4 是否完整

**重要：到此步骤不要 commit。**

---

## Task 4: 最终验证 + 单原子 commit + 收官报告

**Files:**
- Modify: `docs/superpowers/specs/2026-08-20-phase61-final-state.md` (新建)

**Why fourth:** 集中验证 + 单一 commit + 报告。避免分 commit 拆分（与 Phase 60 的 6-子 phase 拆分相反，本阶段范围小、动作原子）。

- [ ] **Step 4.1: 最终 grep 验证**

```bash
cd apps/dashboard/src
grep -rn "useWorkbenchIndex" . 2>/dev/null
grep -rn "useCreatorWorkbenchSelection" . 2>/dev/null
grep -rn "useWorkbenchCheckpoint(\|useWorkbenchValidation(\|useWorkbenchAgent(\|useWorkbenchSelection(\|useWorkbenchIndex(" . 2>/dev/null
```

Expected: 3 个 grep 命令均 0 行输出（退出码 1）。

- [ ] **Step 4.2: 完整 type-check + 测试**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -5
pnpm test 2>&1 | tail -10
pnpm exec vitest run tests/unit/guards/ 2>&1 | tail -10
```

Expected（4 个命令依次）：
1. `vue-tsc --noEmit` 0 errors
2. `vue-tsc -p tsconfig.app.json` 0 errors
3. `Test Files  182 passed (182)` + `Tests  1341 passed (1341)`
4. `Test Files  1 passed (1)` + `Tests  11 passed (11)`

- [ ] **Step 4.3: 检查 working tree 状态**

```bash
git status -s
```

Expected: 7 个 `D` (7 个删除) + 2 个 `M` (index.ts + architecture-guards.spec.ts) + 1 个 `??` (final-state.md 未建)：

```
 M apps/dashboard/src/composables/index.ts
 M apps/dashboard/tests/unit/guards/architecture-guards.spec.ts
 D apps/dashboard/src/composables/useWorkbenchAgent.ts
 D apps/dashboard/src/composables/useWorkbenchCheckpoint.ts
 D apps/dashboard/src/composables/useWorkbenchIndex.ts
 D apps/dashboard/src/composables/useWorkbenchSelection.ts
 D apps/dashboard/src/composables/useWorkbenchValidation.ts
 D apps/dashboard/tests/unit/use-workbench-checkpoint.spec.ts
 D apps/dashboard/tests/unit/use-workbench-selection-intent.spec.ts
?? docs/superpowers/specs/2026-08-20-phase61-final-state.md
```

**如果与你看到的不同**：立即停止调查——可能有多余改动或漏改。

- [ ] **Step 4.4: 写收官报告**

新建文件 `docs/superpowers/specs/2026-08-20-phase61-final-state.md`，内容模板（按 Phase 60 final state 风格）：

```markdown
# Phase 61 — Legacy Workbench Cleanup 收官报告

> **日期**: 2026-08-20
> **范围**: 5 源 + 2 测删除 + index.ts 清理 + 6 守卫
> **基础**: Phase 60 完整闭环

## 累积指标

| 指标 | 值 |
|------|-----|
| Legacy 源文件 | 5 → 0 (-717L) |
| Legacy 测试 | 2 → 0 |
| 总测试数 | 1343 → 1341 (-2) |
| 架构守卫 | 5 → 11 (+6) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 1 (单原子) |

## 改动文件清单

| 文件 | 动作 |
|------|------|
| useWorkbenchCheckpoint.ts | deleted (107L) |
| useWorkbenchValidation.ts | deleted (333L) |
| useWorkbenchAgent.ts | deleted (161L) |
| useWorkbenchSelection.ts (legacy) | deleted (102L) |
| useWorkbenchIndex.ts | deleted (14L) |
| use-workbench-checkpoint.spec.ts | deleted |
| use-workbench-selection-intent.spec.ts | deleted |
| composables/index.ts | 4 处清理 (line 17, 83, 130-132, 135) |
| architecture-guards.spec.ts | +6 guards |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1341 tests PASS |
| `pnpm exec vitest run tests/unit/guards/` | 11 tests PASS |
| `grep -r useWorkbenchIndex apps/dashboard/src` | 0 hits |
| `grep -r useCreatorWorkbenchSelection apps/dashboard/src` | 0 hits |

## 架构守卫（新增 6 项）

- 5 项断言：5 个 legacy 文件不存在
- 1 项断言：`composables/index.ts` 不再 re-export `useWorkbenchIndex`

## 过程 Notes

- 任务顺序修正：Task 1 (index.ts) 先于 Task 2 (delete files)，否则 vue-tsc 报 `Cannot find module './useWorkbenchIndex.js'`。
- 见 plan 的 PATCH 注释。

## 后续 Phase 62+ 候选

- `api/creator.js` (686L, 114 functions) 拆分
- `useCreatorSettings.js` (650L) approval 流程独立
- `useNavStore.js` (497L) 拆分
- E2E Playwright 集成测试
- Performance 优化
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）
```

- [ ] **Step 4.5: 单原子 commit**

```bash
git add apps/dashboard/src/composables/index.ts \
        apps/dashboard/src/composables/useWorkbenchCheckpoint.ts \
        apps/dashboard/src/composables/useWorkbenchValidation.ts \
        apps/dashboard/src/composables/useWorkbenchAgent.ts \
        apps/dashboard/src/composables/useWorkbenchSelection.ts \
        apps/dashboard/src/composables/useWorkbenchIndex.ts \
        apps/dashboard/tests/unit/use-workbench-checkpoint.spec.ts \
        apps/dashboard/tests/unit/use-workbench-selection-intent.spec.ts \
        apps/dashboard/tests/unit/guards/architecture-guards.spec.ts \
        docs/superpowers/specs/2026-08-20-phase61-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(composables): delete legacy workbench placeholders (Phase 61)" \
    -m "Phase 19-20 遗留 5 个 useWorkbench*.ts 占位 (717L) 0 调用方由 grep 验证；对应 2 个测试文件已同步移除；composables/index.ts 清理 re-export 与 alias；新增 6 项架构守卫防回潮。pnpm test 1343 → 1341 PASS，vue-tsc 0 errors。"

git show --stat HEAD
```

Expected: 单 commit，9 files changed (7 deletes + 2 edits + 1 new doc)，与 Step 4.3 状态一致。

- [ ] **Step 4.6: 推送本地 commit（不创建 PR）**

```bash
git log --oneline -1
```

Expected: 显示新的 commit hash（最新 1 行）。Phase 60 模式是直接 commit 到 master，不开 PR。

---

## 自检清单

执行前请确认：

- [ ] 工作目录干净（`git status` 无未追踪改动，**除了本 plan 自身的修改**）
- [ ] 在 `LingWen/` 仓库根目录
- [ ] 当前在 master 分支（`git branch --show-current` 输出 `master`）
- [ ] 上一 commit 是 `e9de635b`（Phase 61 plan）或更晚

执行中遇任何 verify 步骤失败：**立即停止**回退该步骤调查，不要跳过。
