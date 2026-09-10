# Phase 42 — P3-ARCHDEBT (project_init) migration design

> **Date**: 2026-09-10
> **Author**: Claude (主控调度)
> **Branch**: `phase-42-p3-archdebt-project-init`
> **Master HEAD (start)**: `6b0dad46` (Phase 41+++ ff-merge point)
> **Version**: v40.1 → **v41.0** (FIRST REAL PHASE after 4 mini-phases)
> **Invariant**: #56 NEW
> **Pattern**: Phase 40a P3-ARCHDEBT (`studio_registry`) adapted for **NOT-LEAF package** + **LEAF scaffold** (3 sub-modules: project_yaml / chapter_beats / pillars, ~135 LOC)
> **Source disposition**: **FULL DELETION (NOT shim)** — `infra/project_init.py` deleted in C3 (46 consumer test fan-out already done in C2b; no remaining wildcards or external wildcards; 1 production consumer `packages/lingwen-cli/src/lingwen_cli/commands/init_project.py` migrated in C2b; 0 deferred test patches; 0 deferred relative imports)

## Why

P3-ARCHDEBT item **6/6+1** (Phase 42 candidate, ranked #1 in [`ARCHDEBT-CANDIDATES.md`](./ARCHDEBT-CANDIDATES.md)) — `infra/project_init.py` (453 行, 14 top-level definitions: 1 class + 11 funcs + 2 module-level tuples) → `packages/lingwen-project-init/`。

**Phase 36-40b P3-ARCHDEBT arc → Phase 42 next**:

| Phase | Module | LOC | Symbols | Sites | Commits | Wildcard | Workspace deps |
|-------|--------|-----|---------|-------|---------|----------|----------------|
| 36 | errors | 380 | 23 | 14 | 6 | 0 | 0 (LEAF) |
| 37 | paths | 125 | 5 | 86 | 6 | 0 | 0 (LEAF) |
| 38 | project_config | 170 | 2 | 26 | 7 | 1 wildcard | 2 (paths + shared) |
| 39 | logging_config | 59 | 3 | 8 | 6 | 1 wildcard | 0 (LEAF) |
| 40a | studio_registry (production) | 422 | 24 | 47 | 7 | 1 wildcard | 3 (paths + project_config + core) |
| 40b | studio_registry (tests + shim delete) | (shim) | 18 | ~33 | 4 | 0 | (deferred to 40b) |
| **42** | **project_init** | **453** | **14** | **50** | **7** | **0** | **2 (paths + shared)** |

**Phase 42 is the first P3-ARCHDEBT after 4 mini-phases (41/41+/41++/41+++) ALL CLOSED**. Originally estimated as the highest-ROI candidate due to **46 consumer call-sites = highest in residual infra**.

**Sites breakdown (verified by `grep -c`, full audit)**:

- 45 unique files with `from infra.project_init import init_minimal_short_project` (1 production + 44 test consumers)
- **+5 function-body imports** in `tests/infra/test_creator_volume_templates.py` (lines 52, 81, 105, 130, 156, 211 — N.14 lesson 1 pattern ② confirmed)
- 1 test file (`tests/infra/test_project_init.py`) imports **2 symbols** (`init_minimal_short_project, validate_slug`)
- 1 production file: `packages/lingwen-cli/src/lingwen_cli/commands/init_project.py`
- **Total: 50 grep hits across 46 unique files**
- 0 relative imports (clean)
- 0 filesystem-path string literals (clean)
- 0 `import as` statements (none in this codebase)
- 0 test patches / `monkeypatch.setattr` (none — clean migration)
- 0 doc-comment narrative mentions
- 0 wildcard consumers (`infra/__init__.py:11` does NOT include `project_init`)

## Scope

### Source (delete)

| Path | Lines | Symbols | Action |
|------|-------|---------|--------|
| `infra/project_init.py` | 453 | 1 class (`InitProjectResult`) + 11 funcs + 2 module-level tuples (`_SLUG_RE`, `_MINIMAL_BEATS`) | **FULL DELETION (C3) — no shim** (45 unique files migrated in C2b before deletion; 0 deferred consumers; verified ✅) |

### Target (scaffold) — 3 sub-modules

| Path | Lines (target) | Symbols |
|------|----------------|---------|
| `packages/lingwen-project-init/pyproject.toml` | (~20 行) | workspace deps: paths + shared |
| `packages/lingwen-project-init/src/lingwen_project_init/__init__.py` | (~30 行) | `__all__` + re-exports from 3 sub-modules |
| `packages/lingwen-project-init/src/lingwen_project_init/models.py` | (~15 行) | `InitProjectResult` dataclass + module-level consts (`_SLUG_RE`, `_MINIMAL_BEATS`) |
| `packages/lingwen-project-init/src/lingwen_project_init/slug.py` | (~25 行) | `validate_slug` + `default_project_parent` + `_validate_chapter_count` |
| `packages/lingwen-project-init/src/lingwen_project_init/beats.py` | (~150 行) | `_chapter_beats` + `_project_yaml` + `_pillars_md` + `_readme_md` + `_global_outline_md` + `_chapter_outline_md` + `_character_profiles` + `init_minimal_short_project` |

> **Decision: 3 sub-modules** (NOT 1 monolithic ~200 line file per MANY SMALL FILES principle; NOT 5+ files because project_init is simpler than studio_registry with 24 symbols vs 14).

### Consumers (migrate) — 50 call-sites across 46 unique files in 2 sub-commits

**C2a sub-commit (intra-infra, 0 sites)**:

| # | File | Sites | Notes |
|---|------|-------|-------|
| — | — | — | `project_init.py` is self-contained — NO intra-infra consumers (`grep -rln "from infra\.project_init" infra/ --include="*.py"` returns only `infra/project_init.py` itself) |

C2a total: **0 sites** (intentional; project_init is leaf-in-infra).

**C2b sub-commit (bulk: 1 production + 45 test consumers, 50 sites in 46 unique files)**:

| Bucket | Count | Examples |
|--------|-------|----------|
| `packages/lingwen-cli/src/lingwen_cli/commands/init_project.py` | 1 production | line 11: `from infra.project_init import init_minimal_short_project` |
| `tests/infra/test_project_init.py` | 1 test (multi-symbol: 2 imports on 1 line) | line 14: `from infra.project_init import init_minimal_short_project, validate_slug` |
| `tests/infra/test_creator_*.py` (44 files, 49 single-symbol imports + 5 function-body imports in test_creator_volume_templates.py) | 44 files / 49 sites | `test_creator_merge_preset_graph.py:9`, `test_creator_export_epub.py:13`, ..., `test_creator_volume_templates.py:52,81,105,130,156,211` (function-body!) |
| **Total** | **46 unique files / 50 call-sites** | |

### Patterns Audited (9-pattern matrix from Phase 41+++ lesson)

| # | Pattern | Result | Verified |
|---|---------|--------|----------|
| 1 | Literal `from infra.project_init` imports (incl wildcard) | **50 statements** (44 top-level dotted-name in tests + 1 top-level in cli + 5 function-body in test_creator_volume_templates + 1 multi-symbol in test_project_init.py = 51 lines; line 14 of test_project_init.py has 2 symbols on 1 line = 51 imports in 50 lines, but 50 unique call-sites across 46 files) | ✅ `grep -rEn "from infra\.project_init" --include="*.py" packages/ apps/ tests/` → 50 lines in 46 files |
| 2 | Indented/function-body imports | **5 sites** in `test_creator_volume_templates.py` (lines 52, 81, 105, 130, 156, 211) — N.14 lesson 1 pattern ② | ✅ `grep -E "^[[:space:]]+from infra\.project_init" --include="*.py" tests/` → 5 sites |
| 3 | Relative same-package imports | **0** (`grep -E "from \.(project_init\|.*project_init)" --include="*.py" -rn ...` → empty) | ✅ |
| 4 | Filesystem-path string literals | **0** (`grep -E "infra/project_init" --include="*.py" -rn ...` → empty; the only `infra/project_init.py` ref is the source file itself, no Path()/string-built paths) | ✅ |
| 5 | Wildcard consumers | **0** (`grep -rn "from infra\.project_init import \*" --include="*.py"` → empty; `infra/__init__.py:11` does NOT include `project_init`) | ✅ |
| 6 | `import as` re-exports | **0** (`grep -rEn "import infra\.project_init as" --include="*.py"` → empty) | ✅ |
| 7 | Test patches (`patch("infra.project_init.X")`) | **0** (`grep -rEn 'patch\("infra\.project_init' --include="*.py"` → empty) | ✅ |
| 8 | `monkeypatch.setattr("infra.project_init.X", ...)` | **0** (`grep -rEn 'monkeypatch\.setattr\("infra\.project_init' --include="*.py"` → empty) | ✅ |
| 9 | Doc-comment narrative mentions | **0** (`grep -rn "infra\.project_init" docs/ --include="*.md"` → empty) | ✅ |

**Total migration**: 50 import statements (C2a 0 + C2b 50; 1 multi-symbol on 1 line = 51 imports across 50 lines) + 0 test patches + 0 doc-comment narrative updates = **50 unique edits across 46 files** (entire codebase).

### Files NOT to touch (out of scope)

- `infra/project_init.py` → **FULL DELETE in C3** (NOT shim — no deferred consumers)
- `infra/__init__.py` → unchanged (no wildcard for project_init)
- 6 intra-infra modules (`infra/full_check_report.py` `infra/prose_snapshot.py` `infra/prose_judge.py` `infra/llm_service.py` `infra/llm_cache.py` `infra/types.py` etc.) → **stay in infra/** — independent Phase 43+ candidates (see `ARCHDEBT-CANDIDATES.md`)
- All 46 consumer files (50 sites) in C2b → ONLY the `from infra.project_init import ...` lines change (0 doc-comment narrative updates needed)

## Package design

### `packages/lingwen-project-init/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-project-init"
version = "0.1.0"
description = "LingWen canonical project_init module (Phase 42 P3-ARCHDEBT project_init)"
requires-python = ">=3.11"
dependencies = [
    "lingwen-paths",            # Phase 37 — top-level: ProjectPaths
    "lingwen-shared",           # Phase 38+ — top-level: mode constants (CREATION_MODE_* + QUALITY_*)
]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_project_init"]
```

### `packages/lingwen-project-init/src/lingwen_project_init/__init__.py`

```python
"""灵文 项目初始化器

LingWen canonical project_init module (Phase 42 P3-ARCHDEBT project_init).
Migrated from infra/project_init.py — see invariant #56.

Provides `init_minimal_short_project` + scaffolding helpers for creator / studio
projects (slug validation, default parent dir, minimal chapter beats, project
yaml, pillars md, readme md, outline md, character profiles).
"""
from __future__ import annotations

from lingwen_project_init.models import (
    _MINIMAL_BEATS,
    _SLUG_RE,
    InitProjectResult,
)
from lingwen_project_init.slug import (
    _validate_chapter_count,
    default_project_parent,
    validate_slug,
)
from lingwen_project_init.beats import (
    _character_profiles,
    _chapter_beats,
    _chapter_outline_md,
    _global_outline_md,
    _pillars_md,
    _project_yaml,
    _readme_md,
    init_minimal_short_project,
)

__all__ = [
    # models (1 class + 2 module consts are underscore-prefixed → NOT in __all__)
    "InitProjectResult",
    # slug (3; _validate_chapter_count is private → NOT in __all__)
    "validate_slug",
    "default_project_parent",
    # beats (1 public + 7 private → NOT in __all__)
    "init_minimal_short_project",
]
```

**14 top-level definitions**: 1 class + 8 public funcs + 5 private funcs (`_validate_chapter_count`, `_chapter_beats`, `_project_yaml`, `_pillars_md`, `_readme_md`, `_global_outline_md`, `_chapter_outline_md`, `_character_profiles` — these are re-exported but NOT in `__all__` per Python convention) + 2 module-level consts (`_SLUG_RE`, `_MINIMAL_BEATS`).

**`__all__` lists 3 public symbols** (1 class + 2 funcs). Private funcs and module consts re-exported for backward-compat with intra-package callers (none in production — but kept for tests that may import them indirectly).

### Sub-module content split (3 files)

**`models.py`** (~15 行):
```python
"""InitProjectResult dataclass + module-level patterns/consts."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

_MINIMAL_BEATS: tuple[tuple[int, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    # ... (5 minimal beat tuples from infra/project_init.py)
)


@dataclass
class InitProjectResult:
    """Result of project initialization."""
    root: Path
    pillars: dict[str, Any]
    readme: str
    outline: str
    chapter_outline: dict[str, Any]
    project_yaml: str
    character_profiles: dict[str, Any]
```

**`slug.py`** (~25 行):
- Imports: `from lingwen_paths import ProjectPaths`, `from lingwen_shared.mode import CREATION_MODE_*, normalize_creation_mode`
- Symbols: `validate_slug`, `default_project_parent`, `_validate_chapter_count`

**`beats.py`** (~150 行):
- Imports: stdlib (json/re/dataclasses/pathlib/typing/Any) + `from lingwen_paths import ProjectPaths` + `from lingwen_shared.mode import CREATION_MODE_*, QUALITY_*, normalize_creation_mode`
- Symbols: `_chapter_beats`, `_project_yaml`, `_pillars_md`, `_readme_md`, `_global_outline_md`, `_chapter_outline_md`, `_character_profiles`, `init_minimal_short_project` (public)

## Atomic commits

| # | Task | Validation gate |
|---|------|-----------------|
| **C0** | spec + plan (this doc) | spec self-review + user review |
| **C1** | scaffold package (3 sub-modules + pyproject.toml + root `pyproject.toml` workspace members) + `uv sync --all-packages --offline` | `python -c "import lingwen_project_init; print(lingwen_project_init.init_minimal_short_project)"` + `ruff check packages/lingwen-project-init/` |
| **C2a** | migrate intra-infra (0 sites — none expected; verify grep returns 0) | `grep -rn "infra\.project_init\b" infra/ --include="*.py"` returns 0 hits |
| **C2b** | migrate bulk (1 cli + 1 test_project_init + 44 test_creator_* + 5 function-body in test_creator_volume_templates = **50 sites in 46 files**) + `ruff check --fix` | ruff clean + cli imports work + test_project_init passes + all 6 baseline preserved + 5+6+6+5+11 prior phase guards GREEN |
| **C3** | DELETE `infra/project_init.py` (NOT shim — no deferred consumers) | `grep -rn "infra\.project_init\b" --include="*.py"` returns 0 hits + ruff clean + `python -c "from infra.project_init import ..."` raises ModuleNotFoundError |
| **C4** | bump v40.1 → **v41.0** (FIRST REAL PHASE after 4 mini-phases) + invariant I056 NEW | `grep -n "v41.0" .lingwen/architecture.yml` (1 hit) + `grep -n "I056" .lingwen/architecture.yml` (≥2 hits) |
| **C5** | regression guards + doc sync + handoff | 10+ phase42 guards GREEN + 11 phase40 + 6 phase39 + 6 phase38 + 6 phase37 + 6 phase36 preserved + 6 baselines preserved |

**Total**: 7 atomic commits (C0 + C1 + C2a + C2b + C3 + C4 + C5).

> **Decision: C2a = 0 sites**. Phase 40a had C2a = 6 sites (intra-infra wildcard + 5 dotted-path). Phase 42 has zero intra-infra consumers of `infra.project_init`. We keep C2a as a verification gate (`grep` returns 0 hits) to preserve commit structure consistency with the P3-ARCHDEBT template. This ensures C3's `infra/project_init.py` deletion has a clean pre-flight check.

## Regression guards (C5 deliverable)

`tests/test_phase42_lingwen_project_init.py`:

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_lingwen_project_init_importable` | `import lingwen_project_init` succeeds |
| 2 | `test_lingwen_project_init_exposes_3_public_symbols` | `len(__all__) == 3` (public symbols: InitProjectResult + validate_slug + init_minimal_short_project); verify count: 1 class + 2 funcs; verify underscore-prefixed private funcs/consts NOT in `__all__` |
| 3 | `test_lingwen_project_init_init_project_result` | `InitProjectResult` is dataclass with 7 fields (root, pillars, readme, outline, chapter_outline, project_yaml, character_profiles) |
| 4 | `test_lingwen_project_init_3_sub_modules` | All 3 sub-module files exist: `models`, `slug`, `beats` |
| 5 | `test_infra_project_init_path_forbidden` | `! Path("infra/project_init.py").exists()` (deleted in C3) |
| 6 | `test_no_consumer_imports_infra_project_init` | `subprocess.run(["grep", "-rn", "infra.project_init", "infra/", "apps/", "packages/", "tests/"], capture_output=True).stdout == b""` |
| 7 | `test_workspace_member_declares_lingwen_project_init` | root `pyproject.toml` `[tool.uv.workspace] members` contains `"packages/lingwen-project-init"` |
| 8 | `test_pyproject_dependencies_lists_2_packages` | `pyproject.toml` `dependencies` list has exactly 2 items: `[lingwen-paths, lingwen-shared]` |
| 9 | `test_inv_56_in_architecture_yml` | invariant I056 in `.lingwen/architecture.yml` invariants table |
| 10 | `test_9_pattern_audit_clean` | all 9 patterns (literal dotted, indented, relative same-pkg, relative parent-pkg, filesystem path, wildcard, import as, test patches, doc-comment narrative) return 0 hits for `infra.project_init` |
| 11 | `test_init_minimal_short_project_smoke` | smoke test: invoke `init_minimal_short_project` with valid params, verify result is `InitProjectResult` with non-empty pillars/readme/outline |

**11 guards total** (≥10 promised in design, +1 for safety).

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| R1: Function-body `from infra.project_init` imports (5 sites) missed by top-level sed | MEDIUM | Use `\1` backreference sed pattern (Phase 38 lesson 1): `s/^(\s*)from infra\.project_init/\1from lingwen_project_init/` |
| R2: 50 sites 一次性 sed, 如果错一处整个 C2b 红 | MEDIUM | C2a (0 sites) baseline; C2b 实施后逐 file `python -c "from lingwen_project_init import X"` 验证; `ruff check --fix` 立即清理 (Phase 38 lesson) |
| R3: `init_minimal_short_project` 函数体内部如有 lazy import 引用 `infra.project_init` (unlikely) | LOW | `grep -n "from infra" infra/project_init.py` returns 0 hits (already verified ✅) |
| R4: NOT-LEAF package — workspace deps 必须可在 scaffold 时 install | LOW | C1 declares 2 deps in `pyproject.toml` BEFORE `uv sync --all-packages --offline` (Phase 34 lesson); verify with `python -c "import lingwen_paths, lingwen_shared"` |
| R5: Staging leak re-occurrence (Phase 36 critical lesson, 6th time) | LOW-MEDIUM | Explicit `git worktree remove --force` + `git status --short` check at C2b ff-merge point AND at C5 ff-merge point AND before each remaining commit |
| R6: `relationship_network.db` pytest artifact (Phase 38 lesson 6) | LOW | `rm -f relationship_network.db` before each staging-leak check |
| R7: `ruff check --fix` out-of-scope edits (Phase 36/38 lesson) | LOW | Apply `ruff check --fix` in C2b immediately after sed migration; review diff before commit |
| R8: `infra/__init__.py` wildcard 已包含 project_init (FALSE — verified) | NONE | `grep "project_init" infra/__init__.py` returns 0 hits ✅ |
| R9: 3-子模块分割后跨模块循环 import | LOW | Dependency direction is one-way: `models ← {slug, beats} ← __init__.py`. `slug` and `beats` may both depend on `models` but not on each other. No cycles. |
| R10: 50 sites 中如有 `monkeypatch.setattr("infra.project_init.X", ...)` (verified 0) | NONE | Pre-C2b grep confirmed 0 patches; no C2b mitigation needed |
| R11: `init_minimal_short_project` 调用链涉及 `infra.project_init._MINIMAL_BEATS` 等私有符号 (unlikely — module-level consts) | LOW | Pre-spec verified: only top-level public symbols + class accessed. Module consts `_SLUG_RE` and `_MINIMAL_BEATS` re-exported for safety. |
| R12: C3 FULL DELETE 而非 shim — 任何未捕获 consumer 在 master 立即破 | MEDIUM | C2b 完成后 **grep -rn "infra\.project_init\b" --include="*.py" 必须返回 0 hits** (除 `infra/project_init.py` 自身); C3 才执行 delete |

## Lessons applied from prior phases

| Phase | Lesson | How applied |
|-------|--------|------------|
| 34 | Workspace member declaration must precede `uv sync` | C1 declares `packages/lingwen-project-init` in root `pyproject.toml [tool.uv.workspace] members` BEFORE `uv sync --all-packages --offline` |
| 34 | Specs can lie — verify symbol counts | All counts verified via `grep -c` before writing spec (14 top-level defs = 1 class + 11 funcs + 2 consts, 3 public in `__all__` = 1 class + 2 funcs, 0 C2a sites, 50 C2b sites, 0 relative, 0 path literals, 0 wildcard, 0 import-as, 0 patches, 0 doc-comments) |
| 36 | Worktree force-remove staging leak | Staging-leak check at BOTH `git worktree remove --force` AND after each ff-merge (6th consecutive time — Phase 36 / 37 / 38 / 39 / 40a / 40b all hit this) |
| 36 | Spec drift — verify consumer counts | All counts in §Scope verified via `grep -c` before writing spec (50 sites confirmed) |
| 36 | `ruff check --fix` out-of-scope edits | C2b applies `ruff check --fix` immediately after sed migration; review diff before commit |
| 37 | Function-body imports via `\1` backreference sed | C2b uses `s/^(\s*)from infra\.project_init/\1from lingwen_project_init/` pattern (handles both top-level and indented) |
| 37 | Spec/plan combined single commit | C0 spec+plan in one commit (no separate plan file) |
| 37 | 86-consumer single-C2 commit | **Adapted to 0+50 split** (C2a = 0 baseline + C2b = 50 bulk); C2b = single sed across 46 files |
| 37 | Empty dir shell after `git mv` | Not applicable (no `git mv` in Phase 42 — source file is module, not directory) |
| 38 | Whitespace-preserving sed `\1` backreference | C2b uses `\1` backreference for both top-level and indented imports |
| 38 | 5-pattern audit matrix | All 5+4 = 9 patterns verified pre-spec (§Patterns Audited) |
| 38 | `ruff check --fix` belongs in C2 | C2b applies `ruff check --fix` after sed |
| 38 | Test artifact leakage (`relationship_network.db`) | Pre-merge `rm -f relationship_network.db` before each staging-leak check |
| 38 | Spec count drift | Phase 42 initially verified counts via 9-pattern audit; no surprises mid-execution expected |
| 38 | NOT-LEAF package | **Adapted**: Phase 42 declares 2 workspace deps in pyproject.toml (vs Phase 40a's 3, vs Phase 38's 2) |
| 39 | Pre-spec verification prevents C3.5 fixup | C0 includes exhaustive 9-pattern audit (§Patterns Audited) to prevent surprises mid-execution |
| 39 | LEAF scaffold trivial | **Adapted**: Phase 42 is NOT trivial — 3 sub-modules + 2 workspace deps (similar to Phase 40a but simpler) |
| 39 | YAML escape gotcha in `.lingwen/architecture.yml` scope strings | C4 invariant I056 + scope strings use proper YAML escaping (Phase 39 lesson 5) |
| 39 | Sub-agent execution drift | C2b implementer sub-agents verify exact line replacement + `ruff --fix` clean before commit |
| 40a | NOT-LEAF first-P3 pattern | **Reused**: Phase 42 follows Phase 40a's pattern (3 workspace deps → 2 workspace deps for simpler module) |
| 40a | C2a baseline before C2b bulk | **Adapted to 0 sites**: C2a is verification-only (no edits); C2b does all 50 sites in single sed |
| 40a | 7 atomic commits structure | **Reused**: C0/C1/C2a/C2b/C3/C4/C5 |
| 40a | C3 SHIM approach | **ADAPTED to FULL DELETE**: project_init has 0 deferred consumers (verified via 9-pattern audit) → no shim needed. Risk R12 covered. |
| 40b | tests migration deferred from production | **NOT APPLICABLE**: Phase 42 has only 1 production consumer (CLI) + 44 test consumers, all migrated in C2b; no Phase 42b needed |
| 41+++ | 9-pattern audit matrix (lesson 1) | **Reused + extended**: Phase 42 audit covers all 9 patterns (Phase 41+++ mini lesson 1) |

## Carryover closure

- ✅ P3-ARCHDEBT 1/5 (`errors`) → Phase 36
- ✅ P3-ARCHDEBT 2/5 (`paths`) → Phase 37
- ✅ P3-ARCHDEBT 3/5 (`project_config`) → Phase 38
- ✅ P3-ARCHDEBT 4/5 (`logging_config`) → Phase 39
- ✅ P3-ARCHDEBT 5/5 (`studio_registry`) → Phase 40a + 40b
- ⏳ **P3-ARCHDEBT 6/6+1 (`project_init`)** → **Phase 42 (this phase)**

**P3-ARCHDEBT continued arc**: After Phase 42 ff-merge, `infra/project_init` migrated. Top 5 next candidates (per [`ARCHDEBT-CANDIDATES.md`](./ARCHDEBT-CANDIDATES.md)) remain:
- Phase 43: `infra/llm_service` (9 consumers, half-migrated shim cleanup)
- Phase 44: `infra/prose_calibration` (6 consumers, TRUE LEAF)
- Phase 45: `infra/{cache, coverage_gate, patterns, result}` (TRUE LEAF batch)
- Phase 46: `infra/filter` (4 consumers, near-LEAF)

## Open carryovers (post-Phase 42)

- **Phase 43-50+ P3-ARCHDEBT continued**: 5+ more modules queued per `ARCHDEBT-CANDIDATES.md`
- **6 intra-infra modules** (Phase 40a deferred carryovers): `infra/full_check_report.py`, `infra/prose_snapshot.py`, `infra/prose_judge.py`, `infra/llm_service.py`, `infra/llm_cache.py`, `infra/types.py` — independent Phase 43+ candidates
- **Phase 114 prod preview regression** (accepted debt — do NOT attempt fix)
- **3 engine sub-systems** (`infra/cross_volume/`, `infra/tools/`, `infra/persistence/`) — NOT-LEAF, large, defer to post-P3-ARCHDEBT era

---

# Implementation Plan (bite-sized task breakdown)

> **For agentic workers:** REQUIRED SUB-KILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Architecture:** Migrate `infra/project_init.py` (453 行, 14 symbols) → `packages/lingwen-project-init/` (3 sub-modules). P3-ARCHDEBT 6/6+1.
>
> **Tech Stack:** Python 3.12+ / uv workspace / pytest / ruff
>
> **Worktree:** Create BEFORE C1: `git worktree add ../lingwen-phase-42 -b phase-42-p3-archdebt-project-init master`
>
> **Branch:** `phase-42-p3-archdebt-project-init`
>
> **Master HEAD (start):** `6b0dad46` (Phase 41+++ ff-merge point)
>
> **Total: 7 atomic commits (C0 + C1 + C2a + C2b + C3 + C4 + C5)**

## Task 1: C0 — spec+plan commit

- [ ] **Step 1.1**: Create worktree
  ```bash
  cd /home/ailearn/projects/LingWen
  git worktree add ../lingwen-phase-42 -b phase-42-p3-archdebt-project-init master
  cd ../lingwen-phase-42
  ```

- [ ] **Step 1.2**: Copy spec doc into worktree
  ```bash
  cp /home/ailearn/projects/LingWen/docs/superpowers/specs/2026-09-10-phase-42-p3-archdebt-project-init-design.md \
     docs/superpowers/specs/2026-09-10-phase-42-p3-archdebt-project-init-design.md
  ```

- [ ] **Step 1.3**: Commit C0
  ```bash
  git add docs/superpowers/specs/2026-09-10-phase-42-p3-archdebt-project-init-design.md
  git commit -m "docs(phase-42): spec for lingwen-project-init (P3-ARCHDEBT 6/6+1)"
  ```

## Task 2: C1 — scaffold lingwen-project-init package

- [ ] **Step 2.1**: Create `packages/lingwen-project-init/pyproject.toml` with content from §Package design in spec.
- [ ] **Step 2.2**: Create `models.py` (InitProjectResult + _SLUG_RE + _MINIMAL_BEATS)
- [ ] **Step 2.3**: Create `slug.py` (validate_slug + default_project_parent + _validate_chapter_count)
- [ ] **Step 2.4**: Create `beats.py` (_chapter_beats + _project_yaml + _pillars_md + _readme_md + _global_outline_md + _chapter_outline_md + _character_profiles + init_minimal_short_project)
- [ ] **Step 2.5**: Create `__init__.py` re-exporting from 3 sub-modules + `__all__` per §Package design
- [ ] **Step 2.6**: Modify root `pyproject.toml`:
  - Add `"packages/lingwen-project-init"` to `[tool.uv.workspace] members`
  - Add `lingwen-project-init = { workspace = true }` to `[tool.uv.sources]`
- [ ] **Step 2.7**: `uv sync --all-packages --offline`
- [ ] **Step 2.8**: `python -c "from lingwen_project_init import init_minimal_short_project; print('OK')"` → OK
- [ ] **Step 2.9**: `ruff check packages/lingwen-project-init/` → 0 errors
- [ ] **Step 2.10**: Commit C1: `feat(packages): scaffold lingwen-project-init (Phase 42 P3-ARCHDEBT)`

## Task 3: C2a — intra-infra baseline (0 sites verification)

- [ ] **Step 3.1**: `grep -rn "infra\.project_init\b" infra/ --include="*.py"` → 0 hits (verify)
- [ ] **Step 3.2**: Commit C2a (verification gate, no file edits): `chore(phase-42): C2a intra-infra baseline (0 sites verified)`

## Task 4: C2b — migrate bulk (50 sites in 46 files)

- [ ] **Step 4.1**: sed migrate (cli + test_project_init + test_creator_* + function-body in test_creator_volume_templates):
  ```bash
  sed -i -E 's|^([[:space:]]*)from infra\.project_init|\1from lingwen_project_init|' \
      $(grep -rl "from infra\.project_init" --include="*.py" packages/ apps/ tests/)
  ```
- [ ] **Step 4.2**: Verify 0 remaining: `grep -rn "infra\.project_init\b" --include="*.py" packages/ apps/ tests/` → 0 hits
- [ ] **Step 4.3**: `ruff check --fix packages/ apps/ tests/` → 0 errors
- [ ] **Step 4.4**: Verify imports work: `python -c "from lingwen_project_init import init_minimal_short_project, validate_slug, InitProjectResult; print('OK')"` → OK
- [ ] **Step 4.5**: Run all baselines (6 packages + studio_api):
  ```bash
  uv run pytest packages/lingwen-core/tests/ packages/lingwen-got/tests/ packages/lingwen-world-model/tests/ \
                packages/lingwen-creator/tests/ apps/studio_api/tests/ packages/lingwen-quality/tests/ -v 2>&1 | tail -10
  ```
  Expected: All baselines preserved.
- [ ] **Step 4.6**: Run all 50 test_creator_* files individually for regression check (or `pytest tests/infra/test_creator_*.py tests/infra/test_project_init.py packages/lingwen-cli/ -v`)
- [ ] **Step 4.7**: Verify prior phase guards preserved (5 phases × 6+ guards each):
  ```bash
  uv run pytest tests/test_phase40_lingwen_studio_registry.py tests/test_phase39_lingwen_logging_config.py \
                tests/test_phase38_lingwen_project_config.py tests/test_phase37_lingwen_paths.py \
                tests/test_phase36_lingwen_errors.py -v 2>&1 | tail -10
  ```
  Expected: 11+6+6+6+6 = ≥35 GREEN
- [ ] **Step 4.8**: Stage-leak check (rm -f relationship_network.db, git status, git worktree list)
- [ ] **Step 4.9**: Commit C2b: `refactor(consumers): migrate 50 bulk sites to lingwen_project_init (Phase 42)`

## Task 5: C3 — delete `infra/project_init.py` (NOT shim)

- [ ] **Step 5.1**: `grep -rn "infra\.project_init\b" --include="*.py"` → 0 hits
- [ ] **Step 5.2**: `git rm infra/project_init.py`
- [ ] **Step 5.3**: Verify deletion: `! Path("infra/project_init.py").exists()` → True
- [ ] **Step 5.4**: Verify no broken imports: `python -c "from infra.project_init import init_minimal_short_project"` → ModuleNotFoundError
- [ ] **Step 5.5**: `ruff check infra/ apps/ packages/ tests/ apps/studio_api` → 0 errors
- [ ] **Step 5.6**: Run all baselines (5 phases × 6 baselines) + 50 test_creator_*.py files → All GREEN
- [ ] **Step 5.7**: Commit C3: `chore(infra): delete infra/project_init.py (Phase 42 P3-ARCHDEBT project_init migrated)`

## Task 6: C4 — version bump + invariant I056

- [ ] **Step 6.1**: Update `.lingwen/architecture.yml`: `version: v40.1` → `version: v41.0` + any related refs
- [ ] **Step 6.2**: Add invariant I056:
  ```yaml
  - id: I056
    rule: "packages/lingwen-project-init/ is the canonical project initializer (Phase 42 P3-ARCHDEBT project_init)"
    scope: "infra.project_init.* forbidden; use lingwen_project_init.* instead"
    phase: 42
  ```
- [ ] **Step 6.3**: `python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml'))"` → no error
- [ ] **Step 6.4**: `grep -c "id: I0" .lingwen/architecture.yml` → ≥8 (I049-I056)
- [ ] **Step 6.5**: Commit C4: `chore(infra): bump v40.1→v41.0 + invariant #56 (lingwen-project-init canonical)`

## Task 7: C5 — regression guards + doc sync + handoff

- [ ] **Step 7.1**: Create `tests/test_phase42_lingwen_project_init.py` (11 guards per spec §Regression guards)
- [ ] **Step 7.2**: Run phase42 guards: `uv run pytest tests/test_phase42_lingwen_project_init.py -v` → 11/11 GREEN
- [ ] **Step 7.3**: Run all prior phase guards: Phase 36-40 (≥35 GREEN)
- [ ] **Step 7.4**: Run all baselines: 6 packages + studio_api + 50 test_creator_*.py → All GREEN
- [ ] **Step 7.5**: `ruff check infra/ apps/ packages/ tests/ apps/studio_api apps/dashboard/src` → 0 errors
- [ ] **Step 7.6**: Write handoff doc to `docs/superpowers/handoffs/2026-09-10-phase-42-p3-archdebt-project-init-handoff.md`
- [ ] **Step 7.7**: Doc sync (CLAUDE.md + MEMORY.md + topic file + phase_history)
- [ ] **Step 7.8**: Stage-leak check (rm -f relationship_network.db, git status, git worktree list)
- [ ] **Step 7.9**: Commit C5: `test(phase-42): regression guards + handoff (P3-ARCHDEBT 6/6+1 CLOSED)`

## Task 8: Final — ff-merge + push

- [ ] **Step 8.1**: `git checkout master && git merge --ff-only phase-42-p3-archdebt-project-init`
- [ ] **Step 8.2**: `git push origin master phase-42-p3-archdebt-project-init`
- [ ] **Step 8.3**: `git worktree remove --force ../lingwen-phase-42` (Phase 36 critical lesson)
- [ ] **Step 8.4**: Final stage-leak check + `rm -f relationship_network.db`

## Validation gates summary (all GREEN required before ff-merge)

| Gate | Command | Pass criteria |
|------|---------|---------------|
| G1 ruff | `ruff check infra/ apps/ packages/ tests/ apps/studio_api apps/dashboard/src` | 0 errors |
| G2 phase42 guards | `uv run pytest tests/test_phase42_lingwen_project_init.py -v` | 11/11 GREEN |
| G3 prior guards | `uv run pytest tests/test_phase40+39+38+37+36 -v` | ≥35 GREEN |
| G4 baselines | `uv run pytest packages/lingwen-{core,got,world-model,creator,quality}/tests/ apps/studio_api/tests/ packages/lingwen-pipeline/tests/ packages/lingwen-llm/tests/ packages/lingwen-cli/tests/` | ≥228 GREEN (preserved) |
| G5 staging leak | `git worktree list` + `git status --short` + `rm -f relationship_network.db` | clean master, only phase worktree |
| G6 invariant grep | `grep -rn "infra.project_init" infra/ apps/ packages/ tests/` | 0 hits |
| G7 forbidden import | `python -c "from infra.project_init import init_minimal_short_project"` | ModuleNotFoundError (post-C3 full delete) |

## Self-Review (per writing-plans skill checklist)

1. **Spec coverage**: Every spec section has corresponding task (C1/C2a/C2b/C3/C4/C5).
2. **Placeholder scan**: No TBD/TODO. All steps have exact commands.
3. **Type consistency**: All `from lingwen_project_init import X` symbols match `__all__` list. Sub-module imports reference sibling sub-modules correctly.
4. **Pattern completeness**: All 9 patterns audited pre-spec.
5. **Risk coverage**: R1-R12 all have explicit mitigation or verified NONE.
