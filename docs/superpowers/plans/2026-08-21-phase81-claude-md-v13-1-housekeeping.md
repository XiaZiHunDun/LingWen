# Phase 81 Implementation Plan — CLAUDE.md v13.1 Housekeeping

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bump CLAUDE.md v13.0 → v13.1 + add Phase 68-80 close summary. 6 surgical edits. 1 atomic commit.

**Architecture:** Doc-only change. No code, no tests. Grep-based verification.

**Tech Stack:** Markdown, Edit tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase81-claude-md-v13-1-housekeeping-design.md` (commit `b8e1520a`)

---

## File Structure

| File | Action |
|------|--------|
| `CLAUDE.md` | **Modify** (6 edits: version line + new update line + 当前阶段 + 最新版本 + 发布状态 + 版本记录) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Verify current CLAUDE.md state

**Files:** None (verification only)

- [ ] **Step 1.1: Check version line**

Run: `sed -n '3,7p' CLAUDE.md`
Expected: line 3 = `> **版本**: v13.0 ...`, line 5 = `> **更新 (2026-08-20)**：Phase 60-67 落地...`

- [ ] **Step 1.2: Check 当前项目状态**

Run: `sed -n '193,201p' CLAUDE.md`
Expected: line 196 = `**当前阶段**：Phase 60-67 闭环...`, line 198 = `**最新版本**：v13.0`, line 200 = `**发布状态**：Phase 60-67 全部闭环完成`

- [ ] **Step 1.3: Check 版本记录**

Run: `sed -n '463,468p' CLAUDE.md`
Expected: line 464 = `> - v13.0 (2026-08-20)：...`, line 465 = `> - v12.0 (2026-08-14)：...`

---

## Task 2: Edit 1 (line 3) - 版本 bump

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 2.1: Apply Edit 1**

Use Edit tool:
- **old_string**: `> **版本**: v13.0 (Phase 60-67 dashboard 基础设施重构完成)`
- **new_string**: `> **版本**: v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)`

- [ ] **Step 2.2: Verify**

Run: `sed -n '3p' CLAUDE.md`
Expected: `> **版本**: v13.1 (Phase 68-80 dashboard perf + 测量 闭环完成)`

---

## Task 3: Edit 2 (line 6) - New update line for Phase 68-80

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 3.1: Apply Edit 2**

Use Edit tool:
- **old_string**:
  ```
  > **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。工程命名空间沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，不要改成 `moling`）。品牌字符串真源在 `apps/dashboard/src/config/brand.js`。
  ```
- **new_string**:
  ```
  > **更新 (2026-08-21)**：Phase 68-80 perf + 测量 13 phases 闭环——
    useCreatorWriteWorkbench 测试/dashboard 入口/vite bundle/ImpactGraph deep watch 修复等 (Phase 68-72)；
    deep watch sweep 9 sibling sites (Phase 73-74)；
    Phase 74 doc drift fix (Phase 75)；
    Playwright Web Vitals baseline 4 routes × 3 runs × 5 metrics (Phase 76)；
    shallowRef stores/composables 22 conversions + submodules 11 conversions (Phase 77-78)；
    INP measurement real Playwright click (Phase 79)；
    vendor chunk split verified state (Phase 80)。
    Web Vitals baseline: 4/4 routes pass LCP/CLS/FCP/TBT/INP targets.
    Tests: 1549 PASS. Vue-tsc: 0 errors. Build: OK.
    详见 `docs/superpowers/specs/2026-08-21-phase6N-*.md` 与 `docs/perf/playwright-web-vitals-baseline.md`.

  > **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。工程命名空间沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，不要改成 `moling`）。品牌字符串真源在 `apps/dashboard/src/config/brand.js`。
  ```

- [ ] **Step 3.2: Verify**

Run: `grep -c "Phase 68-80 perf" CLAUDE.md`
Expected: 1

---

## Task 4: Edit 3 (line 196) - 当前阶段

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 4.1: Apply Edit 3**

Use Edit tool:
- **old_string**: `**当前阶段**：Phase 60-67 闭环（dashboard 基础设施重构完成）`
- **new_string**: `**当前阶段**：Phase 60-80 闭环（dashboard perf + 测量）`

- [ ] **Step 4.2: Verify**

Run: `grep "当前阶段" CLAUDE.md`
Expected: `**当前阶段**：Phase 60-80 闭环（dashboard perf + 测量）`

---

## Task 5: Edit 4 (line 198) - 最新版本

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 5.1: Apply Edit 4**

Use Edit tool:
- **old_string**: `**最新版本**：v13.0`
- **new_string**: `**最新版本**：v13.1`

- [ ] **Step 5.2: Verify**

Run: `grep "最新版本" CLAUDE.md`
Expected: `**最新版本**：v13.1`

---

## Task 6: Edit 5 (line 200) - 发布状态

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 6.1: Apply Edit 5**

Use Edit tool:
- **old_string**:
  ```
  **发布状态**：Phase 60-67 全部闭环完成（已合并）。Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  ```
- **new_string**:
  ```
  **发布状态**：Phase 60-80 全部闭环完成（已合并）。
    Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
    Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) 已全部合并。
  ```

- [ ] **Step 6.2: Verify**

Run: `grep -A1 "发布状态" CLAUDE.md | head -4`
Expected: contains "Phase 60-80 全部闭环完成（已合并）"

---

## Task 7: Edit 6 (line 463+) - 版本记录 prepend v13.1

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 7.1: Apply Edit 6**

Use Edit tool:
- **old_string**:
  ```
  > - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
  > - v12.0 (2026-08-14)：Phase 18 业务边界 + 接口化完成。
  ```
- **new_string**:
  ```
  > - v13.1 (2026-08-21)：Phase 68-80 dashboard perf + 测量. shallowRef 33 conversions (Phase 77+78). Web Vitals baseline 4 routes × 5 metrics (Phase 76+79). 13 phases closed.
  > - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。
  > - v12.0 (2026-08-14)：Phase 18 业务边界 + 接口化完成。
  ```

- [ ] **Step 7.2: Verify**

Run: `grep "v13.1 (2026-08-21)" CLAUDE.md`
Expected: 1 hit

---

## Task 8: Final verifications

**Files:** None (verification only)

- [ ] **Step 8.1: v13.1 hits count**

Run: `grep -c "v13.1" CLAUDE.md`
Expected: ≥3 (line 3, 版本记录, possibly more)

- [ ] **Step 8.2: Phase 60-80 hits**

Run: `grep -c "Phase 60-80" CLAUDE.md`
Expected: ≥2 (新 update line + 当前阶段 + 发布状态)

- [ ] **Step 8.3: git diff stat**

Run: `git diff --stat CLAUDE.md`
Expected: 1 file changed

- [ ] **Step 8.4: Sanity build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>` (CLAUDE.md change shouldn't affect build, but sanity check)

---

## Task 9: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 9.1: Stage CLAUDE.md**

Run: `git add CLAUDE.md`

- [ ] **Step 9.2: Verify staged**

Run: `git status -s`
Expected: 1 modified file.

- [ ] **Step 9.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: bump CLAUDE.md to v13.1 (Phase 68-80 close)" \
    -m "Phase 81 CLAUDE.md housekeeping:

v13.0 → v13.1 (Phase 68-80 dashboard perf + 测量)

Edits:
1. 版本 line (line 3): v13.0 → v13.1
2. 新增 更新 line: Phase 68-80 summary
3. 当前阶段 (line 196): Phase 60-67 → Phase 60-80
4. 最新版本 (line 198): v13.0 → v13.1
5. 发布状态 (line 200): Phase 60-80 全部闭环
6. 版本记录 (line 463+): prepend v13.1 entry

Phase 68-80 累计: 13 phases closed (perf + 测量).
- shallowRef 33 conversions (Phase 77+78)
- Web Vitals baseline 4 routes × 5 metrics (Phase 76+79)
- deep watch sweep 9 sites (Phase 73-74)
- vite bundle audit (Phase 71) + 2 dead panels delete + 2 lazy load (Phase 72)
- INP measurement improvement (Phase 79)
- vendor chunk split verified (Phase 80)

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 9.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed (CLAUDE.md).

- [ ] **Step 9.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3.1-§3.6 (6 edits) → Tasks 2-7
- Spec §4 (verification) → Task 8
- Spec §6 (1 atomic commit) → Task 9

**Placeholder scan**:
- All Edit patterns have actual content from spec §3
- Verification commands have expected output

**Type consistency**:
- All edits preserve original indentation/formatting
- Version line format unchanged

**Risks covered**:
- Grep-based verification in Task 1 catches line drift
- Sanity build in Task 8.4 catches any unrelated breakage
