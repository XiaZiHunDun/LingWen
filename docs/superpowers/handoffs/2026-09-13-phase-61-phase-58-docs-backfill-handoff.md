# Phase 61 — Phase 58 Docs Backfill Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 58 C6 commit `a64f8604` "add spec + handoff docs" — committed defect-closure spec/handoff but FORGOT cross-volume-failures design/plan (867 LOC)
> **目标**: Backfill 2 untracked Phase 58 docs + 2 regression guards 防止复发

## 1. 背景

Phase 58 (2026-09-12) ff-merge 到 master `8a98c818`。C6 commit `a64f8604` 提交了 3 个 handoff/spec docs:
- ✓ `docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md`
- ✓ `docs/superpowers/specs/2026-09-12-phase-58-defect-closure-design.md`
- ✓ `docs/superpowers/handoffs/2026-09-12-phase-58-defect-closure-handoff.md`

但**漏了** cross-volume-failures 的 design + plan:
- ✗ `docs/superpowers/specs/2026-09-12-phase-58-cross-volume-failures-design.md` (204 LOC)
- ✗ `docs/superpowers/plans/2026-09-12-phase-58-cross-volume-failures.md` (663 LOC)

这 2 文件作为 untracked debris 在 worktree 中存在 24+ 小时，直到 Phase 61 backfill。

## 2. 提交结构 (3 atomic commits on `phase-57-p3-archdebt-reading-power`)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C1 | b82402b1 | docs(phase-58-backfill): commit 2 untracked Phase 58 docs | 2 | +867 |
| C2 | cf054a8d | test(phase-61): 2 regression guards for handoff doc pair completeness | 1 | +126 |
| C2.5 | (this commit) | fix(test-phase-61): add @template header for Phase 60 I079 compliance | 1 | +3/-2 |

**Net**: +867 LOC 历史 docs preserved + 2 guards + no version bump (per Phase 56b2 1-line doc fix precedent).

## 3. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `.venv/bin/python -m pytest tests/test_phase61_handoff_doc_pairs.py -v` | 2 passed | ✅ 2/2 in 0.06s |
| G2 | `.venv/bin/python -m pytest` all 9 phase guard files combined | 89 passed | ✅ 89/89 |
| G3 | `git status --porcelain docs/superpowers/{specs,plans}/` | empty (no untracked) | ✅ |
| G4 | `@template:` reference in Phase 61 docstring (Phase 60 I079 compliance) | string match | ✅ |

## 4. Risk & Rollback

**Risk**: VERY LOW
- 0 production code change
- 0 test code change
- Pure doc backfill (preserves historical Phase 58 records)

**Rollback**: `git revert b82402b1 cf054a8d` removes both commits cleanly (the guards would then re-detect untracked docs).

## 5. Lessons

1. **`docs/superpowers/specs/` 和 `plans/` 是 execution artifacts**：spec/plan 在 phase C0 创建，handoff 在 C4 创建。C0 commit message 必须**显式列出**所有 spec + plan 文件 (per Phase 56c lesson 5 + I079 §A5)。Phase 58 C0 commit message 只写 "add spec + handoff docs" — 模糊措辞漏检 plan 文件。
2. **G6 lazy-check 真正起作用了**：Phase 60 G6 "phase test files aware of template" 立即捕捉 Phase 61 test file 缺 @template header — 说明 lazy check 模式对新增 phase test files 有效，无需手动 enumerate。
3. **C2.5 fixup 比 spec 修改更轻量**：发现 Phase 61 docstring 缺 @template 后，没改 spec，而是直接 amend docstring + 单独 C2.5 commit。保留原始 C2 commit 的 git blame history (Phase 56c lesson 1)。

## 6. Carryover

- ✅ Phase 58 docs backfill → CLOSED
- ✅ Phase 60 I079 enforcement proves itself → Phase 61 catches missing @template via G6
- 新增：无 carryover
- 下一步候选: ff-merge to master (29 commits ahead) OR 产品 brainstorm

## 7. References

- Phase 58 (source leak): commit `a64f8604` "docs(phase-58): add spec + handoff docs (Phase 58 C6)"
- Phase 60 (I079 + G6): handoff `2026-09-13-phase-60-p3-archdebt-template-handoff.md`
- Phase 56b2 (1-line doc fix no-bump precedent): handoff `2026-09-12-phase-56b2-md-roundtrip-paths-handoff.md`
