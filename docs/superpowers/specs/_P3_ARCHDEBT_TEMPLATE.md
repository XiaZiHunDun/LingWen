# P3-ARCHDEBT Spec Template — MANDATORY CHECKLIST

> **目的**: 防止 Phase 56b (world_db) + Phase 56c (cross_volume) + Phase 57 (reading_power) 三次复现的 "P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时 test files 留 tests/X/ = orphan" bug。
> **引用**: Phase 57b handoff lesson (3) "建议 P3-ARCHDEBT spec template 加 'test files migration plan' 强制 checklist"。
> **添加**: Phase 60 (2026-09-13)。
> **编号**: I079 invariant (P3-ARCHDEBT spec MUST reference this template + include §7 test files migration plan)。

## 使用方式

每个 P3-ARCHDEBT phase 的 spec doc (e.g., `2026-09-XX-phase-Y-p3-archdebt-...md`) **必须**:

1. 在文件头部 `@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` 一行声明引用本模板
2. 在 spec §X (Plan 章节) 包含完整的 **§A. test files migration plan** 子章节（见下文）
3. 在 spec §X (Lessons from prior phases) 引用 Phase 56b + 56c + 57b 三次复现的反思

**省略任一项 = spec incomplete**。回归 guard `tests/test_phase60_p3_archdebt_template.py::test_phase_specs_reference_template` 会扫所有 spec 文件验证。

---

## §A. test files migration plan (MANDATORY 子章节)

P3-ARCHDEBT spec **必须**回答以下问题。任一项未回答 = spec incomplete。

### A1. test files inventory

- [ ] 列出**所有**与目标 `infra/X/` 模块相关的 test files (用 `grep -rln "infra\.X\b\|infra/X" tests/`)
- [ ] 标注每个 test file 的 LOC 和 pytest path
- [ ] 确认 test files 在 P3-ARCHDEBT 计划中是 MIGRATE / DELETE / RETAIN-ORPHAN 哪种

### A2. MIGRATE 路径

如果 MIGRATE:
- [ ] 目标位置: `packages/<canonical-package>/tests/<test-file>.py`
- [ ] 迁移步骤: `git mv tests/X/<file>.py packages/<pkg>/tests/<file>.py` (single commit, pathspec BOTH old + new for blame preservation — Phase 56c lesson 1)
- [ ] Imports 迁移: `from infra.X.Y import` → `from <canonical_pkg>.Y import` (sed 全 file)
- [ ] sys.path hack cleanup: 删除 conftest.py `sys.path.insert(...)` (Phase 56b lesson 1)
- [ ] cwd-relative path fixup: `Path(__file__).parent.parent.parent` → `parents[3]` 或删除冗余 (Phase 56b2 lesson 2)
- [ ] Functional gate: `pytest packages/<pkg>/tests/ -v` 必须 100% pass

### A3. DELETE 路径

如果 DELETE:
- [ ] 确认 test file 仅 service deleted infra/X/，无 cross-cutting 价值
- [ ] 删除时 single commit pathspec BOTH old test + new (如适用)
- [ ] 验证无其他 test file 隐式依赖 (e.g., `monkeypatch.setattr("infra.X.Y", ...)` — Phase 57b N.14 lesson 6)

### A4. RETAIN-ORPHAN 路径 (NOT ALLOWED without explicit justification)

如果 RETAIN-ORPHAN (e.g., leave tests/X/ alive while infra/X/ deleted):
- [ ] **必须 explicit justification** — why tests must stay at tests/X/ instead of moving
- [ ] 列出 plan 之外的 dependency (e.g., cross-package fixture, shared conftest)
- [ ] **强烈不推荐** — Phase 56c lesson 3 明确指出 "defer = never" 反模式

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

- [ ] **C3 (FULL DELETE) commit 的 pathspec 必须包含 BOTH** `infra/X/` AND `tests/X/<test-files>` (如适用)
- [ ] **C3 commit message 必须明确**: "deleted infra/X + tests/X/<file>.py + I0XX invariant" (single sentence)
- [ ] **commit message 不能只**写 "+ I0XX" 而跳过 tests 部分
- [ ] 验证: `git show <C3-SHA> --stat` 必须显示 test files 在 deletions 列表中

---

## §B. P3-ARCHDEBT spec 标准结构 (recommended)

虽然本模板强制 §A test files migration plan，其他章节是 recommended structure：

1. **背景** — 触发本 phase 的 prior carryover / spec §6 deferred / audit finding
2. **9-pattern 审计结果** — 表格列出 9 个 pattern + verdict (per N.14 lesson 1)
3. **配套 stale refs** — `__init__.py` docstring, `ALLOWLIST`, gitignore, meta-tests
4. **计划** — 5-column table (Commit / Subject / Files / +/- / Risk)
5. **§A. test files migration plan** ← **MANDATORY**
6. **验证 gates** — pytest functional gate + 9-pattern audit clean
7. **风险评估** — table per change
8. **不在范围** — explicit defer list
9. **完工标准** — checklist

---

## §C. Lessons from prior phases (recommended reference)

每个 P3-ARCHDEBT spec **应该**在 Lessons / Background 引用：

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit, `chr(47)` regex split trick
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location, docstring-stripped regex
- **N.14 lesson 1 (9-pattern audit matrix)**: Phase 51 列出 10 次复现模式

---

## §D. Anti-patterns (must NOT do)

- ❌ 在 C3 commit 中**只**写 "+ I0XX" 而不列 test files
- ❌ 让 tests/X/ 留下孤儿文件 (Phase 56b/56c/57b lesson 3)
- ❌ MIGRATE 测试用 `git rm` 旧路径 + `git add` 新路径 (分开 commit, blame 丢失 — Phase 56c lesson 1)
- ❌ spec 缺 §A test files migration plan (本 template 强制)
- ❌ "defer test migration to followup" (Phase 56c lesson 3: "defer = never")
