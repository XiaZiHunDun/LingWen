# Phase 70 — CharacterRelationships.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 69 (CharacterDetail tests) + Phase 117 (World page implementation)
> **目标**: Add 6 vitest tests for `apps/dashboard/src/components/world/characters/CharacterRelationships.vue`

## 1. 背景

Phase 64-69 closed 8 of 12 untested World/WriteWorkspace components. Phase 70 picks `CharacterRelationships.vue` (53 LOC) — embedded relationships list inside CharacterDetail sidebar.

Picked over `CharacterEditor` (form handling complexity), `FactionGraph`/`FactionGraphCanvas` (vis-network graph viz). CharacterRelationships is simple list rendering.

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-70): CharacterRelationships.vue unit tests (6 tests) | 1 | +106 |

**Net**: +6 vitest tests, v54.8 (no bump), 1948/1949 full vitest.

## 3. Test design (6 tests)

### Setup
- `vi.mock` useWorldDb → listRelationships fixture
- `beforeEach` resets mock

### Container (1 test)
- testid + heading "关系" rendered

### Empty state (1 test)
- "暂无关系" message when relationships array empty
- No `<li>` items rendered

### Render list (3 tests)
- Each relationship renders with `kind → target_kind #target_id` format
- Notes in parentheses when present
- Notes span omitted when notes is empty (verifies the `v-if="rel.notes"`)

### Reload (1 test)
- listRelationships called with current characterId on prop change (immediate watcher)

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/characters/CharacterRelationships.spec.ts` | 6 passed | ✅ 6/6 in 1.29s |
| G2 | `pnpm test` (full vitest) | 1949 passed (1 pre-existing skip) | ✅ 1948/1949 in 20.73s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CharacterRelationships rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Direct `await setProps()` for watch re-trigger**: Test 5 uses `await wrapper.setProps({ characterId: 2 })` then re-asserts listRelationships called with the new characterId. `setProps()` returns a promise that resolves after Vue's reactivity cycle + any `immediate: true` watcher fires. Same pattern as Phase 64 WorldTabs lesson 2.
2. **Conditional rendering with empty string**: `v-if="rel.notes"` evaluates empty string as falsy. Test 4 (omits notes span when notes is empty) catches copy-paste regressions that might render `()` for empty strings. Pattern matches Phase 66 lesson 2 (Chinese comma awareness) — locale-sensitive rendering needs explicit assertions.
3. **Phase 69 stub can now be removed (optional)**: CharacterDetail.spec.ts mocks CharacterRelationships with a stub. Now that CharacterRelationships has its own real test (Phase 70), the stub could be removed in a future phase. Not urgent — the stub isolates CharacterDetail from CharacterRelationships changes, which is still a valid defensive pattern.

## 7. Carryover

- ✅ 9 of 12 untested components covered (75%)
- 新增: 3 remaining (CharacterEditor + FactionGraph + FactionGraphCanvas)
- CharacterEditor: form handling + WorldDb mock
- FactionGraph: graph viz + WorldDb
- FactionGraphCanvas: vis-network (per MEMORY Phase 118)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/characters/CharacterRelationships.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/characters/CharacterRelationships.vue`
- Phase 69 (parent test): CharacterDetail.spec.ts (uses CharacterRelationships stub)
- Phase 64 + 68 (precedents): `setProps()` reactivity + useWorldDb mock patterns
