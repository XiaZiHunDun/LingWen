# Phase 96 — CLAUDE.md Stale Content Audit & Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update CLAUDE.md to reflect current project state. Bump version v13.2 → v14.0. Add 4 new update entries (Phase 89, 95, 99-105b). Fix stale "Phase 60-80 闭环" / "v13.2" / test counts in §## 当前项目状态.

**Architecture:** Doc-only edits. Single atomic commit. No code or config changes.

**Tech Stack:** Markdown, git.

---

## File Structure

**Files modified (1):**
- `CLAUDE.md` — version header + 4 new update entries + §## 当前项目状态 section

---

## Task 1: Pre-flight — git state + verify stale content

**Files:**
- Read-only check.

**- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `e7a90463 docs(spec): Phase 96 — ...`. Tree clean.

**- [ ] **Step 1.2: Verify stale content exists**

```bash
cd /home/ailearn/projects/LingWen && grep -n "v13.2" CLAUDE.md | head -5
```
Expected: matches showing `v13.2` in version header + other places (to be replaced).

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 60-80 闭环\|Phase 60-80 全部" CLAUDE.md
```
Expected: matches showing stale Phase 60-80 references.

```bash
cd /home/ailearn/projects/LingWen && grep -n "1549 PASS\|1546 unit tests" CLAUDE.md
```
Expected: matches showing stale test counts.

**- [ ] **Step 1.3: Capture baseline test + build (should be unchanged)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`. If red, STOP.

---

## Task 2: Edit CLAUDE.md — version header (line 3)

**Files:**
- Modify: `CLAUDE.md` (line 3)

**- [ ] **Step 2.1: View current line 3**

```bash
cd /home/ailearn/projects/LingWen && sed -n '3p' CLAUDE.md
```
Expected: `> **版本**: v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)`

**- [ ] **Step 2.2: Apply Edit**

Use Edit tool.

- **Find (old_string)** (line 3 only):
```
> **版本**: v13.2 (Phase 81-88 maintenance + ESLint extension 闭环完成)
```

- **Replace (new_string)**:
```
> **版本**: v14.0 (Phase 99-105b knip-follow-up 闭环完成)
```

**- [ ] **Step 2.3: Verify**

```bash
cd /home/ailearn/projects/LingWen && sed -n '3p' CLAUDE.md
```
Expected: `> **版本**: v14.0 (Phase 99-105b knip-follow-up 闭环完成)`.

---

## Task 3: Insert Phase 89 update entry (after line 29, before line 31)

**Files:**
- Modify: `CLAUDE.md` (insert new entry before line 31 — "## 品牌" section)

**- [ ] **Step 3.1: View lines around insertion point**

```bash
cd /home/ailearn/projects/LingWen && sed -n '29,32p' CLAUDE.md
```
Expected:
```
  详见 `docs/superpowers/specs/2026-08-21-phase8N-*.md` 各 phase spec.

> **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。
```

**- [ ] **Step 3.2: Apply Edit — insert Phase 89 update entry**

Use Edit tool. Insert the new entry AFTER line 29 (the `详见...phase8N-*.md...` line) and BEFORE line 31 (the `> **品牌**` line).

- **Find (old_string)** (lines 29 + 31, with the > **品牌** line as anchor):
```
  详见 `docs/superpowers/specs/2026-08-21-phase8N-*.md` 各 phase spec.

> **品牌**：本仓库的产品名是
```

- **Replace (new_string)**:
```
  详见 `docs/superpowers/specs/2026-08-21-phase8N-*.md` 各 phase spec.

> **更新 (2026-08-23)**：Phase 89 CLAUDE.md v13.2 housekeeping 闭环——
  bump version header to v13.2; mark Phase 89 plan commit (`docs(plan): Phase 89 — CLAUDE.md v13.2 bump`) for future reference.
  详见 `docs/superpowers/plans/2026-08-23-phase89-claude-md-v13.2-bump.md`.

> **品牌**：本仓库的产品名是
```

(Note: only the FIRST line of `> **品牌**` is in old_string to disambiguate.)

**- [ ] **Step 3.3: Verify insertion**

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 89 CLAUDE.md v13.2 housekeeping" CLAUDE.md
```
Expected: 1 match.

---

## Task 4: Insert Phase 95 update entry (after Phase 89 entry)

**Files:**
- Modify: `CLAUDE.md`

**- [ ] **Step 4.1: Apply Edit — insert Phase 95 update entry after Phase 89 entry**

Use Edit tool.

- **Find (old_string)** (last line of Phase 89 entry + first line of > **品牌**):
```
  详见 `docs/superpowers/plans/2026-08-23-phase89-claude-md-v13.2-bump.md`.

