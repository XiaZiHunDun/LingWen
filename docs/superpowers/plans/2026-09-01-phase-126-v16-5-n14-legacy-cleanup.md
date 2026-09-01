# Phase 126 v16.5 #N.14 — Legacy Pattern Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 5 carryover items from v16.5 #N.13 §"Carryover to v16.5 #N.14+": barrel-import migration, dead code removal, `has_body` drift, knip cleanup, and inline-shape casts.

**Architecture:** Each carryover is independent — atomic 1-commit per item (per DP-06 strict). Investigation findings in design doc drive concrete steps. Primary verification gate: `pnpm tsc --noEmit` + `pnpm vitest run` + `pnpm exec knip`.

**Tech Stack:** Vue 3 + TypeScript strict / Pydantic v2 (lingwen-shared) / vitest / vue-tsc / ruff / hand-rolled JSON Schema → TS codegen / knip

**Reference spec:** [`../specs/2026-09-01-phase-126-v16-5-n14-legacy-cleanup-design.md`](../specs/2026-09-01-phase-126-v16-5-n14-legacy-cleanup-design.md)

---

## Worktree Setup

- [ ] **Step 1: Create worktree + branch**

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-126-v16-5-n14 -b phase-126-v16-5-n14 master
cd .worktrees/phase-126-v16-5-n14
```

- [ ] **Step 2: Sync uv workspace + install test deps (per MEMORY.md N.11.d/e/g gotcha)**

```bash
uv sync --all-packages
uv pip install pytest psutil
```

- [ ] **Step 3: Verify baseline tests pass**

```bash
cd apps/dashboard && pnpm install
pnpm vitest run --reporter=basic 2>&1 | tail -5  # expected: 1763 passed + 1 skipped
pnpm tsc --noEmit                                # expected: 0 errors
pnpm exec knip --reporter compact 2>&1 | tail -10 # expected: 2 unused exports
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared
```

Expected: 1763 vitest passed, 0 vue-tsc errors, 134 shared tests passed, knip 2 unused exports.

---

## Task T1: `useCreatorWrite.js` barrel migration

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWrite.js` (lines 132-143)
- Possibly Modify: `apps/dashboard/tests/unit/use-creator-write.spec.ts` (mock target updates if needed)

- [ ] **Step 1: Read barrel-import + context**

```bash
sed -n '130,150p' apps/dashboard/src/composables/useCreatorWrite.js
```

Confirm: function `recheckChapterP0` uses `await import('../api/index.js')` to get `runCreatorLogicCheck`.

- [ ] **Step 2: Read typed wrapper signature**

```bash
grep -n -B 1 -A 8 "runCreatorLogicCheck" apps/dashboard/src/api/content.ts
```

Signature: `runCreatorLogicCheck(chapter?: number) → Promise<CreatorLogicCheckResponse>`.

- [ ] **Step 3: Apply migration**

Edit `useCreatorWrite.js`:
```js
// Before (top of file): no static import for runCreatorLogicCheck
// Inside function:
async function recheckChapterP0(chapter) {
    try {
      const { runCreatorLogicCheck } = await import('../api/index.js');
      const result = await runCreatorLogicCheck({ chapter, scope: 'p0' });
      chapterRecheckResult.value = result;
      ...
```

```js
// After:
// Add at top of file (near other static imports):
import { runCreatorLogicCheck } from '@/api/content';

// Inside function:
async function recheckChapterP0(chapter) {
    try {
      // v16.5 #N.14 T1: migrate from barrel `await import('../api/index.js')`
      // to typed wrapper. Legacy call passed `{ chapter, scope: 'p0' }`;
      // backend ignores scope (default behavior). Typed-wrapper signature
      // accepts `chapter?: number` matching real backend contract.
      const result = await runCreatorLogicCheck(chapter);
      chapterRecheckResult.value = result;
      ...
```

- [ ] **Step 4: Verify vue-tsc + vitest**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 0 errors, 1763 passed (no NEW tests, 0 regression).

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add apps/dashboard/src/composables/useCreatorWrite.js
git commit -m "refactor(dashboard): N.14 T1 useCreatorWrite.js runCreatorLogicCheck migrate from barrel to typed wrapper"
```

---

## Task T2: `useCreatorSettings.js` dead-code removal

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings.js` (lines 413-424)

- [ ] **Step 1: Verify zero callers of `publishMergePresetToFactory`**

```bash
grep -rn "publishMergePresetToFactory" apps/dashboard/src apps/dashboard/tests
```

