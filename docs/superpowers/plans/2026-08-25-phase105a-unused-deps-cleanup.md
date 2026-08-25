# Phase 105a — Remove 3 Unused Dependencies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 3 truly-dead dependencies (`@vueuse/core`, `animate.css`, `vfonts`) from `apps/dashboard/package.json`. Drop the orphan `@import 'animate.css';` from `style.css`. Update `pnpm-lock.yaml`. Final knip category — `Unused dependencies (0)`.

**Architecture:** Three atomic commits — one per dep. Each commit: edit + `pnpm install` + verify + commit. Independent concerns; rollback can target any single dep.

**Tech Stack:** pnpm 9, Vue 3, knip 6.32.2.

---

## File Structure

**Files modified per commit:**
- Commit 1: `apps/dashboard/src/assets/style.css` (-1 line) + `apps/dashboard/package.json` (-1 line) + `pnpm-lock.yaml` (auto)
- Commit 2: `apps/dashboard/package.json` (-1 line) + `pnpm-lock.yaml` (auto)
- Commit 3: `apps/dashboard/package.json` (-1 line) + `pnpm-lock.yaml` (auto)

---

## Task 1: Pre-flight — git state + baselines

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `508cf489 docs(spec): Phase 105a — ...`. Tree clean.

- [ ] **Step 1.2: Confirm 3 deps are in `apps/dashboard/package.json`**

```bash
cd /home/ailearn/projects/LingWen && grep -nE '"(@vueuse/core|animate.css|vfonts)"' apps/dashboard/package.json
```

Expected: 3 lines (one per dep).

- [ ] **Step 1.3: Confirm `@import 'animate.css';` exists in `style.css:1`**

```bash
cd /home/ailearn/projects/LingWen && head -1 apps/dashboard/src/assets/style.css
```

Expected: `@import 'animate.css';`.

- [ ] **Step 1.4: Verify zero consumer refs for the 3 deps**

```bash
cd /home/ailearn/projects/LingWen && grep -rln "from ['\"]@vueuse/core" apps/dashboard/src --include="*.vue" --include="*.js" --include="*.ts" 2>/dev/null | head -3
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -rln "animate__" apps/dashboard/src --include="*.vue" --include="*.css" 2>/dev/null | head -3
```
Expected: zero matches.

```bash
cd /home/ailearn/projects/LingWen && grep -rln "vfonts" apps/dashboard/src --include="*.vue" --include="*.js" --include="*.ts" --include="*.json" 2>/dev/null | grep -v "package.json" | head -3
```
Expected: zero matches (only self-reference in package.json).

- [ ] **Step 1.5: Capture baseline knip + tests**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused dependencies"
```
Expected: `Unused dependencies (3)`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`. If red, STOP.

---

## Task 2: Commit 1 — Remove `animate.css` dep + drop `@import`

**Files:**
- Modify: `apps/dashboard/src/assets/style.css` (delete line 1)
- Modify: `apps/dashboard/package.json` (delete 1 devDep line)
- Auto: `pnpm-lock.yaml`

- [ ] **Step 2.1: Edit `style.css` — delete line 1**

Use Edit tool.

- **Find (old_string)** (line 1 + surrounding blank line context):
```

@import 'animate.css';
```
(The blank line on the line preceding @import is currently empty; the @import is at line 1; font-face declarations follow at line 2 onward.)

- **Replace (new_string)**:
```

```

(empty — removes both the blank line above and the @import)

If line numbers differ (e.g., if style.css has changed), use `head -5 apps/dashboard/src/assets/style.css` to confirm exact text. The Edit must result in style.css starting with `@font-face {` (or the actual content that was at line 2).

- [ ] **Step 2.2: Verify `@import` removed**

```bash
cd /home/ailearn/projects/LingWen && head -3 apps/dashboard/src/assets/style.css && grep "animate" apps/dashboard/src/assets/style.css
```
Expected: no `animate` string in style.css; head shows font-face declarations immediately.

- [ ] **Step 2.3: Edit `apps/dashboard/package.json` — delete animate.css line**

Use Edit tool.

- **Find (old_string)** (lines 36-39 region):
```
    "@vueuse/core": "^14.3.0",
    "animate.css": "^4.1.1",
```

- **Replace (new_string)**:
```
    "@vueuse/core": "^14.3.0",
```

(Keep `@vueuse/core` line; remove `animate.css` line + adjust comma.)

If exact text differs (e.g., different version), use `grep -n "animate" apps/dashboard/package.json` first to find exact location.

