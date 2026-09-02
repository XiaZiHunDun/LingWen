# Phase 20 — infra/exports/ dead code cleanup — handoff

> **Date**: 2026-09-02
> **Branch**: `phase-20-infra-exports-cleanup`
> **Master HEAD at start**: `e8d49e57` (v19.4)
> **Commits**: 3 source commits (`2c9b1f6a..907e11fd`)
> **Status**: CLOSED ✅

## Summary

Phase 20 closes the longest-running carryover in Phase 18+19 chain — `infra/exports/* → packages/lingwen-storage migration` — via pure deletion rather than migration. verify-before-design revealed the carryover description was a stale Phase 18-era scope label; the actual scope was 4 empty/dead files with 0 external consumers.

**Net effect**: -129 lines, 0 functional code changes, +1 architecture invariant.

## Commits

```
2c9b1f6a  chore(infra): delete infra/exports/ dead code shim
907e11fd  docs(phase-20): CLAUDE.md v20.0 entry + architecture.yml version 20.0
[final]    docs(phase-20): handoff + this document
```

## What was deleted

| File | Lines | Type | Status at deletion |
|---|---|---|---|
| `infra/exports/__init__.py` | 16 | empty placeholder | `__all__: list[str] = []` (TODO(Phase18) marker) |
| `infra/exports/core.py` | 53 | empty placeholder | only docstring (TODO(Phase18) marker) |
| `infra/exports/events.py` | 18 | empty placeholder | only docstring (Phase 17.0 severed) |
| `infra/exports/persistence.py` | 42 | re-export shim | re-exports 23 symbols from `infra.persistence.*` — **0 external consumers** |
| **Total** | **129** | | |

## verify-before-design (N.14 lesson 1, 4th time in Phase 19+ chain)

The carryover description was: "infra/exports/* → packages/lingwen-storage migration".

The actual scope was:

