# Phase 57b reading_power Tests Restoration — Design

> **目标**: 恢复 Phase 57 C3 (e5fccfdb) 误删的 8 个 reading_power 测试文件到 `packages/lingwen-reading-power/tests/`，修 2 处 sys.path hack，加 5+ regression guards，v54.6 → v54.7
> **承接**: Phase 57 P3-ARCHDEBT (e5fccfdb 删 `infra/reading_power/` + `tests/reading_power/` 8 文件) + Phase 56b (world_db tests restoration precedent)
> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`

## 1. 背景 — 跟 Phase 56b/56c 同样半迁移 bug

Phase 57 (2026-09-12) C3 commit `e5fccfdb` 删 `infra/reading_power/` + `tests/reading_power/` 8 文件 (commit message "FULL DELETE ... + tests/reading_power")。**但** `packages/lingwen-reading-power/tests/` 从未被创建。

Phase 57 handoff §Lessons (1) 写明: "P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时 test files 留 tests/X/ = orphan，followup 必须原 phase 规划，不能 defer" — 但 Phase 57 自己 followup plan (Phase 57b) 未列出。

Phase 56c handoff lesson (3) 明确: "P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时**必须**同 phase 或显式 followup planned 迁 tests，不能 defer (Phase 56b + 56c 都吃过这亏)"。

Phase 57 重蹈覆辙 — Phase 57b 是 followup restoration。

## 2. 待恢复 8 文件 (~855 LOC)

| File | LOC | Notes |
|------|-----|-------|
| `__init__.py` | 1 | 包标记 (空) |
| `conftest.py` | 19 | `sys.path.insert(0, ...)` hack — **需修** (Phase 56b lesson 1) |
| `test_coolpoint_tracker.py` | 110 | 已 canonical imports |
| `test_db.py` | 143 | 已 canonical imports |
| `test_e2e.py` | 178 | 已 canonical imports + tmp_path |
| `test_engine.py` | 51 | 已 canonical imports |
| `test_hook_tracker.py` | 85 | 已 canonical imports |
| `test_llm_analyzer.py` | 131 | `Path(__file__).parent.parent.parent` — **需修** (新位置 parents[3]) |
| `test_rule_matcher.py` | 137 | 已 canonical imports + tmp_path |

**审计 (2026-09-13 fresh grep)**:
- 所有 8 文件**已用 canonical `from lingwen_reading_power.X import`** (Phase 57 C2 已 migrate)
- 2 文件含 cwd-relative sys.path hacks:
  - `conftest.py:6`: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))` — 在 `tests/reading_power/` 时解析到 `<package>/`，搬到 `packages/<pkg>/tests/` 后**仍 work** 但冗余 (uv workspace 已 install lingwen_reading_power)
  - `test_llm_analyzer.py:8-9`: `PROJECT_ROOT = Path(__file__).parent.parent.parent; sys.path.insert(0, str(PROJECT_ROOT))` — 在 `tests/reading_power/` 时 `parent.parent.parent` = repo root；搬到 `packages/<pkg>/tests/` 后**错** (parent.parent.parent = packages/, 不是 repo root)

## 3. 计划 (3 atomic commits on `phase-57-p3-archdebt-reading-power`)

| Commit | Subject | Files | +/- |
|--------|---------|-------|-----|
| C0 | spec + plan handoff (this doc) | 1 | +150 |
| C1 | `scaffold(lingwen-reading-power): tests/__init__.py + conftest.py (Phase 57b)` | 2 | +35 |
| C2 | `restore(lingwen-reading-power): 6 test files + 2 sys.path hacks fix (Phase 57b)` | 6 | +719 |
| C3 | `test(phase-57b): 7 regression guards` | 1 | +180 |
| C4 | `docs(phase-57b): I077 note + v54.7 + handoff + sync` | 4 | +200 |

**Net**: +8 files / -0 LOC code, +2 hack fix, +7 guards, v54.6 → v54.7.

### C1 详细

新建 `packages/lingwen-reading-power/tests/`:
- `__init__.py`: 单行 docstring (Phase 35 lingwen-world-model 同模式, Phase 56b lesson 1)
- `conftest.py`: 移除 `sys.path.insert` hack (uv workspace 已 install)；只保留 `temp_db` fixture

### C2 详细

恢复 6 test files (test_coolpoint_tracker / test_db / test_e2e / test_engine / test_hook_tracker / test_rule_matcher) — 这些都已 canonical imports + tmp_path，无需修改。

