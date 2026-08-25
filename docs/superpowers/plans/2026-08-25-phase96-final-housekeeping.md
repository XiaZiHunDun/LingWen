# Phase 96 final housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate `v13.2` description in CLAUDE.md to 1 canonical form + annotate the `−1` test count drift. Pure doc edits.

**Architecture:** Single atomic commit. 2 surgical Edit tool applications to `CLAUDE.md`.

**Tech Stack:** Markdown, git.

---

## File Structure

**Files modified (1):**
- `CLAUDE.md` — 2 line edits (line 281 v13.2 description + line 29 drift note)

---

## Task 1: Pre-flight — git state + baselines

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `44d26b6e docs(spec): Phase 96 final housekeeping — ...`. Tree clean.

- [ ] **Step 1.2: Verify the 2 v13.2 lines that need fixing (line 4 + 281) and the v13.2 line that's already correct (line 548)**

```bash
cd /home/ailearn/projects/LingWen && grep -n "v13.2" CLAUDE.md
```

Expected: 3 matches at lines 4, 281, 548. Line 281 has bare "ESLint" (no "rule extension" suffix); lines 4 + 548 already have the extension wording.

- [ ] **Step 1.3: Verify the 1546 line that needs annotation**

```bash
cd /home/ailearn/projects/LingWen && grep -n "1546" CLAUDE.md
```

Expected: 1 match at line 29 (the Phase 81-88 cumulative baseline).

---

## Task 2: Apply 2 doc edits

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 2.1: Edit line 281 — update v13.2 description to canonical form**

Use Edit tool.

- **Find (old_string)**:
```
**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint 完成)
```

- **Replace (new_string)**:
```
**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint rule extension 完成)
```

- [ ] **Step 2.2: Edit line 29 — append drift note**

- **Find (old_string)**:
```
  Cumulative: 33 shallowRef conversions, 1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS.
```

- **Replace (new_string)**:
```
  Cumulative: 33 shallowRef conversions, 1546 unit tests + 31 e2e + ~18 ESLint rule tests all PASS.
  (Note: subsequent Phase 89/102.2/103/103.1/105a dead-code cleanup removed 1 test for a net of 1545 tests as of Phase 105b.)
```

- [ ] **Step 2.3: Verify both edits applied**

```bash
cd /home/ailearn/projects/LingWen && grep "上一版本" CLAUDE.md
```

Expected: matches the new canonical form (`ESLint rule extension 完成`).

```bash
cd /home/ailearn/projects/LingWen && grep "subsequent Phase 89" CLAUDE.md
```

Expected: matches the new drift note.

---

## Task 3: Verify

**Files:**
- Read-only verification.

- [ ] **Step 3.1: All 3 v13.2 mentions consistent**

```bash
cd /home/ailearn/projects/LingWen && grep -n "v13.2" CLAUDE.md
```

Expected: 3 matches at lines 4, 281, 548. Verify visually that all 3 have consistent "ESLint rule extension" wording (lines 4 + 548 had it; line 281 just added it).

- [ ] **Step 3.2: 1546 mention now annotated**

```bash
cd /home/ailearn/projects/LingWen && grep "1546" CLAUDE.md
```

Expected: 1 match (line 29) with the new drift note on the next line.

- [ ] **Step 3.3: 1545 still present (current count, not removed)**

```bash
cd /home/ailearn/projects/LingWen && grep "1545" CLAUDE.md
```

Expected: 1+ matches (line 82 in the Phase 103+ update entry).

- [ ] **Step 3.4: Diff stat — small**

```bash
cd /home/ailearn/projects/LingWen && git diff --stat
```

Expected: 1 file (`CLAUDE.md`), 2 inserted / 1 deleted (small).

---

## Task 4: Commit + push

**Files:**
- Commit: 1 modified file

- [ ] **Step 4.1: Stage the file**

```bash
cd /home/ailearn/projects/LingWen && git add CLAUDE.md && git status
```

Expected: 1 file staged.

- [ ] **Step 4.2: Commit with spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "docs: consolidate v13.2 description + annotate test count drift (Phase 96 housekeeping)" -m "Phase 96 final housekeeping — code-quality + spec-compliance review follow-up
LOW notes:

1. Consolidate v13.2 description (Phase 81-88 maintenance + ESLint rule extension)
   to a single canonical form. Was 3 variants across CLAUDE.md (line 4
   had 'ESLint extension', line 281 had bare 'ESLint', line 548 had
   'ESLint rule extension'). Now line 281 matches the canonical form.
   Lines 4 and 548 already had the extension wording (intentional from
   Phase 96 commit).

2. Annotate the test count drift: Phase 81-88 entry said 1546 tests,
   Phase 103+ entry said 1545. The -1 test came from Phase 89/102.2/103/
   103.1/105a dead-code cleanup. Add a parenthetical note to the
   historical entry so future readers understand the drift.

No code changes. Doc-only."
```

- [ ] **Step 4.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds.

- [ ] **Step 4.4: Final state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: 3 most recent commits include the Phase 96 housekeeping commit. Tree clean.

---

## Success Criteria

- [ ] Line 281 v13.2 description updated to canonical `Phase 81-88 maintenance + ESLint rule extension 完成`
- [ ] Line 29 appends a note about the test count drift
- [ ] All 3 v13.2 occurrences in CLAUDE.md use consistent wording
- [ ] grep checks per §3 return expected counts
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses (extremely unlikely — docs only):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## Self-Review Notes

**Spec coverage**:
- §4.3 Edit 1 (line 281 v13.2 description) → Task 2.1 ✅
- §4.3 Edit 2 (line 29 drift note) → Task 2.2 ✅
- §4.5 Verification → Task 3 ✅
- §7 Commit Strategy → Task 4 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No code changes. Doc-only text fixes.

**Edge cases handled**:
- Task 1.2 confirm 3 v13.2 lines (catch scope drift)
- Task 1.3 confirm 1546 line (catch scope drift)
- Task 2.3 verify both edits applied (catch missed Edit)
- Task 3.1-3.3 grep checks
- Task 3.4 diff stat small
- Rollback section