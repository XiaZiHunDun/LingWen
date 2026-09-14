# Phase 72 — FactionGraph.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 71 (CharacterEditor tests) + Phase 67 (FactionDetail tests)
> **目标**: Add 8 vitest tests for `apps/dashboard/src/components/world/factions/FactionGraph.vue`

## 1. 背景

Phase 64-71 closed 10 of 12 untested World/WriteWorkspace components. Phase 72 picks `FactionGraph.vue` (~80 LOC) — faction page view-mode toggle (list/graph), second-to-last before the vis-network FactionGraphCanvas.

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-72): FactionGraph.vue unit tests (8 tests) | 1 | +148 |

**Net**: +8 vitest tests, v54.8 (no bump), 1964/1965 full vitest.

## 3. Test design (8 tests)

### Setup
- `vi.mock` useWorldDb → listFactions + listRelationships fixtures
- `vi.mock` stub FactionGraphCanvas (avoids vis-network canvas deps) + FactionDetail
- Real `useWorldStore` (Pinia global setup per Phase 8.30)
- `selectedCharacterId` reused for faction selection (intentional per source comment)

### Render defaults (3 tests)
- Page testid renders
- Toolbar with list + graph toggle buttons
- Default list view (renders faction-list, hides graph canvas, list toggle has is-active class)

### View toggle (2 tests)
- Click 关系图 → switches to graph view (renders canvas stub + graph toggle is-active)
- Click 列表 → back to list view

### Selection (3 tests)
- Faction cards render with slug-based testids
- Click faction card sets store.selectedCharacterId (intentional reuse)
- FactionDetail renders when selection matches a faction

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/factions/FactionGraph.spec.ts` | 8 passed | ✅ 8/8 in 1.15s |
| G2 | `pnpm test` (full vitest) | 1965 passed (1 pre-existing skip) | ✅ 1964/1965 in 20.44s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- FactionGraph rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Reused field names document design quirks**: `store.selectedCharacterId` is used for BOTH character and faction selection. This is intentional per source comment ("复用 Task 13 / 14 的 store 字段"). Test explicitly asserts `store.selectedCharacterId === 10` for a faction click — locks in the design quirk so a future "fix" would fail loudly. Pattern: test the actual behavior, not the ideal behavior.
2. **FactionGraphCanvas stub for isolation**: The vis-network-backed FactionGraphCanvas component is the LAST remaining untested component (very high complexity per MEMORY Phase 118 lesson). Stubbing it in FactionGraph tests lets us test the parent toggle + selection behavior independently of the canvas rendering.
3. **`v-else` + `v-if` together**: FactionGraph uses `v-if="viewMode === 'list'"` for the list + `v-else` for the canvas. Test pattern: `expect(listView).toBe(true)` and `expect(canvasStub).toBe(false)` simultaneously, then flip and verify both directions.

## 7. Carryover

- ✅ 11 of 12 untested components covered (92%)
- 新增: 1 remaining (FactionGraphCanvas — vis-network direct usage, very high complexity per MEMORY Phase 118)
- FactionGraphCanvas requires vis-network mock (network graph lib) + likely canvas-rendering test infrastructure

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/factions/FactionGraph.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/factions/FactionGraph.vue`
- Phase 67 (sibling): FactionDetail test pattern
- Phase 68 (sibling): CharacterList stub pattern (similar view-mode toggle architecture)
- MEMORY Phase 118: vis-network install + testing lessons
