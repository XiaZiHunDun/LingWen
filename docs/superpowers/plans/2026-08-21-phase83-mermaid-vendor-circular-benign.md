# Phase 83 Implementation Plan — Mermaid-Vendor Circular Warning (Benign)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Phase 80 brief comment in vite.config.js with verbose Phase 83 investigation note. Document mermaid↔vendor circular warning as benign (build works, runtime works).

**Architecture:** Doc-only change. 1 file edit (vite.config.js manualChunks function comment). 1 atomic commit.

**Tech Stack:** Markdown, Edit tool, grep, pnpm.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase83-mermaid-vendor-circular-benign-design.md` (commit `95e4e2e8`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/vite.config.js` | **Modify** (replace Phase 80 brief comment with Phase 83 verbose note inside manualChunks function) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Verify current vite.config.js state

**Files:** None (verification only)

- [ ] **Step 1.1: Read current manualChunks function**

Run: `sed -n '20,52p' apps/dashboard/vite.config.js`
Expected: shows Phase 80 comment + NAMED map + vendor catch-all.

- [ ] **Step 1.2: Find Phase 80 comment start**

Run: `grep -n "Phase 80" apps/dashboard/vite.config.js`
Expected: 1 hit pointing to the comment block start.

---

## Task 2: Edit vite.config.js (replace Phase 80 comment with Phase 83 verbose note)

**Files:**
- Modify: `apps/dashboard/vite.config.js`

- [ ] **Step 2.1: Read exact Phase 80 comment text**

Run: `sed -n '20,32p' apps/dashboard/vite.config.js`
Expected output:
```js
        manualChunks(id) {
          // Named chunks: package → chunk name
          // Phase 71: initial 8 chunks. Phase 80: verified state — naive-ui chunk
          // exists (3.11kB) but most Naive UI code remains in vendor (407kB gz)
          // due to inter-deps with vue/pinia. Future: explicit defineAsyncComponent
          // for heavy Naive UI panels (Phase 81+ candidate).
          // Known circular chunk warning: mermaid <-> vendor. Functional but
          // suboptimal — investigate in future phase.
```

- [ ] **Step 2.2: Apply Edit (replace Phase 80 comment with Phase 83 verbose note)**

Use Edit tool. **old_string**: the entire Phase 80 comment block (8 lines, lines 22-29).
**new_string**: the Phase 83 verbose comment from spec §3.1 (replaces lines 22-29, keeping the outer `manualChunks(id) {` line intact).

Note: Use Edit tool with the exact text from Step 2.1 as old_string, and the new text as new_string. The function signature `manualChunks(id) {` on line 20 and the function body on lines 30+ should remain unchanged.

- [ ] **Step 2.3: Verify edit**

Run: `sed -n '20,60p' apps/dashboard/vite.config.js`
Expected: manualChunks function preserved, comment block replaced with Phase 83 verbose note.

---

## Task 3: Build verification

**Files:** None (build verification)

- [ ] **Step 3.1: Run build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -10`
Expected: `✓ built in <time>`. May include `Circular chunk: mermaid -> vendor -> mermaid` warning (acceptable, documented).

- [ ] **Step 3.2: Verify warning still appears (acceptable)**

If circular warning appears, that's expected (documented in vite.config.js now).
If warning no longer appears (e.g., Rollup version change), also acceptable.

---

## Task 4: Test + type-check verification

**Files:** None (verification only)

- [ ] **Step 4.1: pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged).

- [ ] **Step 4.2: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors.

---

## Task 5: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 5.1: Stage vite.config.js**

Run: `cd /home/ailearn/projects/LingWen && git add apps/dashboard/vite.config.js`

- [ ] **Step 5.2: Verify staged**

Run: `git status -s`
Expected: 1 modified file.

- [ ] **Step 5.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(vite): document mermaid-vendor circular warning as benign (Phase 83)" \
    -m "Phase 83 mermaid-vendor circular chunk warning investigation:

vite.config.js: replace Phase 80 brief comment with verbose Phase 83 analysis.

Analysis:
- mermaid chunk imports ~100+ Vue 3 symbols from vendor (legitimate)
- vendor chunk imports 1 symbol (_ as ln) from mermaid (likely marked.js or similar)
- Build succeeds with warning only — runtime works
- True fix requires moving markdown lib out of vendor OR merging mermaid
  into vendor (loses lazy-load isolation). Both worse than current.

Accept trade-off + document explicitly.

测试基线不变: 1549 PASS, 0 type errors, build OK with circular warning."
```

- [ ] **Step 5.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed (vite.config.js).

- [ ] **Step 5.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3.1 (vite.config.js edit) → Task 2
- Spec §4 (verification) → Tasks 3-4
- Spec §6 (1 atomic commit) → Task 5

**Placeholder scan**:
- All Edit patterns have actual content from spec §3.1
- Verification commands have expected output

**Type consistency**:
- Comment format consistent with existing project comments

**Risks covered**:
- Step 3.1 verifies build still succeeds (accepts warning either way)
- Step 4.1-4.2 verify no regression
