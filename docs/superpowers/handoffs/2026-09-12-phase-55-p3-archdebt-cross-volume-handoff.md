# Phase 55 P3-ARCHDEBT cross_volume — Handoff

> **Date**: 2026-09-12
> **Branch**: phase-57-p3-archdebt-reading-power (continuing from Phase 53b)
> **Version**: v53.2 → v54.0
> **Invariant**: I078 NEW (lingwen-cross-volume canonical; infra.cross_volume.* forbidden)

## TL;DR

Phase 55 closes the largest single P3-ARCHDEBT block (4493 LOC, 23 files,
92 consumer files, 255 import sites). Originally skipped as "too large
for single session" — 0-manual-merge daemon (Phase 53b) made the larger
scope feasible. Single comprehensive package (not 2-package split
which was blocked by circular deps).

8 atomic commits (C0-C5 + 2 fixups); all 27 regression guards pass;
net +1 production bug fixed + 5 path literals corrected.

## Validation

| Gate | Result |
|------|--------|
| `uv sync --all-packages` | exit 0 |
| `from lingwen_cross_volume import (9 canonical symbols)` | exit 0 |
| `len(lingwen_cross_volume.__all__) == 9` | ✅ matches original |
| All 17 submodules + 2 subpackages importable | ✅ |
| `grep -rln "from infra\.cross_volume\|import infra\.cross_volume" .` | **0 hits** repo-wide |
| `grep -rln "infra/cross_volume" --include="*.py" .` | 0 path-literal hits (excl. guard itself) |
| `pytest apps/studio_api/tests/` | 82 passed (unchanged from Phase 53b) |
| `pytest tests/cross_volume/` | 286 passed / 16 pre-existing failures (unchanged from master baseline) |
| `pytest tests/test_phase55_p3_archdebt_cross_volume.py` | **27/27 passed** |
| `infra/cross_volume/` | **DELETED** |

## Root cause & approach

**Why single package not 2 packages**: `e2e_seed.py`, `chained_cascade.py`,
and `backfill.py` all use BOTH engine (graph/ripple) AND storage modules.
A 2-package split (lingwen-cross-volume + lingwen-ripple-storage) would
create circular dependencies. The single comprehensive package
preserves the existing module structure with clear internal layering.

## Commits (8 atomic)

| # | SHA | Subject | Files | +/- |
|---|-----|---------|-------|-----|
| C0 | (spec) | `docs(phase-55): spec + plan` | 1 | +200 |
| C1+C1.5 | `9d6a680d` | `feat(packages): scaffold lingwen-cross-volume` | 32 | +4655 |
| C2 | `8669b503` | `refactor(consumers): migrate infra.cross_volume → lingwen_cross_volume` | 99 | +443/-294 |
| (noise) | `3f067070` | `chore(noise): untrack 3 dev artifacts` | 3 | +0/-21 |
| C3 | `de105344` | `chore(infra): FULL DELETE infra/cross_volume/ + I078` | 31 | +1/-4604 |
| C4 | `2d6c3b5b` | `docs(arch): bump v53.2 → v54.0 + I078 invariant` | 2 | +3/-3 |
| C5 | `4df0f898` | `test(phase-55): 27 regression guards + 5 path-literal fixups` | 7 | +296/-7 |

**Net**: -260 LOC (4493 deleted - 4655 added + 296 guards - noise cleanups),
4493 LOC out of `infra/`, 23 files out, 1 invariant in, 27 guards in.

## Module structure (preserved)

```
packages/lingwen-cross-volume/src/lingwen_cross_volume/
├── __init__.py                  (9 canonical __all__ symbols)
├── cache.py                     QueryImpactCache
├── reference_graph.py           CrossVolumeReferenceGraph + ReferenceNode + ReferenceEdge
├── ripple.py                    CrossVolumeRipple
├── scoring.py                   compute_impact_score
├── edge_inferrer.py             EdgeInferrer
├── llm_cache.py                 LLMCache
├── llm_scanner.py               LLMScanner + LLMRetryExhausted
├── scanner_calibration.py       load_scanner_calibration
├── storage.py                   RippleStorage + AuditEntry + ConflictError
├── backfill.py                  Backfiller
├── incremental_backfill.py      backfill_stats_to_dict + 5 helpers
├── cascade_migration.py         migrate_v1_cascade_runs + CascadeMigrationStats
├── cascade_retention.py         PurgeResult + parse_older_than
├── chained_cascade.py           (uses reference_graph + ripple)
├── audit_retention.py           purge_audit_entries_older_than
├── e2e_seed.py                  ensure_e2e_fixtures + 14 helpers
├── perf.py                      perf helpers
├── extraction_rules.yaml        (data, package-relative)
├── scanner_calibration.yaml     (data, package-relative)
├── llm_prompts/                 (subpackage, 5 LLM prompt .txt templates)
└── extractors/                  (subpackage, 4 extractor modules)
```

