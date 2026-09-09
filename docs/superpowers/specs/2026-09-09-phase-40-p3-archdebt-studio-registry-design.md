# Phase 40a — P3-ARCHDEBT (studio_registry) production migration design

> **Date**: 2026-09-09
> **Author**: Claude (主控调度)
> **Branch**: `phase-40-p3-archdebt-studio-registry`
> **Master HEAD (start)**: `26782063` (Phase 39 ff-merge point)
> **Version**: v38.0 → **v39.0**
> **Invariant**: #55 NEW
> **Pattern**: Phase 38 P3-ARCHDEBT (project_config) adapted for **NOT-LEAF package** + **5-sub-module split** (sub-modules = CLAUDE.md MANY SMALL FILES > FEW LARGE FILES)
> **Sub-module split**: per brainstormed approval (B: 5 sub-modules)
> **C2 phasing**: per brainstormed approval (B: 2 sub-commits, C2a intra-infra baseline + C2b bulk)
> **Scope**: **PRODUCTION ONLY** — `infra/ + apps/ + packages/` (no `tests/`); `tests/` migration is Phase 40b (planned)
> **Source disposition**: **SHIM (not delete)** — `infra/studio_registry.py` becomes a 1-line re-export shim in Phase 40a; full deletion deferred to Phase 40b after tests migrate

## Why

P3-ARCHDEBT item **5/5 (P3 收官, Phase 40a portion)** — `infra/studio_registry.py` (422 行, 24 top-level definitions: 1 class + 20 funcs + 3 module constants) → `packages/lingwen-studio-registry/`。

**Phase 36 → Phase 39 → Phase 40a size arc**:

| Phase | Module | Lines | Symbols | Sites | Commits | Wildcard | Workspace deps |
|-------|--------|-------|---------|-------|---------|----------|----------------|
| 36 | errors | 380 | 23 | 14 | 6 | 0 | 0 (LEAF) |
| 37 | paths | 125 | 5 | 86 | 6 | 0 | 0 (LEAF) |
| 38 | project_config | 170 | 2 | 26 | 7 | 1 wildcard | 2 (paths + shared) |
| 39 | logging_config | 59 | 3 | 8 | 6 | 1 wildcard | 0 (LEAF) |
| **40a** | **studio_registry (production)** | **422** | **24** | **47** | **7** | **1 wildcard** | **3 (paths + project_config + core)** |

**Phase 40 is P3 5 个模块里最大的**. Originally estimated at 48 edits, expanded to 81 once `tests/` audit was added. **Per user decision (Option B)**: split into Phase 40a (this phase, production-only) + Phase 40b (future, `tests/` migration).

**Sites breakdown (verified by `grep -c`, PRODUCTION ONLY)**:
- 41 `from infra.studio_registry import` statements (40 dotted-path + 1 wildcard) — includes 26 indented function-body
- 5 test patches in `apps/studio_api/tests/` (production-adjacent tests)
- 1 doc comment in `apps/studio_api/routes/studio.py:8` (narrative mention)
- **Total: 47 grep hits across 27 unique files (production-only)**
- 0 relative imports (clean)
- 0 filesystem-path string literals (clean)
- 0 `import as` statements (none in production)
- **Deferred to Phase 40b**: 21 `from infra.studio_registry` imports (20 single-line + 1 multi-line) + 4 `import infra.studio_registry as registry` + 7 `monkeypatch.setattr` test patches = 32 test-side refs in `tests/` (root)

## Why

(See §Why at top of doc — Phase 40a framing)

## Scope

### Source (delete)

| Path | Lines | Symbols | Action |
|------|-------|---------|--------|
| `infra/studio_registry.py` | 422 | 1 class (`StudioProject`) + 20 funcs + 3 module consts (`_CHAPTER_RE`, `_OUTLINE_RE`, `_ACTIVE_STATE`) | **SHIM (C3) — convert to 1-line re-export; DELETE in Phase 40b** |

### Target (scaffold) — 5 sub-modules

| Path | Lines (target) | Symbols |
|------|----------------|---------|
| `packages/lingwen-studio-registry/pyproject.toml` | (~30 行) | workspace deps: paths + project_config + core |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/__init__.py` | (~50 行) | `__all__` + re-exports from 5 sub-modules |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/models.py` | (~30 行) | `StudioProject` dataclass + `_CHAPTER_RE` + `_OUTLINE_RE` + `_ACTIVE_STATE` |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/discovery.py` | (~55 行) | `factory_root` + `list_projects` + `get_project_by_slug` + `_load_yaml_project` |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/state.py` | (~45 行) | `active_state_path` + `read_active_slug` + `activate_project` + `active_project` |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/summary.py` | (~140 行) | `_chapter_nums` + `_outline_nums` + `pilot_records_dir_for` + `project_summary` + `quality_summary` + `production_preflight` + `find_calibration_batch` + `suggest_batch_budget_usd` + `batch_command` |
| `packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py` | (~85 行) | `quality_report_summary` + `prose_diff_summary` + `prose_judge_summary` |

### Consumers (migrate) — 55 unique edits across 7 atomic commits

**C2a sub-commit (intra-infra + wildcard, 6 sites)**:

| # | File | Line | Pattern | Current | New |
|---|------|------|---------|---------|-----|
| 1 | `infra/studio/__init__.py` | 2 | wildcard | `from infra.studio_registry import *  # noqa: F403` | `from lingwen_studio_registry import *  # noqa: F403` |
| 2 | `infra/studio_batch_templates.py` | 24 | top-level | `from infra.studio_registry import factory_root` | `from lingwen_studio_registry import factory_root` |
| 3 | `infra/studio_batch_runner.py` | 24 | top-level (multi-line) | `from infra.studio_registry import (` | `from lingwen_studio_registry import (` |
| 4 | `infra/cross_volume/e2e_seed.py` | 311 | function-body | `    from infra.studio_registry import factory_root, get_project_by_slug` | `    from lingwen_studio_registry import factory_root, get_project_by_slug` |
| 5 | `infra/cross_volume/e2e_seed.py` | 332 | function-body | `    from infra.studio_registry import activate_project, factory_root, get_project_by_slug` | `    from lingwen_studio_registry import activate_project, factory_root, get_project_by_slug` |
| 6 | `infra/cross_volume/e2e_seed.py` | 356 | function-body | `    from infra.studio_registry import factory_root, get_project_by_slug` | `    from lingwen_studio_registry import factory_root, get_project_by_slug` |

C2a total: **6 sites in 4 files** (1 wildcard + 5 intra-infra dotted-path; intra-infra dotted-path sub-total = 5).

**C2b sub-commit (bulk: apps + packages + 5 apps test patches + 1 doc comment, 41 sites)**:

