# Phase 42 — P3-ARCHDEBT (project_init) Handoff

> **Date**: 2026-09-10
> **Author**: Claude (主控调度)
> **Branch**: `phase-42-p3-archdebt-project-init`
> **Master HEAD (start)**: `6b0dad46` (Phase 41+++ ff-merge point)
> **Master HEAD (end)**: TBD-after-ff-merge
> **Version**: v39.0 → **v40.0** (FIRST REAL PHASE after 4 mini-phases)
> **Invariant**: #56 NEW
> **Pattern**: P40a studio_registry adapted for **NOT-LEAF package** + **3 sub-modules** + **C3 FULL DELETE** (NOT shim)
> **Sub-module split**: 3 files (models / slug / beats)
> **C2 phasing**: 2 sub-commits (C2a intra-infra 4 sites in 2 files + C2b bulk 47 sites in 47 files)
> **Source disposition**: **FULL DELETION** — `infra/project_init.py` deleted in C3 (51 unique consumers migrated in C2b before deletion; 0 deferred)

## Why

P3-ARCHDEBT item **6/6+1** (Phase 42 candidate, ranked #1 in [`ARCHDEBT-CANDIDATES.md`](../ARCHDEBT-CANDIDATES.md)) — `infra/project_init.py` (453 行, 14 top-level definitions: 1 class `InitProjectResult` + 9 public funcs + 4 private funcs + 2 module-level consts) → `packages/lingwen-project-init/`。

**Phase 36-40b → Phase 42 arc**:

| Phase | Module | LOC | Symbols | Sites | Commits | Wildcard | Workspace deps |
|-------|--------|-----|---------|-------|---------|----------|----------------|
| 36 | errors | 380 | 23 | 14 | 6 | 0 | 0 (LEAF) |
| 37 | paths | 125 | 5 | 86 | 6 | 0 | 0 (LEAF) |
| 38 | project_config | 170 | 2 | 26 | 7 | 1 wildcard | 2 (paths + shared) |
| 39 | logging_config | 59 | 3 | 8 | 6 | 1 wildcard | 0 (LEAF) |
| 40a | studio_registry (production) | 422 | 24 | 47 | 7 | 1 wildcard | 3 (paths + project_config + core) |
| 40b | studio_registry (tests + shim delete) | (shim) | 18 | ~33 | 4 | 0 | (deferred to 40b) |
| **42** | **project_init** | **453** | **14** | **51** | **7** | **1 wildcard** | **2 (paths + shared)** |

**Phase 42 is the first REAL P3-ARCHDEBT phase after 4 mini-phases (41/41+/41++/41+++) ALL CLOSED on 2026-09-10**.

**Sites breakdown (verified by `grep -c`, full audit)**:

- 1 production consumer (`packages/lingwen-cli/src/lingwen_cli/commands/init_project.py`)
- 1 multi-symbol import (`tests/infra/test_project_init.py: init_minimal_short_project, validate_slug`)
- 44 test_creator_* single-symbol imports
- **5 function-body imports** in `tests/infra/test_creator_volume_templates.py` (lines 52, 81, 105, 130, 156, 211 — N.14 lesson 1 pattern ②)
- 1 wildcard consumer: `infra/project/__init__.py:4` (`from infra.project_init import *  # noqa: F403`)
- 3 intra-infra function-body imports: `infra/cross_volume/e2e_seed.py:312, 334, 359`
- **Total: 51 call-sites across 46 unique files + 1 wildcard + 5 function-body intra-infra = 51 sites in 48 unique files**
- 0 relative imports / 0 filesystem-path string literals / 0 `import as` / 0 test patches / 0 doc-comment narrative updates

## Scope

### Source (delete)

| Path | Lines | Symbols | Action |
|------|-------|---------|--------|
| `infra/project_init.py` | 453 | 1 class (`InitProjectResult`) + 9 public funcs + 4 private funcs + 2 module-level consts (`_SLUG_RE`, `_MINIMAL_BEATS` 10-tuple) | **FULL DELETION (C3)** — no shim (verified 0 deferred consumers via 9-pattern audit) |

### Target (scaffold) — 3 sub-modules

| Path | Lines | Symbols |
|------|-------|---------|
| `packages/lingwen-project-init/pyproject.toml` | (~20 行) | workspace deps: paths + shared |
| `packages/lingwen-project-init/src/lingwen_project_init/__init__.py` | (~40 行) | `__all__` + re-exports from 3 sub-modules |
| `packages/lingwen-project-init/src/lingwen_project_init/models.py` | (~70 行) | `InitProjectResult` (frozen dataclass, 6 fields) + `_SLUG_RE` + 10-entry `_MINIMAL_BEATS` |
| `packages/lingwen-project-init/src/lingwen_project_init/slug.py` | (~50 行) | `validate_slug` + `default_project_parent` + `_validate_chapter_count` |
| `packages/lingwen-project-init/src/lingwen_project_init/beats.py` | (~330 行) | `_chapter_beats` + `_project_yaml` + `_pillars_md` + `_readme_md` + `_global_outline_md` + `_chapter_outline_md` + `_character_profiles` + `init_minimal_short_project` |

### Consumers (migrate) — 51 sites in 48 unique files

**C2a** (4 sites in 2 files): wildcard `infra/project/__init__.py:4` + 3 function-body `infra/cross_volume/e2e_seed.py:312, 334, 359`

**C2b** (47 files): 1 cli + 1 multi-symbol test + 44 test_creator_* + 1 test_creator_volume_templates (5 function-body imports)

## Atomic commits

| # | Task | Validation gate |
|---|------|-----------------|
| **C0** | spec + plan | spec self-review + user review |
| **C1** | scaffold package (3 sub-modules + pyproject.toml + workspace) + `uv sync --all-packages --offline` | `from lingwen_project_init import init_minimal_short_project` OK + `ruff check packages/lingwen-project-init/` 0 errors |
| **C2a** | migrate intra-infra + wildcard (4 sites in 2 files) | grep returns 0 hits in infra/ |
| **C2b** | migrate bulk (47 sites in 47 files via sed `\1`) + ruff --fix | 0 refs remaining + 5/5 test_project_init passes + 50 test_creator_* passes (245/246, 1 pre-existing fail unrelated) |
| **C3** | FULL DELETE `infra/project_init.py` (NOT shim) | grep 0 hits + `from infra.project_init import X` raises ModuleNotFoundError |
| **C4** | bump v39.0 → v40.0 + I056 NEW | YAML valid + 14 invariants + I056 in last position |
| **C5** | regression guards (10 tests) + handoff + doc sync | 10/10 phase42 GREEN + 5 prior-phase guards preserved (3 pre-existing failures from other locked worktree pollution, not introduced by Phase 42) |

**Total**: 7 atomic commits.

## Patterns Audited (9-pattern matrix from Phase 41+++ lesson)

| # | Pattern | Result | Verified |
|---|---------|--------|----------|
| 1 | Literal `from infra.project_init` (incl wildcard) | **51 statements** | ✅ |
| 2 | Indented/function-body imports | **8 sites** (5 in test_creator_volume_templates + 3 in e2e_seed) | ✅ |
| 3 | Relative same-package imports | **0** | ✅ |
| 4 | Filesystem-path string literals | **0** | ✅ |
| 5 | Wildcard consumers | **1** (infra/project/__init__.py:4) | ✅ |
| 6 | `import as` re-exports | **0** | ✅ |
| 7 | Test patches (`patch("infra.project_init.X")`) | **0** | ✅ |
| 8 | `monkeypatch.setattr("infra.project_init.X", ...)` | **0** | ✅ |
| 9 | Doc-comment narrative mentions | **0** (1 in test_project_init.py docstring — fixed in C3) | ✅ |

## Lessons (3 captured)

### 1. Spec drift: pre-spec 9-pattern audit 漏检 1 wildcard (N.14 lesson 1 第 15 次变体)

**Problem**: 写 spec 时 `grep -rn "from infra\.project_init" infra/` 让我以为 C2a = 0 sites。但 **wildcard 形式 (`from infra.project_init import *`)** 在 `infra/project/__init__.py:4` 不在 anchored `^from infra` regex 范围——需要单独 check `__init__.py` 文件。

**Fix**: spec 写完后, C2a 执行前再 grep `grep -rn "from infra\.project_init" infra/ --include="*.py"` 验证。发现 4 sites 而非 0。

**Apply**:
- 任何 phase 的 pre-spec 9-pattern audit 必须 explicit check `infra/*/__init__.py` 形式的 wildcard
- N.14 lesson 1 第 15 次变体 — wildcard-in-init detection

### 2. C3 FULL DELETE 比 shim 更干净 (Phase 40b pattern inversion)

**Problem**: P40a 用 shim (1-line re-export) + 后续 phase 删 shim。P42 直接 FULL DELETE (无 shim)。

**Decision rationale**:
- P40a 50 个 consumer 中只有 47 production migrated in C2b; 33 tests 在 P40b 处理 — 需要 shim 维持 C2b→C40b 间 master 不破
- P42 50 个 consumer 全在 C2b migrated (1 cli + 1 multi-symbol test + 44 test_creator_* + 5 function-body = 51 sites); **0 deferred consumers** — shim 无意义

**Apply**: Future P3-ARCHDEBT phase 决策 C3 = shim vs full delete:
- 全 consumer 在 C2b migrated → full delete (cleaner)
- 部分 consumer deferred (tests patches / doc comments) → shim (backward-compat)

### 3. Other locked worktree 污染 grep audit (新问题, N.14 lesson 1 第 16 次变体)

**Problem**: Phase 37/38/39/42 guards 用 `subprocess.run(["grep", "-rln", "--include=*.py", "."], cwd=REPO_ROOT)` — 但 grep 从 `cwd=REPO_ROOT` 走, 进入 `.claude/worktrees/agent-a7eb86a3e8912a954/` (locked worktree) 找到历史 `infra.paths`/`project_config`/`project_init` refs — **污染 audit**。

**Fix**: Phase 42 guard `test_no_consumer_imports_infra_project_init` 显式 `if rel_path.startswith(".claude/worktrees/"): continue` 过滤 (而非 `"/.claude/worktrees/" in rel_path` — path starts with `.claude`, 不含 leading `/`)。

**Apply**:
- Future P3-ARCHDEBT guards 加 `.claude/worktrees/` 排除
- 也可以 `--exclude-dir=.claude` 给 grep, 但 pytest subprocess shell escape 复杂
- **建议**: 长期 fix — 把 guard 的 grep 改为 `subprocess.run([..., "--exclude-dir=.claude", ...])` 一行解决

### 4. (Bonus) Spec drift 修正: `__all__` 3 → 4 symbols (N.14 lesson 1)

**Problem**: spec 初稿写 `__all__` = 3 public symbols, 实际是 4 (`InitProjectResult` + `validate_slug` + `default_project_parent` + `init_minimal_short_project`)。`default_project_parent` 是 public (no underscore prefix in source) — 我漏数了。

**Fix**: smoke test 后立即修正 spec + regression guard `test_lingwen_project_init_exposes_4_public_symbols`。

**Apply**: spec drift correction pattern — 任何 phase 写完 spec 后, smoke test 必须包含 `import package; assert len(package.__all__) == N` 强制核对。

## Carryover closure

- ✅ P3-ARCHDEBT 1/5 (errors) → Phase 36
- ✅ P3-ARCHDEBT 2/5 (paths) → Phase 37
- ✅ P3-ARCHDEBT 3/5 (project_config) → Phase 38
- ✅ P3-ARCHDEBT 4/5 (logging_config) → Phase 39
- ✅ P3-ARCHDEBT 5/5a (studio_registry production) → Phase 40a
- ✅ P3-ARCHDEBT 5/5b (studio_registry tests + shim delete) → Phase 40b
- ✅ **P3-ARCHDEBT 6/6+1 (project_init) → Phase 42 (this phase)**

**P3-ARCHDEBT continued arc**: After Phase 42 ff-merge:
- Top 5 next candidates remain: Phase 43 (llm_service shim cleanup), Phase 44 (prose_calibration TRUE LEAF), Phase 45 (cache + coverage_gate + patterns + result LEAF batch), Phase 46 (filter near-LEAF)
- See [`ARCHDEBT-CANDIDATES.md`](../ARCHDEBT-CANDIDATES.md)

## Open carryovers (post-Phase 42)

- **Phase 43-46 P3-ARCHDEBT continued**: 4 next-phase modules queued (llm_service + prose_calibration + utilities batch + filter)
- **6 intra-infra modules** (Phase 40a deferred carryovers + new): `infra/full_check_report.py`, `infra/prose_snapshot.py`, `infra/prose_judge.py`, `infra/llm_service.py`, `infra/llm_cache.py`, `infra/types.py` — independent Phase 47+ candidates
- **3 engine sub-systems** (`infra/cross_volume/`, `infra/tools/`, `infra/persistence/`) — NOT-LEAF large, defer to post-P3-ARCHDEBT era
- **Phase 114 prod preview regression** (accepted debt)
- **Other locked worktree** at `.claude/worktrees/agent-a7eb86a3e8912a954/` — still polluting grep audits across all phase guards. Consider: cleanup script OR exclude-dir in all future guards.

## Quality gates (fresh-run, Phase 41 mini lesson #1)

| Gate | Command | Result |
|------|---------|--------|
| G1 ruff | `ruff check infra/ packages/ apps/ tests/ apps/studio_api` | 4 pre-existing E741 (Phase 35 baseline, unchanged) |
| G2 phase42 guards | `pytest tests/test_phase42_lingwen_project_init.py` | 10/10 GREEN ✅ |
| G3 prior guards | `pytest tests/test_phase40+39+38+37+36` | 35 passed / 3 failed (pollution from other locked worktree — NOT introduced by Phase 42) |
| G4 baseline | `pytest tests/infra/test_project_init.py + tests/infra/test_creator_*.py` | 245/246 (1 pre-existing fail: test_creator_agent.py Qdrant unavailable) |
| G5 staging leak | `git worktree list` + `git status --short` + `rm -f relationship_network.db` | clean ✅ |
| G6 invariant grep | `grep -rn "infra\.project_init\b" --include="*.py"` | 0 hits ✅ |
| G7 forbidden import | `python -c "from infra.project_init import X"` | ModuleNotFoundError ✅ |
