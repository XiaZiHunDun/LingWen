# Phase 71 — CharacterEditor.vue Tests Handoff

> **日期**: 2026-09-14
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 70 (CharacterRelationships tests) + Phase 117 (World page implementation)
> **目标**: Add 8 vitest tests for `apps/dashboard/src/components/world/characters/CharacterEditor.vue`

## 1. 背景

Phase 64-70 closed 9 of 12 untested World/WriteWorkspace components. Phase 71 picks `CharacterEditor.vue` (65 LOC) — the form for proposing new characters via useWorldReview().submitProposal(). Most complex remaining component (v-model + form submit + payload validation).

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-71): CharacterEditor.vue unit tests (8 tests) | 1 | +130 |

**Net**: +8 vitest tests, v54.8 (no bump), 1956/1957 full vitest.

## 3. Test design (8 tests)

### Setup
- `vi.mock` useWorldReview → submitProposal fixture
- `beforeEach` resets mock

### Render (3 tests)
- Form + 4 inputs (slug/name/canon/notes) + submit button all present
- canon_level defaults to 'Draft'
- No success message before submission

### v-model (2 tests)
- slug input value updates on setValue
- name + notes inputs value update on setValue

### Submit (3 tests)
- submitProposal called with structured payload (kind='character.create' + payload object + source='human' + source_context)
- Success message renders with proposal id
- Empty notes string → null in payload (via `|| null`)

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/world/characters/CharacterEditor.spec.ts` | 8 passed | ✅ 8/8 in 1.22s |
| G2 | `pnpm test` (full vitest) | 1957 passed (1 pre-existing skip) | ✅ 1956/1957 in 20.38s |
| G3 | No regression | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- CharacterEditor rendering unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes the spec file.

## 6. Lessons

1. **`setValue()` for v-model input testing**: vitest's `setValue` on input/textarea/select updates the underlying v-model binding. Same pattern as Phase 68 character click — explicit interaction primitive.
2. **`trigger('submit')` not `trigger('click')`**: form submission via `<form @submit.prevent>` requires `trigger('submit')`, NOT clicking the submit button. The `submit` event is a form-level event fired on form submission, then propagates to the submit button. Phase 31 lesson applies.
3. **Empty string → null conversion (`|| null`)**: Test 8 verifies the `draft.notes || null` fallback — if a future refactor changes this to `draft.notes` (empty string), the test will fail, catching the API contract change.

## 7. Carryover

- ✅ 10 of 12 untested components covered (83%)
- 新增: 2 remaining (FactionGraph + FactionGraphCanvas — both vis-network graph viz)
- FactionGraph: graph viz + WorldDb
- FactionGraphCanvas: vis-network (per MEMORY Phase 118 — vis-network install required, complex)

## 8. References

- Spec: `apps/dashboard/tests/unit/components/world/characters/CharacterEditor.spec.ts` (this commit)
- Source: `apps/dashboard/src/components/world/characters/CharacterEditor.vue`
- Phase 70 (sibling): CharacterRelationships test pattern
- Phase 68 (precedent): setValue + setProps patterns
