# Phase 105b — Spec Doc Accuracy Cleanup + Delete Stale Lockfile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct 4 categories of spec/plan doc inaccuracies + delete the stale `apps/dashboard/pnpm-lock.yaml` artifact. Future phases won't have to re-research these facts.

**Architecture:** Single atomic commit. 6 textual corrections across 6 files + 1 file deletion. All changes are doc-only or removing a stale artifact.

**Tech Stack:** pnpm 9, knip 6.32.2 (no code logic changes).

---

## File Structure

**Files modified (6):**
- `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`
- `docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md`
- `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md`
- `docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md`
- `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md`
- `docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md`

**Files deleted (1):**
- `apps/dashboard/pnpm-lock.yaml`

---

## Task 1: Pre-flight — git state + baseline

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `5bdf8ed5 docs(spec): Phase 105b — ...`. Tree clean.

- [ ] **Step 1.2: Confirm baseline inaccuracies exist**

```bash
cd /home/ailearn/projects/LingWen && grep -n "apps/dashboard/pnpm-lock.yaml" docs/superpowers/specs/2026-08-24-phase102.2-*.md docs/superpowers/plans/2026-08-24-phase102.2-*.md 2>/dev/null | head -3
```
Expected: multiple matches (the spec/plan reference this path).

```bash
cd /home/ailearn/projects/LingWen && grep -nE '"binaries" *: *\[' docs/superpowers/specs/2026-08-24-phase102.2-*.md docs/superpowers/plans/2026-08-24-phase102.2-*.md 2>/dev/null | head -3
```
Expected: multiple matches (the docs use wrong field name).

```bash
cd /home/ailearn/projects/LingWen && grep -n "22 dead type\|22 dead type declaration" docs/superpowers/specs/2026-08-25-phase104-*.md docs/superpowers/plans/2026-08-25-phase104-*.md 2>/dev/null | head -3
```
Expected: matches showing stale `22` counts.

```bash
cd /home/ailearn/projects/LingWen && grep -n "refactor(cleanup):" docs/superpowers/specs/2026-08-25-phase105a-*.md docs/superpowers/plans/2026-08-25-phase105a-*.md 2>/dev/null | head -3
```
Expected: matches showing wrong commit subject prefix.

```bash
cd /home/ailearn/projects/LingWen && test -f apps/dashboard/pnpm-lock.yaml && wc -c apps/dashboard/pnpm-lock.yaml
```
Expected: file exists, ~166844 bytes (per Phase 105a reviewer note).

- [ ] **Step 1.3: Capture test + knip baseline (should be unchanged)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```
Expected: NO `Unused` or `Unlisted` lines (all 7 categories = 0 per Phase 105a).

---

## Task 2: Phase 102.2 spec + plan — fix `binaries` → `ignoreBinaries` + lockfile path

**Files:**
- Modify: 2 markdown files

- [ ] **Step 2.1: Edit spec file — replace 4 occurrences of `"binaries"` with `"ignoreBinaries"`**

```bash
cd /home/ailearn/projects/LingWen && sed -i 's|"binaries": \["knip"\]|"ignoreBinaries": ["knip"]|g' docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md
```

Verify with:
```bash
cd /home/ailearn/projects/LingWen && grep -nE '"binaries" *: *\[' docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -nE '"ignoreBinaries" *: *\[' docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md
```
Expected: at least 3 matches (where the original `"binaries": ["knip"]` was).

- [ ] **Step 2.2: Edit plan file — replace occurrences**

```bash
cd /home/ailearn/projects/LingWen && sed -i 's|"binaries"|"ignoreBinaries"|g' docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md
```

Note: this replaces bare `"binaries"` strings (not the array form). Verify with:
```bash
cd /home/ailearn/projects/LingWen && grep -n '"binaries"' docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -n '"ignoreBinaries"' docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md
```
Expected: at least 4 matches.

- [ ] **Step 2.3: Update lockfile path references**

The spec file has references like "Auto-update: `apps/dashboard/pnpm-lock.yaml`" — these should be updated to "root `pnpm-lock.yaml`" (since pnpm 9 workspace uses root lockfile). Edit by hand:

Open `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md` and replace:
- "apps/dashboard/pnpm-lock.yaml" → "root pnpm-lock.yaml"

Open `docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md` and replace:
- "apps/dashboard/pnpm-lock.yaml" → "root pnpm-lock.yaml"

Or use sed:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|apps/dashboard/pnpm-lock.yaml|root `pnpm-lock.yaml`|g' docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md docs/superpowers/plans/2026-08-24-phase102.2-clean-devDep-and-binary-config.md
```