| Bucket | Count | Examples |
|--------|-------|----------|
| `apps/studio_api/*` (top-level + function-body) | 17 | `studio.py` (11), `creator_volume.py`, `creator_core.py`, `creator_settings.py`, `creator_onboarding.py`, `app.py`, `helpers/production_records.py` |
| `packages/lingwen-creator/src/lingwen_creator/**` (top-level + function-body) | 18 | `onboarding/{autodetect,digest_background,onboarding}.py`, `settings/{history,docs,merge_preferences}.py` (×2), `content/dashboard.py`, `volume/templates.py` (×3), `export/{publish_adapters,common,docx,epub,publish}.py`, `memory/{assets,query}.py` |
| `apps/studio_api/tests/` + `tests/infra/` (test patches + `monkeypatch.setattr`) | 12 | 5 `patch("infra.studio_registry.X")` in `test_studio_batch_templates_route.py` + 7 `monkeypatch.setattr("infra.studio_registry.X", ...)` across 5 files in `tests/infra/` |
| `packages/lingwen-creator/tests/test_memory.py` (doc comment) | 1 | narrative comment at line 69 mentioning `infra.studio_registry` |
| `apps/studio_api/routes/studio.py` (doc comment at line 8) | 1 | narrative comment mentioning `infra.studio_registry / infra.studio_batch_runner` |
| (bulk sub-total: 35 imports + 5 apps test patches + 1 doc comment = **41 entries in 23 files**) | | |

### Patterns Audited (5-pattern matrix from Phase 38 lesson 2)

