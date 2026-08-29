# Phase 126 v16.5 #4 — Remaining Packages Migration (Defense-in-Depth) Handoff

> **Status:** closed, 1 commit on `phase-126-v16-5-4` branch (T1: hygiene gate expansion)
> **Previous:** v16.5 #3 (PARTIAL — SqliteStorageAdapter, `a0014a12`)
> **Next:** v16.5 #N (full DP-03 expansion — move SqliteStorageAdapter to packages/lingwen-storage/, migrate 8 remaining files)

## 0. TL;DR

Defense-in-depth hygiene gate expanded to cover `lingwen_core/`, `lingwen_pipeline/`, `lingwen_cli/`. New `import sqlite3` in these packages will fail the regression gate, but 8 known files (Phase 15.0 T2.8 deprecated) are exempted via whitelist.

The full migration (move `SqliteStorageAdapter` from `infra/persistence/` to `packages/lingwen-storage/` and migrate the 8 files) is in v16.5 #N carryover — it requires the shared relocation to avoid circular imports (lingwen_core/pipeline can't currently depend on infra.persistence).

## 1. Why Defense-in-Depth (not full migration)

The 8 files with direct `sqlite3` imports:
- `packages/lingwen-core/src/lingwen_core/agents/budget_persistence.py`
- `packages/lingwen-core/src/lingwen_core/agents/cost_persistence.py`
- `packages/lingwen-core/src/lingwen_core/agents/social_engine/relationship_tracker.py`
- `packages/lingwen-pipeline/src/lingwen_pipeline/state/state_manager.py`
- `packages/lingwen-pipeline/src/lingwen_pipeline/state/database.py`
- `packages/lingwen-pipeline/src/lingwen_pipeline/state/migrate_from_json.py`
- `packages/lingwen-pipeline/src/lingwen_pipeline/state/backends/sqlite.py`
- `packages/lingwen-cli/src/lingwen_cli/commands/doctor.py`

These carry **Phase 15.0 T2.8 deprecation comments** recommending `infra.persistence.registry.get("X")` singleton. The migration requires:
1. Move `SqliteStorageAdapter` from `infra.persistence` to `packages/lingwen-storage` (or `lingwen_shared`)
2. Then lingwen_core/pipeline can import the relocated adapter (no circular dep)
3. Then migrate each of the 8 files

Step 1 alone is a non-trivial architectural move (involves updating all infra.persistence callers too). v16.5 #N will handle this.

For v16.5 #4, we establish the **regression gate** so no NEW direct `sqlite3` imports sneak into these packages.

## 2. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | (this commit) | `test(hygiene)`: expand grep test to cover lingwen_core/pipeline/cli + add 8-file whitelist |

**Total: 1 commit** (plus 1 docs commit in T2).

## 3. Plan Deviations

- **No import-linter expansion**: The original plan could have added lingwen_core/pipeline/cli to the import-linter forbidden source_modules. But this would fail immediately because the 8 whitelisted files still import sqlite3 directly. Grep test (defense-in-depth) is the pragmatic choice.

## 4. Verification Matrix

| Gate | v16.5 #3 partial | v16.5 #4 | Status |
|------|------------------|----------|--------|
| `pytest tests/hygiene/` | 6 | 7 (+1 new) | ✓ |
| `lint-imports` | 3 contracts KEPT | 3 contracts KEPT | ✓ |
| `ruff check` | 0 | 0 | ✓ |
| `pytest tests/persistence/test_sqlite_storage_adapter.py` | 13 | 13 (no regression) | ✓ |
| `pytest tests/infra/ apps/studio_api/tests/` | 392 + 5 skipped | 392 + 5 skipped (no regression) | ✓ |
| **Total backend** | 577 | **578** (+1) | ✓ |

**Net new tests**: +1 (hygiene gate). **Zero regressions**.

## 5. Files Changed

### Modified
- `tests/hygiene/test_no_concrete_sqlite3_import.py` — added `test_no_sqlite3_imports_in_remaining_packages_with_whitelist` + `REMAINING_PACKAGE_SQLITE3_WHITELIST` constant (8 files)

## 6. Lessons Learned

1. **Pragmatic migration > perfect migration** — When full architectural refactor is large (move SqliteStorageAdapter + migrate 8 files = 10-15 commits), start with a regression gate that prevents the problem from getting worse. The full fix can follow incrementally.

2. **Whitelist-based regression gates need clear removal criteria** — The 8 whitelisted files should ALL be removed in v16.5 #N. Each removal should be a separate commit with a clear migration step (e.g., "migrate budget_persistence.py to use relocated SqliteStorageAdapter").

3. **Existing deprecation comments are not enough** — The Phase 15.0 T2.8 comments have been in place but the deprecation wasn't enforced. Active regression gates (tests that fail CI) are stronger than passive comments.

## 7. Carryover to v16.5 #N (Full Migration of 8 Whitelisted Files)

For each of the 8 files, the migration step:
1. Add `from packages.lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter` (after SqliteStorageAdapter is relocated to lingwen-storage)
2. Replace local `_connect()` context manager with `SqliteStorageAdapter.with_transaction()`
3. Replace `conn: sqlite3.Connection` annotation with `ConnectionPort` Protocol
4. Remove the local `import sqlite3`
5. Remove from the whitelist in `tests/hygiene/test_no_concrete_sqlite3_import.py`

## 8. Commit Timeline

```
TBD (T1 commit)
a0014a12 (v16.5 #3 PARTIAL baseline)
```
