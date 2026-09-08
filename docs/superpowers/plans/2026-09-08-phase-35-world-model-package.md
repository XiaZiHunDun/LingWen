# Phase 35 — World Model Package 实施计划

> **Phase**: v34.0 (P2-ARCHDEBT 收官)
> **日期**: 2026-09-08
> **关联 spec**: `docs/superpowers/specs/2026-09-08-phase-35-world-model-package-design.md`
> **Pattern source**: Phase 34 LINGWEN-GOT (v33.0)
> **Worktree**: `.worktrees/phase-35-world-model-package` on branch `phase-35-world-model-package`

---

## Commit map (10 atomic commits, all gated)

| # | Type | Subject | Pre-verify |
|---|------|---------|-----------|
| C0 | docs | spec + plan | wc/lint 验证 |
| C1 | chore(packages) | scaffold lingwen-world-model package skeleton | uv sync OK |
| C2 | chore(packages) | git mv 10 world_model files + subplot_helpers + intra-package imports | ruff + smoke import |
| C3 | refactor(test) | move 13 tests/world_model/*.py → packages/lingwen-world-model/tests/ | 201/201 PASS |
| C4 | refactor(test) | migrate tests/subplot/test_subplot_integration.py | 11/11 PASS |
| C5 | refactor(poc) | migrate infra/poc/run_volume_1.py + string literal | ruff clean |
| C6 | refactor(test) | migrate 2 tests/consistency/checkers/* files | 22/22 PASS |
| preC7 | fix | filesystem-path string literal audit + fixup | grep 0 hits |
| C7 | chore(infra) | delete infra/world_model/ + infra/subplot/helpers.py + invariant #50 | grep 0 hits |
| C8 | test | regression guards + doc sync | 9+/9+ GREEN |

---

## C0 — spec + plan

**Files**:
- `docs/superpowers/specs/2026-09-08-phase-35-world-model-package-design.md` (NEW, ~280 lines)
- `docs/superpowers/plans/2026-09-08-phase-35-world-model-package.md` (NEW, this file)

**Pre-verify** (Phase 34 lesson — never trust hand-counts):
- `grep -c '^    "' infra/world_model/__init__.py` → 37 ✅
- `wc -l infra/world_model/*.py` → 2282 ✅
- `wc -l infra/subplot/helpers.py` → 52 ✅
- `grep -rln "from infra\.world_model\|from infra\.subplot\.helpers" --include="*.py" | grep -v "infra/world_model/" | grep -v "infra/subplot/helpers.py" | grep -v __pycache__` → 16 ✅

**Commit**: `docs(phase-35): spec + plan`

---

## C1 — scaffold lingwen-world-model package skeleton

**Files**:
- `packages/lingwen-world-model/pyproject.toml` (NEW, ~25 lines, mirror lingwen-got)
- `packages/lingwen-world-model/README.md` (NEW, ~15 lines)
- `packages/lingwen-world-model/src/lingwen_world_model/__init__.py` (NEW, empty stub + module docstring)
- `packages/lingwen-world-model/src/lingwen_world_model/__init__.py` placeholder
- root `pyproject.toml` `[tool.uv.workspace] members` → add `"packages/lingwen-world-model"` (Phase 34 lesson: BEFORE uv sync)

**Sub-steps**:
1. Write pyproject.toml (mirror lingwen-got: hatchling build, name=lingwen-world-model, deps=[lingwen-core])
2. Write README.md (1-paragraph description)
3. Create src/lingwen_world_model/__init__.py with minimal stub
4. Edit root pyproject.toml to register workspace member (Phase 34 lesson)
5. Run `uv sync --all-packages --offline` (verify package installable + importable)

**Pre-commit verify**:
- `uv run python -c "import lingwen_world_model"` (should fail with ModuleNotFoundError NOT seen yet, since package is empty — just verify no import errors)
- `ls packages/lingwen-world-model/.venv` or similar

**Commit**: `chore(packages): scaffold lingwen-world-model package skeleton`

---

## C2 — git mv 10 world_model files + subplot_helpers + intra-package imports

**Files**:
- 10 files moved: `infra/world_model/*.py` → `packages/lingwen-world-model/src/lingwen_world_model/*.py` (git mv preserves history)
- 1 file moved + renamed: `infra/subplot/helpers.py` → `packages/lingwen-world-model/src/lingwen_world_model/subplot_helpers.py`
- `packages/lingwen-world-model/src/lingwen_world_model/__init__.py` (fill in 37 `__all__` symbols)
- `packages/lingwen-world-model/src/lingwen_world_model/engine.py` — fix 2 intra-package imports (lifecycle + lazy queries)
- `packages/lingwen-world-model/src/lingwen_world_model/links.py` — fix 1 lazy registry import
- `packages/lingwen-world-model/src/lingwen_world_model/registry.py` — fix 1 lifecycle import
- `packages/lingwen-world-model/src/lingwen_world_model/queries.py` — fix 1 lifecycle import
- `packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py` — fix 1 lazy import
- `packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py` — fix 1 lazy import
- `packages/lingwen-world-model/src/lingwen_world_model/__init__.py` — replace `from infra.subplot.helpers import` with `from lingwen_world_model.subplot_helpers import`

**Sub-steps**:
1. `git mv infra/world_model/{__init__,engine,character_snapshot,foreshadow_snapshot,key_point_graph,lifecycle,links,queries,registry,snapshot_diff,snapshot_store}.py packages/lingwen-world-model/src/lingwen_world_model/`
2. `git mv infra/subplot/helpers.py packages/lingwen-world-model/src/lingwen_world_model/subplot_helpers.py`
3. sed `from infra.world_model.` → `from lingwen_world_model.` across 7 files (engine, links, registry, queries, character_snapshot, foreshadow_snapshot, + __init__)
4. sed `from infra.subplot.helpers` → `from lingwen_world_model.subplot_helpers` (1 site in __init__.py)
5. Update subplot_helpers.py docstring (was referring to `infra/world_model/__init__`)
6. Run `ruff check packages/lingwen-world-model/src/` (Phase 34 lesson: ruff --fix for auto-fixable violations)
7. Verify package importable: `uv run python -c "from lingwen_world_model import RippleEngine, KeyPointGraph, SnapshotStore, subplots_count"` 

**Pre-commit verify**:
- `grep -rn "infra\.world_model\|infra\.subplot\.helpers" packages/lingwen-world-model/src/lingwen_world_model/` → 0 行
- `uv run python -c "import lingwen_world_model; print(len(lingwen_world_model.__all__))"` → 37
- `ruff check packages/lingwen-world-model/src/` → clean

**Commit**: `chore(packages): git mv 10 world_model files + subplot_helpers + intra-package imports`

---

## C3 — move 13 tests/world_model/*.py → packages/lingwen-world-model/tests/

**Files**:
- 13 files moved: `tests/world_model/*.py` → `packages/lingwen-world-model/tests/*.py` (git mv)
- All 13 files: sed `from infra.world_model.` → `from lingwen_world_model.`
- New: `packages/lingwen-world-model/tests/__init__.py` (empty, mirror lingwen-got/tests/)
- Delete: `tests/world_model/` (after verify)

**Sub-steps**:
1. mkdir `packages/lingwen-world-model/tests/`
2. `git mv tests/world_model/test_*.py packages/lingwen-world-model/tests/`
3. sed across 13 files: `from infra.world_model.` → `from lingwen_world_model.`
4. Run `uv run --project packages/lingwen-world-model pytest packages/lingwen-world-model/tests/ -q` → 201/201 PASS

**Pre-commit verify**:
- `grep -rn "infra\.world_model" packages/lingwen-world-model/tests/` → 0 行
- pytest baseline preserved: 201/201

**Commit**: `refactor(test): move 13 tests/world_model/*.py → packages/lingwen-world-model/tests/`

---

## C4 — migrate tests/subplot/test_subplot_integration.py

**Files**:
- `tests/subplot/test_subplot_integration.py:27` — sed `from infra.subplot.helpers import (add_subplot, get_active_subplots, subplots_count)` → `from lingwen_world_model.subplot_helpers import (...)`

**Pre-commit verify**:
- `pytest tests/subplot/test_subplot_integration.py` → 11/11 PASS
- `grep "infra\.subplot\.helpers" tests/subplot/` → 0 行

**Commit**: `refactor(subplot): migrate test_subplot_integration.py to lingwen_world_model`

---

## C5 — migrate infra/poc/run_volume_1.py

**Files**:
- `infra/poc/run_volume_1.py:44` — sed `from infra.world_model import (...)` → `from lingwen_world_model import (...)`
- `infra/poc/run_volume_1.py:312` — sed `source="infra.world_model.WorldSnapshot"` → `source="lingwen_world_model.WorldSnapshot"` (string literal fix)

**Pre-commit verify**:
- `pytest` tests that exercise run_volume_1 (if any) → all PASS
- `grep "infra\.world_model" infra/poc/run_volume_1.py` → 0 行
- `grep '"infra/world_model' infra/poc/run_volume_1.py` → 0 行 (filesystem path string)

**Commit**: `refactor(poc): migrate run_volume_1.py to lingwen_world_model + fix string literal`

---

## C6 — migrate 2 tests/consistency/checkers/* files

**Files**:
- `tests/consistency/checkers/test_pacing_ripple_integration.py:30` — sed registry import
- `tests/consistency/checkers/test_foreshadow_ripple_alignment.py:28-29` — sed lifecycle + registry imports

**Pre-commit verify**:
- `pytest tests/consistency/checkers/test_pacing_ripple_integration.py tests/consistency/checkers/test_foreshadow_ripple_alignment.py` → 22/22 PASS
- `grep "infra\.world_model" tests/consistency/checkers/` → 0 行

**Commit**: `refactor(tests): migrate 2 consistency ripple tests to lingwen_world_model`

---

## preC7 — filesystem-path string literal audit + fixup

**Rationale**: Phase 34 lesson #4 (4th occurrence) — filesystem path string literals 被 import grep 漏掉。

**Audit grep**:
```bash
grep -rn '"infra/world_model' --include="*.py" .
grep -rn '"infra/subplot/helpers' --include="*.py" .
grep -rn "infra/world_model" --include="*.md" .  # docstring/string references
```

**Expected hits** (will fix in this commit):
- `infra/world_model/data_structures.py` 引用 — actually already deleted in Phase 32
- `packages/lingwen-core/src/lingwen_core/domain/{chapter,common}.py` — docstring mentioning historical migration (保留,描述过去迁移事件)
- `packages/lingwen-core/tests/test_domain.py` — docstring
- `infra/subplot/helpers.py` (已删除? — 不,还在,C2 已 mv 到新位置,docstring 应该清理)
- `tests/test_phase32_shim_cleanup.py` — historical reference (保留,描述 Phase 32)
- 可能有的其他 docstring/string references

**Fix scope**:
- docstrings in MIGRATED files (`infra/world_model/__init__.py` 在 C2/C7 之间是否需要 interim docstring?): 不需要,C7 直接删除整个 dir
- LingWen 描述性 docstring 提到 `infra/world_model/` (e.g., `DESIGN.md`): 更新为 `packages/lingwen-world-model/`
- CLAUDE.md 引用:在 C8 doc sync 阶段处理

**Pre-commit verify**:
- `grep -rn '"infra/world_model' --include="*.py" packages/ apps/ tests/ infra/ lingwen-world-model/` → 0 行 (生产代码)
- `grep -rn "infra/world_model" --include="*.md" .lingwen/` → 0 行 (排除 docstring 历史参考)

**Commit**: `fix(workflow-paths): audit + update stale infra/world_model references`

---

## C7 — delete infra/world_model/ + infra/subplot/helpers.py + invariant #50

**Files**:
- `infra/world_model/` (整个 dir) — deleted (10 files)
- `infra/subplot/helpers.py` — deleted (no __pycache__ 残留)
- `infra/world_model/__pycache__/` — deleted (Phase 34 C6 cleanup pattern)
- `.lingwen/architecture.yml` — add invariant #50
- `.lingwen/architecture.yml` version line — bump to "34.0"

**Sub-steps**:
1. `git rm -r infra/world_model/` (rm + dir cleanup)
2. `git rm infra/subplot/helpers.py` (single file)
3. Verify `infra/subplot/__init__.py` 不引用 helpers.py (run grep audit)
4. Edit `.lingwen/architecture.yml`:
   - version → "34.0"
   - invariant #50 NEW
5. Run audit greps (G11):
   - `grep -rln "infra\.world_model\b" --include="*.py" packages/ apps/ tests/ infra/` → 0 行
   - `ls infra/world_model/ 2>/dev/null` → No such file
   - `ls infra/subplot/helpers.py 2>/dev/null` → No such file

**Pre-commit verify**:
- All G11 gates pass
- Phase 35 invariants enforced

**Commit**: `chore(infra): delete infra/world_model/ + infra/subplot/helpers.py + add invariant #50`

---

## C8 — regression guards + doc sync

**Files**:
- `tests/test_phase35_world_model.py` (NEW, ~150 lines, mirror Phase 34 guards):
  - `test_pyproject_exists` — packages/lingwen-world-model/pyproject.toml 存在
  - `test_package_importable` — `import lingwen_world_model` works
  - `test_init_has_37_symbols` — `__all__` 长度 = 37
  - `test_infra_world_model_deleted` — infra/world_model/ 不存在
  - `test_infra_subplot_helpers_deleted` — infra/subplot/helpers.py 不存在
  - `test_subplot_helpers_migrated` — lingwen_world_model.subplot_helpers 存在且 3 functions
  - `test_no_infra_world_model_imports` — 全 repo grep audit 0 hits
  - `test_no_infra_subplot_helpers_imports` — 全 repo grep audit 0 hits
  - `test_canonical_symbols` — 所有 37 __all__ symbols 都能从 lingwen_world_model import
  - `test_invariant_50_in_yaml` — .lingwen/architecture.yml 含 invariant #50
- `tests/test_phase32_shim_cleanup.py` — 更新 (如果之前有断言 "infra/world_model/data_structures.py 已删除",保持不变 — 已正确)
- `CLAUDE.md` — 添加 v34.0 entry
- `collaboration/CURRENT_STATUS.md` — 状态更新
- `collaboration/BACKLOG.md` — P2-ARCHDEBT remaining 1/1 → CLOSED;P3-ARCHDEBT 候选更新

**Pre-commit verify**:
- `pytest tests/test_phase35_world_model.py` → 9+/9+ GREEN
- 所有 G1-G12 gates pass
- ruff clean

**Commit**: `test(phase-35): regression guards + doc sync`

---

## Final verification (post-C8)

| Suite | Target |
|-------|--------|
| `tests/test_phase35_world_model.py` | 9+/9+ GREEN |
| `packages/lingwen-world-model/tests/` | 201/201 PASS |
| `packages/lingwen-core/tests/` | 68/68 PASS |
| `packages/lingwen-got/tests/` | 208/208 PASS |
| `tests/world_model/` (old) | 0 files |
| `apps/studio_api/tests/` | 82/82 PASS |
| `tests/consistency/checkers/{pacing_ripple_integration,foreshadow_ripple_alignment}.py` | 22/22 PASS |
| `tests/subplot/test_subplot_integration.py` | 11/11 PASS |
| ruff (新 + 改 files) | clean |

---

## Risk mitigation summary

| Risk | Mitigation |
|------|-----------|
| workspace member 注册 before uv sync | C1 步骤 4 + uv sync |
| intra-package import 漏改 | C2 步骤 3-4 + grep audit |
| filesystem-path string literal 漏改 | preC7 专项 commit |
| pytest namespace conflict | package tests 用独立 rootdir |
| .db 误 add (Phase 34 C3 lesson) | explicit git add paths |
| ruff auto-fixable violations | ruff --fix post-edit |

---

## Phase history refs

- Phase 32 handoff: `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md`
- Phase 34 handoff: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`
- Phase 35 handoff: TBD (post-merge)
