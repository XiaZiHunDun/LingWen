# Phase 74 — CreatorModeGuideBar.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 73 (FactionGraphCanvas — completed the 12/12 milestone) + P0+ era audit (CreatorBatchRhythm/DeviationFinalize/GuideBar were never tested)
> **目标**: Add 7 vitest tests for `apps/dashboard/src/components/creator/CreatorModeGuideBar.vue` — first of 3 P0+ era gap closure tests

## 1. 背景

Phase 73 closed the 12/12 originally-untested component milestone. Fresh audit of recent (P0+ era, 2026-08+) added components revealed 3 NEW untested components in `apps/dashboard/src/components/creator/`:
- `CreatorBatchRhythm.vue` (272 LOC) — batch progress visualization (Phase 74 candidate 2)
- `CreatorDeviationFinalize.vue` (265 LOC) — finalize diff/close-out (Phase 74 candidate 3)
- `CreatorModeGuideBar.vue` (151 LOC) — mode guide strip with localStorage dismiss

Phase 74 starts the P0+ gap closure campaign with the smallest of the 3 (`CreatorModeGuideBar`).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-74): CreatorModeGuideBar.vue unit tests (7 tests) | 1 | +104 |

**Net**: +7 vitest tests, v54.8 (no bump), 1978/1979 full vitest.

## 3. Test design (7 tests)

### Setup pattern
- `defineComponent` test harness with `provide(CREATOR_WRITE_KEY, { wb: reactive({creationMode}) })`
- `window.localStorage.clear()` in beforeEach

### Render per mode (4 tests)
- companion mode: renders container with `--companion` variant class
- companion: shows "陪伴模式" + "AI 陪你写作" text
- advance: shows "推进模式" + "批改节奏带" text
- studio: shows "工厂模式" + "产线" text

### Dismiss + visibility (3 tests)
- Dismiss click writes mode to localStorage
- Bar hides after dismiss
- Bar does not render when localStorage already has the current mode

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/creator/CreatorModeGuideBar.spec.ts` | 7 passed | ✅ 7/7 in 1.23s |
| G2 | `pnpm test` (full vitest) | 1979 passed (1 pre-existing skip) | ✅ 1978/1979 |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CreatorModeGuideBar rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **`provide`/`inject` test harness**: CreatorModeGuideBar uses `inject(CREATOR_WRITE_KEY)` to get the mode from a parent provider. Standard vitest approach: write a tiny `defineComponent` harness that provides the key + renders the target. This pattern works for any provide/inject component without needing to import the parent provider.
2. **`reactive({...})` for test mutability**: The harness uses `reactive({ creationMode: mode })` so a future test variant could `wb.creationMode = 'advance'` and trigger reactivity. Not used in current 7 tests but sets up the pattern for followup tests.
3. **localStorage as test fixture**: For components that persist UI state to localStorage (dismiss, etc.), `window.localStorage.clear()` in beforeEach + direct setItem in tests gives full control. jsdom provides `localStorage` natively — no extra mock needed.

## 7. Carryover

- NEW campaign: P0+ era creator components gap closure
- ✅ 1 of 3 done (CreatorModeGuideBar)
- 新增: 2 remaining (CreatorBatchRhythm 272 LOC, CreatorDeviationFinalize 265 LOC)
- Both remaining are larger + use usePilotBatch composable (more setup)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/creator/CreatorModeGuideBar.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/creator/CreatorModeGuideBar.vue`
- Phase 64-73 (precedent sequence): 10 prior component test phases covering WorldTabs/WriteWorkspace/etc
- Phase 68 (precedent for Pinia + test harness): similar provide pattern
- CREATOR_WRITE_KEY: `apps/dashboard/src/components/creator/creatorWriteKey.js`
