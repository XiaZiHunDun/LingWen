# Phase 126 v16.5 #N.14 — Legacy Pattern Cleanup Design

> **Date**: 2026-09-01
> **Branch**: `phase-126-v16-5-n14`
> **Worktree**: `.worktrees/phase-126-v16-5-n14`
> **Predecessor**: v16.5 #N.13 (cast cleanup — closed at `247e5e2e`)

## Summary

Closes the 5 carryover items from N.13 §"Carryover to v16.5 #N.14+":

1. `useCreatorWrite.js` legacy barrel-import pattern (`runCreatorLogicCheck` via `await import('../api/index.js')`)
2. `useCreatorSettings.js:413` `publishMergePresetToFactory` dead code (parallel to N.13 T3.P2.c)
3. Pre-existing `has_body` drift — `/api/chapters` Pydantic model drops the field via `extra="ignore"`; frontend filter always returns `[]`
4. knip: 2 unused exports (`listStudioProjects` + `listFactoryVolumeTemplates`) + devDep/config hygiene
5. `useWriteTools.ts` 2 inline-shape casts at lines 87, 103

Each item is small and well-scoped. Estimated total: **5-7 commits**.

## Carryover Investigation Findings

### Item 1: `useCreatorWrite.js` barrel migration

**Original carryover claim**: "Similar legacy cast pattern at line 137 (1-2 casts)"

**Investigation finding**: N.13 handoff was inaccurate. Line 137 area contains ZERO `as unknown as` casts. Actual legacy pattern is a barrel dynamic-import:

```js
// apps/dashboard/src/composables/useCreatorWrite.js:136 (was 137)
async function recheckChapterP0(chapter) {
    try {
      const { runCreatorLogicCheck } = await import('../api/index.js');  // ← legacy barrel
      const result = await runCreatorLogicCheck({ chapter, scope: 'p0' });
```

**Fix**: Static import from typed wrapper `@/api/content` (already exists at `apps/dashboard/src/api/content.ts:96`).

```js
import { runCreatorLogicCheck } from '@/api/content';
async function recheckChapterP0(chapter) {
  try {
    const result = await runCreatorLogicCheck(chapter);  // typed-wrapper signature: chapter?: number
    chapterRecheckResult.value = result;
    ...
```

**Note**: typed-wrapper signature takes `chapter?: number` (not `{ chapter, scope }` object). The legacy call passed `{ chapter, scope: 'p0' }` — backend currently ignores scope (default behavior). Document this drift inline.

### Item 2: `useCreatorSettings.js:413` `publishMergePresetToFactory`

**Confirmed dead code** (parallel to N.13 T3.P2.c):

```js
// apps/dashboard/src/composables/useCreatorSettings.js:413-424
async function publishMergePresetToFactory() {
    mergePresetFactoryPublishing.value = true;
    try {
      const { publishMergePresetToFactory } = await import('@/api/settings');
      await publishMergePresetToFactory({});
      ...
```

Function exists, self-imports same-name function, no callers. **Mirror N.13 T3.P2.c deletion pattern**: delete function, no API-side change needed (already removed in N.13 T3.P2.c on `useMergePresets.js`).

### Item 3: `has_body` drift

**N.13 comment claim**: "backend never sends `has_body`"

**Investigation finding**: True at the wire layer but misleading. The data layer DOES produce `has_body`:

```python
# packages/lingwen-creator/src/lingwen_creator/content/dashboard.py:85,88
chapter_rows.append({
    ...
    "has_body": bool(body),  # ← data layer adds it
})
```

But the response model silently drops it:

```python
# packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py:85-91
class ChapterData(BaseModel):
    """Per-chapter hook / coolpoint statistics."""
    model_config = ConfigDict(extra="ignore")  # ← drops unknown fields silently
    chapter: int
    hook_count: int
    hook_strength_avg: float
    coolpoint_count: int
    coolpoint_density: float
    # ← no `has_body` declared

# packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py:98-103
class ChaptersResponse(BaseModel):
    chapters: list[ChapterData]
```

So `ChaptersResponse.chapters[i].has_body` is undefined on the wire → frontend filter `c.has_body` returns `undefined` → `filter()` gives `[]`.

