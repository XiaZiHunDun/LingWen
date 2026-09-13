# Phase 65 — WorldImportExport.vue Tests Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 64 (WorldTabs.vue tests) + Phase 117 (World page implementation)
> **目标**: Add 5 vitest tests for `apps/dashboard/src/components/world/WorldImportExport.vue`

## 1. 背景

Phase 64 closed WorldTabs test gap (6 tests). Phase 65 targets the second untested World top-level component — WorldImportExport.vue (56 LOC). This is the markdown import/export panel on the World page (Phase 117 Task 21), wrapping useWorldImportExport composable with 2 action buttons + inline summary.

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-65): WorldImportExport.vue unit tests (5 tests) | 1 | +99 |

**Net**: +5 vitest tests, v54.8 (no bump), 1909/1910 full vitest.

## 3. Test design (5 tests in `WorldImportExport.spec.ts`)

### Render structure (2 tests)
- 2 buttons (import + export) with stable testids + Chinese labels
- Summary element NOT rendered before any action

### Import flow (1 test)
- Click import → calls importMarkdown mock → renders summary with characters/factions/lore counts

### Export flow (1 test)
- Click export → calls exportMarkdown mock → renders summary with files_written + output_dir

### State management (1 test)
- Subsequent action (import then export) overwrites summary (no stale state)

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/WorldImportExport.spec.ts` | 5 passed | ✅ 5/5 in 1.24s |
| G2 | `pnpm test` (full vitest) | 1910 passed (1 pre-existing skip) | ✅ 1909/1910 in 22.57s |
| G3 | No regression on existing 248 test files | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- WorldImportExport rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **`vi.mock` for composable wrapping**: WorldImportExport wraps `useWorldImportExport` which itself wraps `useWorldDb` + `useWorldAgent` + `useWorldReview`. Mocking at the component's direct composable boundary (not deeper) keeps the spec focused on WorldImportExport behavior. Pattern matches WorldProposalInbox.spec.ts from Phase 117.
2. **`mockReset()` in beforeEach**: composable mocks must reset between tests — otherwise state from earlier test (e.g., `importMarkdownMock.mockResolvedValue` from test 3 leaks into test 4). `mockReset()` clears both implementations AND call history.
3. **`flushPromises()` after async click**: similar to `await setProps()` (Phase 64 lesson 2), `trigger('click')` returns immediately but the async composable call resolves later. `await flushPromises()` ensures the `.finally { busy.value = false }` block ran + lastSummary reactive update propagated to DOM.

## 7. Carryover

- ✅ 2 of 10 untested components covered (20% of World page top-level — WorldTabs + WorldImportExport)
- 新增: 8 remaining components (WriteChatContextInjector + characters/* 5 + factions/* 3)
- 下一步候选: ff-merge + continue OR switch direction

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/WorldImportExport.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/WorldImportExport.vue`
- Composable: `apps/dashboard/src/composables/world/useWorldImportExport.js`
- Phase 64 (precedent): `apps/dashboard/tests/unit/components/world/WorldTabs.spec.ts`
- Phase 117 (World page impl): Task 21 (WorldImportExport)
