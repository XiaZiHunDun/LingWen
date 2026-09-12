# Phase 57b — reading_power Tests Restoration Handoff

> **日期**: 2026-09-13
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **承接**: Phase 57 (e5fccfdb C3 误删 8 个 test 文件) + Phase 56b (world_db restoration precedent)
> **目标**: 从 `e5fccfdb^:tests/reading_power/` 恢复 8 文件 (~855 LOC) 到 `packages/lingwen-reading-power/tests/` + 修 2 处 sys.path hacks + 7 regression guards + v54.6 → v54.7

## 1. 背景 — 第三次 P3-ARCHDEBT 半迁移 bug

Phase 57 (2026-09-12) commit `e5fccfdb` C3 FULL DELETED `tests/reading_power/` 8 文件 (commit message: "FULL DELETE infra/reading_power + tests/reading_power")。但 `packages/lingwen-reading-power/tests/` 从未被创建 — **reading_power 包从 2026-09-12 起零测试覆盖**。

这是 Phase 56b (world_db) + Phase 56c (cross_volume) 同一模式的第三次复发。Phase 56c lesson (3) 明确："P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时**必须**同 phase 或显式 followup planned 迁 tests，不能 defer (Phase 56b + 56c 都吃过这亏)"。Phase 57 自己 followup plan 未列出 test migration。

## 2. 审计结果 (2026-09-13 fresh grep)

| 项 | Verdict |
|----|---------|
| 所有 8 文件已 canonical imports (`from lingwen_reading_power.X`) | ✅ Phase 57 C2 已 migrate，无需 sed |
| `tests/reading_power/__init__.py` (1 LOC) | ✅ restore as-is |
| `tests/reading_power/conftest.py:6` `sys.path.insert(0, os.path.dirname(__file__) + "/../..")` | ⚠️ 修 — Phase 56b lesson 1 (冗余 + namespace collision risk) |
| `tests/reading_power/test_llm_analyzer.py:8-9` `Path(__file__).parent.parent.parent; sys.path.insert` | ⚠️ 修 — Phase 56b2 lesson 2 (新位置 formula 算错) |
| 其他 6 test files (test_coolpoint_tracker/test_db/test_e2e/test_engine/test_hook_tracker/test_rule_matcher) | ✅ 已用 tmp_path，无 cwd-relative 路径 |

## 3. 提交结构 (4 atomic commits on `phase-57-p3-archdebt-reading-power`)

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | 57a0dcce | spec(phase-57b): reading_power tests restoration design | 1 | +130 |
| C1 | f4e11edb | scaffold(lingwen-reading-power): tests/__init__.py + conftest.py | 2 | +30 |
| C2 | 7ac66e3a | restore(lingwen-reading-power): 6 test files + 1 sys.path hack fix | 7 | +829 |
| C3 | 8774a8d4 | test(phase-57b): 7 regression guards | 1 | +239 |
| C4 | (this commit) | docs(phase-57b): I077 footnote + v54.7 + handoff + sync | 4 | +200 |

**Net**: +8 test files restored (~855 LOC), +2 sys.path hacks fixed, +7 guards, v54.6 → v54.7.

## 4. 验证 gates (all GREEN)

| Gate | 命令 | 期望 | 结果 |
|------|------|------|------|
| G1 | `.venv/bin/python -m pytest packages/lingwen-reading-power/tests/ -v --rootdir=packages/lingwen-reading-power` | 44 passed | ✅ 44/44 in 1.13s |
| G2 | `.venv/bin/python -m pytest tests/test_phase57b_reading_power_tests.py -v` | 15 passed | ✅ 15/15 in 1.58s |
| G3 | `.venv/bin/python -m pytest` all 7 phase guard files combined | 81 passed | ✅ 81/81 in 39.02s |
| G4 | `grep -rn "infra\.reading_power\|infra/reading_power" --include="*.py" --include="*.sh" --include="*.toml" .` | 0 hits | ✅ |
| G5 | I077 invariant + restoration footnote in CLAUDE.md | string match | ✅ |

## 5. sys.path hack 修复细节

### 5.1 conftest.py (Phase 56b lesson 1 模式)

```python
# BEFORE (e5fccfdb^ original):
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import pytest
from lingwen_reading_power.db import ReadingPowerDB
@pytest.fixture
def temp_db(tmp_path: Path) -> ReadingPowerDB:
    db_path = tmp_path / "test_reading_power.db"
    return ReadingPowerDB(db_path=db_path)

# AFTER (Phase 57b C1):
from pathlib import Path
import pytest
from lingwen_reading_power.db import ReadingPowerDB
@pytest.fixture
def temp_db(tmp_path: Path) -> ReadingPowerDB:
    db_path = tmp_path / "test_reading_power.db"
    return ReadingPowerDB(db_path=db_path)
```