Verify:
```bash
cd /home/ailearn/projects/LingWen && grep -n "apps/dashboard/pnpm-lock.yaml" docs/superpowers/specs/2026-08-24-phase102.2-*.md docs/superpowers/plans/2026-08-24-phase102.2-*.md
```
Expected: zero matches in both Phase 102.2 docs.

---

## Task 3: Phase 104 spec + plan — fix counts (10 → 33, 22 → 29)

**Files:**
- Modify: 2 markdown files

- [ ] **Step 3.1: Edit spec file — update counts**

Open `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md` and make these edits:

- Header line 5: `~27 individual type names` → `~27 individual type names (actual: 33 names / 29 dead declarations across 10 source files)`
- §1 Context line 12: `Unused exported types (10)` → `Unused exported types (10 — actual was 33)`
- §9 Success Criteria: `22 type declarations in 9 source files have \`export\` keyword removed` → `29 type declarations in 9 source files have \`export\` keyword removed`

Use sed where possible:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|Unused exported types (10)|Unused exported types (10 — actual was 33)|g; s|22 type declarations in 9 source files|29 type declarations in 9 source files|g' docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md
```

Verify:
```bash
cd /home/ailearn/projects/LingWen && grep -n "22 dead type\|22 type declarations\|Unused exported types (10)" docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md
```
Expected: zero matches for `22 dead type` and `22 type declarations`. `Unused exported types (10 — actual was 33)` may still appear (intentional correction).

- [ ] **Step 3.2: Edit plan file — update counts and commit subject**

Open `docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md` and make these edits:

- §Goal (line 5): "22 dead type declarations" → "29 dead type declarations"
- §Task 1.4 (line 77): `Unused exported types (10)` → actual `(33)`
- §Task 2.13 (line 186): "or 6 — 22 dead types → 4 test types remain" → "or 10 — 29 dead types → 4 test types remain"
- §Task 2.14 commit message: "refactor(cleanup): drop export from 22 dead type declarations" → "29 dead type declarations"
- §Task 2.14 body: "Drop `export` keyword from 22 type declarations" → "29 type declarations"

Use sed:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|drop export from 22 dead type declarations|drop export from 29 dead type declarations|g; s|22 dead type declarations|29 dead type declarations|g; s|22 type declarations|29 type declarations|g' docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md
```

Also update Task 1.4 expected output:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|Unused exported types (10)|Unused exported types (33)|g' docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md
```

And Task 2.13 expected:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|or 6 — 22 dead types → 4 test types remain|or 10 — 29 dead types → 4 test types remain|g' docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md
```

