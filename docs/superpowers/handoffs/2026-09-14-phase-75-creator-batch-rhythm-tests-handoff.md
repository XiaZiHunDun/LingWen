# Phase 75 — CreatorBatchRhythm.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 74 (CreatorModeGuideBar tests — P0+ era campaign start) + Phase 68 (Pinia+composable mock pattern)
> **目标**: Add 8 vitest tests for `apps/dashboard/src/components/creator/CreatorBatchRhythm.vue`

## 1. 背景

Phase 74 started the P0+ era creator component gap closure campaign with CreatorModeGuideBar (151 LOC). Phase 75 picks CreatorBatchRhythm (272 LOC) — read-only batch progress visualization (REQ-001 slice C).

Picked over CreatorDeviationFinalize (265 LOC, similar complexity but diff visualization) since CreatorBatchRhythm has clearer state machine (empty / loaded / deviations).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-75): CreatorBatchRhythm.vue unit tests (8 tests) | 1 | +150 |

**Net**: +8 vitest tests, v54.8 (no bump), 1986/1987 full vitest.

## 3. Test design (8 tests)

### Setup pattern
- `vi.mock` returns refs directly (not unwrapped values) — so component can do `activeJob.value`
- Reactive test state via top-level refs shared with mock
- `beforeEach` resets refs

### Mount + empty state (2 tests)
- refreshActive called on mount
- Empty-state message renders when no activeJob

### Loaded state — happy path (2 tests)
- Status label + range + progress for running batch (status='running', chapters 1-5, 2 completed → "2/5")
- 5 band cells rendered with raw chapter num in testids (NOT padded)

### Deviations (2 tests)
- Cell marked `data-state="deviating"` when completed before prior chapters
- Deviations section lists each one with count "2 处偏差"

### Status mapping (2 tests)
- "已完成" label for status='completed'
- "当前批次已结束" hint when isJobActive=false

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/creator/CreatorBatchRhythm.spec.ts` | 8 passed | ✅ 8/8 in 1.23s |
| G2 | `pnpm test` (full vitest) | 1987 passed (1 pre-existing skip) | ✅ 1986/1987 in 20.49s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CreatorBatchRhythm rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **`vi.mock` returns refs directly, not getters**: First version used `get activeJob() { return activeJobRef.value; }` getter pattern (Phase 68 style). But composable consumer does `pilot.activeJob.value` which expects a ref, not a value. Switched to returning the ref directly: `{ activeJob: activeJobRef }`. Pattern: match the consumer's expectation — if the consumer does `.value`, return a ref; if it does `.x` (no .value), return a value.

2. **Field naming conventions matter in mocks**: First version used `chapter: 1` but real `computeCompletedNums` expects `chapter_num`. The TypeScript types in BatchEventLite catch this in production but mocks bypass type checks. Lesson: when mocking event shapes, copy from the actual interface (BatchEventLite) verbatim.

3. **Testid naming: raw vs padded values**: Cell testid uses raw `cell.num` (e.g., `cell-1`), but display text uses padded format (e.g., `ch001`). Tests must match both — assert on `data-testid="creator-batch-rhythm-cell-1"` AND `text()` containing "ch001".

## 7. Carryover

- P0+ era creator campaign: 2 of 3 done
- ✅ CreatorModeGuideBar (Phase 74)
- ✅ CreatorBatchRhythm (Phase 75)
- 新增: 1 remaining (CreatorDeviationFinalize 265 LOC)
- CreatorDeviationFinalize is a "finalize diff" workflow component — likely needs usePilotBatch + Pinia + form mocking

## 8. References

- Spec: `apps/dashboard/tests/unit/components/creator/CreatorBatchRhythm.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/creator/CreatorBatchRhythm.vue`
- Phase 74 (precedent sibling): CreatorModeGuideBar tests in same campaign
- Phase 68 (precedent): CharacterList Pinia mock pattern
- batchDeviation utility: `apps/dashboard/src/utils/batchDeviation.ts`
- usePilotBatch composable: `apps/dashboard/src/composables/usePilotBatch.ts`
