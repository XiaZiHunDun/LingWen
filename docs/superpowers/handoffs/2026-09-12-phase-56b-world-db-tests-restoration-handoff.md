# Phase 56b Handoff — world_db tests restoration

> **Phase**: 56b (follow-up to Phase 56 P3-ARCHDEBT)
> **Branch**: `phase-57-p3-archdebt-reading-power`
> **Date**: 2026-09-12
> **Author**: Claude (session continuation post Phase 55 ff-merge)
> **Status**: Implementation complete; awaiting ff-merge to master

## Context

Phase 56 P3-ARCHDEBT (v52.0) relocated `infra/world_db/` (1291 LOC, 13 files
incl. queries/ subdir) → `packages/lingwen-world-db/`, FULL DELETED the source
directory, added invariant I076. During that phase, **5 test files in
`tests/infra/world_db/` were left behind** still importing from the deleted
`infra.world_db` namespace — they failed at pytest collect time.

Phase 58 (defect closure, commit `0f3239f4`) deleted those 5 stale files
(491 LOC) but the commit message **explicitly deferred** restoration:

> "The package-local tests/ directory in packages/lingwen-world-db/ does NOT
>  exist (test coverage was lost in Phase 56; restoring package-local tests
>  is a separate follow-up)"

**Phase 56b completes that follow-up.**

## What was done

### C1: Scaffold (`5e5f5dcf`)

Created `packages/lingwen-world-db/tests/`:
- `__init__.py` (empty, marks directory as Python package)
- `conftest.py` (sys.path bootstrap — **later removed in C3**, see Lessons)

### C2: Restore + migrate (`4e22667f`)

Recovered all 5 files from `0f3239f4^` (parent of the Phase 58 deletion commit):

| File | LOC | Purpose |
|------|-----|---------|
| `test_schema.py` | 21 | Schema smoke test (all 7 tables exist) |
| `test_character_queries.py` | 61 | Character CRUD + revision conflict |
| `test_other_queries.py` | 120 | Faction/relationship/lore/timeline/proposal CRUD |
| `test_markdown_roundtrip.py` | 87 | Parse/serialize round-trip + project import |
| `test_agent_extractors.py` | 202 | LLM proposal extraction + JSON parsing |
| **Total** | **491** | |

Single sed migration across all 5 files:
```
sed -i 's|from infra\.world_db|from lingwen_world_db|g' <file>
```

All imports verified against canonical `lingwen_world_db` public API
(`__all__ = ['init_schema', 'get_connection']`; 13 sub-modules importable
directly via `lingwen_world_db.{module}`).

### C3: Regression guards (`1a5e7e9b`)

Added `tests/test_phase56b_p3_archdebt_world_db_tests.py` (5 guards):
- **G1**: `tests/infra/world_db/` MUST NOT EXIST (Phase 58 C4 deletion sticks)
- **G2**: `packages/lingwen-world-db/tests/` MUST EXIST (canonical restored)
- **G3**: All 5 expected test files present
- **G4**: No test file imports from `infra.world_db` (drift guard)
- **G5**: `tests/__init__.py` carries Phase 56b context (sanity check)

Also **deleted** the redundant `conftest.py` from C1 (see Lesson 1 below).

## Validation

| Suite | Result |
|-------|--------|
| 5/5 regression guards (Phase 56b) | PASSED in 0.03s |
| 27/27 package-local tests | PASSED in 1.05s |
| 5 prior Phase 56 guards (test_phase56_*) | PASSED (preserved) |
| cross_volume pre-existing failures | Still 16 (no regression) |

Pre-existing pytest tooling limitation: running `pytest packages/*/tests/`
alongside root `tests/` produces collection namespace collisions
(`ModuleNotFoundError: No module named 'tests.test_X'`). This affects
Phase 35's `lingwen-world-model/tests/` identically and is out of scope
for Phase 56b. Workaround: invoke package tests alone from root.

## File diff summary

