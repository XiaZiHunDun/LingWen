# Phase 89 Implementation Plan — CLAUDE.md v13.2 Housekeeping

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bump CLAUDE.md v13.1 → v13.2 + add Phase 81-88 update line + update stale sections. 5 surgical edits. 1 atomic commit.

**Architecture:** Docs-only. No code change. No test change.

**Tech Stack:** Markdown, Edit tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase89-claude-md-v13-2-housekeeping-design.md` (commit `35ef6110`)

---

## File Structure

| File | Action |
|------|--------|
| `CLAUDE.md` | **Modify** (5 surgical edits) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Verify current CLAUDE.md state

**Files:** None (verification only)

- [ ] **Step 1.1: Read version line (line 3-4)**

Run: `sed -n '3,5p' CLAUDE.md`
Expected: `> **版本**: v13.1 (Phase 68-80...)` + `  → v13.0 (Phase 18...)`

- [ ] **Step 1.2: Read line 8 (around update lines)**

Run: `sed -n '7,15p' CLAUDE.md`
Expected: Phase 68-80 update line.

- [ ] **Step 1.3: Read 最新版本 (line 211)**

Run: `sed -n '210,212p' CLAUDE.md`

- [ ] **Step 1.4: Read 发布状态 (line 215)**

Run: `sed -n '214,217p' CLAUDE.md`

- [ ] **Step 1.5: Read 版本记录 (line 479-481)**

Run: `sed -n '478,482p' CLAUDE.md`
Expected: v13.1 + v13.0 entries.

---

## Task 2: Apply 5 surgical edits

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 2.1: Edit version line**

Use Edit tool with text from Step 1.1:

- **old_string**: (from Step 1.1)
- **new_string**: `> **版本**: v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)\n  → v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)`

- [ ] **Step 2.2: Add Phase 81-88 update line after existing Phase 68-80 update**

Use Edit tool. Find the boundary between Phase 68-80 update line and `> **品牌**:` line.

- **old_string**: (last line of Phase 68-80 update + `> **品牌**：...`)
- **new_string**: (last line of Phase 68-80 update + new Phase 81-88 update line + `> **品牌**：...`)

New Phase 81-88 update line content (from spec §3.2).

- [ ] **Step 2.3: Edit 最新版本 (line 211)**

Use Edit tool:

- **old_string**: `**最新版本**：v13.1`
- **new_string**: `**最新版本**：v13.2`

- [ ] **Step 2.4: Edit 发布状态 (line 215)**

Use Edit tool:

- **old_string**: `Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) 已全部合并。`
- **new_string**: `Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) 已全部合并。`

- [ ] **Step 2.5: Prepend v13.2 entry to 版本记录**

Use Edit tool:

- **old_string**: `> - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.`
- **new_string**: `> - v13.2 (2026-08-21)：Phase 81-88 maintenance + ESLint rule extension. 8 phases closed (v13.1 housekeeping + ESLint rule + dead cleanup + housekeeping).\n> - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.`

---

## Task 3: Final verifications

**Files:** None (verification only)

- [ ] **Step 3.1: grep — v13.2 count**

Run: `grep "v13.2" CLAUDE.md | wc -l`
Expected: `4` (version line, 最新版本, 发布状态, 版本记录)

- [ ] **Step 3.2: grep — v13.1 count**

Run: `grep "v13.1" CLAUDE.md | wc -l`
Expected: `≥2` (history chain + 版本记录)

- [ ] **Step 3.3: grep — v13.0 count**

Run: `grep "v13.0" CLAUDE.md | wc -l`
Expected: `2` (history chain + 版本记录)

- [ ] **Step 3.4: pnpm test sanity**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -3`
Expected: `Tests  1546 passed (1546)` (unchanged)

- [ ] **Step 3.5: vue-tsc sanity**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 3.6: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat CLAUDE.md`
Expected: 1 file modified.

---

## Task 4: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 4.1: Stage CLAUDE.md**

Run: `git add CLAUDE.md`

- [ ] **Step 4.2: Verify staged**

Run: `git status -s`
Expected: 1 modified file.

- [ ] **Step 4.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: bump CLAUDE.md to v13.2 (Phase 81-88 maintenance close)" \
    -m "Phase 89 CLAUDE.md housekeeping:

Phase 81-88 closed (8 phases): CLAUDE.md v13.1 (81), no-shallowref-mutation ESLint rule + extension (82+88), mermaid-vendor circular documented (83), 7 dead refs + 9 dead mocks + 3 test cases cleanup (84+85), stale header fix (86), Phase 78 spec housekeeping (87).

5 surgical edits to CLAUDE.md:
1. Version line (line 3-4): v13.1 → v13.2
2. Add Phase 81-88 update line (after line 8)
3. 最新版本 (line 211): v13.1 → v13.2
4. 发布状态 (line 215): add v13.2 reference
5. 版本记录 (line 479): prepend v13.2 entry

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 4.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed.

- [ ] **Step 4.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3.1-§3.5 (5 edits) → Task 2
- Spec §4 (verification) → Task 3
- Spec §6 (1 atomic commit) → Task 4

**Placeholder scan**:
- All Edit patterns have actual content from spec §3
- All grep commands have expected output

**Type consistency**:
- All edits are docs changes, no syntax risk

**Risks covered**:
- Step 1.1-1.5 reads confirm exact text before edit
- Step 3.1-3.3 grep verifies version counts
- Step 3.4-3.5 regression checks

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout CLAUDE.md
```