> **品牌**：本仓库的产品名是
```

- **Replace (new_string)**:
```
  详见 `docs/superpowers/plans/2026-08-23-phase89-claude-md-v13.2-bump.md`.

> **更新 (2026-08-23)**：Phase 95 knip integration 闭环——
  add knip 6.32.2 devDep to root package.json (lockfile updated);
  knip.json config scaffold (entry/project/ignore base arrays);
  GitHub Actions dashboard-frontend-ci.yml adds knip step (non-blocking).
  详见 `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md` 与 `docs/superpowers/plans/2026-08-23-phase95-knip-ci.md`.

> **品牌**：本仓库的产品名是
```

**- [ ] **Step 4.2: Verify**

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 95 knip integration" CLAUDE.md
```
Expected: 1 match.

---

## Task 5: Insert Phase 100 + 99 update entry

**Files:**
- Modify: `CLAUDE.md`

**- [ ] **Step 5.1: Apply Edit — insert Phase 100 + 99 entry**

- **Find (old_string)**:
```
  详见 `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md` 与 `docs/superpowers/plans/2026-08-23-phase95-knip-ci.md`。

> **品牌**：本仓库的产品名是
```

- **Replace (new_string)**:
```
  详见 `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md` 与 `docs/superpowers/plans/2026-08-23-phase95-knip-ci.md`.

> **更新 (2026-08-23)**：Phase 100 knip duplicate exports 闭环——
  delete 2 unused default exports (`useWidgetRegistry`, `logger`) per Phase 95 knip finding;
  knip Unused exports 2 → 0.
  Phase 99 knip gate promote 闭环：knip CI step flipped from non-blocking (`|| echo`) to hard error;
  pre-existing pnpm setup version conflict surfaced (worked around in Phase 99.1).
  详见 `docs/superpowers/specs/2026-08-23-phase100-knip-duplicates-design.md` 与 `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md`.

> **品牌**：本仓库的产品名是
```

**- [ ] **Step 5.2: Verify**

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 100 knip duplicate" CLAUDE.md
```
Expected: 1 match.

---

## Task 6: Insert Phase 99.1 + 102 + 102.1 + 102.2 update entry

**Files:**
- Modify: `CLAUDE.md`

**- [ ] **Step 6.1: Apply Edit**

- **Find (old_string)**:
```
  详见 `docs/superpowers/specs/2026-08-23-phase100-knip-duplicates-design.md` 与 `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md`.

> **品牌**：本仓库的产品名是
```

- **Replace (new_string)**:
```
  详见 `docs/superpowers/specs/2026-08-23-phase100-knip-duplicates-design.md` 与 `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md`.