Expected: only the function definition + dynamic self-import inside it (no callers).

- [ ] **Step 2: Search for template bindings**

```bash
grep -n "publishMergePresetToFactory\|mergePresetFactoryPublishing\|factoryPublish" apps/dashboard/src/composables/useCreatorSettings.js
grep -rn "publishMergePreset\|factoryPublish" apps/dashboard/src/components apps/dashboard/src/pages
```

Confirm: no UI button or template binding calls this function.

- [ ] **Step 3: Delete the function + cleanup refs**

Edit `useCreatorSettings.js`:
- Remove the `publishMergePresetToFactory` function (lines 413-424).
- Remove `mergePresetFactoryPublishing` ref declaration if it has no other users (check usage first).

- [ ] **Step 4: Verify vue-tsc + vitest**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 0 errors, 1763 passed.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add apps/dashboard/src/composables/useCreatorSettings.js
git commit -m "refactor(dashboard): N.14 T2 useCreatorSettings publishMergePresetToFactory dead code removed (parallel to N.13 T3.P2.c)"
```

---

## Task T3: `has_body` Pydantic field addition (Plan A)

**Decision**: Plan A — add `has_body` to `ChapterData` Pydantic so wire layer includes the field (data layer already produces it; Pydantic drops via `extra="ignore"`).

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py` (ChapterData class)
- Regenerate: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/health.ts` via codegen
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` (drop 2 casts)
- Add test: `packages/lingwen-shared/tests/test_health_dto.py` (field assertion)

- [ ] **Step 1: Add `has_body: bool = False` to ChapterData**

Edit `health.py` (around line 91):
```python
class ChapterData(BaseModel):
    """Per-chapter hook / coolpoint statistics."""

    model_config = ConfigDict(extra="ignore")

    chapter: int
    has_body: bool = False  # NEW (v16.5 #N.14 T3): present in source dict but Pydantic was dropping
    hook_count: int
    hook_strength_avg: float
    coolpoint_count: int
    coolpoint_density: float
```

- [ ] **Step 2: Regenerate TS codegen**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
python tooling/contracts/generate.py
```

Verify `packages/lingwen-shared/src/lingwen_shared/contracts/ts/health.ts` now has `has_body: boolean;` in `ChapterData`.

- [ ] **Step 3: Add backend test for `has_body` field**

Edit `packages/lingwen-shared/tests/test_health_dto.py`:
```python
def test_chapter_data_accepts_has_body():
    """v16.5 #N.14 T3: ChapterData must declare has_body so backend
    /api/chapters response includes the field (data layer already produces it)."""
    from lingwen_shared.contracts.python.health import ChapterData
    ch = ChapterData(
        chapter=1, has_body=True,
        hook_count=0, hook_strength_avg=0.0,
        coolpoint_count=0, coolpoint_density=0.0,
    )
    assert ch.has_body is True


def test_chapter_data_has_body_default_false():
    """Default False (legacy callers that don't set it still validate)."""
    from lingwen_shared.contracts.python.health import ChapterData
    ch = ChapterData(
        chapter=1,
        hook_count=0, hook_strength_avg=0.0,
        coolpoint_count=0, coolpoint_density=0.0,
    )
    assert ch.has_body is False
```

- [ ] **Step 4: Run backend tests**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared
```

Expected: 134 passed + 2 NEW = 136 passed.

- [ ] **Step 5: Run frontend vue-tsc (must still pass — codegen refreshes DTO) + vitest**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 0 errors, 1763 passed.

- [ ] **Step 6: Drop `as` casts in useProductExport**

Edit `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts`:

Lines 142-159 (resolveExportChapterNums — submission branch):
```typescript
// Before:
// v16.5 #N.13 T2.P1.d: fetchChapters() returns canonical
// `ChaptersResponse` from typed wrapper. `ChapterData` does NOT include
// `has_body` — backend never sends it — so the filter `c.has_body`
// always returns []. Pre-existing data-shape drift documented per
// v16.5 #7 §5 lesson 2; runtime behavior unchanged.
const resp = await fetchChapters();
const chapters = resp.chapters as Array<{
  chapter: number;
  has_body?: boolean;
}>;
const nums = chapters
  .filter((c) => c.has_body)
  .map((c) => c.chapter);
```

```typescript
// After:
// v16.5 #N.14 T3: ChapterData Pydantic now declares `has_body` — backend
// /api/chapters response includes it (data layer was producing it; Pydantic
// was dropping via extra="ignore"). Filter now functions as intended.
const resp = await fetchChapters();
const nums = resp.chapters
  .filter((c) => c.has_body)
  .map((c) => c.chapter);
```