- [ ] **Step 2.4: Verify package.json valid JSON**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('apps/dashboard/package.json'));print('OK, animate.css in deps:', 'animate.css' in d.get('dependencies', {}))"
```
Expected: `False`.

- [ ] **Step 2.5: Run `pnpm install` to update lockfile**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install
```

Expected: install completes. Per Phase 102.2 finding, pnpm 9 may update root `pnpm-lock.yaml` rather than apps/dashboard/pnpm-lock.yaml. Note any changes.

- [ ] **Step 2.6: Verify lockfile updated**

```bash
cd /home/ailearn/projects/LingWen && grep -E "animate\.css" apps/dashboard/package.json pnpm-lock.yaml 2>/dev/null
```
Expected: zero matches (animate.css fully removed).

- [ ] **Step 2.7: Verify knip after Commit 1**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused dependencies"
```
Expected: `Unused dependencies (2)` (animate.css removed; @vueuse/core + vfonts remain).

- [ ] **Step 2.8: Verify tests + build still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```
Expected: build OK.

- [ ] **Step 2.9: Commit 1**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/src/assets/style.css apps/dashboard/package.json && git status
```
Expected: 2 files staged (style.css + package.json; lockfile may or may not be auto-modified).

If lockfile was modified by pnpm install, also stage it:
```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/package.json && git status
```

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): remove unused animate.css dep (Phase 105a)" -m "Phase 105a — resolve knip Unused dependencies (1 of 3):

- Delete \`animate.css\` from apps/dashboard/package.json devDeps
- Delete \`@import 'animate.css';\` from
  apps/dashboard/src/assets/style.css:1 (the @import was the only
  consumer, but no \`animate__*\` class names are used in any
  template, so the CSS rules were loaded but never applied)
- pnpm install auto-updates pnpm-lock.yaml

Verified:
- pnpm knip: Unused dependencies 3 → 2 (animate.css removed)
- pnpm test: 1545/1545 passed
- Style.css no longer references animate.css
- Build OK, lint clean

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md"
```

- [ ] **Step 2.10: Do NOT push yet** — wait for Commit 2.

---

## Task 3: Commit 2 — Remove `@vueuse/core`

**Files:**
- Modify: `apps/dashboard/package.json` (delete 1 devDep line)
- Auto: `pnpm-lock.yaml`

- [ ] **Step 3.1: Edit `package.json`**

Use Edit tool.

- **Find (old_string)**:
```
    "@vueuse/core": "^14.3.0",
```

- **Replace (new_string)**:
```
```

(empty — removes the entire line)

If the previous commit removed `animate.css` and now `@vueuse/core` is the first dep, it might look like:
```
    "@vueuse/core": "^14.3.0",
    "axios": "^1.7.0",
```

The Edit above removes the `@vueuse/core` line + trailing comma.

- [ ] **Step 3.2: Verify package.json valid JSON**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('apps/dashboard/package.json'));print('OK, @vueuse/core in deps:', '@vueuse/core' in d.get('dependencies', {}))"
```
Expected: `False`.

- [ ] **Step 3.3: Run `pnpm install`**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install
```

- [ ] **Step 3.4: Verify lockfile updated**

```bash
cd /home/ailearn/projects/LingWen && grep "@vueuse" apps/dashboard/package.json pnpm-lock.yaml 2>/dev/null
```
Expected: zero matches.

- [ ] **Step 3.5: Verify knip after Commit 2**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused dependencies"
```
Expected: `Unused dependencies (1)` (only vfonts remains).

- [ ] **Step 3.6: Tests pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

- [ ] **Step 3.7: Commit 2**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/package.json && git status
```

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): remove unused @vueuse/core dep (Phase 105a)" -m "Phase 105a — resolve knip Unused dependencies (2 of 3):

- Delete \`@vueuse/core\` from apps/dashboard/package.json devDeps
- pnpm install auto-updates pnpm-lock.yaml

Verified via grep: 0 imports of @vueuse/core across apps/dashboard/src
(case-insensitive grep returns zero matches in .js/.ts/.vue files).

Verified:
- pnpm knip: Unused dependencies 2 → 1 (@vueuse/core removed)
- pnpm test: 1545/1545 passed

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md"
```

- [ ] **Step 3.8: Do NOT push yet** — wait for Commit 3.

---

## Task 4: Commit 3 — Remove `vfonts` (final dep)

**Files:**
- Modify: `apps/dashboard/package.json` (delete 1 devDep line)
- Auto: `pnpm-lock.yaml`

- [ ] **Step 4.1: Edit `package.json`**

Use Edit tool.

- **Find (old_string)** — locate vfonts line in current state (use `grep -n vfonts apps/dashboard/package.json` first if needed):
```
    "vfonts": "^0.0.3",
```

