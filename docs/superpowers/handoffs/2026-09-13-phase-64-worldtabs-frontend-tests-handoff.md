# Phase 64 — WorldTabs.vue Tests Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 63 (Reading Power frontend tests for `creationModeHint.js`) + Phase 117 (World page implementation)
> **目标**: Add 6 vitest tests for `apps/dashboard/src/components/world/WorldTabs.vue`

## 1. 背景

Phase 63 closed the Reading Power frontend test gap by adding 7 tests for `creationModeHint.js`. Audit found 10 more untested frontend components:

- `apps/dashboard/src/components/writeWorkspace/WriteChatContextInjector.vue` (36 LOC)
- `apps/dashboard/src/components/world/WorldImportExport.vue` (56 LOC)
- `apps/dashboard/src/components/world/WorldTabs.vue` (57 LOC) ← **this phase**
- `apps/dashboard/src/components/world/characters/*` (5 components)
- `apps/dashboard/src/components/world/factions/*` (3 components)

`WorldTabs.vue` 是 top-level World page tab 切换条 (Phase 117 Task 12 / F). 4 个 hardcoded tabs: 人物卡 / 势力图 / 时间线 / 世界书. Simple component — high testability.

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-64): WorldTabs.vue unit tests (6 tests) | 1 | +108 |

**Net**: +6 vitest tests, v54.8 (no bump), 1904/1905 full vitest.

## 3. Test design (6 tests in `WorldTabs.spec.ts`)

### Render structure (2 tests)
- All 4 tabs in stable order with correct labels (人物卡/势力图/时间线/世界书)
- Container has `world-tabs` testid for hub-level selectors

### Active tab highlighting (2 tests)
- Only the active tab has `world-tab--active` class
- Prop change moves `--active` class to new tab + removes from old

### Switch emission (2 tests)
- Click emits `switch` event with clicked tab id
- Multiple clicks emit distinct switch events correctly

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/WorldTabs.spec.ts` | 6 passed | ✅ 6/6 in 1.12s |
| G2 | `pnpm test` (full vitest) | 1905 passed (1 pre-existing skip) | ✅ 1904/1905 in 20.12s |
| G3 | No `world-tab-*` testid collisions | unique IDs | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- WorldTabs rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Contradictory assertion in forEach**: First test version had `expect(btn.classes()).toContain('world-tab--active')` always, then conditional `expect(...).not.toContain(...)`. That's logically impossible — both branches couldn't pass. Refactored to `if/else` pattern with single assertion per branch. Lesson: assertion logic in loops needs single per-iteration assertion, not overlapping branches.
2. **`@vue/test-utils` `setProps()` reactivity**: Test 4 uses `await wrapper.setProps({ activeTab: 'lore' })` which is async (triggers Vue reactivity). Without `await`, assertions run on stale DOM. Pattern: any prop-change test must `await setProps()` before assertions.
3. **Component test pattern matches project**: Following existing pattern (WorldProposalInbox.spec.ts) — `mount` from `@vue/test-utils` + `vi.mock` for composables (not needed for WorldTabs which has no composables) + `data-testid` selectors (per MEMORY convention).

## 7. Carryover

- ✅ 1 of 10 untested components covered (10% of World page top-level)
- 新增: 9 remaining components (WriteChatContextInjector + WorldImportExport + characters/* 5 + factions/* 3) — potential future Phase 65+
- 下一步候选: ff-merge + continue component coverage OR 切回 ARCHDEBT

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/WorldTabs.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/WorldTabs.vue`
- Phase 63 (precedent): `apps/dashboard/tests/unit/utils/creationModeHint.spec.ts`
- Phase 117 (World page impl): WorldTabs.vue + WorldImportExport.vue + WorldProposalInbox.vue
