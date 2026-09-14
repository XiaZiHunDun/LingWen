# Phase 69 — CharacterDetail.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 68 (CharacterList tests) + Phase 66 (CharacterCard tests)
> **目标**: Add 8 vitest tests for `apps/dashboard/src/components/world/characters/CharacterDetail.vue`

## 1. 背景

Phase 64-68 closed 7 of 12 untested World/WriteWorkspace components. Phase 69 picks `CharacterDetail.vue` (~80 LOC) — the closeable character sidebar with embedded CharacterRelationships + conditional CharacterEditor.

Picked over CharacterEditor (form handling complexity), CharacterRelationships (nested), FactionGraph/FactionGraphCanvas (vis-network).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-69): CharacterDetail.vue unit tests (8 tests) | 1 | +134 |

**Net**: +8 vitest tests, v54.8 (no bump), 1942/1943 full vitest.

## 3. Test design (8 tests)

### Setup
- `vi.mock` useWorldDb → getCharacter fixture
- `vi.mock` CharacterRelationships + CharacterEditor → stubs (data-testid + data-character-id attrs for assertions)

### Render (4 tests)
- Container testid renders
- Name/slug/canon_level visible after data resolves; loading indicator cleared
- JSON-stringified attributes rendered (pre block)
- Embedded CharacterRelationships stub present with characterId prop

### States (2 tests)
- Loading indicator shown while getCharacter pending (`mockReturnValue(new Promise(()=>{}))`)
- No character section when getCharacter resolves null

### Interactions (2 tests)
- Close button emits `close` event
- Edit toggle mounts/unmounts CharacterEditor stub (editing=true/false)

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/characters/CharacterDetail.spec.ts` | 8 passed | ✅ 8/8 in 1.28s |
| G2 | `pnpm test` (full vitest) | 1943 passed (1 pre-existing skip) | ✅ 1942/1943 in 20.47s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CharacterDetail rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Contradictory assertion regression (Phase 64 v2)**: First test version had `expect(...).toContain('加载中')` followed by `expect(...).not.toContain('加载中')` — both can't pass simultaneously. Phase 64 lesson 1 (forEach branch conflict) was a different flavor but same anti-pattern: copy-paste leftover assertion. Fixed by deleting the contradictory `toContain` line.
2. **`new Promise(()=>{})` for never-resolving**: Standard pattern for testing loading state without timing/flakiness. Resolves only when test ends, so loading state is observed at assertion time. Alternative `setTimeout` would be flaky.
3. **Stub `data-character-id` attribute**: CharacterRelationships stub template includes `:data-character-id="characterId"` so tests can verify the prop was correctly passed. Same pattern as Phase 68 CharacterList stub for `data-testid`.

## 7. Carryover

- ✅ 8 of 12 untested components covered (67%)
- 新增: 4 remaining (CharacterEditor/CharacterRelationships + FactionGraph/FactionGraphCanvas)
- CharacterEditor: form handling + WorldDb mock
- CharacterRelationships: nested WorldDb mock
- FactionGraph/FactionGraphCanvas: vis-network mocks (per MEMORY Phase 118 lesson)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/characters/CharacterDetail.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/characters/CharacterDetail.vue`
- Phase 68 (precedent): CharacterList stub pattern
- Phase 66 (precedent): CharacterCard test pattern
- Phase 8.30 (Pinia global setup): not needed here (CharacterDetail doesn't use Pinia)
