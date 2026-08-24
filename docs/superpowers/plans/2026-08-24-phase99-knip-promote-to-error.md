# Phase 99 — Promote knip to Hard Error Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pnpm exec knip` a hard-blocking CI gate so any future knip finding fails the dashboard-frontend-ci workflow.

**Architecture:** Single 1-line edit to `.github/workflows/dashboard-frontend-ci.yml` — remove the `|| echo` non-blocking suffix and update the step name. No code, no knip.json changes, no tests. The "test" is the CI itself: next PR with a knip issue will fail the workflow.

**Tech Stack:** GitHub Actions YAML, knip 6.32.2, pnpm.

---

## File Structure

**Files modified (1):**
- `.github/workflows/dashboard-frontend-ci.yml` — modify the `Run knip` step (lines ~50 area)

**Files NOT created.** No tests, no config, no ignore entries.

---

## Task 1: Pre-flight — confirm git state + locate knip CI step

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -1 && git status
```

Expected: HEAD on commit `2c44c814 docs(spec): Phase 99 — promote knip to hard error design` (or later if spec amendment). Working tree clean.

- [ ] **Step 1.2: Locate the knip CI step**

```bash
cd /home/ailearn/projects/LingWen && grep -n -B 1 -A 2 "knip" .github/workflows/dashboard-frontend-ci.yml
```

Expected: a single match showing the current step:
```yaml
      - name: Run knip (dead-export detection, non-blocking)
        run: pnpm exec knip || echo "knip found issues (non-blocking — Phase 95)"
```

If the line numbers differ, use the actual line numbers found. The exact text is what matters.

- [ ] **Step 1.3: Confirm knip baseline is stable**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected (Phase 100 state):
```
Unused files (36)
Unused dependencies (1)
Unused devDependencies (1)
Unlisted binaries (1)
Unused exports (27)
```
With no `Duplicate` line (Phase 100 cleared those).

This is the baseline that will fail CI after the flip. If counts differ (e.g., a new issue appeared since Phase 100), STOP and report — the expected behavior is the same but the failure summary may need updating.

- [ ] **Step 1.4: Confirm tests still pass (no Phase 99 code changes expected)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: 1545 tests pass. If red, STOP — pre-existing breakage not caused by us.

---

## Task 2: Edit knip CI step

**Files:**
- Modify: `.github/workflows/dashboard-frontend-ci.yml` (knip step, ~line 50)

- [ ] **Step 2.1: View lines surrounding the knip step**

```bash
cd /home/ailearn/projects/LingWen && grep -n -B 2 -A 4 "Run knip" .github/workflows/dashboard-frontend-ci.yml
```

Expected: shows the full step definition with `name:` and `run:` lines, plus 1 line of context before/after.

- [ ] **Step 2.2: Apply the edit**

Use Edit tool.

- **Find (old_string)**:
```yaml
      - name: Run knip (dead-export detection, non-blocking)
        run: pnpm exec knip || echo "knip found issues (non-blocking — Phase 95)"
```

- **Replace (new_string)**:
```yaml
      - name: Run knip (dead-export detection)
        run: pnpm exec knip
```

The edit:
- Drops `(non-blocking)` from the step name (no longer accurate).
- Drops the `|| echo "knip found issues (non-blocking — Phase 95)"` suffix.
- Now any non-zero exit from `knip` fails the step (and the workflow job).

- [ ] **Step 2.3: Verify the edit**

```bash
cd /home/ailearn/projects/LingWen && grep -n -B 1 -A 1 "Run knip\|pnpm exec knip" .github/workflows/dashboard-frontend-ci.yml
```

Expected:
```yaml
      - name: Run knip (dead-export detection)
        run: pnpm exec knip
```

No `|| echo`, no `non-blocking` anywhere on these lines.

- [ ] **Step 2.4: Validate YAML syntax**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import yaml,sys;yaml.safe_load(open('.github/workflows/dashboard-frontend-ci.yml'));print('YAML OK')"
```

Expected: `YAML OK`. If YAML parse error, STOP — fix indentation/structure.

---

## Task 3: Local verification — knip behavior unchanged

**Files:**
- Read-only verification.