- **Replace (new_string)**:
```
```

(empty — removes the entire line)

- [ ] **Step 4.2: Verify package.json valid JSON**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('apps/dashboard/package.json'));print('OK, vfonts in deps:', 'vfonts' in d.get('dependencies', {}))"
```
Expected: `False`.

- [ ] **Step 4.3: Run `pnpm install`**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm install
```

- [ ] **Step 4.4: Verify lockfile updated**

```bash
cd /home/ailearn/projects/LingWen && grep "vfonts" apps/dashboard/package.json pnpm-lock.yaml 2>/dev/null
```
Expected: zero matches.

- [ ] **Step 4.5: Verify knip after Commit 3 — ALL CATEGORIES ZERO**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected: NO lines starting with `Unused` or `Unlisted` (all categories at 0). If anything shows, STOP.

- [ ] **Step 4.6: Tests pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

- [ ] **Step 4.7: Build, tsc, lint**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```
Expected: build OK.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -3
```
Expected: 0 errors.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run lint:all 2>&1 | tail -3
```
Expected: clean.

- [ ] **Step 4.8: Commit 3**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/package.json && git status
```

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): remove unused vfonts dep (Phase 105a)" -m "Phase 105a — resolve knip Unused dependencies (3 of 3, final):

- Delete \`vfonts\` from apps/dashboard/package.json devDeps
- pnpm install auto-updates pnpm-lock.yaml

Verified via grep: 0 imports of vfonts across apps/dashboard/src
(only self-reference in package.json).

Verified:
- pnpm knip: Unused dependencies 1 → 0 (final — knip gate clean)
- pnpm test: 1545/1545 passed

Effect: all knip categories are now zero (Unused exports/files/types/
devDeps/dependencies/Unlisted binaries/Duplicate exports). CI knip
gate will PASS end-to-end.

Refs: docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md"
```

- [ ] **Step 4.9: Push all 3 commits to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```
Expected: push succeeds with 3 new commits.

- [ ] **Step 4.10: Final state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```
Expected: 5 most recent commits include 3 Phase 105a commits. Tree clean.

---

## Task 5: Final verification — Phase 105a complete

**Files:**
- Read-only verification.

- [ ] **Step 5.1: Final knip state — all categories zero**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```
Expected: NO lines starting with `Unused` or `Unlisted`. This proves all 7 knip categories are clean.

- [ ] **Step 5.2: 1545 tests pass (re-confirm)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

- [ ] **Step 5.3: No stale refs to the 3 deps anywhere**

```bash
cd /home/ailearn/projects/LingWen && grep -rln "@vueuse/core\|animate\.css\|vfonts" apps/dashboard/src apps/dashboard/tests --include="*.vue" --include="*.js" --include="*.ts" --include="*.css" --include="*.json" 2>/dev/null | grep -v node_modules
```
Expected: zero matches. If any match (e.g., historical docs), STOP and investigate.

---

## Success Criteria

- [ ] `apps/dashboard/src/assets/style.css` no longer has `@import 'animate.css';`
- [ ] `apps/dashboard/package.json` no longer has `@vueuse/core`, `animate.css`, or `vfonts`
- [ ] Lockfile updated (3 entries removed across root + apps/dashboard)
- [ ] `pnpm exec knip` reports all 7 categories = 0 (no `Unused` or `Unlisted` lines)
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Three atomic commits on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD~2..HEAD --no-edit && git push origin master
```

Reverts all 3 commits. No data loss.

Per-commit rollback if needed:
- Commit 1 only: `git revert HEAD~2 --no-edit`
- Commit 2 only: `git revert HEAD~1 --no-edit`
- Commit 3 only: `git revert HEAD --no-edit`

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Change Set → Task 2 (animate.css + style.css) + Task 3 (@vueuse/core) + Task 4 (vfonts) ✅
- §4.5 Verification → Task 5 ✅
- §7 Commit Strategy (3 commits) → Task 2.9 + Task 3.7 + Task 4.8 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only dep removals + 1 line @import removal.

**Edge cases handled**:
- Task 1.2 confirm 3 deps in package.json — catch scope drift
- Task 1.4 zero consumers — catch accidental consumer
- Task 1.5 baseline (3 unused) — catch pre-existing drift
- Task 2.2 verify @import removed (don't just remove from package.json)
- Task 2.7 intermediate knip (2 after Commit 1) — verify progress
- Task 3.5 intermediate knip (1 after Commit 2) — verify progress
- Task 4.5 final knip state — ALL categories zero (primary success)
- Task 5.3 grep no stale refs — catch missed cleanup
- Rollback section with per-commit granularity