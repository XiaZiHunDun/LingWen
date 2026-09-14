# Phase 68 — CharacterList.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 67 (FactionDetail tests) + Phase 8.30 (Pinia global setup)
> **目标**: Add 6 vitest tests for `apps/dashboard/src/components/world/characters/CharacterList.vue`

## 1. 背景

Phase 64-67 closed 6 of 12 untested World/WriteWorkspace components. Phase 68 picks CharacterList (MEDIUM complexity — requires Pinia store + composable mock + 2 child stubs).

Picked over `CharacterDetail` (requires CharacterRelationships/Editor stubs which we haven't tested), `CharacterEditor` (form handling), `CharacterRelationships` (likely complex), `FactionGraph`/`FactionGraphCanvas` (vis-network graph viz).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-68): CharacterList.vue unit tests (6 tests) | 1 | +94 |

**Net**: +6 vitest tests, v54.8 (no bump), 1934/1935 full vitest.

## 3. Test design (6 tests)

### Setup pattern
- `vi.mock` `useWorldDb` → listCharacters fixture
- `vi.mock` CharacterCard + CharacterDetail → stub components (isolate from child logic)
- Real `useWorldStore` (Pinia set up globally via `tests/unit/setup.ts`)
- `beforeEach` creates fresh Pinia + resets mock

### Filter buttons (4 tests)
- 3 buttons rendered (Draft/Provisional/Established) with stable testids
- Active class applied to current filter (via store.canonLevelFilter)
- Click inactive filter → activates it (store updates)
- Click active filter → clears it (toggles to null)

### Characters + selection (2 tests)
- listCharacters called on mount
- Click character card → sets store.selectedCharacterId

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/characters/CharacterList.spec.ts` | 6 passed | ✅ 6/6 in 1.33s |
| G2 | `pnpm test` (full vitest) | 1935 passed (1 pre-existing skip) | ✅ 1934/1935 |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CharacterList rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Pinia global setup (Phase 8.30 reuse)**: `tests/unit/setup.ts` already calls `setActivePinia(createPinia())` once per test file. Spec just needs `beforeEach(() => setActivePinia(createPinia()))` for fresh state. Pattern reused from `useWorldStore.spec.js`.
2. **Stub child components to isolate behavior**: CharacterList depends on CharacterCard + CharacterDetail. Stubbing them as `defineComponent({ template: '<button @click="$emit(\'click\')">...' })` keeps the spec focused on CharacterList's filter + selection logic, not child behavior. The stubs still emit `click` so CharacterList's selection flow can be verified end-to-end.
3. **Stub data-testid with dynamic bindings**: Stub component template uses `:data-testid="`stub-card-${character.slug}`"` so test selectors remain stable across stub vs real component swap. When CharacterCard test is added later, the stubs can be deleted without changing test assertions.

## 7. Carryover

- ✅ 7 of 12 untested components covered (58%)
- 新增: 5 remaining (CharacterDetail/CharacterEditor/CharacterRelationships + FactionGraph/FactionGraphCanvas)
- CharacterDetail still depends on CharacterRelationships + CharacterEditor stubs (chain)
- FactionGraph/FactionGraphCanvas likely need vis-network mocks (Phase 118 lesson)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/characters/CharacterList.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/characters/CharacterList.vue`
- Pinia setup: `apps/dashboard/tests/unit/setup.ts` (Phase 8.30)
- Phase 8.43.3: test-utils 2.4+ enableAutoUnmount (afterEach auto-unmount)
- Phase 66 + 67 (precedents): CharacterCard + FactionDetail test patterns
