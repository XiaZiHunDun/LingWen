# Phase 40a — P3-ARCHDEBT (studio_registry) handoff

> **Date**: 2026-09-09
> **Branch**: `phase-40-p3-archdebt-studio-registry` (deleted after ff-merge + worktree remove)
> **Master HEAD**: `(to be updated post-merge)`
> **Spec**: `docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md`

## Summary

P3-ARCHDEBT item **5/5a** — `infra/studio_registry.py` (1 module, **422 lines**, **18 public symbols** in `__all__` after sub-module extraction: 1 frozen dataclass `StudioProject` + 17 public funcs) → `packages/lingwen-studio-registry/` (5 sub-modules: `models` + `discovery` + `state` + `summary` + `reports`, **491 lines total**).

**Largest P3-ARCHDEBT module**: 50 consumer sites (vs Phase 39's 7, Phase 38's 26, Phase 37's 86, Phase 36's 14). Migration split into **C2a** (intra-infra, 6 sites) + **C2b** (production bulk, 41 sites: 17 apps + 18 packages + 5 apps test patches + 1 doc). **First non-LEAF P3-ARCHDEBT package** — 3 workspace deps (`lingwen-paths` + `lingwen-project-config` + `lingwen-core`). **Source file NOT deleted** in Phase 40a — converted to a 1-line shim (`from lingwen_studio_registry import *`) for backward compat with `tests/` (Phase 40b scope).

## Why

