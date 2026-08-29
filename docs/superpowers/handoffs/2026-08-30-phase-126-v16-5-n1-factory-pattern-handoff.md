# Phase 126 v16.5 #N.1 — StoragePort Factory Pattern Handoff

> **Status:** closed, 4 commits on `phase-126-v16-5-n1` branch
> **Previous:** v16.5 #N.0 (SqliteStorageAdapter relocated to packages/lingwen-storage/, `8a05b805`)
> **Next:** v16.5 #N.2 — migrate 19 apps/* files to use `get_default_storage()` from lingwen_shared

## 0. TL;DR

Factory pattern added to `lingwen_shared.ports.storage`, mirroring v16.5 #1 LLMServiceAdapter:
- `_DEFAULT_STORAGE_FACTORY` module variable
- `set_default_storage_factory(factory)` — register default factory
- `get_default_storage_factory()` — introspect
- `get_default_storage()` — convenience constructor for consumers

`lingwen_storage.sqlite_storage_adapter` registers itself as default factory at module load. Apps can now use `get_default_storage()` from `lingwen_shared` (no direct sqlite3 import, no direct `lingwen_storage` import needed).

## 1. Why Factory Pattern

Without a factory, consumers must construct `SqliteStorageAdapter(db_path=...)` explicitly. But:
- Construction requires DB path (config concern)
- Apps don't want to import the concrete (DP-03 architectural invariant)
- Each consumer would need its own wiring logic

Factory pattern: SOMETHING (the canonical module) registers a default factory at module load. CONSUMERS (apps) call `get_default_storage()` with no args and get a working StoragePort.

## 2. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | `05c58b9b` | `feat(lingwen-shared)`: factory functions in `lingwen_shared/ports/storage.py` |
| T2 | `bd95ca6c` | `feat(lingwen-storage)`: register `SqliteStorageAdapter` as default factory at module load |
| T3 | `02906d32` | `test(lingwen-storage)`: 4 factory pattern tests |
| T4 | (TBD) | `docs(phase-126)`: handoff + CLAUDE.md + architecture.yml |

## 3. Architecture

```
apps/* ─────────────────┐
                        │ uses get_default_storage()
                        ▼
lingwen_shared.ports.storage (Protocol + factory functions, NO sqlite3)
                        ▲
                        │ registers factory at module load
                        │
lingwen_storage.sqlite_storage_adapter (canonical, ONLY sqlite3 importer)
                        ▲
                        │ re-export shim (no sqlite3)
                        │
infra.persistence.sqlite_storage_adapter (back-compat shim)
```

## 4. Verification Matrix

| Gate | v16.5 #N.0 | v16.5 #N.1 | Status |
|------|-----------|-----------|--------|
| `pytest packages/lingwen-storage/tests/` | 31 | 35 (+4 factory tests) | ✓ |
| `pytest tests/hygiene/ tooling/hygiene/tests/` | 39 | 39 (no regression) | ✓ |
| `lint-imports` | 3 KEPT | 3 KEPT | ✓ |
| `ruff check` | 0 | 0 | ✓ |
| `lingwen_shared` sqlite3 imports | 0 | 0 | ✓ |
| `lingwen_storage` sqlite3 imports | 1 | 1 | ✓ |

## 5. Files Changed

### Modified
- `packages/lingwen-shared/src/lingwen_shared/ports/storage.py` — added `_DEFAULT_STORAGE_FACTORY`, `set_default_storage_factory`, `get_default_storage_factory`, `get_default_storage`
- `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` — append factory registration at module load
- `packages/lingwen-storage/tests/test_sqlite_storage_adapter.py` — added 4 factory tests + fixture
- `CLAUDE.md` — version + new 更新 (2026-08-30) #N.1 section
- `.lingwen/architecture.yml` — version + DP-03 enforcement_phase

### Created
- `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n1-factory-pattern-handoff.md` (this file)

## 6. Lessons Learned

1. **Factory pattern scales** — Same pattern works for LLM (v16.5 #1) and Storage (v16.5 #N.1). Future ports (Network, Auth) can follow the same template.

2. **Module-load side effects are powerful** — `set_default_storage_factory(...)` at module load means anyone importing the canonical module triggers registration. No explicit bootstrap step needed.

3. **`restore_default_factory` fixture pattern** — Tests that modify module-level state need cleanup. The fixture pattern (save → test → restore) prevents test pollution.

4. **Default `:memory:` DB for factory** — Production code should register its own factory with the right `db_path`. The default `:memory:` factory is for tests + minimal bootstrap.

5. **Documented deviation: 4 tests, not 3** — Spec said 3 factory tests; added a 4th (`test_default_factory_returns_sqlite_storage_adapter`) that verifies the end-to-end chain (default factory → SqliteStorageAdapter). Cheap regression guard against future factory override accidents.

## 7. Carryover to v16.5 #N.2+ (Now Unblocked)

- **#N.2**: Migrate 19 `apps/*` files to use `get_default_storage()` from `lingwen_shared`
- **#N.3**: Migrate 8 whitelisted `infra/*` files (Phase 15.0 T2.8 deprecated) to drop `import sqlite3`
- **#N.4**: Migrate 21 remaining `infra/*` files to drop `import sqlite3`
- **#N.5**: Expand import-linter contract `source_modules = ["lingwen_creator", "apps"]`
- **#N.6**: Migrate 12 whitelisted `tools/*` files to use `LLMServiceAdapter()` from `lingwen_llm.port_adapter`

## 8. Commit Timeline

```
TBD (T4 docs)
02906d32 (T3 factory tests)
bd95ca6c (T2 register factory)
05c58b9b (T1 factory functions)
8a05b805 (v16.5 #N.0 baseline)
```
