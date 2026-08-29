# Phase 126 v16.5 #2 — DP-03 (StoragePort enforcement) Handoff

> **Status:** closed, 3 commits on `phase-126-v16-5-dp03` branch (ready for merge to master + push)
> **Previous:** v16.5 #1 (eliminate grimp-evasion hack, `ee83d9e1`)
> **Next:** v16.5 #3..#7 — DP-01 + async port conformance + remaining packages migration + tools migration + DTO schema audit

## 0. TL;DR

DP-03 enforcement: business code (`lingwen_creator` + `apps`) MUST NOT import `sqlite3` directly. Use `StoragePort` from `lingwen_shared.ports.storage` instead. Enforced via import-linter forbidden contract + 4 hygiene regression tests + defense-in-depth grep gate.

**Scope assessment**: Investigated all 30+ sqlite3 usages in the codebase:
- `apps/studio_api/app.py:18` — **1 dead import** (removed in T1)
- `packages/lingwen-creator/` — 0 imports (clean)
- `packages/lingwen-core/pipeline/cli/` — 8 files (carryover #4 — remaining packages)
- `infra/*` — 25+ files (below business layer, NOT in scope)

Only 1 file required cleanup. T1 removed the dead import; T2 added the architectural guard.

## 1. Architecture Invariant

Business code (`lingwen_creator` + `apps`) MUST NOT import `sqlite3` directly. Storage access goes through `StoragePort` (declared in `packages/lingwen-shared/src/lingwen_shared/ports/storage.py`).

**Defense-in-depth enforcement** (T2 documented deviation):
1. **import-linter forbidden contract** `no_concrete_sqlite3_in_business_code` — covers `lingwen_creator` only (NOT `apps`).
2. **Hygiene grep test** `test_no_sqlite3_imports_in_business_code` — covers BOTH `apps/` and `lingwen_creator/` for direct imports.

**Why split enforcement**: import-linter's `forbidden` contract follows transitive imports. `apps/studio_api/routes/*` legitimately composes `infra/*` modules that import sqlite3 (e.g., `infra.world_db.queries.proposals`, `infra.cross_volume.storage`, `infra.persistence.sqlite_config`). The chain `apps → infra → sqlite3` would fail the contract. Restricting `source_modules` to `lingwen_creator` (which doesn't transitively reach sqlite3) lets the contract pass cleanly today. The grep test fills the gap by catching direct violations anywhere in business code.

## 2. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | `87e2374f` | `chore(apps)`: remove dead `import sqlite3` from `apps/studio_api/app.py:18` |
| T2 | `ea4a14aa` | `feat(import-linter)`: add `no_concrete_sqlite3_in_business_code` forbidden contract + 4 hygiene tests |
| T3 | (this commit) | `docs(phase-126)`: handoff + CLAUDE.md + architecture.yml |

**Total: 3 commits** (plan estimated 3 — no deviation).

## 3. T2 Documented Deviation

The original T2 spec had `source_modules = ["lingwen_creator", "apps"]`. The implementer found that:

> `apps/studio_api/routes/*` legitimately composes `infra/*` modules that import sqlite3 (e.g., `infra.world_db.queries.proposals`, `infra.cross_volume.storage`, `infra.persistence.sqlite_config`). The chain `apps → infra → sqlite3` would fail the contract.

**Solution adopted**: `source_modules = ["lingwen_creator"]` only. Compensated by the grep test which checks `apps/` directly.

