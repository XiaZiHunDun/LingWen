# Phase 67 — FactionDetail.vue Tests Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 66 (WriteChatContextInjector + CharacterCard batch)
> **目标**: Add 6 vitest tests for `apps/dashboard/src/components/world/factions/FactionDetail.vue`

## 1. 背景

Phase 64-66 closed 5 of 12 untested World/WriteWorkspace components. Phase 67 picks the simplest remaining — `FactionDetail.vue` (60 LOC, pure presentational, no composables, no child components).

Picked over `CharacterDetail` (80 LOC, requires `useWorldDb` mock + CharacterRelationships stub + CharacterEditor stub) and `FactionGraph`/`FactionGraphCanvas` (vis-network graph viz, complex).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-67): FactionDetail.vue unit tests (6 tests) | 1 | +66 |

**Net**: +6 vitest tests, v54.8 (no bump), 1928/1929 full vitest.

## 3. Test design (6 tests)

### Render with valid faction (3 tests)
- Container `faction-detail` testid renders
- Faction name + description visible
- Close button emits `close` event

### Null fallback (3 tests)
- Container still renders when `faction=null`
- Description paragraph omitted when faction=null (via `v-if="faction"`)
- Close button still emits even when faction=null

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/factions/FactionDetail.spec.ts` | 6 passed | ✅ 6/6 in 1.32s |
| G2 | `pnpm test` (full vitest) | 1929 passed (1 pre-existing skip) | ✅ 1928/1929 |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- FactionDetail rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **Pick simple wins to maintain momentum**: After Phase 66's complex batch (13 tests with `it.each` + destructuring + Chinese comma tests), Phase 67 deliberately picks the simplest remaining component (60 LOC pure presentational, no mocks needed). Avoids over-engineering and maintains high success rate. Phase 53d lesson: small-step rapid-iteration preserves rigor without complexity creep.
2. **Optional prop null fallback worth testing explicitly**: FactionDetail defaults `faction: { default: null }`. The `v-if="faction"` branch must work for the null case (close button still emits even with no faction). 3 tests cover this state explicitly — future refactors that break null handling will be caught.

## 7. Carryover

- ✅ 6 of 12 untested components covered (50%)
- 新增: 6 remaining (CharacterDetail/CharacterEditor/CharacterList/CharacterRelationships + FactionGraph/FactionGraphCanvas)
- CharacterDetail/FactionGraph/FactionGraphCanvas are complex (multi-mock + vis-network)
- CharacterList requires Pinia store mock (medium)
- CharacterEditor likely form-heavy (medium-complex)
- CharacterRelationships likely complex

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/factions/FactionDetail.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/factions/FactionDetail.vue`
- Phase 66 (precedent batch): WriteChatContextInjector + CharacterCard