## Workspace deps (3)

- `lingwen-shared` — ConnectionPort protocol
- `lingwen-llm` — LLMServiceAdapter + ModelTier
- `lingwen-core` — decision_queue (for e2e_seed)

## Path literal fixups (caught by guards)

The first run of the path-literal guard caught **5 stray references**
that the import-migration sed had missed:

| File | Type | Fix |
|------|------|-----|
| `lingwen-cli/.../backfill.py:18` | `DEFAULT_RULES_PATH` default | cwd-relative → package-relative via `importlib.util.find_spec` |
| `lingwen-cli/.../parsers/backfill.py:13` | docstring example | path string → "lingwen_cross_volume package" |
| `lingwen-cli/.../parsers/backfill.py:49` | `--rules` help text | updated |
| `lingwen-cli/.../parsers/ripple_scan.py:39` | `--calibration` help text | updated |
| `lingwen-cross-volume/.../scanner_calibration.py:277` | user-facing error | path → new package location |
| `tooling/hygiene/check_file_size.py:44` | dead ALLOWLIST entry | removed (file no longer exists) |

## Lessons

1. **N.14 lesson 1: STRING LITERAL references (N.14 Pattern 7)** are
   not caught by `sed 's|from infra\.X|from canonical|g'`. A complete
   migration needs **two passes**:
   - Pass 1: `from|import` patterns (the obvious)
   - Pass 2: `"infra\.X"` / `'infra\.X'` / `` `infra\.X` `` in strings

   Phase 55 missed 9 files in pass 1 that pass 2 caught. Without the
   second pass, tests would have failed at runtime with monkeypatch
   setattr pointing at non-existent module attributes.

2. **Repo-wide grep guards catch the unknown unknowns.** Phase 55's
   repo-wide grep found 5 more `infra/cross_volume` path literals
   in production code (CLI help text, default paths, allowlists)
   that no per-file list would have predicted. The pattern of
   "scan everything with a single guard" remains the most reliable
   check for cross-cutting migrations.

3. **N.14 lesson 6: `__pycache__` lingers after `git rm -r`.** Same
   as Phase 58 — the C3 commit's `git rm -r infra/cross_volume/`
   removed tracked files but the untracked `__pycache__/` and
   `extractors/__pycache__/` remained. A follow-up `rm -rf` was
   needed. Future phase cleanups should pair `git rm -r` with
   `rm -rf <dir>`.

4. **`git add -A` picks up noise.** Both C2 and C5 this phase had
   noise commits to clean up `.state/decisions.json` and
   `relationship_network.db`. Lesson: explicitly enumerate files
   in `git add` or use `git add -u` for tracked-only changes.

5. **2-package split rejected due to circular deps.** The
   original Phase 55 spec proposed
   `lingwen-cross-volume` + `lingwen-ripple-storage`, but
   `e2e_seed.py` / `chained_cascade.py` / `backfill.py` use BOTH
   engine and storage modules. A future 2-package split would
   need to first decouple these modules (e.g., move e2e_seed
   to a third `lingwen-test-fixtures` package).

## Out of scope

- `tests/cross_volume/` 16 pre-existing failures (verified unrelated)
- `collaboration/*.md` (user-curated project-management meta)
- `docs/LINGWEN_ARCHITECTURE_SPEC.md` (deferred for major review)
- BACKLOG.md update (deferred)

## FF-merge

The auto-merge daemon will sync master to `phase-57-p3-archdebt-reading-power`
within 30s of the next push. No user action needed.

```bash
# (No user action needed — daemon handles it)
# Or manually:
cd /home/ailearn/projects/LingWen && \
  git checkout master && \
  git merge --ff-only phase-57-p3-archdebt-reading-power && \
  git push origin master
```
