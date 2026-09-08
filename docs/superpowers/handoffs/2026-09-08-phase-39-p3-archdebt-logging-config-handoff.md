# Phase 39 — P3-ARCHDEBT (logging_config) handoff

> **Date**: 2026-09-08
> **Branch**: `phase-39-p3-archdebt-logging-config` (deleted after ff-merge + worktree remove)
> **Master HEAD**: `(to be updated post-merge)`
> **Spec**: `docs/superpowers/specs/2026-09-08-phase-39-p3-archdebt-logging-config-design.md`

## Summary

P3-ARCHDEBT item **4/5** — `infra/logging_config.py` (59 行, 3 public symbols: `StructuredFormatter` + `setup_logging` + `logger` module-level instance) → `packages/lingwen-logging-config/`.

**Smallest P3 module so far**: 8 consumer sites (vs Phase 38's 26, Phase 37's 86, Phase 36's 14), 0 function-body imports, 0 test consumers, 0 filesystem path literals, 1 wildcard. **LEAF package** (only stdlib deps).

## Why

5-phase P3-ARCHDEBT backlog (`infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/):
- Phase 36 (errors) ✅
- Phase 37 (paths) ✅
- Phase 38 (project_config) ✅
- **Phase 39 (logging_config) — this handoff**
- Phase 40 (studio_registry) ⏳

## Atomic commits (5)

| # | SHA (target) | Task |
|---|--------------|------|
| **C0** | `7dd36886` | spec for lingwen-logging-config |
| **C1** | `10bf6c43` | scaffold lingwen-logging-config (incl. uv.lock) |
| **C2** | `c2d014a4` | migrate 7 consumers + ruff --fix (2 isort reorders) |
| **C3** | `6454cd49` | delete infra/logging_config.py + clean wildcard |
| **C4** | `f3c6969a` | bump v37.0→v38.0 + invariant #54 |
| **C5** | (this) | regression guards + doc sync + handoff |

No C3.5 fixup needed (pre-spec verification: 0 function-body, 0 path literals, 0 prior-phase guards → no surprises during execution).

## Validation gates

| Gate | Status |
|------|--------|
| ruff clean | ✅ (4 pre-existing E741 unchanged, 0 new) |
| Phase 39 guards | ✅ 7/7 GREEN |
| Phase 38 guards preserved | ✅ 6/6 GREEN |
| Phase 37 guards preserved | ✅ 5/5 GREEN |
| lingwen-core + lingwen-pipeline baselines | ✅ 69/69 pass |
| YAML structure (architecture.yml) | ✅ parses via yaml.safe_load |
| workspace member declared BEFORE uv sync | ✅ (C1, Phase 34 lesson) |
| ruff --fix in C2 | ✅ (Phase 38 lesson 5 — 2 isort reorders in task_orchestrator.py + memory_service.py) |
| whitespace-preserving `\1` sed | ✅ (Phase 38 lesson 1 — applied even though 0 function-body sites) |
| 5-pattern audit matrix | ✅ all 5 patterns verified pre-spec |

## Consumer migration (7 sites + 1 wildcard)

| # | File | Line | Style |
|---|------|------|-------|
| 1 | `packages/lingwen-pipeline/.../run_checker.py` | 16 | top-level |
| 2 | `packages/lingwen-pipeline/.../update_state.py` | 17 | top-level |
| 3 | `packages/lingwen-pipeline/.../block_proceed.py` | 12 | top-level |
| 4 | `packages/lingwen-pipeline/.../notify.py` | 11 | top-level |
| 5 | `packages/lingwen-pipeline/.../workflow_validator.py` | 5 | top-level |
| 6 | `packages/lingwen-core/.../task_orchestrator.py` | 16 | top-level (ruff reordered to stdlib group) |
| 7 | `infra/memory_service.py` | 26 | top-level (ruff reordered to stdlib group) |
| 8 | `infra/core/__init__.py` | 6 | **wildcard** (deleted in C3) |

## Carryover closure

- ✅ P3-ARCHDEBT 4/5 (`logging_config`) → CLOSED 2026-09-08
- ⏳ P3-ARCHDEBT 5/5 (`studio_registry`, 50 consumers) → Phase 40

## Phase 39 lessons

1. **Pre-spec verification prevented surprises**: All 4 critical counts (consumer sites=8, function-body=0, test consumers=0, path literals=0) verified via `grep -c` BEFORE writing spec. Result: 0 mid-execution surprises, 0 C3.5 fixup commit needed. Phase 38 lesson 3 applied successfully.

2. **LEAF package = trivial scaffold**: pyproject.toml template is identical to `lingwen-paths` (hatchling, deps=[]). 1-line workspace member addition + 1-line workspace source addition. Faster than non-LEAF packages (Phase 38's `lingwen-project-config` had 2 workspace deps to declare).

3. **`\1` backreference is cheap insurance**: Even when pre-spec audit shows 0 function-body sites, the whitespace-preserving sed pattern costs nothing extra and protects against late-discovered indented imports.

4. **ruff --fix in C2 keeps C5 lean**: 2 isort reorders caught and fixed in C2 (vs Phase 38 where they bled into C5 as scope drift). C5 has zero ruff work needed.

5. **YAML double-quoted backslash escape gotcha**: When inserting YAML strings with `\` characters (e.g. `infra\.logging_config`), must use `\\` (double-escape) to survive YAML's escape sequence parsing. Caught in C4 via `yaml.safe_load` verification before commit.

## Files changed (Phase 39)

| Category | Files |
|----------|-------|
| NEW scaffold | `packages/lingwen-logging-config/pyproject.toml` |
| NEW source | `packages/lingwen-logging-config/src/lingwen_logging_config/__init__.py` |
| NEW spec | `docs/superpowers/specs/2026-09-08-phase-39-p3-archdebt-logging-config-design.md` |
| NEW handoff | `docs/superpowers/handoffs/2026-09-08-phase-39-p3-archdebt-logging-config-handoff.md` |
| NEW guards | `tests/test_phase39_lingwen_logging_config.py` |
| Modified | 7 consumer files (Phase 39 sites 1-7) |
| Modified | `infra/core/__init__.py` (wildcard line removed) |
| Modified | `pyproject.toml` (workspace member + source) |
| Modified | `uv.lock` (workspace sync artifact) |
| Modified | `.lingwen/architecture.yml` (version bump + I054) |
| Modified | `CLAUDE.md` (version + I054 + v38.0 entry) |
| DELETED | `infra/logging_config.py` |

## Stats

- Master HEAD before: `f36b0814`
- Master HEAD after: `(this phase)`
- Commits added: 5 (C0/C1/C2/C3/C4 — C5 is this commit)
- Files changed: 16 total (4 NEW + 11 modified + 1 deleted)
- Lines: `+~120 / -61` (mostly scaffold + spec/handoff + guards)
- Test pass count: 69 (lingwen-core + lingwen-pipeline) + 18 (Phase 37/38/39 guards)
- New package: `packages/lingwen-logging-config/` (1 module, 59 lines)
- New regression test: `tests/test_phase39_lingwen_logging_config.py` (7 guards)
- New invariants: I054 NEW (canonical `packages/lingwen-logging-config/`; `infra.logging_config.*` forbidden)
- Version bump: v37.0 → v38.0