> **更新 (2026-08-24)**：Phase 99.1 + 102 + 102.1 + 102.2 knip-setup 闭环——
  Phase 99.1: remove `version: 9` from 11 `pnpm/action-setup@v4` invocations in 6 workflows;
  let `package.json#packageManager: "pnpm@9.0.0"` be single source of truth.
  Phase 102: delete 30 unused files + add 5 knip false-positives to `apps/dashboard/knip.json#ignore`;
  out-of-plan commit 3 moves `knip.json` from root to `apps/dashboard/` (knip doesn't walk parent dirs).
  Phase 102.1: restore root `pnpm knip` delegation (root `package.json` script) + clean 5 stale
  JSDoc comments in preserved creator key files.
  Phase 102.2: remove unused `eslint-plugin-local-rules` devDep + add `ignoreBinaries: ["knip"]`
  to `apps/dashboard/knip.json` (correct field name per knip 6.32.2 schema; "binaries" rejected).
  Cumulative: knip Unused devDependencies 0, Unlisted binaries 0.
  详见 `docs/superpowers/specs/2026-08-24-phase99.1-pnpm-setup-fix-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102-unused-files-audit-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102.1-knip-config-and-comment-cleanup-design.md`,
  `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`.

> **品牌**：本仓库的产品名是
```

**- [ ] **Step 6.2: Verify**

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 99.1 + 102 + 102.1 + 102.2" CLAUDE.md
```
Expected: 1 match.

---

## Task 7: Insert Phase 103 + 103.1 + 104 + 105a + 105b update entry

**Files:**
- Modify: `CLAUDE.md`

**- [ ] **Step 7.1: Apply Edit**

- **Find (old_string)**:
```
  `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`.

> **品牌**：本仓库的产品名是
```

- **Replace (new_string)**:
```
  `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md`.

> **更新 (2026-08-25)**：Phase 103 + 103.1 + 104 + 105a + 105b knip-follow-up 闭环——
  Phase 103: delete 47 unused exports (4 whole-file deletes, 19 partial source edits,
  barrel re-exports of dead sources stripped) + 1 dead file (`types/index.ts`) + 9 dead types
  in `types/composables.ts`; pivot to knip.json#ignore for `useWidgetRegistry.js` /
  `creatorPanelMatrix.js` (live consumers discovered mid-implementation); `composables/index.ts`
  added to knip.json#ignore (public-API barrel). All 7 subcategories dead exports cleared.
  Phase 103.1: delete dead `useWriteValidation.ts` (zero consumers post-Phase 103) + 2 stale JSDoc
  references; knip Unused files 1 → 0.
  Phase 104: drop `export` keyword from 29 dead type declarations across 9 source files + add
  `tests/helpers/strict-test-types.ts` to `apps/dashboard/knip.json#ignore` (knip can't trace
  helper-function return types); knip Unused exported types 33 → 0.
  Phase 105a: delete 3 truly-dead deps (`@vueuse/core`, `animate.css`, `vfonts`) + drop
  `@import 'animate.css';` from `style.css:1`; knip Unused dependencies 3 → 0.
  Phase 105b: housekeeping — correct 4 doc inaccuracies flagged by reviewers (Phase 102.2/104/105a
  spec wording) + delete stale `apps/dashboard/pnpm-lock.yaml` (Phase 17.2 npm-lock artifact
  ignored by pnpm 9 workspace mode).
  Cumulative: knip gate fully clean (Unused exports 0, files 0, exported types 0, dependencies 0,
  devDependencies 0, Unlisted binaries 0, Duplicate exports 0).
  Tests: 1545 PASS. Vue-tsc: 0 errors. Build: OK.
  详见 `docs/superpowers/specs/2026-08-24-phase103-unused-exports-audit-design.md`,
  `docs/superpowers/specs/2026-08-24-phase103.1-delete-dead-useWriteValidation-design.md`,
  `docs/superpowers/specs/2026-08-25-phase104-unused-types-audit-design.md`,
  `docs/superpowers/specs/2026-08-25-phase105a-unused-deps-cleanup-design.md`,
  `docs/superpowers/specs/2026-08-25-phase105b-knip-cleanup-housekeeping-design.md`.

> **品牌**：本仓库的产品名是
```

**- [ ] **Step 7.2: Verify**

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 103 + 103.1 + 104 + 105a + 105b" CLAUDE.md
```
Expected: 1 match.

```bash
cd /home/ailearn/projects/LingWen && grep -n "1545 PASS" CLAUDE.md
```
Expected: 1 match (in the new Phase 103+ entry).

---

## Task 8: Update §## 当前项目状态 section (line 217+)

**Files:**
- Modify: `CLAUDE.md`

**- [ ] **Step 8.1: View current state**

```bash
cd /home/ailearn/projects/LingWen && sed -n '217,228p' CLAUDE.md
```
Expected: current project state section with stale "Phase 60-80" content.

**- [ ] **Step 8.2: Apply Edit — bump version + stage + version chain**

Use Edit tool.

- **Find (old_string)** (lines 220, 222, 223 — separate edits to keep surgical):
Edit 1: `**当前阶段**：Phase 60-80 闭环（dashboard perf + 测量）`
Replace with: `**当前阶段**：Phase 60-105b 闭环（dashboard perf + 测量 + knip gate enforcement）`

Edit 2: `**最新版本**：v13.2`
Replace with: `**最新版本**：v14.0`

Edit 3: `**上一版本**：v12.0 (Phase 18 业务边界 + 接口化 完成)`
Replace with: `**上一版本**：v13.2 (Phase 81-88 maintenance + ESLint 完成)`

**- [ ] **Step 8.3: Apply Edit — 发布状态 block**

- **Find (old_string)**:
```
**发布状态**：Phase 60-80 全部闭环完成（已合并）。
  Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) 已全部合并。
```

- **Replace (new_string)**:
```
**发布状态**：Phase 60-105b 全部闭环完成（已合并）。
  Phase 16.7（删陈旧 infra 目录）已于 Phase 18（基础设施重构）完成。
  Phase 60-67 dashboard 基础设施重构 (v13.0) + Phase 68-80 perf + 测量 (v13.1) + Phase 81-88 maintenance + ESLint (v13.2) + Phase 89 housekeeping + Phase 95 knip integration + Phase 99-105b knip-follow-up (v14.0) 已全部合并。
```

