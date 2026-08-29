# Phase 126 v16.5 #3 — DP-03 Full Fix (PARTIAL) Handoff

> **Status:** PARTIAL — 1 commit on `phase-126-v16-5-dp03-fullfix` branch (T1: SqliteStorageAdapter)
> **Previous:** v16.5 #2 (DP-03 initial enforcement, `f6f5d97e`)
> **Next:** v16.5 #N (full DP-03 expansion: break apps → infra chains via factory pattern + Protocol migration)

## 0. TL;DR

DP-03 full fix split into two layers:

1. **DONE (v16.5 #3 partial)**: Created concrete `SqliteStorageAdapter` (the canonical SQLite backend implementing `StoragePort`). This is the architectural foundation for future expansion — `infra/persistence/sqlite_storage_adapter.py` is the ONLY allowed `import sqlite3` site in `infra/`.

2. **DEFERRED to v16.5 #N**: Expand import-linter forbidden contract `no_concrete_sqlite3_in_business_code` from `["lingwen_creator"]` to `["lingwen_creator", "apps"]`. Requires:
   - Add factory pattern to `lingwen_shared.ports.storage` (mirror v16.5 #1 LLMServiceAdapter)
   - Migrate 19 `apps/` files to use `get_default_storage()` from `lingwen_shared` instead of `infra.persistence.*` directly
   - Migrate 22 `infra/` files to drop `import sqlite3` (grimp follows TYPE_CHECKING — confirmed empirically)
   - Each query function's `conn: sqlite3.Connection` annotation → `ConnectionPort` Protocol

This was scoped down from the original plan after empirical testing revealed the full expansion requires service layer changes across the FastAPI app boundary (genuinely 30-50 commits of mechanical refactor).

## 1. T1 — SqliteStorageAdapter Concrete Implementation

### Commit

`e8b51ab9` — `feat(persistence): v16.5 #3 DP-03 — SqliteStorageAdapter concrete impl`

### Components

**`infra/persistence/sqlite_storage_adapter.py`** (200 lines):
- `SqliteConnection`: wraps `sqlite3.Connection`, satisfies `ConnectionPort` Protocol via structural subtyping. `__getattr__` delegates cursor methods (`fetchall`, `row_factory`, `cursor()`, etc.) so existing call sites keep working unchanged.
- `FileSystemMarkdownRoundtrip`: `MarkdownRoundtripPort` impl with atomic write via `.tmp + rename`.
- `SqliteStorageAdapter`: concrete `StoragePort` impl with:
  - `with_connection(fn)`: read-only use, no commit
  - `with_transaction(fn)`: commit on success, rollback on error
  - `markdown_roundtrip()`: returns the markdown round-trip accessor

### Tests

**`tests/persistence/test_sqlite_storage_adapter.py`** (13 tests, all pass):
1. `test_with_connection_returns_row_data` — read path
2. `test_with_transaction_commits` — write path persists across connections
3. `test_with_transaction_rolls_back_on_error` — error → rollback
4. `test_with_connection_does_not_commit` — explicit documentation of sqlite3 3.51 behavior (DML on close-without-commit rolls back)
5. `test_sqlite_connection_delegates_to_underlying` — `__getattr__` delegation works
6. `test_with_transaction_returns_callback_return_value` — return value passthrough
7. `test_markdown_roundtrip_writes_atomically` — atomic .tmp + rename
8. `test_markdown_roundtrip_read_returns_content` — read
9. `test_markdown_roundtrip_list_chapters_missing_dir` — dir missing returns []
10. `test_markdown_roundtrip_list_chapters_returns_sorted_paths` — sorted enumeration
11. `test_markdown_roundtrip_singleton_via_storage` — singleton accessor
12. `test_default_timeout_is_5_seconds` — timeout config
13. `test_storage_adapter_satisfies_protocol` — duck-typed Protocol check

### Documented Deviations (from T1 spec)

1. **Test location**: `tests/persistence/test_sqlite_storage_adapter.py` (matches project convention with sibling persistence tests)
2. **`params: object = ()` (not `...`)**: sqlite3 rejects Ellipsis as "unsupported parameter type" when forwarded to `sqlite3.Connection.execute()`. Empty tuple is the documented "no params" sentinel.
3. **Protocol conformance check via duck-typing** (not `isinstance`): `StoragePort` is not `@runtime_checkable`, so `isinstance` raises `TypeError`. Replacement test verifies all 3 required methods are bound.
4. **Empirical finding**: Python 3.13 + sqlite3 3.51 rolls back pending DML on close-without-commit. `with_connection` test uses `with_transaction` for INSERTs (otherwise the test would fail). Documented in a companion test `test_with_connection_does_not_commit`.

### Architecture Invariant (Documented)

`infra/persistence/sqlite_storage_adapter.py` is the ONLY allowed `import sqlite3` site in `infra/`. This is documented in the module docstring. **Not yet enforced by import-linter** (enforcement comes in v16.5 #N when apps is added to the forbidden contract source_modules).

## 2. Empirical Test Result (T1.5 — pre-T1)

Before dispatching T1, ran a quick empirical test to verify grimp behavior on `TYPE_CHECKING` blocks:

- **Question**: Does grimp follow `if TYPE_CHECKING: import sqlite3`?
- **Result**: **YES** — grimp treats TYPE_CHECKING imports identically to runtime imports for transitive analysis.
- **Implication for v16.5 #N**: The migration cannot rely on TYPE_CHECKING to keep type annotations while removing runtime imports. Each query function's `conn: sqlite3.Connection` annotation must change to `ConnectionPort` (or use the `SqliteConnection` wrapper).

## 3. Why v16.5 #3 is PARTIAL (not FULL)

The original v16.5 #3 goal was to expand the import-linter contract to include `apps/`. Investigation showed:

- **19 files in `apps/` import from `infra/`** (verified via `grep -rl "from infra\." apps/` → 19 results, e.g. `studio_api/routes/world.py`, `studio_api/routes/health.py`, `studio_api/routes/cvg.py`, `studio_api/app.py`, `studio_api/protocols.py`, plus many more — full list captured in §6 carryover)
- Routes like `apps/studio_api/routes/world.py` directly import `from infra.world_db.schema import get_connection, init_schema` AND `from infra.world_db.queries.characters import list_characters`
- The import chain `apps → infra → sqlite3` would still trigger the forbidden contract even after migrating infra files

To fully expand the contract, apps must go through `lingwen_shared` Protocols (not direct infra imports). This is a service layer / port-binding refactor across the FastAPI app boundary — genuinely 30-50 commits of mechanical refactor.

**Decision**: Defer the full expansion to v16.5 #N. Merge v16.5 #3 partial (T1 only) as the architectural foundation.

### Verified Empirical Counts (post-T1)

| Metric | Value | Notes |
|--------|-------|-------|
| `infra/` files with `import sqlite3` | **22** | Includes `sqlite_storage_adapter.py` (T1 site) + 21 internal callers (target of v16.5 #N.3) |
| `apps/` files importing from `infra.` | **19** | All in `apps/studio_api/` (routes/helpers/protocols/tests); target of v16.5 #N.2 |

## 4. Verification Matrix (post-T1)

| Gate | v16.5 #2 baseline | v16.5 #3 partial | Status |
|------|-------------------|------------------|--------|
| `lint-imports` | 3 contracts KEPT | 3 contracts KEPT | OK |
| `pytest tests/persistence/test_sqlite_storage_adapter.py` | n/a | 13 passed | OK NEW |
| `pytest tests/hygiene/` | 6 passed | 6 passed (no regression) | OK |
| `pytest tests/infra/ apps/studio_api/tests/` | 392 passed, 5 skipped | 392 passed, 5 skipped (no regression) | OK |
| `pytest packages/lingwen-creator/tests/` | 73 passed | 73 passed (no regression) | OK |
| `pytest packages/lingwen-shared/tests/` | 85 passed | 85 passed (no regression) | OK |
| `pytest packages/lingwen-llm/tests/` | 8 passed | 8 passed (no regression) | OK |
| `ruff check` (all 5 surfaces) | 0 | 0 | OK |
| **Backend total** | 564 passed | **577 passed** (+13 NEW) | OK |
| `pnpm vitest run` | 1729 | 1729 (no regression; out of scope) | OK |

**Net new tests**: +13 (SqliteStorageAdapter). **Zero regressions**.

## 5. Lessons Learned

1. **TYPE_CHECKING does NOT help import-linter** — grimp's static analysis treats `if TYPE_CHECKING: import X` identically to `import X`. This is a critical finding for any DP-03 migration: type annotations that need `sqlite3.Connection` either become `ConnectionPort` Protocol (the proper fix) or require grimp evasion (the wrong fix). Future DPs (DP-01, DP-04) should know this upfront.

2. **sqlite3 3.51 + Python 3.13 quirk** — `sqlite3.Connection.close()` without explicit `commit()` rolls back pending DML transactions. This is a behavioral change from earlier versions. `SqliteStorageAdapter.with_connection` is documented as read-only; INSERTs must use `with_transaction`. Tests verify both behaviors.

3. **Scope expansion reality** — Initial "DP-03 full fix" estimate (15-20 commits) was based on a flawed mental model (assumed `apps` already used `lingwen_shared` Protocols). Reality: apps still imports infra directly across 19 files, requiring a service layer refactor before the import-linter contract can expand. v16.5 #3 closed as PARTIAL with the architectural foundation; full expansion deferred to v16.5 #N.

4. **Documentation must surface scope reality early** — The initial v16.5 #2 handoff described the full DP-03 carryover as "refactor infra/* to use StoragePort internally" without acknowledging the apps service layer dependency. v16.5 #3 should have started with an empirical check of `apps → infra` chains to surface the gap upfront.

## 6. Carryover to v16.5 #N (Full DP-03 Expansion)

The full DP-03 expansion is a multi-phase effort. **Recommended decomposition**:

### v16.5 #N.1 — Add factory pattern to lingwen_shared
- Mirror v16.5 #1 LLMServiceAdapter pattern: add `set_default_storage_factory()` + `get_default_storage()` to `lingwen_shared.ports.storage`
- `infra.persistence.sqlite_storage_adapter` registers itself as default factory at module load time
- ~3-5 commits

### v16.5 #N.2 — Migrate apps/* to use lingwen_shared Protocols
- **19 files** (verified post-T1): `apps/studio_api/app.py` + `apps/studio_api/e2e_entry.py` + `apps/studio_api/protocols.py` + 14 routes (`world.py`, `cvg.py`, `health.py`, `creator_core.py`, `creator_onboarding.py`, `creator_settings.py`, `creator_volume.py`, `ctx.py`, `studio.py`, `write_workspace.py`, `workflows.py`) + 2 helpers (`helpers/__init__.py`, `helpers/cvg.py`, `helpers/production_records.py`) + 2 test files (`test_world_route.py`, `test_write_workspace_route.py`)
- Each file: replace `from infra.persistence.X import Y` with `from lingwen_shared.ports.storage import get_default_storage`
- Pattern: `storage.with_transaction(lambda conn: query_func(conn, data))` instead of `with connection_context(...) as conn`
- ~10-15 commits (1 file per commit per DP-06 budget)

### v16.5 #N.3 — Migrate infra/* to drop `import sqlite3`
- **22 files** (verified post-T1, minus the T1 sqlite_storage_adapter.py itself = 21 callers): world_db (`schema.py` + 6 query modules + `_helpers.py`), `event_sourcing/store.py`, `reading_power/db.py`, `cross_volume/storage.py`, `infra/persistence/{connection,schemas,sqlite_config}.py`, `infra/persistence/migrations/__init__.py`, `tools/migrate_to_sqlite.py`, `tools/workflow/lib/{db,checkpoints,migration,state,tasks}.py`
- Each file: change `conn: sqlite3.Connection` annotation to `ConnectionPort` (or use `SqliteConnection` wrapper)
- Migrate call sites to use `SqliteStorageAdapter.with_*` instead of direct `connection_context`
- `infra.persistence.connection` becomes a thin wrapper that delegates to `SqliteStorageAdapter`
- ~15-25 commits

### v16.5 #N.4 — Expand import-linter contract
- `source_modules = ["lingwen_creator", "apps"]` (from `["lingwen_creator"]`)
- Update hygiene grep test to remove the redundant apps check (now covered by import-linter)
- Verify no regression in any existing test
- ~2-3 commits

**Total v16.5 #N estimated**: ~30-50 commits.

## 7. Pre-merge Checklist

- [x] T1 commit on `phase-126-v16-5-dp03-fullfix` branch
- [x] All verification gates green (lint-imports, ruff, hygiene, persistence, infra+studio_api, all 3 packages)
- [x] Handoff doc written (this file)
- [x] CLAUDE.md updated
- [x] `.lingwen/architecture.yml` updated (version 16.5.3 + DP-03 enforcement_phase)
- [ ] `git checkout master && git merge phase-126-v16-5-dp03-fullfix --no-ff` (pending)
- [ ] `git push origin master`

## 8. Commit Timeline

```
e8b51ab9 (T1 — SqliteStorageAdapter concrete impl + 13 tests)
f6f5d97e (v16.5 #2 master baseline)
```