Apply same pattern to lines 161-170 (non-submission branch).

- [ ] **Step 7: Re-run vitest (verify tests with `has_body: true` mocks still pass)**

```bash
cd apps/dashboard && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 1763 passed (mock data with `has_body: true` now flows through real filter).

- [ ] **Step 8: Commit (Python + TS codegen + frontend)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py \
        packages/lingwen-shared/src/lingwen_shared/contracts/ts/health.ts \
        packages/lingwen-shared/tests/test_health_dto.py
git commit -m "feat(lingwen-shared): N.14 T3 ChapterData declares has_body field (closes /api/chapters schema drift carryover)"

git add apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts
git commit -m "refactor(dashboard): N.14 T3 useProductExport fetchChapters 2 casts dropped via ChapterData.has_body"
```

---

## Task T4: `useWriteTools.ts` 2 cast sites cleanup

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts` (lines 87, 103)
- Modify: `apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts` deps contract (line 23)

- [ ] **Step 1: Read deps contract + cast sites**

```bash
sed -n '15,30p' apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts
echo "---"
sed -n '80,110p' apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts
```

Confirm: `overview: Ref<Record<string, unknown> | null>` and 2 cast sites reading `chapters` array.

- [ ] **Step 2: Define local type for chapter row**

Add at top of file (after imports):
```typescript
interface OverviewChapterRow {
  chapter: number;
  has_body?: boolean;
  has_outline?: boolean;
  word_count?: number;
}

interface OverviewShape {
  chapters?: OverviewChapterRow[];
}
```

- [ ] **Step 3: Widen deps contract**

Edit line 23:
```typescript
// Before:
overview: Ref<Record<string, unknown> | null>;

// After:
overview: Ref<OverviewShape | null>;
```

- [ ] **Step 4: Remove cast at line 87**

```typescript
// Before:
const overviewChapters = (overview.value as { chapters?: Array<{ chapter: number; has_body?: boolean }> } | null)?.chapters || [];

// After:
const overviewChapters = overview.value?.chapters || [];
```

- [ ] **Step 5: Remove cast at line 103**

```typescript
// Before:
const overviewChapters = (overview.value as { chapters?: Array<{ chapter: number; has_body?: boolean; has_outline?: boolean; word_count?: number }> } | null)?.chapters || [];

// After:
const overviewChapters = overview.value?.chapters || [];
```

- [ ] **Step 6: Verify the deps contract widening doesn't break callers**

```bash
cd apps/dashboard && pnpm tsc --noEmit
```

Expected: 0 errors. If a caller passes `Ref<Record<string, unknown> | null>`, vue-tsc will complain that the wider type isn't assignable to the narrower one — fix the caller's type if so.

- [ ] **Step 7: Verify vitest**

```bash
cd apps/dashboard && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 1763 passed.

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts
git commit -m "refactor(dashboard): N.14 T4 useWriteTools 2 inline-shape casts dropped via OverviewShape deps contract widening"
```

---

## Task T5: knip unused exports cleanup

**Files:**
- Modify: `apps/dashboard/src/api/studio.ts` (remove `listStudioProjects`)
- Modify: `apps/dashboard/src/api/volume.ts` (remove `listFactoryVolumeTemplates`)

### T5.1: Confirm zero consumers (double-check)

- [ ] **Step 1: Final consumer scan**

```bash
grep -rn "listStudioProjects" apps/dashboard/src apps/dashboard/tests
grep -rn "listFactoryVolumeTemplates" apps/dashboard/src apps/dashboard/tests
```

Expected: ZERO matches (only the export declaration site).

### T5.2: Delete `listStudioProjects`

- [ ] **Step 2: Read full function**

```bash
sed -n '25,45p' apps/dashboard/src/api/studio.ts
```

- [ ] **Step 3: Delete function + surrounding comments**

Edit `studio.ts` to remove lines 25-34 (function + 7 comment lines above).

### T5.3: Delete `listFactoryVolumeTemplates`

- [ ] **Step 4: Read full function**

```bash
sed -n '380,400p' apps/dashboard/src/api/volume.ts
```

- [ ] **Step 5: Delete function + surrounding comments**

Edit `volume.ts` to remove lines 386-391 (function + 4 comment lines above).

### T5.4: Verify

- [ ] **Step 6: Run knip**

```bash
cd apps/dashboard && pnpm exec knip --reporter compact 2>&1 | tail -15
```

Expected: 0 unused exports (other warnings unchanged).

- [ ] **Step 7: Run vue-tsc + vitest**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic 2>&1 | tail -3
```