```
packages/lingwen-world-db/tests/__init__.py             (new, 16 lines — context doc)
packages/lingwen-world-db/tests/conftest.py             (new in C1, DELETED in C3)
packages/lingwen-world-db/tests/test_schema.py         (new, 21 lines)
packages/lingwen-world-db/tests/test_character_queries.py   (new, 61 lines)
packages/lingwen-world-db/tests/test_other_queries.py   (new, 120 lines)
packages/lingwen-world-db/tests/test_markdown_roundtrip.py (new, 87 lines)
packages/lingwen-world-db/tests/test_agent_extractors.py   (new, 202 lines)
tests/test_phase56b_p3_archdebt_world_db_tests.py       (new, 161 lines — 5 guards)
CLAUDE.md                                              (v54.0 → v54.1)
```

Total: 491 LOC test coverage restored + 181 LOC guard file.

## Lessons

### 1. Package-local `conftest.py` sys.path hack is redundant (NEW)

uv workspace already exposes `lingwen_world_db` as importable from project
root (verified: `import lingwen_world_db` works without any conftest). The
C1 conftest that added `sys.path.insert(0, src_dir)` was:

- **Redundant**: workspace install handles it.
- **Harmful**: triggered a pytest collection namespace collision because
  both root `tests/conftest.py` and `packages/lingwen-world-db/tests/conftest.py`
  register as `tests.conftest`, which pytest treats as the same module.

**Fix**: dropped the conftest, moved the Phase 56b context comment into
`tests/__init__.py` docstring — same pattern as Phase 35's
`lingwen-world-model/tests/__init__.py`.

### 2. pytest multi-path collection conflict is pre-existing tooling limit

Running `pytest packages/lingwen-world-db/tests/ packages/lingwen-world-model/tests/`
(or with root `tests/`) produces `ModuleNotFoundError: No module named
'tests.test_X'` for the second package's collection. Phase 35 has the
identical issue. Workaround: run each package's tests alone, or use
`--rootdir` override. **Out of scope** for Phase 56b — the new tests work
correctly when run alone (27/27 PASSED).

### 3. Phase 58 commit message as follow-up discovery hook

The Phase 58 deletion commit (`0f3239f4`) explicitly stated
"restoring package-local tests is a separate follow-up" — leaving a clear
discovery hook for future sessions. This pattern (commits that name their
own follow-ups) is good engineering hygiene. Phase 56b was identified as
the next-actionable item by `grep`-ing commit messages for "follow-up".

### 4. cwd-dependent test paths inherit worktree assumption

`test_markdown_roundtrip.py` uses `Path("docs/character-bible")` (relative
to cwd). When pytest is invoked from worktree root, this resolves correctly.
When invoked from the package dir, it fails. This is **not** Phase 56b's
bug — it's inherited from the original test design — but worth noting
for future package test work.

## Carryover closure

| Item | Status |
|------|--------|
| Phase 58 follow-up (world_db tests restoration) | **CLOSED** |
| P3-ARCHDEBT 16/15+1 | Preserved (no new invariant needed; no code relocation) |
| I076 (lingwen-world-db canonical) | Unchanged (still authoritative) |

## Next-actionable candidates

After Phase 56b ff-merge:
- (a) Phase 56b2: investigate the cwd-dependent `Path("docs/character-bible")`
  pattern in `test_markdown_roundtrip.py` (Lesson 4) — would make tests
  cwd-independent.
- (b) Investigate the pre-existing 16 cross_volume test failures (worktree
  fixture mismatch — see session analysis 2026-09-12).
- (c) Phase 53c: `tools/legacy/` 19-script cleanup (low-risk, more dead code).
- (d) Resume product features (Write Workspace / World).

**Recommendation**: (b) — the cross_volume 16 failures share a single root
cause (worktree lacks `03_内容仓库/04_正文` content fixtures that master has),
and would benefit from a focused investigation. ~1-2 hour scope.
