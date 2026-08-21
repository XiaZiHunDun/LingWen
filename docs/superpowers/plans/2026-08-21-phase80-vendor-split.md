# Phase 80 Implementation Plan — Vendor Chunk Split (Naive UI)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract Naive UI from the `vendor` catch-all chunk into its own named chunk. Foundation for future lazy loading.

**Architecture:** One line added to `vite.config.js` manualChunks NAMED map. Build verification. No app code change.

**Tech Stack:** Vite 5.x, Rollup, esbuild, Vue 3 + Naive UI.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase80-vendor-split-design.md` (commit `1d86ff19`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/vite.config.js` | **Modify** (1 line addition to NAMED map) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Capture before baseline

**Files:** None (verification only)

- [ ] **Step 1.1: Build current state**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -25`
Expected: `✓ built in <time>` with chunk list.

- [ ] **Step 1.2: Save before baseline**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
echo "=== BEFORE Phase 80 ===" > /tmp/phase80-before.txt
ls -la dist/assets/vendor-*.js dist/assets/naive-ui-*.js 2>&1 >> /tmp/phase80-before.txt
pnpm run build 2>&1 | grep -E "vendor|naive-ui" >> /tmp/phase80-before.txt
cat /tmp/phase80-before.txt
```

Expected: vendor chunk exists (~1462kB raw / 407kB gz), no naive-ui chunk.

---

## Task 2: Edit vite.config.js

**Files:**
- Modify: `apps/dashboard/vite.config.js`

- [ ] **Step 2.1: Read current manualChunks**

Run: `sed -n '20,40p' apps/dashboard/vite.config.js`
Confirm NAMED map is visible.

- [ ] **Step 2.2: Add 'naive-ui' to NAMED map**

Use Edit tool:
- **old_string**:
  ```
          const NAMED = {
            echarts: 'echarts',
            mermaid: 'mermaid',
            cytoscape: 'cytoscape',
            katex: 'katex',
            'naive-ui': 'naive-ui',
            'vue-router': 'vue-router',
  ```
- Wait — check if `naive-ui` is ALREADY in the NAMED map. If yes, no edit needed; just verify build.

Let me re-check the file. Re-read first.

If NOT in map, add it. If already in map, just confirm build.

- [ ] **Step 2.3: Verify edit**

Run: `grep "naive-ui" apps/dashboard/vite.config.js`
Expected: 1+ hit showing naive-ui in NAMED map.

---

## Task 3: Build + verify naive-ui chunk

**Files:** None (build verification)

- [ ] **Step 3.1: Build**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -25`
Expected: `✓ built in <time>` with new chunks.

- [ ] **Step 3.2: Verify naive-ui chunk exists**

Run: `ls -la apps/dashboard/dist/assets/naive-ui-*.js 2>&1 | head -3`
Expected: 1 file (the new naive-ui chunk).

- [ ] **Step 3.3: Compare vendor chunk size**

Run: `ls -la apps/dashboard/dist/assets/vendor-*.js | head -3`
Expected: file exists, ideally smaller than before.

- [ ] **Step 3.4: Save after baseline**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
echo "=== AFTER Phase 80 ===" > /tmp/phase80-after.txt
ls -la dist/assets/vendor-*.js dist/assets/naive-ui-*.js 2>&1 >> /tmp/phase80-after.txt
pnpm run build 2>&1 | grep -E "vendor|naive-ui" >> /tmp/phase80-after.txt
cat /tmp/phase80-after.txt
```

- [ ] **Step 3.5: Verify total chunks sum**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
ls -la dist/assets/*.js | awk '{sum+=$5} END {print "Total raw: " sum " bytes"}'
```
Compare to before.

---

## Task 4: Test + type-check verification

**Files:** None (verification only)

- [ ] **Step 4.1: pnpm test**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged).

- [ ] **Step 4.2: vue-tsc**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors.

- [ ] **Step 4.3: Build re-verify**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`.

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
    commit -m "build(vite): extract naive-ui from vendor chunk (Phase 80)" \
    -m "Phase 80 vendor chunk split:

vite.config.js: add 'naive-ui': 'naive-ui' to manualChunks NAMED map.

Before: vendor-*.js = 1462kB raw / 407kB gz (Naive UI ~80% + other libs)
After: naive-ui-*.js separate, vendor-*.js smaller

Foundation for Phase 81+ lazy loading of Naive UI components.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 5.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed (vite.config.js, +1 line).

- [ ] **Step 5.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3.1 (vite.config.js change) → Task 2
- Spec §3.2 (expected outcome) → Tasks 1 + 3
- Spec §4 (verification) → Tasks 3-4
- Spec §6 (1 atomic commit) → Task 5

**Placeholder scan**:
- Edit pattern has actual content
- All grep commands have expected output

**Risks covered**:
- Task 3.2 verifies naive-ui chunk exists (catches no-edit case)
- Task 4.1 catches functional regressions
- Task 4.2 catches type errors

## Rollback Strategy

If build fails or tests break:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/vite.config.js
```