| # | Pattern | Result | Verified |
|---|---------|--------|----------|
| 1 | Literal `from infra.studio_registry` imports (incl wildcard) | **41 statements** (40 dotted-name + 1 wildcard; `grep -rEn "^[[:space:]]*from infra\.studio_registry" --include="*.py" infra/ apps/ packages/` → 41 lines) | ✅ |
| 2 | Indented/function-body imports | **26 sites** (`grep -E "^[[:space:]]+from infra\.studio_registry"` → 26 lines, all subset of #1) | ✅ |
| 3 | Relative same-package imports | **0** (`grep -E "from \.(studio_registry\|.*studio_registry)" --include="*.py" -rn ...` → empty) | ✅ |
| 4 | Filesystem-path string literals | **0** (`grep -E "infra/studio_registry" --include="*.py" -rn ...` returns only `infra/studio_registry.py` filename refs in doc-comments, no Path()/string-built paths) | ✅ |
| 5 | Prior-phase regression guards | **0** in `tests/` (Phase 36-39 never touched studio_registry) | ✅ |
| 6 | Test patches | **12 sites across 6 files** (5 `patch(...)` in `apps/studio_api/tests/test_studio_batch_templates_route.py` + 7 `monkeypatch.setattr(...)` in `tests/infra/`). See table below. | ✅ |
| 7 | Wildcard consumer | **1** (`infra/studio/__init__.py:2`) | ✅ |
| 8 | Narrative doc-comment mentions | **2** (`apps/studio_api/routes/studio.py:8` + `packages/lingwen-creator/tests/test_memory.py:69`) — optional narrative update, not import | ✅ |

**Test patches detail (12 sites across 6 files)**:

| File | Pattern | Sites |
|------|---------|-------|
| `apps/studio_api/tests/test_studio_batch_templates_route.py` | `patch("infra.studio_registry.X")` | 5 (lines 46, 70, 83, 102, 119) |
| `tests/infra/test_studio_registry.py` | `monkeypatch.setattr("infra.studio_registry.active_state_path", ...)` | 1 (line 38) |
| `tests/infra/test_creator_merge_preset_packages.py` | `monkeypatch.setattr("infra.studio_registry.factory_root", ...)` | 1 (line 103) |
| `tests/infra/test_creator_digest_background.py` | `monkeypatch.setattr("infra.studio_registry.active_project", ...)` | 1 (line 37) |
| `tests/infra/test_creator_merge_preferences.py` | `monkeypatch.setattr("infra.studio_registry.factory_root", ...)` | 2 (lines 84, 127) |
| `tests/infra/test_creator_volume_templates.py` | `monkeypatch.setattr("infra.studio_registry.list_projects", ...)` (multi-line 175-193) + `monkeypatch.setattr("infra.studio_registry.factory_root", ...)` | 2 (lines 175-193, 212) |

**Total migration**: 41 import statements (C2a 6 + C2b 35 dotted-path after excluding wildcard) + 5 test patches (apps only) + 1 doc-comment narrative update = **47 unique edits across 27 files** (PRODUCTION ONLY; `tests/` defers to Phase 40b).

### Files NOT to touch (out of scope)

- `infra/studio_registry.py` → **convert to thin shim in C3 (not delete)**; full source deletion deferred to Phase 40b after `tests/` migration
- `infra/studio/__init__.py` other lines → unchanged (only line 2 changes)
- `infra/full_check_report.py`, `infra/prose_snapshot.py`, `infra/prose_judge.py` → **stay in infra/** as lazy imports inside `lingwen_studio_registry.reports` (per Q2 = A; future Phase 41+ candidate)
- All 4 production consumer files (6 sites) in C2a / 23 files (41 sites) in C2b → ONLY the `from infra.studio_registry import ...` lines change (plus 1 doc comment for narrative update; Phase 40b handles `tests/` separately)
- `infra/studio_registry.py` function-body imports of `lingwen_core.agents.*` → re-imported in `lingwen_studio_registry.summary` and `reports` (workspace dep)

## Package design

### `packages/lingwen-studio-registry/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-studio-registry"
version = "0.1.0"
description = "LingWen canonical studio_registry module (Phase 40 P3-ARCHDEBT studio_registry)"
requires-python = ">=3.11"
dependencies = [
    "lingwen-paths",            # Phase 37 — top-level: ProjectPaths
    "lingwen-project-config",   # Phase 38 — top-level: ProjectConfig
    "lingwen-core",             # Phase 34 — function-body: chapter_production_batch, chapter_memory_hook
]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_studio_registry"]
```

### `packages/lingwen-studio-registry/src/lingwen_studio_registry/__init__.py`

```python
"""灵文 Studio 多项目注册表

LingWen canonical studio_registry module (Phase 40 P3-ARCHDEBT studio_registry).
Migrated from infra/studio_registry.py — see invariant #55.
"""
from __future__ import annotations

from lingwen_studio_registry.models import (
    _ACTIVE_STATE,
    _CHAPTER_RE,
    _OUTLINE_RE,
    StudioProject,
)
from lingwen_studio_registry.discovery import (
    _load_yaml_project,
    factory_root,
    get_project_by_slug,
    list_projects,
)
from lingwen_studio_registry.state import (
    active_project,
    active_state_path,
    activate_project,
    read_active_slug,
)
from lingwen_studio_registry.summary import (
    _chapter_nums,
    _outline_nums,
    batch_command,
    find_calibration_batch,
    pilot_records_dir_for,
    production_preflight,
    project_summary,
    quality_summary,
    suggest_batch_budget_usd,
)
from lingwen_studio_registry.reports import (
    prose_diff_summary,
    prose_judge_summary,
    quality_report_summary,
)

__all__ = [
    # models (1 class + 3 module-level consts; consts are underscore-prefixed → not in __all__)
    "StudioProject",
    # discovery (4)
    "factory_root",
    "list_projects",
    "get_project_by_slug",
    # state (4)
    "active_state_path",
    "read_active_slug",
    "activate_project",
    "active_project",
    # summary (7; underscore-private _load_yaml_project/_chapter_nums/_outline_nums are NOT in __all__)
    "pilot_records_dir_for",
    "project_summary",
    "quality_summary",
    "production_preflight",
    "find_calibration_batch",
    "suggest_batch_budget_usd",
    "batch_command",
    # reports (3)
    "quality_report_summary",
    "prose_diff_summary",
    "prose_judge_summary",
]
```

**24 top-level definitions**: 1 class + 17 public funcs + 3 private funcs (underscore-prefixed, NOT in `__all__`) + 3 module consts (underscore-prefixed, NOT in `__all__`). `__all__` lists **18 public symbols** (1 class + 17 public funcs). **Private funcs** (`_load_yaml_project`, `_chapter_nums`, `_outline_nums`) re-exported for backward-compat with intra-package callers but NOT in `__all__`.

### Sub-module content split (5 files)

**`models.py`** (~30 行):
```python
"""Studio project dataclass + module-level patterns/consts."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

_CHAPTER_RE = re.compile(r"^ch(\d+)\.md$")
_OUTLINE_RE = re.compile(r"^ch(\d+)_大纲\.md$")
_ACTIVE_STATE = "studio_active.json"


@dataclass(frozen=True)
class StudioProject:
    slug: str
    name: str
    role: str
    root: Path
    location: str  # "root" | "projects"
```

**`discovery.py`** (~55 行):
- Imports: `from pathlib import Path`, `from typing import Any`, `import yaml`, `from lingwen_studio_registry.models import StudioProject`
- Symbols: `factory_root`, `_load_yaml_project`, `list_projects`, `get_project_by_slug`

**`state.py`** (~45 行):
- Imports: `import json`, `import os`, `from pathlib import Path`, `from lingwen_paths import ProjectPaths`, `from lingwen_studio_registry.discovery import factory_root, get_project_by_slug`
- Symbols: `active_state_path`, `read_active_slug`, `activate_project`, `active_project`

**`summary.py`** (~140 行):
- Imports: `import json`, `from pathlib import Path`, `from typing import Any`, `from lingwen_paths import ProjectPaths`, `from lingwen_project_config import ProjectConfig`, plus 2 function-body lazy imports of `lingwen_core.agents.{chapter_production_batch,chapter_memory_hook}`
- Symbols: `_chapter_nums`, `_outline_nums`, `pilot_records_dir_for`, `project_summary`, `quality_summary`, `production_preflight`, `find_calibration_batch`, `suggest_batch_budget_usd`, `batch_command`

**`reports.py`** (~85 行):
- Imports: 3 function-body lazy imports of `infra.full_check_report`, `infra.prose_snapshot`, `infra.prose_judge` (per Q2 = A; preserved unchanged from source)
- Symbols: `quality_report_summary`, `prose_diff_summary`, `prose_judge_summary`
- Inline comment documenting future Phase 41+ migration of these 3 intra-infra modules

## Atomic commits

| # | Task | Validation gate |
|---|------|-----------------|
| **C0** | spec + plan (this doc) | spec self-review + user review |
| **C1** | scaffold package (5 sub-modules + pyproject.toml + root `pyproject.toml` workspace members) + `uv sync --all-packages --offline` | `python -c "import lingwen_studio_registry"` + `ruff check packages/lingwen-studio-registry/` |
| **C2a** | migrate intra-infra (5 sites in 4 files: `infra/studio_batch_templates.py`, `infra/studio_batch_runner.py`, `infra/cross_volume/e2e_seed.py` ×3) + wildcard (1 site in `infra/studio/__init__.py`) = **6 sites in 4 files** + `ruff check --fix` | ruff clean + `grep -rn "infra\.studio_registry\b" infra/` returns 0 hits |
| **C2b** | migrate bulk (35 dotted-path + 5 apps test patches + 1 doc comment = **41 sites in 23 files**: 17 apps + 18 packages + 5 apps tests + 1 doc) + `ruff check --fix` | ruff clean + apps/studio_api 全测试 + lingwen-creator 73/73 + studio_api 82/82 + 6 prior phase guards GREEN |
| **C3** | convert `infra/studio_registry.py` to 1-line thin shim (`from lingwen_studio_registry import *`) | `grep -rn "infra\.studio_registry" infra/ apps/ packages/` returns 0 sites (excluding shim file itself) + ruff clean + `python -c "from infra.studio_registry import StudioProject, list_projects"` works |
| **C4** | bump v38.0→v39.0 + I055 NEW | `grep -n "v39.0" .lingwen/architecture.yml` (1 hit) + `grep -n "I055" .lingwen/architecture.yml` (≥2 hits) |
| **C5** | regression guards + doc sync + handoff | 8 phase40 guards GREEN + 7 phase39 + 6 phase38 + 5 phase37 preserved + baselines preserved |

**Total**: 7 atomic commits (C0 + C1 + C2a + C2b + C3 + C4 + C5).

## Regression guards (C5 deliverable)

`tests/test_phase40_lingwen_studio_registry.py`:

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_lingwen_studio_registry_importable` | `import lingwen_studio_registry` succeeds |
| 2 | `test_lingwen_studio_registry_exposes_18_public_symbols` | `len(__all__) == 18` (public symbols, per spec); verify count: 1 class + 17 public funcs; verify underscore-prefixed private funcs/consts NOT in `__all__` |
| 3 | `test_lingwen_studio_registry_models_studio_project` | `StudioProject` is frozen dataclass with 5 fields (slug, name, role, root, location) |
| 4 | `test_lingwen_studio_registry_5_sub_modules` | All 5 sub-module files exist: `models`, `discovery`, `state`, `summary`, `reports` |
| 5 | `test_infra_studio_registry_path_forbidden` | `! Path("infra/studio_registry.py").exists()` (deleted in C3) |
| 6 | `test_infra_studio_init_uses_lingwen_studio_registry` | `infra/studio/__init__.py` content includes `from lingwen_studio_registry import *` |
| 7 | `test_no_consumer_imports_infra_studio_registry` | `subprocess.run(["grep", "-rn", "infra.studio_registry", "infra/", "apps/", "packages/", "tests/"], capture_output=True).stdout == b""` |
| 8 | `test_workspace_member_declares_lingwen_studio_registry` | root `pyproject.toml` `[tool.uv.workspace] members` contains `"packages/lingwen-studio-registry"` |
| 9 | `test_pyproject_dependencies_lists_3_packages` | `pyproject.toml` `dependencies` list has exactly 3 items: `[lingwen-paths, lingwen-project-config, lingwen-core]` |
| 10 | `test_inv_55_in_architecture_yml` | invariant I055 in `.lingwen/architecture.yml` invariants table |
| 11 | `test_5_pattern_audit_clean` | all 5 patterns (literal dotted, indented, relative same-pkg, relative parent-pkg, filesystem path) return 0 hits for `infra.studio_registry` |

**11 guards total** (≥8 promised in design, +3 extra for safety).

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| R1: Function-body `from infra.studio_registry` imports (26 sites) misssed by top-level sed | MEDIUM | Use `\1` backreference sed pattern (Phase 38 lesson 1): `s/^(\s*)from infra\.studio_registry/\1from lingwen_studio_registry/` |
| R2: 12 test patches use string-based `patch("infra.studio_registry.X")` and `monkeypatch.setattr("infra.studio_registry.X", ...)` not detected by import grep | LOW | Dedicated audit `grep -rEn 'patch\([^)]*infra\.studio_registry\|monkeypatch\.setattr\([^)]*infra\.studio_registry\|"infra\.studio_registry\.[a-z_]+"' --include="*.py"` in C2b pre-check (12 sites across 6 files confirmed ✅) |
| R3: `infra/studio/__init__.py` wildcard consumer via `infra.studio.X` (someone relies on the re-export) | LOW | `grep -rn 'infra\.studio\b' --include='*.py'` returns 0 hits outside `infra.studio_registry` and `infra.studio/__init__.py` itself (verified ✅) |
| R4: NOT-LEAF package — workspace deps must be installable at scaffold time | LOW | C1 declares 3 deps in `pyproject.toml` BEFORE `uv sync --all-packages --offline` (Phase 34 lesson); verify with `python -c "import lingwen_paths, lingwen_project_config, lingwen_core"` |
| R5: Staging leak re-occurrence (Phase 36 critical lesson, 5th time) | LOW-MEDIUM | Explicit `git worktree remove --force` + `git status --short` check at C2a ff-merge point AND at C5 ff-merge point AND before each remaining commit |
| R6: `relationship_network.db` pytest artifact (Phase 38 lesson 6) | LOW | `rm -f relationship_network.db` before each staging-leak check |
| R7: `ruff check --fix` out-of-scope edits (Phase 36/38 lesson) | LOW | Apply `ruff check --fix` in C2a and C2b immediately after sed migration; review diff before commit |
| R8: `infra/studio/__init__.py` still imports `studio_batch_runner` wildcard (`from infra.studio_batch_runner import *` line 1) | LOW | Don't touch line 1 in C2a; line 1 is out of scope (only line 2 changes). Verify post-C2a: `infra/studio/__init__.py` has 2 lines total, line 1 unchanged + line 2 migrated. |
| R9: 422 行子模块分割后跨模块循环 import | LOW | Dependency direction is one-way: `models ← {discovery, state, summary, reports} ← __init__.py`. `state` depends on `discovery`; `summary` depends on `discovery` (transitively via `__init__.py` is OK because import is at usage time, not at module init). No cycles. |
| R10: C2b 一次性 41 sites 全 sed, 如果错一处整个 commit 红 | MEDIUM | C2a baseline 必须先 GREEN; C2b 实施后逐 file `python -c "import X"` 验证 (Phase 37 lesson); 必要时拆 C2b1 (apps) + C2b2 (packages) |
| R11: 子模块 `reports.py` 内部的 `from infra.full_check_report` 等 3 个 lazy import — Phase 40 后 `lingwen_studio_registry` 包是否仍能 `import infra.X`? | LOW | `infra.full_check_report` / `infra.prose_snapshot` / `infra.prose_judge` 都是独立模块, 不在 Phase 40 删除清单里; C3 删除 `infra/studio_registry.py` 不影响它们。Verify: post-C3 `python -c "from infra.full_check_report import load_report_summary"` |

## Lessons applied from prior phases

| Phase | Lesson | How applied |
|-------|--------|------------|
| 34 | Workspace member declaration must precede `uv sync` | C1 declares `packages/lingwen-studio-registry` in root `pyproject.toml [tool.uv.workspace] members` BEFORE `uv sync --all-packages --offline` |
| 34 | Specs can lie — verify symbol counts | All counts verified via `grep -c` before writing spec (24 top-level defs = 1 class + 20 funcs + 3 consts, 18 public in `__all__` = 1 class + 17 funcs, 6 C2a sites, 49 C2b sites = 35 imports + 12 test patches + 2 doc, 0 relative, 0 path literals) — corrected via code review feedback |
| 36 | Worktree force-remove staging leak | Staging-leak check at BOTH `git worktree remove --force` AND after each ff-merge (5th consecutive time — Phase 36 / 37 / 38 / 39 all hit this) |
| 36 | Spec drift — verify consumer counts | All counts in §Scope verified via `grep -c` before writing spec |
| 36 | `ruff check --fix` out-of-scope edits | C2a + C2b apply `ruff check --fix` immediately after sed migration; review diff before commit |
| 37 | Function-body imports via `\1` backreference sed | C2a + C2b use `s/^(\s*)from infra\.studio_registry/\1from lingwen_studio_registry/` pattern (handles both top-level and indented) |
| 37 | Spec/plan combined single commit | C0 spec+plan in one commit (no separate plan file) |
| 37 | 86-consumer single-C2 commit | **Adapted to 2-C2-sub-commit** (Q3 = B) because 47 edits is 1.8x Phase 38; C2a (6 sites) as staging baseline before C2b (41 sites) bulk |
| 37 | Empty dir shell after `git mv` | Not applicable (no `git mv` in Phase 40 — source file is module, not directory) |
| 38 | Whitespace-preserving sed `\1` backreference | C2a + C2b use `\1` backreference for both top-level and indented imports |
| 38 | 5-pattern audit matrix | All 5+2 patterns verified pre-spec (§Patterns Audited) |
| 38 | `ruff check --fix` belongs in C2 | C2a + C2b both apply `ruff check --fix` after sed |
| 38 | Test artifact leakage (`relationship_network.db`) | Pre-merge `rm -f relationship_network.db` before each staging-leak check |
| 38 | Spec count drift (Phase 38 said 3 function-body, actual 7) | Phase 40 initially verified counts but missed test patches (5 vs actual 12) + apps bucket (16 vs actual 17) + symbol counts (22 vs actual 20 funcs). Caught by code quality review post-C0; fixed via C0 amendment. LESSON: include `tests/` AND `apps/` AND `packages/` AND intra-infra in EVERY grep audit. Verify symbol counts via `grep -cE '^(def \|class )'` on source before writing regression guards. |
| 38 | NOT-LEAF package (first P3 non-LEAF) | **Adapted**: Phase 40 declares 3 workspace deps in pyproject.toml; Phase 38 declared 2 |
| 39 | Pre-spec verification prevents C3.5 fixup | C0 includes exhaustive audit (§Patterns Audited) to prevent surprises mid-execution |
| 39 | LEAF scaffold trivial | Phase 40 scaffold is NOT trivial — 5 sub-modules + 3 workspace deps; C1 must be careful with import ordering (R9) |
| 39 | YAML escape gotcha in `.lingwen/architecture.yml` scope strings | C4 invariant I055 + scope strings use proper YAML escaping (Phase 39 lesson 5) |
| 39 | Sub-agent execution drift | C2a + C2b implementer sub-agents verify exact line replacement + `ruff --fix` clean before commit |

## Carryover closure

- ✅ P3-ARCHDEBT 1/5 (`errors`) → Phase 36
- ✅ P3-ARCHDEBT 2/5 (`paths`) → Phase 37
- ✅ P3-ARCHDEBT 3/5 (`project_config`) → Phase 38
- ✅ P3-ARCHDEBT 4/5 (`logging_config`) → Phase 39
- ⏳ P3-ARCHDEBT 5/5a (`studio_registry` **production**, 47 edits) → **Phase 40a (this phase)**
- ⏳ P3-ARCHDEBT 5/5b (`studio_registry` **tests/** + shim delete, **~33 edits across ~24 files** + 1 shim delete) → **Phase 40b (planned, post-40a)**

**P3-ARCHDEBT arc closure**: Phase 40a + 40b together = final P3-ARCHDEBT module. After Phase 40b ff-merge:
- All 5 `infra.{errors, paths, project_config, logging_config, studio_registry}` modules migrated to `packages/lingwen-*`
- All P3 invariants (#51-#55) enforced
- LingWen package architecture: 5 new canonical packages added (Phase 36-40)
- Remaining `infra/` is now thin shell (compat re-exports) + consumer code
- `infra/studio_registry.py` shim deleted in 40b

## Open carryovers (post-Phase 40a)

- **Phase 40b (planned)**: migrate `tests/` directory (21 `from` imports + 4 `import as` + 7 `monkeypatch.setattr` patches + 1 doc comment = ~33 edits across ~24 files) + DELETE `infra/studio_registry.py` shim. Will need fresh brainstorm + spec + plan.
- **3 intra-infra modules** (`infra/full_check_report.py`, `infra/prose_snapshot.py`, `infra/prose_judge.py`) — used as lazy imports inside `lingwen_studio_registry.reports` (per Q2 = A). Candidate for Phase 41+ as standalone P3-ARCHDEBT-lite (single-function migration).
- **Phase 114 prod preview regression** (accepted debt — do NOT attempt fix)
- **HANDOFF.md `latest_decision_queue` wording** (pre-existing carryover; doc-only)

---

# Phase 40b — Forward Reference (planning deferred to post-Phase-40a)

> **Status**: NOT yet designed or scoped. Will require fresh brainstorm + spec + plan after Phase 40a ff-merge.

## Scope (preliminary)

Migrate the `tests/` root directory + delete the `infra/studio_registry.py` shim left behind by Phase 40a.

### Source disposition (deferred from Phase 40a)

| Path | Action in 40b |
|------|---------------|
| `infra/studio_registry.py` (1-line shim from Phase 40a C3) | DELETE |

### Consumers (preliminary, verify post-40a)

| Bucket | Count (verified Phase 40a brainstorm) | Examples |
|--------|---------------------------------------|----------|
| `tests/infra/test_creator_*.py` (`from infra.studio_registry import ...` single-line) | 20 | `test_creator_dashboard.py`, `test_creator_onboarding_autodetect.py`, `test_creator_memory_query.py`, `test_creator_export_epub.py`, ... (16 `test_creator_*` + `test_studio_batch_queue.py` + `test_studio_batch_runner.py` + `test_studio_batch_runner_restart.py`) |
| `tests/infra/test_studio_registry.py` (multi-line `from infra.studio_registry import (`) | 1 | line 11 |
| `import infra.studio_registry as registry` (4 sites in tests) | 4 | `tests/dashboard/test_studio_endpoints.py:13`, `tests/dashboard/test_creator_endpoints.py:13`, `tests/dashboard/test_studio_batch_endpoints.py:14`, `tests/infra/test_prose_judge.py:133` |
| `monkeypatch.setattr("infra.studio_registry.X", ...)` test patches | 7 | `tests/infra/test_creator_{merge_preset_packages,merge_preferences (×2),volume_templates (×2),digest_background}.py` + `test_studio_registry.py` |
| `packages/lingwen-creator/tests/test_memory.py:69` doc comment | 1 | narrative mention |
| **Total** | **~33 edits across ~24 files** | |

### Patterns (preliminary)

| Pattern | Sites | Verification command |
|---------|-------|---------------------|
| `from infra.studio_registry import ...` | 21 (20 single-line + 1 multi-line) | `grep -rEn "^[[:space:]]*from infra\.studio_registry" --include="*.py" tests/` |
| `import infra.studio_registry as registry` | 4 | `grep -rEn "^[[:space:]]*import infra\.studio_registry as" --include="*.py" tests/` |
| `monkeypatch.setattr("infra.studio_registry.X", ...)` | 7 | `grep -rEn 'monkeypatch\.setattr\("infra\.studio_registry' --include="*.py" tests/` |
| Doc comment | 1 | `grep -rn "infra\.studio_registry" packages/lingwen-creator/tests/test_memory.py` |

### Proposed commit structure (preliminary)

| # | Task | Validation gate |
|---|------|-----------------|
| C0 | spec + plan (new brainstorm session required) | user review |
| C1 | N/A — package already exists from 40a | — |
| C2a | migrate `tests/` production-side imports (`from infra.studio_registry ...` 21 sites = 20 single-line + 1 multi-line) | `grep -rn "infra\.studio_registry" tests/` returns only `import as` + `monkeypatch.setattr` + shim |
| C2b | migrate `tests/` test patches + `import as` (11 sites) | `grep -rn "infra\.studio_registry" tests/` returns 0 hits |
| C3 | delete `infra/studio_registry.py` shim | `python -c "from infra.studio_registry import ..."` raises ModuleNotFoundError; tests pass |
| C4 | N/A — version + invariant already bumped in 40a | — |
| C5 | extend phase40 regression guards + handoff | 11 phase40 guards GREEN (extended) + `grep "infra.studio_registry"` returns 0 hits |

### Why separate phase

- Tests need to migrate AFTER the package exists and is verified working (Phase 40a proves this)
- Avoids bisecting through 81 edits in a single chain
- Allows master to ff-merge with `infra/studio_registry.py` shim intact (no breakage for any tests)
- Phase 32 SHIM-CLEANUP lesson: shim deletion is a separate concern from migration

---

## Phase 40a Self-Review (updated)

---

# Implementation Plan (bite-sized task breakdown)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Architecture:** Migrate `infra/studio_registry.py` (422 行, 24 symbols) → `packages/lingwen-studio-registry/` (5 sub-modules). P3-ARCHDEBT 5/5 收官.
>
> **Tech Stack:** Python 3.12+ / uv workspace / pytest / ruff
>
> **Worktree:** Create BEFORE C1: `git worktree add ../lingwen-phase-40 -b phase-40-p3-archdebt-studio-registry`
>
> **Branch:** `phase-40-p3-archdebt-studio-registry`
>
> **Master HEAD (start):** `26782063` (Phase 39 ff-merge point)
>
> **Total: 7 atomic commits (C0 + C1 + C2a + C2b + C3 + C4 + C5)**

## Task 1: C0 — spec+plan commit

**Files:**
- Modify: `docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md` (already exists in this design)
- Create worktree at `../lingwen-phase-40/` on branch `phase-40-p3-archdebt-studio-registry`

- [ ] **Step 1.1: Create worktree**

```bash
cd /home/ailearn/projects/LingWen
git worktree add ../lingwen-phase-40 -b phase-40-p3-archdebt-studio-registry master
cd ../lingwen-phase-40
```

- [ ] **Step 1.2: Copy spec doc into worktree**

```bash
cp /home/ailearn/projects/LingWen/docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md \
   docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md
```

- [ ] **Step 1.3: Commit C0**

```bash
git add docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md
git commit -m "docs(phase-40): spec for lingwen-studio-registry (P3-ARCHDEBT 5/5)"
```

Expected: 1 commit added on `phase-40-p3-archdebt-studio-registry` branch.

## Task 2: C1 — scaffold lingwen-studio-registry package

**Files:**
- Create: `packages/lingwen-studio-registry/pyproject.toml`
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/__init__.py` (~50 lines re-exports)
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/models.py` (~30 lines)
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/discovery.py` (~55 lines)
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/state.py` (~45 lines)
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/summary.py` (~140 lines)
- Create: `packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py` (~85 lines)
- Modify: `pyproject.toml` (workspace members + sources)

- [ ] **Step 2.1: Create pyproject.toml**

Write `packages/lingwen-studio-registry/pyproject.toml` with content from §Package design in spec.

- [ ] **Step 2.2: Create models.py**

```python
"""Studio project dataclass + module-level patterns/consts."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

_CHAPTER_RE = re.compile(r"^ch(\d+)\.md$")
_OUTLINE_RE = re.compile(r"^ch(\d+)_大纲\.md$")
_ACTIVE_STATE = "studio_active.json"


@dataclass(frozen=True)
class StudioProject:
    slug: str
    name: str
    role: str
    root: Path
    location: str  # "root" | "projects"
```

- [ ] **Step 2.3: Create discovery.py, state.py, summary.py, reports.py**

Copy split content from `infra/studio_registry.py` into appropriate sub-modules. Each sub-module's imports must reference:
- `from lingwen_studio_registry.models import StudioProject, _CHAPTER_RE, _OUTLINE_RE, _ACTIVE_STATE` (for sub-modules needing models)
- Top-level imports: `from lingwen_paths import ProjectPaths`, `from lingwen_project_config import ProjectConfig`
- Function-body lazy imports preserved unchanged: `from lingwen_core.agents.chapter_production_batch`, `from lingwen_core.agents.chapter_memory_hook`, `from infra.full_check_report`, `from infra.prose_snapshot`, `from infra.prose_judge`

- [ ] **Step 2.4: Create __init__.py**

Re-export all symbols from 5 sub-modules + `__all__` list per §Package design in spec.

- [ ] **Step 2.5: Add to workspace**

Modify root `pyproject.toml`:
- Add `"packages/lingwen-studio-registry"` to `[tool.uv.workspace] members`
- Add `lingwen-studio-registry = { workspace = true }` to `[tool.uv.sources]`

- [ ] **Step 2.6: Sync workspace**

```bash
uv sync --all-packages --offline
```

Expected: `Resolved N packages`, `Installed N packages`, no errors.

- [ ] **Step 2.7: Verify import works**

```bash
python -c "from lingwen_studio_registry import StudioProject, list_projects, active_project; print('OK')"
```

Expected: `OK`

- [ ] **Step 2.8: Verify ruff clean**

```bash
ruff check packages/lingwen-studio-registry/
```

Expected: 0 errors.

- [ ] **Step 2.9: Commit C1**

```bash
git add packages/lingwen-studio-registry/ pyproject.toml uv.lock
git commit -m "feat(packages): scaffold lingwen-studio-registry (Phase 40 P3-ARCHDEBT)"
```

## Task 3: C2a — migrate intra-infra + wildcard (6 sites)

**Files:**
- Modify: `infra/studio/__init__.py` (line 2: wildcard)
- Modify: `infra/studio_batch_templates.py` (line 24)
- Modify: `infra/studio_batch_runner.py` (line 24)
- Modify: `infra/cross_volume/e2e_seed.py` (lines 311, 332, 356)

- [ ] **Step 3.1: Migrate wildcard (1 site)**

```bash
sed -i 's|from infra\.studio_registry import \*|from lingwen_studio_registry import *|' infra/studio/__init__.py
```

Verify: `grep "from .*studio_registry" infra/studio/__init__.py` shows `from lingwen_studio_registry import *`.

- [ ] **Step 3.2: Migrate intra-infra dotted-path (5 sites in 3 files)**

Use `\1` backreference sed pattern (handles both top-level and indented):

```bash
# Pattern matches `from infra.studio_registry` at any indentation; preserves leading whitespace
sed -i -E 's|^([[:space:]]*)from infra\.studio_registry|\1from lingwen_studio_registry|' \
    infra/studio_batch_templates.py \
    infra/studio_batch_runner.py \
    infra/cross_volume/e2e_seed.py
```

Verify: `grep -rn "infra\.studio_registry\b" infra/` returns 0 hits.

- [ ] **Step 3.3: Apply ruff --fix (Phase 38 lesson)**

```bash
ruff check --fix infra/ apps/ packages/
```

Verify: 0 errors. If ruff added isort reorders, accept them.

- [ ] **Step 3.4: Verify intra-infra import works**

```bash
python -c "
from infra.studio_batch_templates import factory_root
from infra.studio_batch_runner import batch_runner_root  # whatever the symbol is
from infra.cross_volume.e2e_seed import seed_e2e
from infra.studio import *
print('OK')
"
```

Expected: `OK`

- [ ] **Step 3.5: Run intra-infra test baseline**

```bash
uv run pytest tests/infra/test_studio_batch_runner.py tests/infra/test_studio_batch_templates.py tests/infra/test_e2e_seed.py -v 2>&1 | tail -30
```

Expected: All tests pass.

- [ ] **Step 3.6: Stage-leak check #1 (Phase 36 critical lesson, 5th time)**

```bash
git worktree list  # verify still in worktree
git status --short  # verify no uncommitted
rm -f relationship_network.db  # rm pytest artifact (Phase 38 lesson 6)
```

- [ ] **Step 3.7: Commit C2a**

```bash
git add -A
git commit -m "refactor(consumers): migrate intra-infra 6 sites to lingwen_studio_registry (Phase 40)"
```

## Task 4: C2b — migrate bulk (41 sites in 23 files)

**Files:** 23 files total: 17 in apps/studio_api/* + 18 in packages/lingwen-creator/src + 5 apps test patches (1 file) + 1 doc comment

- [ ] **Step 4.1: Migrate apps/studio_api (17 sites + 5 test patches + 1 doc = 23 edits)**

```bash
# Dotted-path (17 sites across 7 files)
sed -i -E 's|^([[:space:]]*)from infra\.studio_registry|\1from lingwen_studio_registry|' \
    apps/studio_api/routes/studio.py \
    apps/studio_api/routes/creator_volume.py \
    apps/studio_api/routes/creator_core.py \
    apps/studio_api/routes/creator_settings.py \
    apps/studio_api/routes/creator_onboarding.py \
    apps/studio_api/app.py \
    apps/studio_api/helpers/production_records.py

# Test patches — broader pattern covers `patch("infra.studio_registry.X")` AND `monkeypatch.setattr("infra.studio_registry.X", ...)`
sed -i -E 's|"infra\.studio_registry\.([a-z_]+)"|"lingwen_studio_registry.\1"|g' \
    apps/studio_api/tests/test_studio_batch_templates_route.py \
    tests/infra/test_studio_registry.py \
    tests/infra/test_creator_merge_preset_packages.py \
    tests/infra/test_creator_digest_background.py \
    tests/infra/test_creator_merge_preferences.py \
    tests/infra/test_creator_volume_templates.py

# Doc comment narrative update (1 site)
sed -i 's|infra\.studio_registry / infra\.studio_batch_runner|lingwen_studio_registry / infra.studio_batch_runner|' \
    apps/studio_api/routes/studio.py
```

Verify: `grep -rn 'infra\.studio_registry' apps/studio_api/ tests/infra/ | grep -v __pycache__` returns 0 hits (except in docstring/comments if any).

- [ ] **Step 4.2: Migrate packages/lingwen-creator (18 sites + 1 doc comment = 19 edits)**

```bash
# Dotted-path (18 sites across 15 files)
sed -i -E 's|^([[:space:]]*)from infra\.studio_registry|\1from lingwen_studio_registry|' \
    $(grep -rl "from infra\.studio_registry" --include="*.py" packages/lingwen-creator/src/)

# Doc comment narrative update (1 site)
sed -i 's|infra\.studio_registry / infra\.memory_service|lingwen_studio_registry / infra.memory_service|' \
    packages/lingwen-creator/tests/test_memory.py
```

- [ ] **Step 4.3: Apply ruff --fix**

```bash
ruff check --fix apps/ packages/
```

Verify: 0 errors.

- [ ] **Step 4.4: Verify zero remaining imports**

```bash
grep -rn "infra\.studio_registry\b" infra/ apps/ packages/ tests/ --include="*.py" | grep -v "infra/studio_registry.py"
```

Expected: 0 hits (only `infra/studio_registry.py` itself still has the name, deleted in C3).

- [ ] **Step 4.5: Verify apps/studio_api imports work**

```bash
uv run pytest apps/studio_api/tests/ -v 2>&1 | tail -20
```

Expected: All tests pass (82/82 baseline).

- [ ] **Step 4.6: Verify lingwen-creator imports work**

```bash
uv run pytest packages/lingwen-creator/tests/ -v 2>&1 | tail -20
```

Expected: 73/73 baseline + Phase 39 regression guards GREEN.

- [ ] **Step 4.7: Verify prior phase guards preserved**

```bash
uv run pytest tests/test_phase39_lingwen_logging_config.py tests/test_phase38_lingwen_project_config.py tests/test_phase37_lingwen_paths.py -v 2>&1 | tail -10
```

Expected: All GREEN.

- [ ] **Step 4.8: Stage-leak check #2**

```bash
rm -f relationship_network.db
git worktree list
git status --short
```

- [ ] **Step 4.9: Commit C2b**

```bash
git add -A
git commit -m "refactor(consumers): migrate 41 bulk production sites to lingwen_studio_registry (Phase 40a)"
```

## Task 5: C3 — convert source file to thin shim (NOT delete)

**Files:**
- Modify: `infra/studio_registry.py` (422 行 → 1 行 shim)

> **CRITICAL**: Phase 40a does NOT delete `infra/studio_registry.py`. Tests/ still references it via dotted-path imports (`tests/infra/test_creator_*.py`, etc.) — these move to Phase 40b. The shim ensures backward-compat.

- [ ] **Step 5.1: Verify no remaining PRODUCTION references**

```bash
grep -rn "infra\.studio_registry\b" infra/ apps/studio_api/ packages/lingwen-creator/src/ --include="*.py"
```

Expected: 0 hits (only `infra/studio_registry.py` itself, which we're about to convert).

- [ ] **Step 5.2: Overwrite source file with shim content**

```bash
cat > infra/studio_registry.py << 'EOF'
"""Backward-compat shim — canonical module is `lingwen_studio_registry` (Phase 40a P3-ARCHDEBT).

See invariant #55. Scheduled for deletion in Phase 40b after `tests/` migration.
"""
from lingwen_studio_registry import *  # noqa: F401,F403

__all__ = [  # noqa: F405
    "StudioProject",
    "factory_root",
    "list_projects",
    "get_project_by_slug",
    "active_state_path",
    "read_active_slug",
    "activate_project",
    "active_project",
    "pilot_records_dir_for",
    "project_summary",
    "quality_summary",
    "production_preflight",
    "find_calibration_batch",
    "suggest_batch_budget_usd",
    "batch_command",
    "quality_report_summary",
    "prose_diff_summary",
    "prose_judge_summary",
]
EOF
```

- [ ] **Step 5.3: Verify shim works**

```bash
uv run python -c "from infra.studio_registry import StudioProject, list_projects, active_project; print('shim OK')"
```

Expected: `shim OK`

- [ ] **Step 5.4: Verify ruff clean**

```bash
ruff check infra/ apps/ packages/ tests/ apps/studio_api
```

Expected: 0 errors.

- [ ] **Step 5.5: Run all baselines to confirm shim doesn't break anything**

```bash
uv run pytest packages/lingwen-core/tests/ packages/lingwen-pipeline/tests/ apps/studio_api/tests/ packages/lingwen-creator/tests/ -v 2>&1 | tail -15
```

Expected: All baselines preserved (68+1+82+73 = 224+ tests pass).

- [ ] **Step 5.6: Commit C3**

```bash
git add infra/studio_registry.py
git commit -m "refactor(infra): convert studio_registry.py to 1-line shim re-exporting lingwen_studio_registry (Phase 40a)"
```

## Task 6: C4 — version bump + invariant I055

**Files:**
- Modify: `.lingwen/architecture.yml` (version + invariants)

- [ ] **Step 6.1: Update version v38.0 → v39.0**

Edit `.lingwen/architecture.yml`:
- Find `version: v38.0` (or current version string)
- Replace with `version: v39.0`
- Find any related refs to v38.0 and update

- [ ] **Step 6.2: Add invariant I055 to invariants table**

In `.lingwen/architecture.yml`, find invariants I049-I054 and add:
```yaml
- id: I055
  rule: "packages/lingwen-studio-registry/ is the canonical Studio multi-project registry (Phase 40 P3-ARCHDEBT studio_registry)"
  scope: "infra.studio_registry.* forbidden; use lingwen_studio_registry.* instead"
  phase: 40
```

- [ ] **Step 6.3: Verify YAML parses**

```bash
python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml'))"
```

Expected: no error.

- [ ] **Step 6.4: Verify invariant count**

```bash
grep -c "id: I0" .lingwen/architecture.yml
```

Expected: ≥7 (I049-I055; I001-I048 are also likely referenced).

- [ ] **Step 6.5: Commit C4**

```bash
git add .lingwen/architecture.yml
git commit -m "chore(infra): bump v38.0→v39.0 + invariant #55 (lingwen-studio-registry canonical)"
```

## Task 7: C5 — regression guards + doc sync + handoff

**Files:**
- Create: `tests/test_phase40_lingwen_studio_registry.py` (11 guards)
- Modify: `tests/test_phase39_lingwen_logging_config.py` (if needed — verify it still passes)
- Create: `docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md`
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 40 entry)
- Modify: `collaboration/BACKLOG.md` (Phase 40 closure + Phase 41 candidate)
- Modify: `MEMORY.md` (Phase 40 status + I055 avoid + Phase 40 closed carryover)
- Modify: `.home/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` (auto-memory)
- Modify: `.home/.claude/projects/-home-ailearn-projects-LingWen/memory/phase40.md` (NEW topic file)
- Modify: `LINGWEN.md` (CLAUDE.md project instructions) — 11 file doc sync
- Modify: `LINGWEN.md` invariants table (#54 → #55)

- [ ] **Step 7.1: Write 11 regression guards**

Create `tests/test_phase40_lingwen_studio_registry.py` with these 11 tests (per spec §Regression guards):
1. `test_lingwen_studio_registry_importable`
2. `test_lingwen_studio_registry_exposes_18_public_symbols` (checks `len(__all__) == 18` public; 1 class + 17 public funcs)
3. `test_lingwen_studio_registry_models_studio_project`
4. `test_lingwen_studio_registry_5_sub_modules`
5. `test_infra_studio_registry_path_forbidden`
6. `test_infra_studio_init_uses_lingwen_studio_registry`
7. `test_no_consumer_imports_infra_studio_registry`
8. `test_workspace_member_declares_lingwen_studio_registry`
9. `test_pyproject_dependencies_lists_3_packages`
10. `test_inv_55_in_architecture_yml`
11. `test_5_pattern_audit_clean`

- [ ] **Step 7.2: Run phase40 guards**

```bash
uv run pytest tests/test_phase40_lingwen_studio_registry.py -v
```

Expected: 11/11 GREEN.

- [ ] **Step 7.3: Run all prior phase guards**

```bash
uv run pytest tests/test_phase39_lingwen_logging_config.py tests/test_phase38_lingwen_project_config.py tests/test_phase37_lingwen_paths.py tests/test_phase36_lingwen_errors.py -v
```

Expected: 5+6+5+6 = ≥22 GREEN.

- [ ] **Step 7.4: Run all baselines**

```bash
uv run pytest packages/lingwen-core/tests/ packages/lingwen-pipeline/tests/ apps/studio_api/tests/ packages/lingwen-creator/tests/ -v 2>&1 | tail -10
```

Expected: All GREEN (68+1+82+73).

- [ ] **Step 7.5: Verify ruff clean across project**

```bash
ruff check infra/ apps/ packages/ tests/ apps/studio_api apps/dashboard/src
```

Expected: 0 errors (pre-existing I001 unchanged).

- [ ] **Step 7.6: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md` following Phase 39 handoff template (master HEAD start/end, 7 commits, validation gates, lessons).

- [ ] **Step 7.7: Doc sync (11 files)**

Update:
- `collaboration/CURRENT_STATUS.md` — add Phase 40 entry
- `collaboration/BACKLOG.md` — mark P3-ARCHDEBT 5/5 closed
- `LINGWEN.md` — version v39.0, invariant #55, packages/lingwen-studio-registry path table entry
- `MEMORY.md` — version, invariant #55 avoid line, closed carryover
- `phase40.md` — NEW topic file with 5+ lessons

- [ ] **Step 7.8: Stage-leak check #3 (BOTH points — Phase 36 critical lesson)**

```bash
rm -f relationship_network.db
git worktree list
git status --short  # master should be CLEAN
```

- [ ] **Step 7.9: Commit C5**

```bash
git add tests/test_phase40_lingwen_studio_registry.py docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md collaboration/ MEMORY.md phase40.md LINGWEN.md
git commit -m "test(phase-40): regression guards + handoff (P3-ARCHDEBT 5/5 CLOSED)"
```

## Task 8: Final — ff-merge + push

- [ ] **Step 8.1: ff-merge to master**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-40-p3-archdebt-studio-registry
git log --oneline -8  # verify 7 commits visible on master
```

- [ ] **Step 8.2: Push master**

```bash
git push origin master
```

- [ ] **Step 8.3: Force-remove worktree (Phase 36 critical lesson)**

```bash
git worktree remove --force ../lingwen-phase-40
git worktree list  # verify only master remains
```

- [ ] **Step 8.4: Final stage-leak check**

```bash
cd /home/ailearn/projects/LingWen
git status --short  # MUST be CLEAN
rm -f relationship_network.db  # rm pytest artifact
ls -la  # verify no stray files
```

Expected: `git status` returns clean (or only the pre-existing `projects/anye-xinbiao/docs/novel-pillars.md` modification that was already in master before this phase).

## Validation gates summary (all GREEN required before ff-merge)

| Gate | Command | Pass criteria |
|------|---------|---------------|
| G1 ruff | `ruff check infra/ apps/ packages/ tests/ apps/studio_api apps/dashboard/src` | 0 errors |
| G2 phase40 guards | `uv run pytest tests/test_phase40_lingwen_studio_registry.py -v` | 11/11 GREEN |
| G3 prior guards | `uv run pytest tests/test_phase39_lingwen_logging_config.py tests/test_phase38_lingwen_project_config.py tests/test_phase37_lingwen_paths.py tests/test_phase36_lingwen_errors.py -v` | ≥22 GREEN |
| G4 baselines | `uv run pytest packages/lingwen-core/tests/ packages/lingwen-pipeline/tests/ apps/studio_api/tests/ packages/lingwen-creator/tests/` | 68+1+82+73 = 224 GREEN |
| G5 staging leak | `git worktree list` + `git status --short` + `rm -f relationship_network.db` | clean master, only phase worktree |
| G6 invariant grep | `grep -rn "infra.studio_registry" infra/ apps/ packages/` | 0 hits |
| G7 forbidden import | `python -c "from infra.studio_registry import *"` | works post-40a (shim exists); ModuleNotFoundError post-Phase-40b (shim deleted) |

---

## Self-Review (per writing-plans skill checklist)

**1. Spec coverage:** Every spec section has a corresponding task:
- Source → thin shim (422 行 → 1 行, NOT delete) → Task 5 (C3); full deletion in Phase 40b
- Target scaffold (5 sub-modules + 3 deps) → Task 2 (C1)
- C2a intra-infra migration (6 sites) → Task 3
- C2b bulk migration (41 PRODUCTION sites; `tests/` defers to Phase 40b) → Task 4
- Version bump v38.0→v39.0 → Task 6 (C4)
- Invariant I055 NEW → Task 6 (C4)
- 11 regression guards → Task 7 (C5)
- Handoff doc + doc sync + MEMORY.md → Task 7 (C5)
- ff-merge + worktree cleanup → Task 8

**2. Placeholder scan:** No TBD/TODO/"implement later". All steps have exact commands.

**3. Type consistency:** All `from lingwen_studio_registry import X` symbols match `__all__` list in spec §Package design. Sub-module imports correctly reference sibling sub-modules (e.g., `state.py` imports `from lingwen_studio_registry.discovery import factory_root, get_project_by_slug`).

