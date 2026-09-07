# Phase 32 — PHASE-COMPAT shim cleanup (B1 战术版) — design

> **Date**: 2026-09-07
> **Branch**: `phase-32-shim-cleanup`
> **Master HEAD at start**: `69e620d7` (v31.0)
> **Status**: SPEC — approved for execution

## Goal

Delete 3 PHASE-COMPAT shim files and migrate 6 test consumers. Mechanical refactor, zero design risk.

## Scope (IN)

| Shim file | Lines | Type | Consumer count |
|-----------|-------|------|---------------|
| `infra/subplot/data_structures.py` | 32 | Pure re-export from `lingwen_core.domain.subplot` | **0** |
| `infra/world_model/data_structures.py` | 69 | Pure re-export from `lingwen_core.domain.*` | **0** |
| `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` | 11 | Pure re-export from `lingwen_pipeline.master_controller` | **6 test files** (12 import sites) |

**Test consumer migration pattern**: `from lingwen_core.agents import master_controller as mc_mod` → `from lingwen_pipeline import master_controller as mc_mod`

## Scope (OUT — Phase 33+)

- **`infra/world_model/__init__.py` split** (mixed file: canonical re-exports + behavior services, 5 consumers): 1 phase / 8-12 commits
- **`infra.got.*` → `packages/lingwen-got/` migration**: 199 tests / multi-day

## Consumer topology (verified)

### `infra.subplot.data_structures` — 0 consumers
Unanchored grep across `apps/`, `tests/`, `packages/`, `infra/`, `scripts/`:
- 2 hits, both non-consumer: own shim docstring (line 5) + `infra/world_model/links.py:29` historical comment

### `infra.world_model.data_structures` — 0 consumers
- 2 hits, both non-consumer: own shim docstring (line 23) + own comment (line 30)

### `lingwen_core.agents.master_controller` — 6 test files (12 import sites)
Exact pattern `from lingwen_core.agents import master_controller as mc_mod`:
- `tests/agent_system/test_master_controller_workflow.py:246`
- `tests/agent_system/test_decision_integration.py:33`
- `tests/agent_system/test_got_bridge.py:591, 813, 847`
- `tests/dashboard/test_decision_api.py:27, 633`
- `tests/dashboard/test_app_workflow_production_summary_f66.py:9`
- `tests/dashboard/test_app_workflow_status.py:18, 91, 187, 282`

All 12 sites use `mc_mod.MasterController.__new__(mc_mod.MasterController)`. Single-symbol use, mechanical replacement.

### Canonical `lingwen_pipeline.master_controller` — 38 active imports
Confirmed via `grep -RIn`: 32 test imports + 5 production imports (workflow_runner.py × 2, chapter_golden_path.py:71, chapter_production_pilot.py:430, polisher/prompts.py:132) + 1 self-shim docstring. Production-side already uses canonical path — migration is proven safe.

## TDD approach (RED → GREEN → REFACTOR)

### RED (C1)
Write `tests/test_phase32_shim_cleanup.py` mirroring Phase 18.4 / Phase 21 patterns. Three test categories:
1. **Path-existence guard** (parametrized 3 shim paths): assert `not (REPO_ROOT / shim_path).exists()`
2. **Consumer text-absence guard** (parametrized 6 test files): assert no `from lingwen_core.agents import master_controller as mc_mod` in each file
3. **Canonical-symbol guard**: assert `lingwen_core/domain/__init__.py` re-exports `Plot`/`WorldSnapshot`/`Ripple`/`KeyPoint` (proves canonical replacement paths exist)

Use static grep (path-existence + text search) — no Python import execution — to avoid dependency on `lingwen-pipeline` wheel at test-collection time.

### GREEN (C2-C5)
1. **C2**: `git rm infra/subplot/data_structures.py` (32 lines)
2. **C3**: `git rm infra/world_model/data_structures.py` (69 lines) + clean stale comment in `infra/world_model/links.py:28-29`
3. **C4**: Batch migrate 12 import sites in 6 test files (single commit, mechanical sed-equivalent)
4. **C5**: `git rm packages/lingwen-core/src/lingwen_core/agents/master_controller.py` (11 lines)

After C5, run `pytest tests/test_phase32_shim_cleanup.py -v` — expect 4/4 (or N/4 depending on count) GREEN.

## Edge case (flag, NOT in Phase 32 scope)

`packages/lingwen-core/src/lingwen_core/agents/agents/polisher/prompts.py:132` has `from lingwen_pipeline.master_controller import _safe_label` but `_safe_label` is defined in `mc_utils.py:25`, not `master_controller.py`. Latent broken import — predates Phase 32. Flag for Phase 33+ audit. `build_merge_synthesis_prompt` is reachable only via `test_got_bridge.py:521` which imports `_S1_S8_NAMES` only, so the broken `_safe_label` import is not exercised at test-collection time.

