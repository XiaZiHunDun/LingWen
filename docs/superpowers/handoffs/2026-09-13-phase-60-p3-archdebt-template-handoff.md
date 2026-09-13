# Phase 60 — P3-ARCHDEBT Spec Template Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 57b handoff lesson (3) — "建议 P3-ARCHDEBT spec template 加 'test files migration plan' 强制 checklist"
> **目标**: 防止 Phase 56b (world_db) + Phase 56c (cross_volume) + Phase 57 (reading_power) 三次半迁移 bug 再次发生
> **新增**: `docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` + I079 invariant + 6 regression guards

## 1. 背景 — 第三次复发的根因

Phase 57b handoff lesson (3):
> "Phase 56c lesson (3) **第三次复现** (Phase 56b world_db + Phase 56c cross_volume + Phase 57 reading_power) — P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时**必须**同 phase 或显式 followup planned 迁 tests。建议 P3-ARCHDEBT spec template 加 'test files migration plan' 强制 checklist。"

Phase 60 实施该建议。

## 2. 模板结构 (4 sections)

### §A. test files migration plan (MANDATORY)

每个 P3-ARCHDEBT spec **必须**回答 5 个子问题：

- **A1. test files inventory** — 列出所有相关 test files + 标注 MIGRATE/DELETE/RETAIN-ORPHAN
- **A2. MIGRATE 路径** — `git mv tests/X/<file>.py packages/<pkg>/tests/`, sed migrate imports, sys.path hack cleanup (Phase 56b lesson 1), cwd-path fixup (Phase 56b2 lesson 2)
- **A3. DELETE 路径** — single commit pathspec BOTH old test + new, 验证无 cross-cutting dependency
- **A4. RETAIN-ORPHAN 路径** (NOT ALLOWED) — explicit justification required
- **A5. Half-migration defense** — C3 pathspec BOTH, commit message must list test files explicitly

### §B. P3-ARCHDEBT spec 标准结构 (recommended)

9 sections: 背景 / 9-pattern audit / 配套 stale refs / 计划 / **§A** / 验证 gates / 风险评估 / 不在范围 / 完工标准

### §C. Lessons from prior phases

强制引用 Phase 56b/56c/57b + N.14 lesson 1

### §D. Anti-patterns

- ❌ C3 commit 只写 "+ I0XX" 而跳过 test files
- ❌ 让 tests/X/ 留下孤儿文件
- ❌ MIGRATE 测试用 `git rm` + `git add` (分开 commit, blame 丢失)
- ❌ spec 缺 §A
- ❌ "defer test migration to followup"

## 3. 提交结构 (3 atomic commits on `phase-57-p3-archdebt-reading-power`)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | 7afbe20a | spec(phase-60): P3-ARCHDEBT spec template with mandatory test files migration plan | 1 | +96 |
| C1 | (this commit) | chore(arch+guards): I079 invariant + 6 regression guards + CLAUDE.md | 2 | +200 |
| C2 | (this commit) | docs(phase-60): v54.8 + handoff + sync | 4 | +150 |

**Net**: +1 template doc + 1 invariant + 6 guards, v54.7 → v54.8.

## 4. I079 invariant

```yaml
# .lingwen/architecture.yml
- id: I079   # ★ Phase 60 NEW
  rule: "每个 P3-ARCHDEBT spec doc 必须 (1) 在文件头声明
    '@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md'
    引用本模板 + (2) 包含完整 §A. test files migration plan 子章节
    (Phase 57b lesson 3 third occurrence prevention — Phase 56b
    world_db + Phase 56c cross_volume + Phase 57 reading_power 三次复现).
    enforcement: tests/test_phase60_p3_archdebt_template.py 扫所有 spec
    文件验证模板引用 + §A 章节存在"
  severity: error
  scope: "all future P3-ARCHDEBT specs; template file lives at
    docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md"
```

## 5. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `.venv/bin/python -m pytest tests/test_phase60_p3_archdebt_template.py -v` | 6 passed | ✅ 6/6 in 0.04s |
| G2 | `.venv/bin/python -m pytest` all 8 phase guard files combined | 87 passed (was 81 + 6) | ✅ |
| G3 | `_P3_ARCHDEBT_TEMPLATE.md` exists with all required sections | string matches | ✅ |
| G4 | I079 in architecture.yml + CLAUDE.md invariant table | string match | ✅ |

## 6. Risk & Rollback

**Risk**: VERY LOW
- 只新增 template doc + invariant + guards, 0 production code change
- I079 不影响现有 spec (只强制 future spec)

**Rollback**: `git revert` 3 commits cleanly.

## 7. Lessons

1. **Meta-improvement (process change) 比 code change ROI 高**: 1 个 template doc + 1 个 invariant 防止未来 N 次半迁移 bug。比再清理 10000 LOC dead code ROI 高 (因为预防未来更大问题)。
2. **Lesson 3 from prior phase 是 systematic anti-pattern 信号**: Phase 57b lesson (3) 说"第三次复现" — 这是 anti-pattern 已形成的信号，需要 system change (template + invariant) 而非个案处理。
3. **Template doc 是 machine-readable process contract**: 模板不仅给人类看，I079 + regression guards 让它 enforce-able by automation。Phase 56b/56c/57b 的"defer to followup"反模式现在有强制 check。

## 8. Carryover

- ✅ Phase 57b handoff lesson (3) "P3-ARCHDEBT spec template 加 test files migration plan" → CLOSED
- 新增：建议未来 P3-ARCHDEBT phase (e.g., Phase 70+) 必须引用本模板 + 包含 §A
- 下一步候选: ff-merge to master (本会话 24 commits ahead) OR 产品 brainstorm

## 9. References

- Template: `docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md`
- I079 invariant: `.lingwen/architecture.yml` (after I070)
- Guards: `tests/test_phase60_p3_archdebt_template.py`
- Phase 57b (source lesson): `docs/superpowers/handoffs/2026-09-13-phase-57b-reading-power-tests-restore-handoff.md` lesson (3)
- Phase 56c (third occurrence root): `docs/superpowers/handoffs/2026-09-12-phase-56c-p3-archdebt-cross-volume-tests-handoff.md` lesson (3)
