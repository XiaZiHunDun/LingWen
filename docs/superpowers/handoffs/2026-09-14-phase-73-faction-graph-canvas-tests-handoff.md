# Phase 73 — FactionGraphCanvas.vue Tests Handoff (FINAL component)

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 72 (FactionGraph tests) + MEMORY Phase 118 (vis-network lessons)
> **目标**: Add 7 vitest tests for `apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue` — FINAL of 12 originally-untested components

## 1. 背景 — MILESTONE

Phase 64-72 closed 11 of 12 originally-untested World/WriteWorkspace components. Phase 73 completes the cycle with the last one — `FactionGraphCanvas.vue` (70 LOC), which wraps vis-network's Network class for the faction relationship graph.

**MILESTONE**: 12/12 originally-untested components now have frontend unit tests (100% coverage). Original list:
- WorldTabs, WorldImportExport, FactionDetail, FactionGraph, FactionGraphCanvas
- CharacterCard, CharacterList, CharacterDetail, CharacterRelationships, CharacterEditor
- WriteChatContextInjector
- creationModeHint utility

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-73): FactionGraphCanvas.vue unit tests (7 tests) | 1 | +133 |

**Net**: +7 vitest tests, v54.8 (no bump), 1971/1972 full vitest.

## 3. Test design (7 tests)

### Setup
- `vi.mock('vis-network/standalone')` → Network class mock + setData/destroy spies
- Avoids vis-network + canvas-rendering complexity per MEMORY Phase 118

### Mount (3 tests)
- Container testid renders
- Network instantiated on mount (with container DOM + data + options)
- Nodes built from factions (id='faction-N', label=name, shape='box')

### Data updates (3 tests)
- setData called on factions prop change with updated node count
- Relationship filter to enemy/ally only (drops trade/rival)
- Red color to enemy edges (#ef4444) + green to ally edges (#10b981)

### Unmount (1 test)
- Network.destroy called on unmount

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/factions/FactionGraphCanvas.spec.ts` | 7 passed | ✅ 7/7 in 1.15s |
| G2 | `pnpm test` (full vitest) | 1972 passed (1 pre-existing skip) | ✅ 1971/1972 in 20.63s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- FactionGraphCanvas rendering unchanged
- 0 production code change
- vis-network mock is scoped to spec file (no global side-effect)

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **`vi.mock('vis-network/standalone')` for network library mocking**: vis-network is a heavy dependency (requires install, depends on canvas rendering which jsdom doesn't support per MEMORY Phase 118). The mock isolates FactionGraphCanvas behavior — verifies Network is instantiated with right args + setData/destroy called at right times — without actually rendering the graph. Real canvas rendering would require Playwright (deferred to e2e per project convention).
2. **Color-coded edges as data assertions**: enemy=red, ally=green is a UI semantic locked in via edge color assertions (`#ef4444`, `#10b981`). Future redesign changes would fail these tests, catching accidental visual regressions at the data layer.
3. **MILESTONE: 100% coverage of originally-untested**: Started Phase 64 with 12 untested components in scope. Phase 73 closes the last one. Future frontend test work shifts to NEW untested components (which emerge with new features).

## 7. Carryover (CLOSED)

- ✅ 12 of 12 originally-untested components covered (**100%**)
- 新增：无 carryover (FINAL phase of this campaign)
- 下一步候选: ff-merge to master + **stop** OR shift to different work (product feature / ARCHDEBT-MINI new cycle / etc.)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/factions/FactionGraphCanvas.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/factions/FactionGraphCanvas.vue`
- Phase 72 (sibling): FactionGraph stub pattern for parent
- MEMORY Phase 118: vis-network install + canvas testing lessons
- Phases 64-72 (precedent sequence): 10 prior component tests