- [ ] **Step 3.1: knip output should be identical to baseline**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)" | sort
```

Expected output (same as Task 1.3):
```
Unlisted binaries (1)
Unused dependencies (1)
Unused devDependencies (1)
Unused exports (27)
Unused files (36)
```

(Sorted alphabetically — order may differ in raw output, but counts must match.)

- [ ] **Step 3.2: knip exit code is 1 (still failing locally — that's the gate)**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip > /dev/null 2>&1; echo "exit=$?"
```

Expected: `exit=1` (knip reports issues → non-zero exit). If `exit=0`, STOP — knip has been silenced; investigate.

This is the **intended local state**. Engineers who run `pnpm exec knip` locally see the same warnings as before. Only the CI behavior changes (now fails instead of warning).

- [ ] **Step 3.3: Tests still pass (sanity check, no code changed)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: 1545 tests pass. Same as Task 1.4.

---

## Task 4: Commit + push

**Files:**
- Commit: 1 file modified.

- [ ] **Step 4.1: Stage**

```bash
cd /home/ailearn/projects/LingWen && git add .github/workflows/dashboard-frontend-ci.yml && git status
```

Expected: 1 file modified, staged.

- [ ] **Step 4.2: Commit with the spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "build(ci): promote knip to hard error (Phase 99)" -m "Phase 99 — promote knip from non-blocking to blocking:

- Remove \`|| echo \"knip found issues (non-blocking — Phase 95)\"\` suffix
  from knip CI step in \`.github/workflows/dashboard-frontend-ci.yml\`
- Update step name to remove 'non-blocking' qualifier

Effect: CI now fails on any knip finding. Phase 100 cleared the 2 real
Duplicate exports; remaining 36 unused files / 27 unused exports / 12
unused exported types / 1 unused dep / 1 unused devDep / 1 unlisted binary
become follow-up phases (Phase 102+ per spec §4.4).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors. CI itself fails
on first post-merge run (intended — proves the gate)." 2>&1 | tail -5
```

Expected: one commit created. Subject + multi-line body.

- [ ] **Step 4.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds. `origin/master` advances by 1 commit.

- [ ] **Step 4.4: Final local state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```

Expected: 5 most recent commits include the Phase 99 refactor commit. Working tree clean.

---

## Task 5: Post-merge verification (gate works)

**Files:**
- Read-only verification (CI dashboard).

- [ ] **Step 5.1: Confirm CI run triggered**

Visit `https://github.com/XiaZiHunDun/LingWen/actions/workflows/dashboard-frontend-ci.yml` (or use `gh run list`).

Expected: latest run is the commit just pushed (`<phase99-sha>`).

- [ ] **Step 5.2: Confirm knip step FAILED (intended)**

In the CI run, find the `Run knip (dead-export detection)` step. Expected status: ❌ failed.

If step PASSED, STOP — knip is reporting zero issues, which would mean Phase 99 is over-scoped (it shouldn't be, since we documented known issues). Investigate before continuing.

- [ ] **Step 5.3: Confirm all other steps still passed**

In the same CI run, all OTHER steps (lint, typecheck, build, tests, etc.) should still pass.

Expected: only the knip step fails; everything else green.

- [ ] **Step 5.4: Document the CI evidence**

Save the CI run URL + failing step name to your final report so the user can verify the gate works.

---

## Success Criteria

- [ ] `.github/workflows/dashboard-frontend-ci.yml` knip step has no `|| echo` fallback
- [ ] Step name no longer contains "non-blocking"
- [ ] YAML parses cleanly (no syntax errors)
- [ ] Local knip behavior unchanged (same warnings, same exit code 1)
- [ ] Local tests pass (1545)
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master
- [ ] First post-merge CI run shows knip step failing (intended)

---

## Rollback

If the CI flip causes unanticipated failures:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts the 1-line change + restores non-blocking `|| echo` form. No data loss.

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Change Set → Task 2 ✅
- §4.2 Risk Analysis → Task 3 + Task 5 verify the predicted CI failure ✅
- §4.3 Verification Strategy → Task 5 ✅
- §7 Commit Strategy → Task 4 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions introduced. Only deletion + text change.

**Edge cases handled**:
- Task 1.3 baseline knip snapshot — catch drift between spec and current state
- Task 2.4 YAML validation — catch indentation/structure errors
- Task 3.2 exit code check — catch accidental silencing
- Task 5.2 expected failure gate verification — proves the change took effect
- Rollback section included (low-cost insurance)