1. **`infra/exports/` was effectively empty** — 3 of 4 files were `__all__: list[str] = []` placeholders with only TODO(Phase18) docstrings.
2. **`packages/lingwen-storage/` covers different concern** — it hosts `sqlite_storage_adapter.py` (Phase 126 v16.5 #N.0 migration target) + `events/{jsonl_store.py, reducer.py}` (Phase 17.0 migration target). It does NOT and never did cover `infra.persistence.*` plumbing re-exported by `infra/exports/persistence.py`.
3. **Zero external consumers** — unanchored grep (`grep -rn "from infra.exports" --include="*.py"`) returned only:
   - 3 self-references in `infra/exports/*.py` docstrings (deleted files)
   - 1 regression guard test `tests/test_infra_init_no_deferred_re_exports.py` (asserts `infra/__init__.py` has no `import infra.exports as exports` — already true at v19.4 baseline, continues to pass after deletion)
4. **All `infra.persistence.*` real consumers import directly from source** — verified via per-symbol grep:
   - `connection_context`, `get_connection`: 4 files import from `infra.persistence.connection`
   - 6 `*_DB` path constants: 4 import sites from `infra.persistence.paths`
   - `Query`, `QueryRegistry`, etc.: 3 import sites from `infra.persistence.queries`
   - 7 `registry` functions: 11 import sites from `infra.persistence.registry`
   - `SCHEMAS`, `apply_schema`, `get_schema`: 3 import sites from `infra.persistence.schemas`
   - **NO consumer went through `infra.exports.persistence`**

**Decision**: pure deletion is the correct approach — no migration needed because the "migration target" was already complete (for the only meaningful scope — events.py — Phase 17.0 severed those imports and lingwen-storage/events/ already exists).

## Verification gates (all green)

| Gate | Command | Result |
|---|---|---|
| Regression guard | `pytest tests/test_infra_init_no_deferred_re_exports.py -v` | **8 passed** ✅ |
| Frontend vitest | `pnpm exec vitest run` | **1762 + 1 skipped** (matches v19.4 baseline) ✅ |
| vue-tsc | `pnpm exec tsc --noEmit` | **0 errors** ✅ |
| ESLint | `pnpm exec eslint .` | **0 errors** ✅ |
| knip | `pnpm exec knip` | **0 issues** (`{"issues":[]}`) ✅ |
| ruff | `ruff check .` | **All checks passed!** ✅ |
| lint-imports | `.venv/bin/lint-imports` | **3 contracts KEPT, 0 broken** (324 files / 1393 deps analyzed) ✅ |
| grep audit | `grep -rn "infra.exports" --include="*.py" apps/ tests/ packages/ infra/` | **0 results** (only historical docs in `docs/superpowers/plans/`) ✅ |
| Backend pytest (key tests) | `pytest tests/persistence/ apps/studio_api/tests/` | **95 passed, 1 pre-existing fail** (FastAPI API drift in test_write_workspace_route — not related to deletion) ✅ |
| Backend pytest (infra) | `pytest tests/infra/test_plugin_manager.py tests/infra/test_creator_agent.py tests/infra/test_prose_judge.py apps/studio_api/tests/test_world_route.py apps/studio_api/tests/test_cvg_adapter.py` | **49 passed, 2 skipped, 1 pre-existing fail** (plugin_manager v15.7.1 known issue — not related) ✅ |

**Pre-existing failures verified NOT caused by deletion**:
- `tests/tools/test_llm_quality_deep_check.py` — `ImportError: socksio package not installed` (worktree env issue, also fails on master baseline before any changes)
- `tests/agent_system/test_master_controller_workflow.py` — same worktree env issue (no tools on PYTHONPATH)
- `apps/studio_api/tests/test_write_workspace_route.py::test_get_endpoint_registered` — FastAPI version API drift (no `.path` attr on `_IncludedRouter`), unrelated to `infra.exports`
- `tests/infra/test_creator_agent.py::test_stream_llm_tokens_when_provider_streams` — plugin_manager v15.7.1 latent bug (per MEMORY.md known carryover, NOT introduced by Phase 20)

## Architecture invariants enforced (1 NEW, 45 total)

- **#45 (NEW)** ✅ `infra/exports/` directory does not exist (deleted Phase 20).

## Files modified

**Deleted** (`git rm -r`):
- `infra/exports/__init__.py`
- `infra/exports/core.py`
- `infra/exports/events.py`
- `infra/exports/persistence.py`
- `infra/exports/__pycache__/` (auto-cleaned, not git-tracked)

**Updated**:
- `CLAUDE.md` — v20.0 entry at line 3, v19.4 demoted to line 4 with `~~CLOSED by v20.0~~` strike-through on infra/exports migration in carryover list
- `.lingwen/architecture.yml` — version 19.4 → 20.0 + new `phase_20:` block at end with carryover_to_phase_21

**New**:
- `docs/superpowers/handoffs/2026-09-02-phase-20-infra-exports-cleanup-handoff.md` (this file)

## Lessons

### 1. verify-before-design re-confirmed (N.14 lesson 1, 4th time in Phase 19+ chain)

The Phase 18 carryover description "infra/exports/* → packages/lingwen-storage" was a **stale Phase 18-era scope label** that did not match the actual codebase state in v19.4. Patterns observed across Phase 19+ chain:

| Phase | Claimed scope | Actual scope | Off-by factor |
|---|---|---|---|
| 19+ Sub1 | "30+" | 16 | ~2x |
| 19+ Sub2 | "30+" | 6 | 5x |
| 19+ Sub3 | "30+" | 1 | 30x |
| **20** | **"→ packages/lingwen-storage migration"** | **0 (pure deletion)** | **∞** |

Going forward: every carryover item must start with `grep -rln "infra.X" --include="*.py" | grep -v "infra/X/" | wc -l` to count real consumers. If 0 → consider pure deletion before designing migration.

### 2. PHASE-COMPAT shim detection pattern matured

Three signals identify a deletion-safe PHASE-COMPAT shim:
1. `__all__: list[str] = []` — empty re-export
2. Files contain only docstring (no actual code)
3. `# TODO(Phase...)` markers referencing never-built packages

Combine all 3 + 0 consumers = safe to delete without migration plan.

### 3. Regression guard naturally passes on deletion (negative test pattern)

`tests/test_infra_init_no_deferred_re_exports.py` was a **negative test** — it asserted `infra/__init__.py` does NOT have `import infra.exports as exports`. This is the **opposite direction** of typical regression tests:

- Typical: "ensure X exists" — fails when X is removed
- Negative: "ensure X does NOT exist" — passes when X is removed

For deletion cleanup, negative tests are MORE valuable than positive tests because they enforce the invariant that the cleanup is permanent. No new test code was needed to verify Phase 20 cleanup — the existing guard was sufficient.

### 4. Agent reports may conflict with direct file reads — trust file content

The Explore agent's report claimed `infra/exports/core.py` "does have actual content — re-exports `Result`/`Ok`/`Err`/types/errors". My direct file read showed the file was 53 lines of docstring + `__all__: list[str] = []`. **Direct file read was correct** — the agent's claim was wrong (likely confused with another file or extrapolated from the docstring's mention of "core" submodule).

**Lesson**: when an Explore agent's report conflicts with a direct file read, the file read is the source of truth. Always spot-check Explore agent claims with `Read` or `cat` before incorporating into plan or handoff.

## Carryover closure

| Carryover | Status |
|---|---|
| `infra/exports/* → packages/lingwen-storage` (Phase 18 v18, propagated through Sub1/Sub2/Sub3) | **CLOSED** by v20.0 (pure deletion — migration was moot) |

## Carryover to Phase 21+

- **lingwen_llm test-env gap** — `pytest` loads `.env` via deepeval/langsmith plugins → `MINIMAX_API_KEY` set → real LLM calls hang. Workaround: `env -u MINIMAX_API_KEY` prefix. CI should set this in the env.
- **ruff format cleanup** — `ruff format --check` reports reformatting needed in many test files (pre-existing).
- **Phase 114 prod preview regression** — accepted (per CLAUDE.md); cytoscape-fcose CJS / rollup incompatibility; 5 phases of effort failed.
- **Optional**: delete `infra/consistency/` + `infra/agent_system/` shims now that 0 code consumers remain (v19.3 + v19.4 closed their consumer chains) — same pattern as Phase 20, 2 commits.

## Solo workflow closure

```
$ git checkout master && git merge --ff-only phase-20-infra-exports-cleanup
$ git push origin master
$ git worktree remove ../LingWen-phase-20
```

Master HEAD after merge: `907e11fd` (v20.0).