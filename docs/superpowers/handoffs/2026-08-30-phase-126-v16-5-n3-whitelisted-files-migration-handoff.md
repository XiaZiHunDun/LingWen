# Phase 126 v16.5 #N.3 — Whitelisted Files Migration Handoff

> **Status:** closed, 9 commits on `phase-126-v16-5-n3` branch
> **Previous:** v16.5 #N.1 (factory pattern, `8bce4c97`) + v16.5 #N.0 (SqliteStorageAdapter relocated to `packages/lingwen-storage/`, `8bce4c97` chain)
> **Next:** v16.5 #N.4 — migrate 21 remaining `infra/*` files to drop `import sqlite3`

## 0. TL;DR

Migrated all 8 whitelisted infra/* files (Phase 15.0 T2.8 deprecated) to use `SqliteStorageAdapter` from `lingwen_storage`. Each file dropped its `import sqlite3` statement. The 8-file whitelist in the hygiene test was removed (gate simplified to a pure grep test). `lingwen-cli` already had `lingwen-storage` as a workspace dep (T0 was a no-op).

## 1. Files Migrated

| File | Class/Function | Commit |
|------|----------------|--------|
| `packages/lingwen-core/src/lingwen_core/agents/budget_persistence.py` | `BudgetService` | `6891665c` (T1) |
| `packages/lingwen-core/src/lingwen_core/agents/cost_persistence.py` | `CostTrackerDB` | `736d23ee` (T2) |
| `packages/lingwen-core/src/lingwen_core/agents/social_engine/relationship_tracker.py` | `RelationshipTracker` | `668ebd84` (T3) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state/state_manager.py` | `StateManager` | `4f1c6ecf` (T4) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state/database.py` | `WorkflowDB` | `59d27dc4` (T5) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state/migrate_from_json.py` | `migrate_from_json` | `db9d4d6f` (T6) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state/backends/sqlite.py` | `SQLiteBackend` | `0a7774fb` (T7) |
| `packages/lingwen-cli/src/lingwen_cli/commands/doctor.py` | `DoctorCommand` | `245d58a3` (T8) |

Plus:
- T9 `tests/hygiene/test_no_concrete_sqlite3_import.py` (`2ea30f81`) — removed 8-file whitelist, gate now pure grep.
- T8.fixup `chore(ruff)` (`21819b09`) — ruff --fix for 9 W292 violations across 8 files.

T0 (`packages/lingwen-cli/pyproject.toml` — add `lingwen-storage` dep) was a no-op: the dep was already declared (alphabetical order, between `lingwen-quality` and the closing `]`).

## 2. Migration Pattern

For each file (the simple case — `budget_persistence.py`, `cost_persistence.py`, `backends/sqlite.py`):

1. Add `from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter`.
2. Remove `import sqlite3` (and `from contextlib import contextmanager` if no longer needed).
3. Construct `self._storage = SqliteStorageAdapter(str(self.db_path))` in `__init__`.
4. Replace each `with self._connect() as conn: <stmts>` with one of:
   - `self._storage.with_transaction(lambda conn: <stmts>)` — write path (commit/rollback auto-managed).
   - `self._storage.with_connection(lambda conn: <stmts>)` — read-only path.
5. Keep public API unchanged.

For `state_manager.py` / `database.py` (fcntl-protected transaction):

1. Replace `with self._connect() as conn: ...` with `with self._storage._transaction_cm() as conn:` (uses the adapter's internal context manager to keep public contextmanager semantics).
2. Wrap `_transaction()` / `transaction()` body with `fcntl.flock` around `_storage._transaction_cm()` — flock retained for R3-001 cross-process serialization.
3. The adapter handles BEGIN/COMMIT/ROLLBACK; flock handles inter-process write mutex.

For `relationship_tracker.py` (dual sqlite+json backend):

1. Only construct `self._storage` when backend is sqlite.
2. Use `_storage._transaction_cm()` for `_init_sqlite_schema` (PRAGMA + executescript).
3. Manual `BEGIN/COMMIT/ROLLBACK` in `_save_network_sqlite` is dropped; `with_transaction` callback handles the atomic boundary.
4. `_load_network_sqlite` uses `with_connection` callback.

For `migrate_from_json.py` (one-shot function):

- The whole migration body is a single `with_transaction` callback that returns counts via the callback return value.

For `doctor.py` (diagnostic):

- Replace `import sqlite3` + `sqlite3.connect()` + cursor with `SqliteStorageAdapter(db_path)` + `with_connection(lambda conn: conn.execute(...).fetchall())`.

## 3. Verification Matrix

| Gate | v16.5 #N.1 | v16.5 #N.3 | Status |
|------|-----------|-----------|--------|
| `import sqlite3` count in 8 whitelisted files | 8 | 0 | ✓ |
| `tests/agent_system/test_budget_persistence.py` | 22 | 22 | ✓ |
| `tests/agent_system/test_cost_persistence.py` | 18/19 (1 pre-existing infra→lingwen_core path) | 18/19 (same) | ✓ |
| `tests/agent_system/test_relationship_tracker.py` | 7 | 7 | ✓ |
| `tests/state/test_sqlite_state.py` | 14 | 14 | ✓ |
| `tests/state/test_workflow_db.py` | 7 (incl. fcntl concurrency) | 7 | ✓ |
| `tests/hygiene/test_no_concrete_sqlite3_import.py` | 5 (incl. 8-file whitelist) | 5 (no whitelist, pure grep) | ✓ |
| `tests/persistence/test_registry.py` | passes | passes | ✓ |
| `lint-imports` | 3 KEPT | 3 KEPT | ✓ |
| `ruff check <8 files>` | 0 | 0 | ✓ |
| `vitest` | 1729 (untouched) | 1729 (untouched) | ✓ |
| `vue-tsc` | 0 | 0 | ✓ |

The `tests/agent_system/test_phase7_1_production_fixes.py` failures and `test_e2e_workflow.py` collection errors are pre-existing worktree env-sync issues (master_controller loaded from `/home/ailearn/projects/LingWen/packages/lingwen-core/...` not the worktree path; `skill_registry.yaml not found`). Documented in v16.4 §3 lesson 3 — unrelated to this migration.

## 4. Carryover to v16.5 #N.4

**22 remaining files** under `infra/` still import `sqlite3` directly:
- `infra/world_db/` (8 files)
- `infra/cross_volume/storage.py`
- `infra/reading_power/db.py`
- `infra/event_sourcing/store.py`
- `infra/persistence/{sqlite_config,schemas,migrations/__init__}.py`
- `infra/tools/workflow/lib/*` (5 files)
- `infra/tools/migrate_to_sqlite.py`
- (and several others)

Each migration follows the same pattern as v16.5 #N.3:
1. Construct `SqliteStorageAdapter(db_path)` instead of `sqlite3.connect(db_path)`.
2. Use `.with_transaction(lambda conn: ...)` / `.with_connection(lambda conn: ...)` instead of contextmanagers.
3. Remove `import sqlite3`.
4. Keep public API unchanged.

Estimated: ~22 commits (1 per file).

Special-case files that need extra care:
- `infra/persistence/sqlite_config.py` — provides `apply_sqlite_pragmas(conn: sqlite3.Connection)`. The new contract should accept `ConnectionPort` (or its SqliteConnection wrapper). Several T5 callers (WorkflowDB._init_db) still call this with the adapter's wrapper, which works because `wrapper.execute()` delegates to sqlite3.Connection.execute.
- `infra/world_db/*` — uses `apply_sqlite_pragmas` pervasively. Same concern.

## 5. Lessons Learned

1. **Atomic commits per file** — Each migration is independent. 1 commit per file keeps history clean and rollback easy. v16.5 #N.3 = 9 commits (8 migrations + 1 hygiene test).

2. **Public API stability** — None of the 8 files changed their public API. Only internal implementation changed. Callers (`infra.persistence.bootstrap`, `tests/agent_system/test_*`, `apps/studio_api/tests/test_*`) work without modification.

3. **Phase 15.0 T2.8 deprecation comments are now obsolete** — The carryover said "use infra.persistence.registry.get('X')" but the better path was to migrate to SqliteStorageAdapter. The registry pattern is for SERVICE singletons; SqliteStorageAdapter is for STORAGE abstraction. Different concerns. Deprecation comments retained for now (full removal is follow-up).

4. **`lingwen_storage` as leaf package enabled this migration** — Without the v16.5 #N.0 relocation, migrating these files would create `lingwen_core → infra.persistence` cycles. The relocation was the architectural prerequisite.

5. **fcntl.flock vs SQLiteStorageAdapter transaction** — Both serve different purposes: flock handles inter-process write mutex (R3-001), SQLiteStorageAdapter handles in-process BEGIN/COMMIT/ROLLBACK. They compose: flock wraps the adapter's `_transaction_cm` for cross-process atomicity.

6. **Private API access (`_transaction_cm`, `_connection_cm`) is acceptable for the canonical consumer** — These context managers are explicitly intended as the callback-flavored API's "raw" form. Used by StateManager/WorkflowDB to preserve public contextmanager API.

7. **`sqlite3.Row` row factory is set transparently by SqliteStorageAdapter._open()** — Callers don't need to set `conn.row_factory = sqlite3.Row` themselves. Just access `row["column_name"]` and `dict(row)` work as expected.

## 6. Commit Timeline

```
T1 (6891665c) refactor(lingwen-core): v16.5 #N.3 — migrate BudgetService to SqliteStorageAdapter
T2 (736d23ee) refactor(lingwen-core): v16.5 #N.3 — migrate CostTrackerDB to SqliteStorageAdapter
T3 (668ebd84) refactor(lingwen-core): v16.5 #N.3 — migrate RelationshipTracker to SqliteStorageAdapter
T4 (4f1c6ecf) refactor(lingwen-pipeline): v16.5 #N.3 — migrate StateManager to SqliteStorageAdapter
T5 (59d27dc4) refactor(lingwen-pipeline): v16.5 #N.3 — migrate WorkflowDB to SqliteStorageAdapter
T6 (db9d4d6f) refactor(lingwen-pipeline): v16.5 #N.3 — migrate migrate_from_json to SqliteStorageAdapter
T7 (0a7774fb) refactor(lingwen-pipeline): v16.5 #N.3 — migrate SQLiteBackend to SqliteStorageAdapter
T8 (245d58a3) refactor(lingwen-cli): v16.5 #N.3 — migrate doctor.py diagnostic to SqliteStorageAdapter
T9 (2ea30f81) test(hygiene): v16.5 #N.3 — remove 8-file whitelist (migration complete)
T8.fixup (21819b09) chore(ruff): v16.5 #N.3 — ruff --fix for 9 W292 (no newline at end of file)

Base: 8bce4c97 (v16.5 #N.1)
```