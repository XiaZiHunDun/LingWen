# Phase 126 v16.5 #N.0 — Relocate SqliteStorageAdapter Handoff

> **Status:** closed, 2 commits on `phase-126-v16-5-n0` branch
> **Previous:** v16.5 #7 (DTO audit + typed wrapper narrowing, `0158ce84`)
> **Next:** v16.5 #N.1 — add factory pattern to `lingwen_shared.ports.storage`

## 0. TL;DR

`SqliteStorageAdapter` relocated from `infra/persistence/sqlite_storage_adapter.py` to `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py`. The infra version becomes a back-compat re-export shim. This unblocks migration of `lingwen_core/pipeline/cli` (the 8 whitelisted Phase 15.0 T2.8 deprecated files) without circular import.

## 1. Why Relocate?

`SqliteStorageAdapter` was placed in `infra/persistence/` during v16.5 #3 PARTIAL. That works for `infra/` itself but blocks migration of `lingwen_core`, `lingwen_pipeline`, `lingwen_cli`:

- `infra` already depends on `lingwen_core` (e.g., `infra.persistence.bootstrap` imports `BudgetService`, `CostTrackerDB` from `lingwen_core.agents`)
- If `lingwen_core.agents.budget_persistence` imports `infra.persistence.sqlite_storage_adapter`, it creates a cycle: `lingwen_core → infra → lingwen_core`

Solution: move `SqliteStorageAdapter` to a leaf package (`packages/lingwen-storage/`) which has no `lingwen_*` dependencies. Now both `infra/` AND `lingwen_core/pipeline/cli` can use it.

## 2. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | `5cb6adc4` | `feat(lingwen-storage)`: create `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` (217 lines including module docstring) + add `lingwen-shared` workspace dep to `packages/lingwen-storage/pyproject.toml` |
| T2 | `6800a4c8` | `refactor(persistence)`: back-compat shim + delete `tests/persistence/test_sqlite_storage_adapter.py` (canonical location is now `packages/lingwen-storage/tests/`) |
| T3 | (this commit) | `docs(phase-126)`: handoff doc |

## 3. Architecture Invariant (Preserved)

After relocation:
- `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` is the canonical SQLite backend implementation
- It is the ONLY file in the entire `lingwen-*` package family that imports `sqlite3`
- `infra/persistence/sqlite_storage_adapter.py` is now a thin re-export shim (zero `import sqlite3`)
- Both locations expose the same symbols (`SqliteStorageAdapter`, `SqliteConnection`, `FileSystemMarkdownRoundtrip`)
- Test ownership follows package ownership: `packages/lingwen-storage/tests/test_sqlite_storage_adapter.py`

## 4. Verification Matrix

| Gate | v16.5 #7 | v16.5 #N.0 | Status |
|------|----------|------------|--------|
| `pytest packages/lingwen-storage/tests/` | 18 (jsonl+reducer) | 31 (+13 NEW sqlite) | ✓ |
| `pytest tests/hygiene/test_no_concrete_sqlite3_import.py` | 5 | 5 (no regression) | ✓ |
| `pytest tests/hygiene/ tooling/hygiene/tests/` | 39 | 39 (no regression) | ✓ |
| `lint-imports` | 3 KEPT | 3 KEPT | ✓ |
| `ruff check` | 0 | 0 | ✓ |
| `infra/` `import sqlite3` count | 22 (pre-baseline) | 21 (shim no longer imports) | ✓ |

**Net**: -1 `import sqlite3` in `infra/`. **Zero regressions** in any existing test.

Note: `tests/persistence/test_*.py` shows 8 pre-existing failures (`TestRegisterAll`) due to `ModuleNotFoundError: No module named 'lingwen_llm'` (worktree environment missing editable install of `lingwen-llm`). These failures are baseline environmental issues (reproduce on master `0158ce84` without any of my changes), NOT a regression from v16.5 #N.0.

## 5. Files Changed

### Created
- `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` (217 lines, relocated from infra + extended module docstring)
- `packages/lingwen-storage/tests/test_sqlite_storage_adapter.py` (273 lines, moved from `tests/persistence/`)
- `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n0-relocate-sqlitestorageadapter-handoff.md` (this file)

### Modified
- `packages/lingwen-storage/pyproject.toml` — added `lingwen-shared` to `dependencies`
- `infra/persistence/sqlite_storage_adapter.py` — now a 17-line thin re-export shim (was 217 lines)

### Deleted
- `tests/persistence/test_sqlite_storage_adapter.py` — moved to `packages/lingwen-storage/tests/` (matches package ownership convention)

## 6. Carryover to v16.5 #N.1+ (Next Phases)

v16.5 #N.0 enables:
- **#N.1**: Add factory pattern (`set_default_storage_factory()` + `get_default_storage()`) to `lingwen_shared.ports.storage` (mirror v16.5 #1 LLMServiceAdapter)
- **#N.2**: Migrate 19 `apps/*` files to use `get_default_storage()` from lingwen_shared
- **#N.3**: Migrate 8 whitelisted `infra/*` files (Phase 15.0 T2.8 deprecated) to drop `import sqlite3`
- **#N.4**: Migrate 21 remaining `infra/*` files to drop `import sqlite3`
- **#N.5**: Expand import-linter contract `source_modules = ["lingwen_creator", "apps"]`
- **#N.6**: Migrate 12 whitelisted `tools/*` files to use `LLMServiceAdapter()` from `lingwen_llm.port_adapter`

Total estimated: ~30-50 commits for the full DP-03 expansion.

## 7. Lessons Learned

1. **Package placement matters for cycle avoidance** — `SqliteStorageAdapter` originally in `infra/` blocked `lingwen_core` from migrating. Moving to a leaf package (`lingwen-storage`, no `lingwen_*` deps) breaks the cycle.

2. **Back-compat shims enable non-breaking relocations** — The 17-line shim at `infra/persistence/sqlite_storage_adapter.py` means no consumer needs to change import paths immediately. Future migrations can be done commit-by-commit (per DP-06).

3. **Test ownership should follow package ownership** — Tests moved from `tests/persistence/` (top-level test dir) to `packages/lingwen-storage/tests/` (package-local tests). Matches the convention for other packages (e.g., `packages/lingwen-llm/tests/`).

4. **`lingwen-shared` becomes a transitive dep of `lingwen-storage`** — Adding `lingwen-shared` to `packages/lingwen-storage/pyproject.toml` was required (workspace source auto-resolves via existing `lingwen-shared = { workspace = true }` in root pyproject.toml).

5. **Ruff I001 import-block sort merges first-party with project imports** — Project's ruff config treats third-party and first-party as one block, so `import pytest` and `from lingwen_storage...` end up on adjacent lines. Identified and `ruff --fix`-applied during verification gate.

## 8. Commit Timeline

```
6800a4c8 (T2: refactor(persistence) — back-compat shim + move tests)
5cb6adc4 (T1: feat(lingwen-storage) — relocate SqliteStorageAdapter)
0158ce84 (v16.5 #7 baseline)
```
