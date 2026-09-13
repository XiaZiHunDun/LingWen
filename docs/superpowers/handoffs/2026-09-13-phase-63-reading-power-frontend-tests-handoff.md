# Phase 63 — Reading Power Frontend Tests Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 57b reading_power backend tests restoration (44/44 functional gate)
> **目标**: Add dedicated frontend unit tests for Reading Power display surface in `apps/dashboard/src/utils/creationModeHint.js`

## 1. 背景

Phase 57b (2026-09-13) restored 8 reading_power Python test files (44/44 functional gate) for `packages/lingwen-reading-power/`. But the **frontend usage** of Reading Power concepts had no dedicated unit tests — only 3 smoke tests indirectly covered the surface (insight-page.spec.ts, dashboard.spec.ts, app-smoke.spec.ts).

Frontend Reading Power references:
- `apps/dashboard/src/pages/InsightPage.vue` (primary)
- `apps/dashboard/src/pages/AnalyticsPage.vue`
- `apps/dashboard/src/pages/OverviewPage.vue`
- `apps/dashboard/src/utils/creationModeHint.js` ← **chosen target** (pure utility, easy to unit test)
- `apps/dashboard/src/config/dashboardNav{ByMode,}.js`

`creationModeHint.js` exports:
- `creationModeMeta(mode)` — returns mode metadata
- `resolveTodayPrimaryAction(ctx)` — picks the single primary CTA for the Today hub

The "查看追读力洞察" CTA (View Reading Power Insight) is returned by `resolveTodayPrimaryAction` as the reviewer-mode fallback when no other priority signals exist.

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-63): Reading Power frontend unit tests (7 tests) | 1 | +133 |

**Net**: +7 vitest tests, v54.8 (no bump), 1898/1899 (1 pre-existing skip) full vitest.

## 3. Test design (7 tests in `creationModeHint.spec.ts`)

### creationModeMeta (3 tests)
- All 3 known modes return full metadata
- Unknown mode returns fallback stub with mode string as label
- Nullish input (null/undefined) returns "未知模式" fallback

### resolveTodayPrimaryAction — Reading Power fallback (4 tests)
- Reviewer mode + no signals → "查看追读力洞察" CTA
- Reviewer mode + pendingDecisions=3 → decisions CTA (priority over RP)
- Reviewer mode + pendingRipples=2 → ripples CTA (priority over RP)
- Non-reviewer mode → never returns RP fallback (other CTAs selected)

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/utils/creationModeHint.spec.ts` | 7 passed | ✅ 7/7 in 1.08s |
| G2 | `pnpm test -- tests/unit/utils/` (all utils tests) | 67 passed (60 + 7 new) | ✅ 67/67 in 1.27s |
| G3 | `pnpm test` (full vitest suite) | 1899 passed (1 skipped pre-existing) | ✅ 1898/1899 in 24.72s |
| G4 | pnpm-lock.yaml changed | no (package.json untouched) | ✅ no change |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition (no production code change)
- Reading Power frontend behavior unchanged
- All baselines preserved

**Rollback**: `git revert HEAD` removes the spec file (no other effects).

## 6. Lessons

1. **Parameter name drift (Phase 53c/57b pattern)**：测试代码假设 `isReviewerMode`，实际函数用 `isReviewer`。TypeScript 不能阻止这种 naming drift（都是 string keys）。建议：未来 frontend utility 用 typed wrapper 或 zod schema 强制参数名 (类似 backend 的 typed wrapper)。
2. **`#` vs `//` comment syntax**：第一次 spec 用了 Python-style `#` separator → TypeScript 编译失败。TS 只支持 `//` line comments。这是 Python 用户写 TS 的常见 catch。
3. **Reading Power frontend surface 比 backend 小但同样 critical**：`creationModeHint.js` 只有 172 LOC 但包含 4 处 Reading Power references (`查看追读力洞察` + InsightPage nav routing + creationModeHint context)。Reading Power 概念贯穿 dashboard 多个 page，但只有 1 个 utility 直接 testable — 真正的 component-level test 需要 Pinia + vue-router + hub mocks (类似 Phase 31 lesson 1)。本 phase 选择 utility-level 是合理 ROI 平衡。
4. **1891 → 1898 vitest tests**：与 MEMORY "vitest 1884" baseline 已有 +7 增长（应该是其他 phase 累积）。本 phase 1891 → 1898 是 **+7 测试 0 回归**。

## 7. Carryover

- ✅ Phase 57b reading_power backend tests → CLOSED (Python side)
- ✅ Phase 63 reading_power frontend tests → CLOSED (this phase, JS side)
- 新增：建议 future phase 继续补 World / WriteWorkspace 单元测试 (10 个 untested components found during audit)
- 下一步候选: ff-merge to master (35 commits ahead) OR 更多 frontend 测试 OR 产品功能改进

## 8. References

- Spec: `apps/dashboard/tests/unit/utils/creationModeHint.spec.ts` (this commit)
- Source: `apps/dashboard/src/utils/creationModeHint.js`
- Phase 57b (backend precedent): `docs/superpowers/handoffs/2026-09-13-phase-57b-reading-power-tests-restore-handoff.md`