完全删除 sys.path hack — `lingwen_reading_power` 是 uv workspace member 已 install。

### 5.2 test_llm_analyzer.py (Phase 56b2 lesson 2 模式)

```python
# BEFORE (e5fccfdb^ original):
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # = repo root when in tests/reading_power/
sys.path.insert(0, str(PROJECT_ROOT))
from unittest.mock import MagicMock
import pytest
from lingwen_reading_power.llm_analyzer import ...

# AFTER (Phase 57b C2):
from unittest.mock import MagicMock
import pytest
from lingwen_reading_power.llm_analyzer import ...
```

完全删除 sys.path block (理由: 同 conftest.py)。`parent.parent.parent` 公式在新位置 (`packages/lingwen-reading-power/tests/`) 会解析为 `packages/`，不是 repo root — 即使保留也会算错。

## 6. Risk & Rollback

**Risk**: LOW
- 所有 8 文件已 canonical imports (Phase 57 C2 已 migrate)
- 2 sys.path hacks 删除后 import 仍 work (uv workspace install)
- Functional gate 44/44 PASS 证明 API 兼容

**Rollback**: `git revert 8774a8d4^..57a0dcce` reverses all 4 commits cleanly (no DB migration, no schema change).

## 7. Lessons

1. **N.14 v19 变体 (conftest.py docstring 误报)**：G4 原版用 `assert "sys.path.insert" not in text` — conftest.py docstring **legitimately mentions** "sys.path.insert" 解释为什么删除，结果 G4 false-positive 失败。修复：用 `re.sub(r'""".*?""""', "", text, flags=re.DOTALL)` 移除 docstring 后再 regex search 实际 call (`re.search(r"^\s*sys\.path\.insert\s*\(", ...)`)。Phase 56b/56c lesson: test guards 引用 deleted patterns 时必须 strip docstring，避免自我引用陷阱。
2. **`parent.parent.parent` 在新位置是隐藏 bug**：原 test_llm_analyzer.py 用 `Path(__file__).parent.parent.parent` 解析 repo root — 在 `tests/reading_power/` 时正确 (3 层到 root)，搬到 `packages/<pkg>/tests/` 后**变 3 层到 packages/**，silent wrong。Phase 56b2 lesson 2: `parents[N]` 的 N 取决于文件深度，必须在新位置重新验证或直接删除冗余 sys.path block。
3. **Phase 56c lesson (3) 第三次复现**："P3-ARCHDEBT 删 infra/* + scaffold packages/*-db 时必须同 phase 或显式 followup planned 迁 tests"。Phase 57 spec 包含 I077 invariant 但**没有** test migration followup plan — 闭环 gap。Pattern 现在已 3 次重复 (Phase 56b world_db, Phase 56c cross_volume, Phase 57 reading_power) — 应在 P3-ARCHDEBT spec template 加强制 checklist: "test files 迁移 plan" 是必填项。
4. **`tests/` package 残留 0 + `packages/<pkg>/tests/` 完整 = 干净闭环**：本次 restoration 同时把 `tests/reading_power/` 空目录删除 (`rmdir` after `git mv`)，避免 Phase 53f 级别的 trivial cleanup 后续工作。

## 8. Carryover

- ✅ Phase 57 spec §6 "不在范围" carryover → CLOSED (本 phase 就是该 followup)
- ✅ `packages/lingwen-reading-power/` 零测试覆盖 critical bug → CLOSED
- 新增：建议 P3-ARCHDEBT spec template 加 "test files migration plan" 强制 checklist (lesson 3)。
- 下一步候选: 产品 brainstorm OR ff-merge to master。

## 9. References

- Spec: `docs/superpowers/specs/2026-09-13-phase-57b-reading-power-tests-restore-design.md`
- Phase 57 (source bug): commit `e5fccfdb` + handoff `docs/superpowers/handoffs/2026-09-12-phase-57-p3-archdebt-reading-power-handoff.md`
- Phase 56b (precedent): `docs/superpowers/handoffs/2026-09-12-phase-56b-world-db-tests-restoration-handoff.md`
- Phase 56b2 (cwd-paths): `docs/superpowers/handoffs/2026-09-12-phase-56b2-md-roundtrip-paths-handoff.md`
- Phase 56c (cross_volume): `docs/superpowers/handoffs/2026-09-12-phase-56c-p3-archdebt-cross-volume-tests-handoff.md`