**Decision: Option B (drop filter, remove casts)** per N.13 lesson 5 ("3+ tests depend on legacy shape" — drop the field rather than break fixtures; **counter**: actually 9+ test files pass `has_body` in mocks. But the *filter behavior* is the issue, not the field presence. Tests that pass `has_body: true` as fixture data aren't asserting the filter output specifically).

**Plan A (preferred)**: Add `has_body: bool` to `ChapterData` Pydantic. Backend data already produces it; just declare it. Frontend gets the field naturally; remove `as { has_body?: boolean }` casts.

**Plan B (fallback)**: Drop filter from frontend, keep DTO unchanged.

**Decision criteria**:
- If the filter is intended functionality (export chapter nums that have body) → Plan A
- If the filter is dead code (always `[]`) → Plan B

Per N.13 handoff: "Documented inline (TODO with v16.5 #N.14 carryover) rather than silently dropping". The original author wanted it to work → **Plan A** is the correct intent.

### Item 4: knip cleanup

**Confirmed unused exports** (zero callers in src/ + tests/):

| File:line | Export | Consumers |
|-----------|--------|-----------|
| `src/api/studio.ts:31` | `listStudioProjects` | 0 |
| `src/api/volume.ts:388` | `listFactoryVolumeTemplates` | 0 |

**Fix**: Delete both exports.

**knip config hint carryover** ("src/main.js redundant entry pattern") — investigation shows current knip output is:
- "Unlisted binaries (3)": `.husky/pre-commit` (lint-staged), `.lintstagedrc.json` (vitest, vue-tsc, tsc), `package.json` (vite, playwright, lint-staged, vitest, tsc, vue-tsc, husky)
- "Unused devDependencies (1)": `@vue/server-renderer`, `husky`, `lint-staged`, `vue-tsc`

The "Unlisted binaries" warning is a knip config issue (knip doesn't know about npm script binaries). Fix by adding to knip config OR leaving as advisory.

The "Unused devDependencies" includes false positives (`vue-tsc` IS used via npm script). Verify each before deleting.

**`@tiptap/pm`** flagged as unused dep — but it's a peer dep of `@tiptap/vue-3` + `@tiptap/starter-kit` (TipTapEditor.vue uses it transitively). **Do not delete** — knip false positive.

### Item 5: `useWriteTools.ts` 2 casts

```typescript
// apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts:87
const overviewChapters = (overview.value as { chapters?: Array<{ chapter: number; has_body?: boolean }> } | null)?.chapters || [];

// apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts:103
const overviewChapters = (overview.value as { chapters?: Array<{ chapter: number; has_body?: boolean; has_outline?: boolean; word_count?: number }> } | null)?.chapters || [];
```

**Fix**: `overview` is typed as `Ref<Record<string, unknown> | null>` (deps contract). Widen deps contract to `Ref<OverviewData | null>` where `OverviewData` is a typed interface (chapter rows: `chapter, has_body?, has_outline?, word_count?`). 

If `overview` is populated from `/api/creator/...` endpoint that DOES return `has_body` (separate from `fetchChapters`), this is a real `chapters` shape — create a `OverviewChapterRow` local type and use it.

## Architecture Invariants (no NEW; verify existing)

- **#30** Zero runtime `as unknown as` casts in `apps/dashboard/src/composables/` (preserved)
- **#32 (NEW candidate)** Backend `ChaptersResponse` includes `has_body` field — closes the wire-layer drift
- **#33 (NEW candidate)** knip unused exports count = 0 (closes pre-N.11 carryover)

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| T3 Pydantic `has_body` addition breaks consumer assumptions | MEDIUM | Backend `extra="ignore"` is forgiving; only consumers reading `chapters[i].has_body` are affected — frontend already reads it |
| T1 `runCreatorLogicCheck` signature change (legacy `{chapter, scope}` vs typed `chapter?`) | LOW | Backend ignores scope currently; typed wrapper matches real contract |
| T5 deps contract widening for `overview` | LOW | `overview` is internal to useCreatorWrite composable chain; no external API change |

## Test Strategy

- T1, T2, T4, T5: run existing vitest suite (no NEW test files needed — these are pure refactors)
- T3 (Plan A): backend shared test for `ChaptersResponse` + run frontend vitest to verify field now flows through

## Commit Plan (estimated 6 commits)

| # | Task | Files | Lines |
|---|------|-------|-------|
| 1 | T1 useCreatorWrite.js barrel migration | 1 | -3 / +2 |
| 2 | T2 useCreatorSettings.js publishMergePresetToFactory deletion | 1-2 | -15 |
| 3 | T3 has_body Pydantic addition (Plan A) | 3-4 (Python + TS codegen + frontend) | +3 |
| 4 | T4 useWriteTools.ts 2 cast sites | 1-2 | -2 / +6 |
| 5 | T5 knip 2 unused exports deletion | 2 | -20 |
| 5b | T5 knip config tightening (optional) | 1-2 | +5 |
| 6 | T6 handoff + CLAUDE.md + MEMORY.md | 3 | +100 |

Plus possibly:
- 5c: devDep cleanup (verify + delete unused) — only if verification confirms truly unused

## Carryover to v16.5 #N.15+

- `lingwen_quality` module missing (15 tests infra/, v15.7.1 debt)
- `plugin_manager.py:_discover_internal_providers` module path bug (v15.7.1 debt)
- knip "Unlisted binaries" / devDep warnings (if not addressed in N.14)