## Doc-sync scope (C6)

| File | Change |
|------|--------|
| `CLAUDE.md` | v32.0 entry (mirror v31.0 format) |
| `.lingwen/architecture.yml` | version 31.0 → 32.0; update invariants #37 + #39 to "deleted Phase 32" |
| `docs/LINGWEN_ARCHITECTURE_SPEC.md:669` | Remove `SubplotDataStructures` row (or repoint to `packages/lingwen-core/src/lingwen_core/domain/subplot.py`) |
| `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md:26` | Flip status: "PHASE-COMPAT shim, 留 P2-ARCHDEBT" → "deleted Phase 32" |
| `docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md:39,162` | Flip "Phase 32+ 候选" → "CLOSED by Phase 32" |
| `docs/superpowers/specs/2026-09-07-phase-31-archdebt-mini-design.md:26,418` | Flip Phase 32 candidate → CLOSED |
| `packages/lingwen-pipeline/README.md:19-20` | Flip historical shim note → "deleted Phase 32" |

## Verification gates (G1-G8)

| Gate | Command | Pass criteria |
|------|---------|--------------|
| G1 ruff | `ruff check .` | 0 errors |
| G2 guard | `pytest tests/test_phase32_shim_cleanup.py -v` | All passing |
| G3 modified suites | `pytest <6 consumer test files> -v` | All passing (baseline 116 + 1 skipped, no regression) |
| G4 full backend | `pytest tests/ --rootdir=.` | tests/agent_system + tests/got + tests/dashboard baseline, 0 new failures |
| G5 frontend | `pnpm vitest run` | Baseline 1862 + 1 skipped (no regression; shim deletion is backend-only) |
| G6 knip | `pnpm exec knip` | `{"issues":[]}` (frontend unaffected) |
| G7 lint-imports | `.venv/bin/lint-imports` | 3 contracts KEPT, file count validation |
| G8 grep audit | `grep -rn "infra.subplot.data_structures\|infra.world_model.data_structures\|lingwen_core.agents.master_controller" --include="*.py" apps/ tests/ packages/ infra/ scripts/` | 0 consumer hits |

## Commit ordering (9 atomic commits)

```
c0: docs(phase-32): write spec + plan design docs        # phase start
c1: test(shim): add Phase 32 regression guard tests (RED)
c2: chore(infra): delete infra/subplot/data_structures.py shim (1 of 3)
c3: chore(infra): delete infra/world_model/data_structures.py shim (2 of 3)
c4: refactor(test): migrate 6 MasterController test imports to lingwen_pipeline (3a of 3)
c5: chore(packages): delete lingwen-core/agents/master_controller.py shim (3b of 3)
c6: docs(architecture): CLAUDE.md v32.0 + architecture.yml version 32.0 + arch spec + carryover flips
c7: docs(phase-32): handoff + CURRENT_STATUS + BACKLOG sync
c8: chore(merge): ff-merge phase-32-shim-cleanup to master
```

1 task per commit (N.14 lesson 7). Each independently revertable. Bisect-friendly.

## Risks

| Risk | Mitigation |
|------|-----------|
| Unanchored grep missed a consumer | Phase 19+ sub1 polish T9b lesson. G8 uses unanchored grep (no `^`). 7 packages/apps already use canonical `lingwen_pipeline.master_controller` (agent-verified) so migration proven. |
| Worktree venv missing deps | Phase 31 carryover lesson. Install pytest-timeout/pytest-cov/psutil explicitly (uv pip install --offline). |
| `infra/world_model/links.py` stale comment breaks G8 grep | C3 includes comment cleanup. G8 verifies 0 hits after both C3 + C5. |
| Guard test depends on lingwen-pipeline wheel at collection time | Use static grep (path-exists + text search) — no Python import execution. Phase 18.4 pattern. |
| Latent `_safe_label` import break in `polisher/prompts.py:132` | Out of Phase 32 scope. Pre-existing bug. Flag for Phase 33+ audit. |

## Carryover closure

| Carryover | Status |
|-----------|--------|
| P2-ARCHDEBT PHASE-COMPAT shim deletion (v31.0 剩余 1/2) | **CLOSED** by Phase 32 |

## Carryover to Phase 33+

- **`infra.got.*` → `packages/lingwen-got/` migration** — 199 tests, multi-day
- **`infra/world_model/__init__.py` split** — 5 consumer migration, 1 phase / 8-12 commits
- **`polisher/prompts.py:132` `_safe_label` import** — latent broken, needs separate fix
- **HANDOFF.md `latest_decision_queue` wording fix** — pre-existing carryover
- **PHASE-COMPAT docstring in tests/__init__.py + tests/consistency/__init__.py + tests/infra/__init__.py** — false positive (legitimate pytest package init). Leave as-is.