Expected: 0 errors, 1763 passed.

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add apps/dashboard/src/api/studio.ts apps/dashboard/src/api/volume.ts
git commit -m "refactor(dashboard): N.14 T5 knip 2 unused exports deleted (listStudioProjects + listFactoryVolumeTemplates)"
```

---

## Task T6: Handoff + CLAUDE.md + MEMORY.md update

### T6.1: Final verification gate

- [ ] **Step 1: Frontend full gate**

```bash
cd apps/dashboard
pnpm vitest run --reporter=basic 2>&1 | tail -3   # expected: 1763 passed + 1 skipped
pnpm tsc --noEmit                                  # expected: 0 errors
pnpm eslint .                                      # expected: 0 errors
pnpm exec knip --reporter compact 2>&1 | tail -5   # expected: 0 unused exports
```

- [ ] **Step 2: Backend full gate**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared  # expected: 136 passed (+2 NEW)
ruff check packages/lingwen-shared/src/lingwen_shared/ apps/studio_api/  # expected: 0
```

- [ ] **Step 3: Architecture invariant #30 verification**

```bash
grep -rn "as unknown as" apps/dashboard/src/composables/ | grep -v "// N\." | wc -l
```

Expected: 0 (still zero runtime casts).

### T6.2: Write handoff doc

- [ ] **Step 4: Create handoff doc**

Create `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n14-legacy-cleanup-handoff.md` matching N.13 format:
- Summary
- Commits (list all 7-9)
- Architecture invariants verified
- Test results table
- Files changed
- Lessons learned
- Carryover to v16.5 #N.15+

### T6.3: Update CLAUDE.md + MEMORY.md

- [ ] **Step 5: Update root CLAUDE.md**

Add v16.5 #N.14 closure section at top of version history (after N.13 section), increment version line, note invariant #32 (#33 conditional) if added.

- [ ] **Step 6: Update MEMORY.md**

Update "Project State" section: version line + carryover list.

### T6.4: Commit + Push + Merge + Cleanup

- [ ] **Step 7: Commit handoff**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n14
git add docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n14-legacy-cleanup-handoff.md CLAUDE.md
git commit -m "docs(phase-126): N.14 legacy pattern cleanup handoff + CLAUDE.md"
```

Also commit MEMORY.md if updated:
```bash
git add ~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md 2>/dev/null
# OR for project-local MEMORY:
ls CLAUDE.local.md MEMORY.md 2>/dev/null
```

- [ ] **Step 8: Push branch + merge to master (direct merge per N.11.d/e/g + N.13 precedent)**

```bash
git push -u origin phase-126-v16-5-n14
cd /home/ailearn/projects/LingWen
git checkout master
git merge --no-ff phase-126-v16-5-n14 -m "Merge phase-126-v16-5-n14: legacy pattern cleanup + has_body drift + knip unused exports"
git push origin master
```

- [ ] **Step 9: Clean up worktree + branch**

```bash
git worktree remove .worktrees/phase-126-v16-5-n14
git branch -d phase-126-v16-5-n14
```

---

## Self-Review (per writing-plans skill checklist)

### 1. Spec coverage

| Spec section | Plan task |
|---|---|
| Item 1 (barrel migration) | T1 |
| Item 2 (dead code) | T2 |
| Item 3 (has_body drift) | T3 (Plan A) |
| Item 4 (knip cleanup) | T5 |
| Item 5 (inline-shape casts) | T4 |
| Architecture invariants | T6.1 verifies; T6.3 documents |
| Risk register | Per-task mitigation |
| Commit plan (6-9 commits) | T1-T5 = 6 commits + T6 = 1 commit = 7 |

### 2. Placeholder scan

No "TBD" / "TODO" / "implement later" / "fill in details". Investigation findings documented inline.

### 3. Type consistency

- `ChapterData`, `ChaptersResponse`, `has_body: bool` referenced consistently in T3
- `OverviewChapterRow`, `OverviewShape` referenced consistently in T4
- `runCreatorLogicCheck(chapter?: number)` signature consistent in T1

### 4. Ambiguity check

- "Verify vue-tsc + vitest" — exact commands provided
- "Delete function + surrounding comments" — line ranges specified
- "Widen deps contract" — before/after code provided