迁移 `test_llm_analyzer.py`:
```python
# BEFORE (e5fccfdb^ original, 在 tests/reading_power/):
PROJECT_ROOT = Path(__file__).parent.parent.parent  # = repo root when in tests/reading_power/
sys.path.insert(0, str(PROJECT_ROOT))

# AFTER (in packages/lingwen-reading-power/tests/):
# Use parents[3] (tests → lingwen-reading-power → packages → repo)
# But the sys.path.insert is redundant — drop it entirely
# (uv workspace already installs lingwen_reading_power)
```

实际方案: 完全删除 sys.path block (Phase 56b lesson 1 — workspace install 已足够)。如果未来 test_llm_analyzer 真的需要 PROJECT_ROOT (比如访问 fixtures/), 用 `Path(__file__).resolve().parents[3] / "..."` 模式 (Phase 56b2 lesson 2)。

### C3 详细: 7 regression guards

| Guard | Assertion |
|-------|-----------|
| G1 | `packages/lingwen-reading-power/tests/` EXISTS |
| G2 | 8 specific test files present |
| G3 | `from lingwen_reading_power.X import` 0 references to `infra.reading_power` |
| G4 | conftest.py 不含 `sys.path.insert` (Phase 56b lesson 1) |
| G5 | test_llm_analyzer.py 不含 cwd-relative sys.path hack |
| G6 | `tests/reading_power/` directory NOT EXIST (no orphan back) |
| G7 | `pytest packages/lingwen-reading-power/tests/ -v` 全部通过 (functional gate) |

### C4 详细

**I077 note**: 加 footnote 说明 Phase 57b followup (v53.0 invariant 主体不动, 只补 followup history)

**Version bump**: v54.6 → v54.7 in CLAUDE.md version line.

**Handoff**: `docs/superpowers/handoffs/2026-09-13-phase-57b-reading-power-tests-restore-handoff.md`.

## 4. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `.venv/bin/python -m pytest packages/lingwen-reading-power/tests/ -v` | 全部通过 (估 ~50+ tests) |
| G2 | `.venv/bin/python -m pytest tests/test_phase57b_reading_power_tests.py tests/test_phase53e_orphan_runtime_artifacts.py tests/test_phase53d_event_sourcing.py tests/test_phase53c_tools_legacy_top.py tests/test_phase53_p3_archdebt_dead_code_cleanup.py tests/test_phase58_cross_volume_failures.py tests/test_infra_init_no_deferred_re_exports.py` | 7+4+7+26+6+16+7 = 73 GREEN |
| G3 | `grep -rn "infra\.reading_power\|infra/reading_power" --include="*.py" .` | 0 hits |
| G4 | 3 cwd 验证 (repo root / package dir / tests dir) 全部通过 | 全部 pass |

## 5. 风险评估

| 风险 | 概率 | 缓解 |
|------|------|------|
| Phase 57 当时已 mograte 部分 test 内容, 恢复后与当前 packages/lingwen-reading-power/src/ API 不匹配 | MEDIUM | C2 跑 pytest functional gate (G1), 如果 fail 用 sed 重 migrate |
| conftest.py sys.path 删除后 fixture 失效 | LOW | uv workspace install 已包含 lingwen_reading_power, 移除 sys.path hack 后 import 仍 work |
| test_llm_analyzer.py 真的需要 PROJECT_ROOT (e.g., 访问 fixtures/) | LOW | 审计源码确认 (现在不需要) |

**Overall risk**: LOW — Phase 56b 同模式成功闭环，Phase 56b2 cwd-path fixup 模式已知。

## 6. 不在范围

- Reading power 自身功能改进 (out of scope for restoration)
- Phase 57 当时迁移的 4 bug fixups (已 shipped via C1.5 in Phase 57, 保留)
- `tests/reading_power/` 空目录清理 (deferred 到 Phase 53f 或后续 — 不是 P0 因为空目录无害)

## 7. 完工标准

- [ ] C0-C4 commit on `phase-57-p3-archdebt-reading-power`
- [ ] master ff-merged after user approval
- [ ] v54.7 in version line
- [ ] 8 test files restored to `packages/lingwen-reading-power/tests/`
- [ ] 2 sys.path hacks fixed
- [ ] 7 NEW guards GREEN
- [ ] Functional pytest gate: `packages/lingwen-reading-power/tests/` 全部通过
- [ ] All baselines preserved (66/66 → 73/73)
- [ ] handoff committed
- [ ] CURRENT_STATUS + BACKLOG synced