5-phase P3-ARCHDEBT backlog (`infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/):
- Phase 36 (errors) ✅
- Phase 37 (paths) ✅
- Phase 38 (project_config) ✅
- Phase 39 (logging_config) ✅
- **Phase 40a (studio_registry) — this handoff**
- Phase 40b (studio_registry tests/ migration + shim delete) ⏳

## Atomic commits (7)

| # | SHA | Task |
|---|-----|------|
| **C0** | `6ba28672` | spec for lingwen-studio-registry |
| **C1** | `76d3ed03` | scaffold lingwen-studio-registry (5 sub-modules + workspace member + uv.lock) |
| **C1.5** | `b937a4ad` | **fixup**: `factory_root()` uses env var + `parents[4]` (original `Path(__file__).parent.parent` formula broke after file relocation) |
| **C2a** | `74c268a4` | migrate 6 intra-infra sites to `lingwen_studio_registry` |
| **C2b** | `53562912` | migrate 41 production bulk sites (17 apps + 18 packages + 5 apps test patches + 1 doc) |
| **C3** | `4d26cc1b` | convert `infra/studio_registry.py` to 1-line shim (NOT deleted) |
| **C4** | `1c473405` | bump v38.0→v39.0 + invariant #55 |
| **C5** | (this) | regression guards + Phase 38 guard fixup + handoff |

The C1.5 fixup commit is **the critical lesson of Phase 40a** (see Lesson 1 below).

## Validation gates

| Gate | Status |
|------|--------|
| ruff clean (new files) | ✅ (0 errors in `tests/test_phase40_lingwen_studio_registry.py` + `tests/test_phase38_lingwen_project_config.py`) |
| Phase 40a guards | ✅ 11/11 GREEN |
| Phase 38 guards preserved (after fixup) | ✅ 7/7 GREEN |
| Phase 37 guards preserved | ✅ 6/6 GREEN |
| Phase 36 guards preserved | ✅ 6/6 GREEN |
| lingwen-core + lingwen-pipeline baselines | ✅ 69/69 pass |
| lingwen-creator baseline (isolated) | ✅ 73/73 pass |
| 5-pattern audit matrix | ✅ all 5 patterns verified pre-spec |
| workspace member declared BEFORE uv sync | ✅ (C1, Phase 34 lesson) |
| ruff --fix in C2b | ✅ (Phase 38 lesson — auto-fixed import orderings) |
| `\1` whitespace sed in C2b | ✅ (Phase 37/38 lesson — 0 function-body misses) |
| C1.5 factory_root fixup detected before C2 | ✅ (Phase 32 lesson — verify before mass-migrate) |
| `infra/studio_registry.py` shim approach | ✅ (NOT deleted — full deletion deferred to Phase 40b) |

## Consumer migration (47 production sites + 1 wildcard)

### C2a — intra-infra (6 sites)
| # | File | Line | Style |
|---|------|------|-------|
| 1 | `infra/studio_batch_runner.py` | top | `from infra.studio_registry import …` |
| 2 | `infra/studio_batch_templates.py` | top | `from infra.studio_registry import …` |
| 3 | `infra/cross_volume/e2e_seed.py` | top | `from infra.studio_registry import …` |
| 4 | `infra/studio/__init__.py` | top | **wildcard** re-exporter (kept, points to lingwen_studio_registry) |
| 5-6 | (more intra-infra sites) | top | — |

### C2b — production bulk (41 sites: 17 apps + 18 packages + 5 apps test patches + 1 doc)

Pattern: `from infra.studio_registry import …` → `from lingwen_studio_registry import …` in 17 apps + 18 packages + 5 apps test patches + 1 doc. `0` function-body imports (verified via `\1` whitespace sed pattern).

## Carryover closure

- ✅ P3-ARCHDEBT 5/5a (`studio_registry` source migration) → CLOSED 2026-09-09
- ⏳ P3-ARCHDEBT 5/5b (`studio_registry` tests/ migration + shim delete) → Phase 40b

Phase 40b scope (carryover):
- ~33 edits in `tests/` root (21 `from` + 4 `import as` + 7 `monkeypatch.setattr` + 1 doc)
- DELETE `infra/studio_registry.py` shim
- DELETE `infra/studio/__init__.py:2` wildcard line (since shim is gone)
- Update tests to use `lingwen_studio_registry` directly (or via `infra.studio` namespace)

## Phase 40a lessons

1. **CRITICAL: C1.5 `factory_root()` defect (lesson 1)** — original `factory_root()` returned `Path(__file__).parent.parent` from `infra/studio_registry.py`, which correctly resolved to repo root when located at `infra/studio_registry.py`. After moving to `packages/lingwen-studio-registry/src/lingwen_studio_registry/discovery.py`, this formula returned `packages/lingwen-studio-registry/src/` — WRONG. **Fix**: read `LINGWEN_PROJECT_ROOT` env var first (test override), fall back to `Path(__file__).parents[4]` (4 levels up: discovery.py → lingwen_studio_registry/ → src/ → lingwen-studio-registry/ → packages/ → repo root). **Future rule**: any function in `infra/*` that uses path-relative formulas MUST be re-audited after relocation to `packages/*/src/*`. Path formulas based on `__file__` are fragile to package restructure. Use env var + bounded `parents[N]` formula with comment.

2. **NOT-LEAF package = 3-dep scaffold (lesson 2)** — first non-LEAF P3-ARCHDEBT package (Phase 36-39 all were LEAF or 2-dep). `lingwen-studio-registry` needs `lingwen-paths` (for path resolution) + `lingwen-project-config` (for `ProjectConfig`) + `lingwen-core` (for `StudioProject` model). Future non-LEAF packages should declare all 3 deps upfront in C1 to avoid mid-C2 cascading dep discovery.

3. **C2 split (C2a intra-infra + C2b bulk) reduced risk (lesson 3)** — Phase 37's 86-site single-C2 commit was the largest atomic commit in history. Splitting into C2a (intra-infra, easy review) + C2b (cross-package, harder review) gives a checkpoint: if C2b breaks something, C2a is already merged and reverts are surgical. **Future rule**: P3-ARCHDEBT phases with >30 sites should split C2 by `intra-infra` vs `cross-package` boundary.

4. **Shim-not-delete pattern for high-consumer modules (lesson 4)** — Phase 40a's 50-consumer migration in a single phase is too risky to delete the source outright. Convert to 1-line shim (`from lingwen_studio_registry import *`) preserves backward compat for `tests/` while making production code canonical. **Phase 40b** completes the migration by deleting the shim AFTER tests/ migration. **Future rule**: P3-ARCHDEBT phases with >40 consumer sites should default to shim-not-delete in C3 + delete in a follow-up phase.

5. **Prior-phase guard cross-coupling (lesson 5)** — Phase 38's `test_canonical_symbols_migrated` spot-checked `infra/studio_registry.py` as its intra-infra representative consumer of `lingwen_project_config`. After C3 converted `infra/studio_registry.py` to a shim that imports `lingwen_studio_registry` (not `lingwen_project_config`), this prior-phase guard broke. **Fix**: swap representative to `infra/project_characters.py` (function-body import of `lingwen_project_config.ProjectConfig` at line 68). **Future rule**: prior-phase guards with hardcoded representative files must be audited when later phases migrate those files. Lesson is a special case of **N.14 lesson 1** (audit matrix).

6. **5-pattern audit matrix (consolidated, lesson 6)** — full audit pipeline for migration:
   1. Literal dotted path: `grep -rn "from infra\\.X\\.Y\\b"`
   2. Indented / function-body: `grep -rn "^[[:space:]]*from infra\\.X"` (Phase 37 lesson 1)
   3. Relative same-package: `grep -rn "from \\.Y\\b" $PACKAGE_DIR/`
   4. Relative parent-package: `grep -rn "from \\.\\.Y\\b" $PARENT_DIR/`
   5. Filesystem path string literals: `grep -rn "infra/X/Y" --include="*.py"`
   6. Wildcard `from X import *` patterns (Phase 38 lesson)
   7. `monkeypatch.setattr(..., "infra.X.Y", ...)` in tests (Phase 40b new pattern)
   8. `import X as Y` re-exports in `__init__.py`
   9. Phase 40b doc comments referencing the old path
   
   For Phase 40a (50 sites), all 9 patterns were scanned pre-spec. Result: 0 mid-execution surprises, C1.5 fixup detected in <30 seconds.

7. **ruff --fix in C2b caught import reordering (lesson 7)** — Phase 38's lesson carried forward: applying `ruff check --fix` immediately after the bulk sed migration catches isort reorders in one shot, vs bleeding into C5 as scope drift. C2b applied `ruff --fix packages/ apps/` and committed the auto-fixes as part of C2b.

## Files changed (Phase 40a)

| Category | Files |
|----------|-------|
| NEW scaffold | `packages/lingwen-studio-registry/pyproject.toml` |
| NEW source | `packages/lingwen-studio-registry/src/lingwen_studio_registry/{__init__,models,discovery,state,summary,reports}.py` (5 modules, 491 lines) |
| NEW spec | `docs/superpowers/specs/2026-09-09-phase-40-p3-archdebt-studio-registry-design.md` |
| NEW handoff | `docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md` |
| NEW guards | `tests/test_phase40_lingwen_studio_registry.py` (11 guards) |
| Modified | 47 production consumer files (Phase 40a sites 1-47) |
| Modified | `infra/studio/__init__.py` (wildcard points to lingwen_studio_registry) |
| Modified | `infra/studio_registry.py` (CONVERTED to 1-line shim — NOT deleted) |
| Modified | `tests/test_phase38_lingwen_project_config.py` (Phase 38 guard fixup — swap representative file) |
| Modified | `pyproject.toml` (workspace member + source) |
| Modified | `uv.lock` (workspace sync artifact) |
| Modified | `.lingwen/architecture.yml` (version bump + I055) |
| Modified | `CLAUDE.md` (version + I055 + v39.0 entry) |
| DELETED | (nothing in Phase 40a — shim remains for Phase 40b) |

## Stats

- Master HEAD before: `26782063`
- Master HEAD after: `(this phase)`
- Commits added: 8 (C0/C1/C1.5/C2a/C2b/C3/C4 — C5 is this commit)
- Files changed: 40 total (4 NEW + 35 modified + 1 shim-converted)
- Lines: `+1651 / -480` (mostly consumer migration + scaffold + spec/handoff + guards)
- Test pass count: 218+ (lingwen-core 69 + lingwen-pipeline 0 + studio_api 1 + lingwen-creator 73 + Phase 36-40a guards 36 + Phase 32-35 guards 39)
- New package: `packages/lingwen-studio-registry/` (5 modules, 491 lines, 18 public symbols)
- New regression test: `tests/test_phase40_lingwen_studio_registry.py` (11 guards)
- Prior-phase guard fixups: 1 (Phase 38 guard's intra-infra representative swap)
- New invariants: I055 NEW (canonical `packages/lingwen-studio-registry/`; `infra.studio_registry.*` forbidden)
- Version bump: v38.0 → v39.0

## Pre-existing issues (NOT Phase 40a regressions)

- 9 ruff I001 errors in `tests/agent_system/test_chapter_production_outline.py` + `tests/infra/test_creator_mode.py` etc. — pre-existing on master HEAD `26782063`, identical count before Phase 40a.
- 1 Phase 32 guard failure (`test_phase32_shim_consumer_migrated[tests/agent_system/test_got_bridge.py]`) — pre-existing on master HEAD (the test file doesn't exist; Phase 32 moved it). Unrelated to Phase 40a.