**Future "full fix"** (carryover to v16.5 #3+):
1. Refactor all `infra/*` sqlite3 usages to go through `StoragePort` internally (25+ files).
2. Then `apps/` can use `StoragePort` cleanly without transitive contamination.
3. Then the contract can be expanded to `source_modules = ["lingwen_creator", "apps"]`.

This mirrors the v16.4 → v16.5 #1 trajectory for DP-02:
- DP-02 v16.4: factory pattern in port_adapter (limits but doesn't eliminate transitive)
- DP-02 v16.5 #1: relocate data types to lingwen_shared (full elimination)
- DP-03 v16.5 #2: defense-in-depth grep + restricted contract (pragmatic start)
- DP-03 v16.5 #N: refactor infra/* to use StoragePort internally (full elimination)

## 4. Verification Matrix

| Gate | v16.5 #1 baseline | v16.5 #2 | Status |
|------|-------------------|----------|--------|
| `pytest tests/infra/ apps/studio_api/tests/ tests/hygiene/` | 394 passed | 398 passed (+4 hygiene) + 5 skipped | ✓ |
| `pytest packages/lingwen-creator/tests/` | 73 | 73 | ✓ |
| `pytest packages/lingwen-shared/tests/` | 85 | 85 | ✓ |
| `pytest packages/lingwen-llm/tests/` | 8 | 8 | ✓ |
| `pnpm vitest run` | 1729 | 1729 (no frontend changes) | ✓ |
| `ruff check` | 0 | 0 | ✓ |
| `lint-imports` | 2 contracts | **3 contracts KEPT** (added DP-03) | ✓ |
| `pnpm tsc --noEmit` | 0 | 0 | ✓ |

**Total backend**: 564 passed (398+73+85+8) + 5 skipped. **0 regressions**.
**Net new tests**: +4 (DP-03 hygiene). 6 hygiene tests total (2 v16.5 #1 grimp-evasion + 4 v16.5 #2 DP-03).

## 5. Files Changed

### Modified
- `apps/studio_api/app.py` — removed 1 line (dead import)
- `pyproject.toml` — added `no_concrete_sqlite3_in_business_code` forbidden contract
- `CLAUDE.md` — added v16.5 #2 section (this commit)
- `.lingwen/architecture.yml` — DP-03 status updated, version bumped to 16.5.2

### Created
- `tests/hygiene/test_no_concrete_sqlite3_import.py` — 4 regression tests
- `docs/superpowers/handoffs/2026-08-29-phase-126-v16-5-dp03-storage-port-enforcement-handoff.md` — this file

## 6. Lessons Learned

1. **DP enforcement often requires defense-in-depth** — A single mechanism (import-linter OR grep test) isn't enough when transitive imports complicate the strict form. Combining both (import-linter for clean modules + grep test for transitively-contaminated modules) gives full coverage with acceptable false-positive resistance. Document the split clearly.

2. **Forbid `sqlite3` is the same shape as forbid `infra.llm_service`** — Both are "concrete resource is forbidden; use the port instead." The mechanical pattern is identical: import-linter forbidden contract + hygiene test + back-compat cleanup. Future DPs (DP-01, DP-04) should follow the same template.

3. **Dead imports are a low-cost find** — When investigating for DP enforcement, `grep "import sqlite3"` on a file with no other sqlite3 references is a free win. T1 was a 1-line commit with zero risk because the import was provably unused (verified via `grep -nE "sqlite3\.|sqlite3\)|= sqlite3"`). DP migration can start with these.

## 7. Architecture Invariants Now Enforced

1. **`lingwen_creator` MUST NOT import `sqlite3`** — import-linter forbidden contract (strictest form, passes because lingwen_creator doesn't transitively reach sqlite3).
2. **`apps/` MUST NOT directly import `sqlite3`** — hygiene grep test (covers what import-linter can't because of infra transitives).
3. **`StoragePort` Protocol is the canonical persistence interface** — declared in `lingwen_shared/ports/storage.py`. Any new persistence code should use this port.

## 8. Pre-merge Checklist

- [x] All 3 commits on `phase-126-v16-5-dp03` branch (local; push pending)
- [x] All 5 verification gates green (564 backend passed, 1729 vitest, 0 ruff, 3 contracts KEPT)
- [x] Handoff doc written (this file)
- [x] CLAUDE.md updated
- [x] `.lingwen/architecture.yml` updated
- [ ] `git checkout master && git merge phase-126-v16-5-dp03 --no-ff && git push origin master` (Step 3.7-3.8)
- [ ] Cleanup worktree (Step 3.9)

## 9. Carryover to v16.5 #3..#7

- **DP-03 full fix** (high-priority for v16.5 #3+): refactor `infra/*` to use `StoragePort` internally (25+ files). Then `apps/` can use `StoragePort` cleanly and the import-linter contract can expand to `["lingwen_creator", "apps"]`.
- **DP-01** (cross-package contracts via ports): enumerate 4 allowed import forms (contracts / ports / value_objects / pure util) across `lingwen-*` packages.
- **Async port conformance**: rewrite `LLMServiceAdapter` with `async execute → LLMResult`.
- **Remaining packages migration** (`lingwen_core` / `lingwen_pipeline` / `lingwen_prompt` / `lingwen_cli`): 8 files using sqlite3 directly need similar treatment to apps/.
- **Tools migration** (`tools/llm_*.py` — 11 files): carryover from v16.4.
- **DTO schema audit + typed wrapper narrowing** (v16.3 carryover).

## 10. Commit Timeline

```
ea4a14aa (T2 — DP-03 forbidden contract + 4 tests)
87e2374f (T1 — Remove dead sqlite3 import)
ee83d9e1 (master baseline — v16.5 #1)
```
