# Phase 66 — WriteChatContextInjector + CharacterCard Tests Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 65 (WorldImportExport.vue) + Phase 64 (WorldTabs.vue)
> **目标**: Batch-test 2 more of the 10 untested components — WriteChatContextInjector (36 LOC) + CharacterCard (62 LOC)

## 1. 背景

Phase 64 + 65 closed 2 of 10 untested World/WriteWorkspace top-level components. Phase 66 batches 2 more:
- `WriteChatContextInjector.vue` (36 LOC) — Write Workspace chat flow context metadata (4 chips, 2 optional)
- `CharacterCard.vue` (~62 LOC) — World page character summary (3 canon_level CSS variants)

## 2. 提交结构 (1 atomic commit + sync)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | (HEAD) | test(phase-66): WriteChatContextInjector + CharacterCard tests (13 tests) | 2 | +204 |

**Net**: +13 vitest tests, v54.8 (no bump), 1922/1923 full vitest.

## 3. Test design (13 tests)

### WriteChatContextInjector (6 tests)
- Render with full context (3): container testid, all 4 chips visible, characters joined with Chinese comma
- Optional chip conditional rendering (3): empty array hides chip, missing key hides chip, falsy prev_chapter_tail hides chip

### CharacterCard (7 tests)
- Render (3): name/canon_level/status, status omitted when missing, slug-derived testid
- canon_level variant (3 via `it.each`): draft / provisional / established CSS class
- Click emission (1): click emits 'click' event

## 4. 验证 gates

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `pnpm test -- tests/unit/components/writeWorkspace/WriteChatContextInjector.spec.ts tests/unit/components/world/characters/CharacterCard.spec.ts` | 13 passed | ✅ 13/13 in 1.15s |
| G2 | `pnpm test` (full vitest) | 1923 passed (1 pre-existing skip) | ✅ 1922/1923 |
| G3 | No regression on existing 248 test files | all pass | ✅ |

## 5. Risk & Rollback

**Risk**: VERY LOW
- Pure test addition
- Both component behaviors unchanged
- 0 production code change

**Rollback**: `git revert HEAD` removes both spec files.

## 6. Lessons

1. **vitest `it.each` for parametrized variant testing**: CharacterCard canon_level has 3 variants (draft/provisional/established). Using `it.each([['draft', 'draft'], ['provisional', 'provisional'], ['established', 'established']])` expands to 3 tests from 1 spec definition. Cleaner than 3 separate `it()` blocks + matches the established Phase 53c-style parametrized pattern. Captured in Phase 53c G2 lesson.
2. **Chinese enumeration comma (`、`)**: WriteChatContextInjector uses `、` not `,` to join characters in scene. Test must verify the comma is `、` not `,` to catch copy-paste regressions. Pattern matches Phase 53c lesson on Unicode-aware testing.
3. **Destructuring with `void` for unused**: CharacterCard test uses `const { status, ...rest } = baseCharacter; void status;` to discard the unused destructured property without ESLint/TS6133 errors. Pattern from common TS strict-mode workaround.

## 7. Carryover

- ✅ 5 of 10 untested components covered (50%)
- 新增: 6 remaining (characters/CharacterDetail, CharacterEditor, CharacterList, CharacterRelationships + factions/FactionDetail, FactionGraph, FactionGraphCanvas — wait that's 7)
- Wait, recount: WorldTabs + WorldImportExport + WriteChatContextInjector + CharacterCard = 4 done, characters: CharacterDetail/Editor/List/Relationships = 4 remaining, factions: 3 remaining = **7 remaining** (I miscounted in CURRENT_STATUS.md, fixed here)
- 下一步候选: ff-merge + continue with 1 character detail (CharacterDetail likely next-best ROI)

## 8. References

- Specs (this commit):
  - `apps/dashboard/tests/unit/components/writeWorkspace/WriteChatContextInjector.spec.ts`
  - `apps/dashboard/tests/unit/components/world/characters/CharacterCard.spec.ts`
- Sources:
  - `apps/dashboard/src/components/writeWorkspace/WriteChatContextInjector.vue`
  - `apps/dashboard/src/components/world/characters/CharacterCard.vue`
- Phase 64 + 65 (precedents): WorldTabs + WorldImportExport