Verify:
```bash
cd /home/ailearn/projects/LingWen && grep -n "22 dead type\|22 type declarations\|Unused exported types (10)" docs/superpowers/plans/2026-08-25-phase104-unused-types-audit.md
```
Expected: zero matches for `22 dead type` / `22 type declarations`. `Unused exported types (10)` may remain (it's still mentioned in §Goal context).

---

## Task 4: Phase 105a spec + plan — fix commit subject prefix (`refactor(cleanup):` → `build(deps):`)

**Files:**
- Modify: 2 markdown files

- [ ] **Step 4.1: Edit spec file — update 3 commit subjects**

Use sed:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|`refactor(cleanup): remove unused animate.css dep (Phase 105a)`|`build(deps): remove unused animate.css dep (Phase 105a)`|; s|`refactor(cleanup): remove unused @vueuse/core dep (Phase 105a)`|`build(deps): remove unused @vueuse/core dep (Phase 105a)`|; s|`refactor(cleanup): remove unused vfonts dep (Phase 105a)`|`build(deps): remove unused vfonts dep (Phase 105a)`|' docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```

Verify:
```bash
cd /home/ailearn/projects/LingWen && grep -n "refactor(cleanup):" docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -n "build(deps):" docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md
```
Expected: 3 matches (animate.css, @vueuse/core, vfonts).

- [ ] **Step 4.2: Edit plan file — update 3 commit commands**

Use sed:
```bash
cd /home/ailearn/projects/LingWen && sed -i 's|"refactor(cleanup): remove unused animate.css dep (Phase 105a)"|"build(deps): remove unused animate.css dep (Phase 105a)"|; s|"refactor(cleanup): remove unused @vueuse/core dep (Phase 105a)"|"build(deps): remove unused @vueuse/core dep (Phase 105a)"|; s|"refactor(cleanup): remove unused vfonts dep (Phase 105a)"|"build(deps): remove unused vfonts dep (Phase 105a)"|' docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md
```

Verify:
```bash
cd /home/ailearn/projects/LingWen && grep -n "refactor(cleanup):" docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -n "build(deps):" docs/superpowers/plans/2026-08-25-phase105a-unused-deps-cleanup.md
```
Expected: 3 matches.

---

## Task 5: Delete stale `apps/dashboard/pnpm-lock.yaml`

**Files:**
- Delete: 1 file

- [ ] **Step 5.1: Verify the file is stale**

```bash
cd /home/ailearn/projects/LingWen && wc -c apps/dashboard/pnpm-lock.yaml
```
Expected: ~166844 bytes (Phase 17.2 artifact).

```bash
cd /home/ailearn/projects/LingWen && head -3 apps/dashboard/pnpm-lock.yaml
```
Expected: shows `lockfileVersion: 1` (npm format) or similar — confirming it's an npm-lock, not pnpm-lock.

- [ ] **Step 5.2: Delete the stale lockfile**

```bash
cd /home/ailearn/projects/LingWen && git rm apps/dashboard/pnpm-lock.yaml
```

Expected: `rm 'apps/dashboard/pnpm-lock.yaml'`.

Verify:
```bash
cd /home/ailearn/projects/LingWen && test ! -f apps/dashboard/pnpm-lock.yaml && echo "STALE LOCKFILE DELETED"
```
Expected: `STALE LOCKFILE DELETED`.

- [ ] **Step 5.3: Verify pnpm install no longer emits warning**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install 2>&1 | grep -i "lockfile\|apps/dashboard" | head -10
```
Expected: NO warning about apps/dashboard/pnpm-lock.yaml being ignored. (Or warning text that doesn't reference the deleted file.)

---

## Task 6: Stage all changes + commit + push

**Files:**
- Commit: 6 modified files + 1 deleted file

- [ ] **Step 6.1: Stage all changes**

```bash
cd /home/ailearn/projects/LingWen && git add -A && git status
```

Expected: 7 changes (6 modified + 1 deleted). Nothing else.

- [ ] **Step 6.2: Verify all grep checks per spec §4.3**

Run all 6 spec §4.3 grep checks:

```bash
cd /home/ailearn/projects/LingWen && grep -n "apps/dashboard/pnpm-lock.yaml" docs/superpowers/specs/2026-08-24-phase102.2-*.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -nE '"binaries" *: *\[' docs/superpowers/specs/2026-08-24-phase102.2-*.md docs/superpowers/plans/2026-08-24-phase102.2-*.md
```
Expected: zero matches in Phase 102.2 docs.

```bash
cd /home/ailearn/projects/LingWen && grep -n "22 dead type\|22 dead type declaration" docs/superpowers/specs/2026-08-25-phase104-*.md docs/superpowers/plans/2026-08-25-phase104-*.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -n "refactor(cleanup):" docs/superpowers/specs/2026-08-25-phase105a-*.md docs/superpowers/plans/2026-08-25-phase105a-*.md
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && test ! -f apps/dashboard/pnpm-lock.yaml && echo "STALE LOCKFILE DELETED"
```
Expected: `STALE LOCKFILE DELETED`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install 2>&1 | grep -i "apps/dashboard/pnpm-lock.yaml is ignored" | head -1
```
Expected: zero matches (no warning about the deleted file).

- [ ] **Step 6.3: Verify tests still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

- [ ] **Step 6.4: Verify knip still zero**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```
Expected: zero matches (all categories still = 0).

- [ ] **Step 6.5: Commit**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "docs(spec): fix stale count + knip field + commit-subject inaccuracies (Phase 105b)" -m "Phase 105b — Phase 102.2 / 104 / 105a review follow-up housekeeping:

1. Phase 102.2 docs: correct 'binaries' → 'ignoreBinaries' (knip 6.32.2
   schema rejects 'binaries' field; implementer discovered and used the
   correct field 'ignoreBinaries'). Also correct lockfile path
   apps/dashboard/pnpm-lock.yaml → root pnpm-lock.yaml (pnpm 9 workspace
   uses root lockfile only; apps/dashboard/pnpm-lock.yaml is a stale
   Phase 17.2 artifact).

2. Phase 104 docs: correct 'Unused exported types (10) → (33)' and
   '22 dead type declarations → 29'. Per-file type lists were correct;
   only the headline counts were stale.

3. Phase 105a docs: correct commit subject prefix
   'refactor(cleanup):' → 'build(deps):' (more accurate — these are
   build-affecting dep changes; implementer chose correctly).

4. Delete apps/dashboard/pnpm-lock.yaml (Phase 17.2 npm-lock artifact,
   ignored by pnpm 9 workspace mode with a warning; safe to delete).

No code logic changes. 1545 tests still pass.

Refs:
- Phase 102.2 code-quality + spec-compliance review notes
- Phase 104 code-quality + spec-compliance review notes
- Phase 105a code-quality + spec-compliance review notes"
```

Expected: 1 commit created.

- [ ] **Step 6.6: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```
Expected: push succeeds.

- [ ] **Step 6.7: Final state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```
Expected: 3 commits visible. Tree clean.

---

## Success Criteria

- [ ] Phase 102.2 docs use `"ignoreBinaries"` and reference root `pnpm-lock.yaml`
- [ ] Phase 104 docs use counts `33` / `29`
- [ ] Phase 105a docs use commit subject prefix `build(deps):`
- [ ] `apps/dashboard/pnpm-lock.yaml` deleted
- [ ] All 6 grep checks per spec §4.3 return expected counts
- [ ] `pnpm install` no longer emits warning about apps/dashboard/pnpm-lock.yaml
- [ ] 1545 tests pass
- [ ] knip all categories = 0
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Edit 1-4 → Task 2-4 ✅
- §4.1 Delete 1 → Task 5 ✅
- §4.3 Verification → Task 6.2-6.4 ✅
- §7 Commit Strategy → Task 6.5-6.7 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only doc text corrections + 1 file deletion.

**Edge cases handled**:
- Task 1.2 baseline inaccuracies exist (catch scope drift)
- Task 1.3 baseline tests pass (no regressions before edits)
- Task 6.2 all 6 grep checks confirm corrections
- Task 6.3 tests pass after edits
- Task 6.4 knip still zero after edits
- Task 6.5 atomic commit
- Rollback section