**- [ ] **Step 8.4: Verify all 4 edits in §## 当前项目状态**

```bash
cd /home/ailearn/projects/LingWen && sed -n '217,228p' CLAUDE.md
```
Expected: all 4 edits applied (Phase 60-105b, v14.0, last v13.2, full status).

---

## Task 9: Stage + commit + push

**Files:**
- Commit: `CLAUDE.md` (single file with 8 edits)

**- [ ] **Step 9.1: Stage CLAUDE.md**

```bash
cd /home/ailearn/projects/LingWen && git add CLAUDE.md && git status
```

Expected: 1 file staged.

**- [ ] **Step 9.2: Verify grep checks per spec §4.4**

Run all spec §4.4 grep checks:

```bash
cd /home/ailearn/projects/LingWen && grep "v13.2\|Phase 60-80 闭环" CLAUDE.md
```
Expected: some matches for `v13.2` (historical context mentions, fine) but ZERO matches for `Phase 60-80 闭环`.

```bash
cd /home/ailearn/projects/LingWen && grep "1545 PASS" CLAUDE.md
```
Expected: 1+ matches.

```bash
cd /home/ailearn/projects/LingWen && grep -n "Phase 89\|Phase 95\|Phase 99-105b\|knip gate" CLAUDE.md | head -5
```
Expected: at least 4 mentions in new update entries.

```bash
cd /home/ailearn/projects/LingWen && head -10 CLAUDE.md
```
Expected: line 3 shows `v14.0`.

**- [ ] **Step 9.3: Verify tests + knip still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```
Expected: zero matches.

**- [ ] **Step 9.4: Commit**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "docs: bump CLAUDE.md to v14.0 + add Phase 89/95/99-105b update entries (Phase 96)" -m "Phase 96 — Phase 89 follow-up housekeeping (audit remaining 19 CLAUDE.md
sections for stale content):

- Bump version header v13.2 → v14.0 (knip gate enforcement milestone)
- Add Phase 89 update entry (CLAUDE.md v13.2 housekeeping plan)
- Add Phase 95 update entry (knip 6.32.2 devDep + config + CI step)
- Add Phase 100 + 99 update entries (duplicate exports + knip gate promote)
- Add Phase 99.1 + 102 + 102.1 + 102.2 update entries (pnpm setup fix + 30 file
  deletes + root knip delegation + devDep removal)
- Add Phase 103 + 103.1 + 104 + 105a + 105b update entries (47 unused exports
  + dead useWriteValidation.ts + 29 unused types + 3 unused deps + housekeeping)
- Update ## 当前项目状态 section: Phase 60-80 闭环 → Phase 60-105b 闭环,
  v13.2 → v14.0, last-version v12.0 → v13.2
- Cumulative: 1545 PASS tests baseline unchanged across all phases

No code or config changes. Doc-only."
```

Expected: 1 commit created.

**- [ ] **Step 9.5: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```
Expected: push succeeds.

**- [ ] **Step 9.6: Final state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```
Expected: 5 most recent commits include the Phase 96 commit. Tree clean.

---

## Success Criteria

- [ ] Line 3 says `v14.0` (not `v13.2`)
- [ ] 4 new update entries added (Phase 89, 95, 100+99, 99.1+102+102.1+102.2, 103+103.1+104+105a+105b)
- [ ] §## 当前项目状态: `Phase 60-105b 闭环`, `v14.0`, `上一版本 v13.2`
- [ ] `1545 PASS` mentioned at least once
- [ ] All 4 grep checks per spec §4.4 return expected counts
- [ ] All other 17 sections unchanged (workflow, agents, decisions, etc.)
- [ ] 1545 tests pass
- [ ] knip clean
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
- §4.1 Edit 1 (version header) → Task 2 ✅
- §4.1 Edits 2-6 (5 update entries) → Task 3-7 ✅
- §4.1 Edit 7 (§## 当前项目状态) → Task 8 ✅
- §4.4 Verification → Task 9.2 ✅
- §7 Commit Strategy → Task 9.4 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only doc text edits.

**Edge cases handled**:
- Task 1.2 baseline stale content exists (catch scope drift)
- Task 1.3 baseline tests pass (no regressions before)
- Task 2.3 version header line verified
- Task 3.3 / 4.2 / 5.2 / 6.2 / 7.2 each insert verified by grep
- Task 8.4 all 4 §## 当前项目状态 edits verified
- Task 9.2 all 4 grep checks per spec §4.4
- Task 9.3 tests + knip unchanged
- Task 9.4 atomic commit
- Rollback section