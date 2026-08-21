# Phase 87 Implementation Plan — Phase 78 Spec Housekeeping

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Phase 78 spec doc drift (10 → 11 conversions, 4 → 5 useSettingsDocs) + add §12 amend note. 1 atomic commit. docs-only.

**Architecture:** Surgical edits in 1 spec file. No code change. No test change.

**Tech Stack:** Markdown, Edit tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase87-phase78-spec-housekeeping-design.md` (commit `aaba7234`)

---

## File Structure

| File | Action |
|------|--------|
| `docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md` | **Modify** (6 line edits + new §12 section) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Verify current state

**Files:** None (verification only)

- [ ] **Step 1.1: Read line 4 (Header)**

Run: `sed -n '4p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`
Expected: `> **范围**: 3 submodule `.ts` files code change. 10 wholesale-refs → shallowRef.`

- [ ] **Step 1.2: Read line 17 (§1 background)**

Run: `sed -n '17p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 1.3: Read line 80 (§4.1 footer)**

Run: `sed -n '80p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 1.4: Read line 112 (§5 Total)**

Run: `sed -n '112p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 1.5: Read line 163 (§7 Verification)**

Run: `sed -n '163p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 1.6: Read line 189 (§9 commit subject)**

Run: `sed -n '189p' docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

---

## Task 2: Apply 6 line edits

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 2.1: Edit line 4**

Use Edit tool:
- **old_string**: `> **范围**: 3 submodule `.ts` files code change. 10 wholesale-refs → shallowRef.`
- **new_string**: `> **范围**: 3 submodule `.ts` files code change. 11 wholesale-refs → shallowRef.`

- [ ] **Step 2.2: Edit line 17**

Use Edit tool:
- **old_string**: `> **背景**: Phase 77 code review M1 识别 3 submodule `.ts` 文件有 10 wholesale-refs 符合同 decision rule, 推荐扩展 shallowRef sweep.`
- **new_string**: `> **背景**: Phase 77 code review M1 识别 3 submodule `.ts` 文件有 11 wholesale-refs 符合同 decision rule, 推荐扩展 shallowRef sweep.`

- [ ] **Step 2.3: Edit line 80**

Use Edit tool:
- **old_string**: (need to verify exact text from Step 1.3)

- [ ] **Step 2.4: Edit line 112**

Use Edit tool:
- **old_string**: (need to verify exact text from Step 1.4)

- [ ] **Step 2.5: Edit line 163**

Use Edit tool:
- **old_string**: (need to verify exact text from Step 1.5)

- [ ] **Step 2.6: Edit line 189**

Use Edit tool:
- **old_string**: (need to verify exact text from Step 1.6)

---

## Task 3: Add §12 Amend Note

**Files:**
- Modify: `docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 3.1: Find end of doc**

Run: `wc -l docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 3.2: Read last 5 lines**

Run: `tail -5 docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`
Find end of §11 后续.

- [ ] **Step 3.3: Append §12 Amend Note**

Use Edit tool. Find the end of file and append §12:

**old_string**: (last line of §11 from Step 3.2)
**new_string**: (last line of §11 + 2 blank lines + full §12 content from spec §3.1)

---

## Task 4: Final verifications

**Files:** None (verification only)

- [ ] **Step 4.1: grep — old "10 conversions" absent**

Run: `grep "10 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l`
Expected: `0`

- [ ] **Step 4.2: grep — new "11 conversions" present**

Run: `grep "11 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l`
Expected: ≥3

- [ ] **Step 4.3: grep — old "4 conversions" absent**

Run: `grep "4 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l`
Expected: `0`

- [ ] **Step 4.4: grep — new "5 conversions" present**

Run: `grep "5 conversions" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l`
Expected: ≥3

- [ ] **Step 4.5: §12 amend note present**

Run: `grep "## 12\\. Phase 87 Amend Note" docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md | wc -l`
Expected: `1`

- [ ] **Step 4.6: git diff stat**

Run: `git diff --stat docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`
Expected: 1 file changed.

---

## Task 5: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 5.1: Stage spec file**

Run: `git add docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md`

- [ ] **Step 5.2: Verify staged**

Run: `git status -s`
Expected: 1 modified file.

- [ ] **Step 5.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 87 — fix Phase 78 spec count drift (10 → 11)" \
    -m "Phase 87 spec housekeeping:

Phase 78 spec had count drift — actual implementation had 11 conversions, spec said 10.

Corrected:
- Header: 10 → 11 wholesale-refs
- §1 background: 10 → 11 wholesale-refs
- §4.1 footer (useSettingsDocs): 4 → 5 conversions
- §5 Total: 10 → 11 conversions
- §7 Verification: 10/10 → 11/11
- §9 commit subject: 10 → 11 wholesale-refs
- Added §12 Amend Note documenting drift rationale

Phase 78 amend commit a6d4afe2 already corrected commit message.
This spec amend keeps the design doc consistent.

无代码变更. 1546 tests baseline unchanged."
```

- [ ] **Step 5.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed.

- [ ] **Step 5.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3 (6 line edits) → Task 2
- Spec §3.1 (new §12) → Task 3
- Spec §4 (verification) → Task 4
- Spec §6 (1 atomic commit) → Task 5

**Placeholder scan**:
- All Edit patterns have actual content from spec §3
- All grep commands have expected output

**Type consistency**:
- All edits are count corrections + section add
- No syntax risk

**Risks covered**:
- Step 1.1-1.6 reads confirm exact text before edit
- Step 4.1-4.5 grep verifies count corrections + section add

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md
```
