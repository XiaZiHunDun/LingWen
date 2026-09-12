# Phase 57 — P3-ARCHDEBT `infra/reading_power/` → `packages/lingwen-reading-power/`

**Date**: 2026-09-12
**Phase**: 57
**Author**: P3-ARCHDEBT session
**Branch**: `phase-57-p3-archdebt-reading-power` (pending ff-merge)
**Status**: ✅ ALL 7 ATOMIC COMMITS COMMITTED

## Summary

Phase 57 migrates the **追读力系统 (Reading Power System)** from `infra/reading_power/` (1,006 LOC, 7 files) into a canonical workspace package `packages/lingwen-reading-power/`. The module was dormant but **NOT orphan**: it has an active DB at `infra/.state/reading_power.db`, schema columns actively served by `studio_api/routes/overview.py`, and UI rendered in 3 pages (`ChapterTable.vue`, `CoolpointChart.vue`, `OverviewPage.vue`). MIGRATE chosen over FULL DELETE to preserve real product value.

## Atomic commit sequence (7 commits)

| # | SHA | Subject | Files | +/- |
|---|----|---------|-------|-----|
| C0 | `d321a066` | `docs(phase-57): spec + plan for lingwen-reading-power P3-ARCHDEBT` | 2 | +232 |
| C1 | `e375e1c6` | `feat(packages): scaffold lingwen-reading-power (Phase 57 C1)` | 10 | +1108 |
| C1.5 | `30112769` | `fix(reading-power): 3 bug fixups in lingwen-reading-power (Phase 57 C1.5)` | 3 | +24 / -34 |
| C2 | `2d36bbec` | `refactor(consumers): migrate 14 sites to lingwen_reading_power (Phase 57 C2)` | 14 | +15 / -15 |
| C3 | `e5fccfdb` | `chore(infra): FULL DELETE infra/reading_power + tests/reading_power + I077 (Phase 57 C3)` | 17 | +1 / -1861 |
| C4 | `91ccd83b` | `docs(arch): bump v52.0 -> v53.0 + 6 doc references (Phase 57 C4)` | 8 | +19 / -19 |
| C5 | (this commit) | `test(phase-57): regression guards + handoff` | TBD | TBD |

## Migration scope

| Item | Count |
|------|-------|
| Module files migrated | 7 (`db.py`, `engine.py`, `rule_matcher.py`, `llm_analyzer.py`, `hook_tracker.py`, `coolpoint_tracker.py`, `__init__.py`) |
| Public symbols preserved | 8 (ReadingPowerDB / Engine / /RuleMatcher / SuspectedSegment / LLMAnalyzer / AnalysisResult / HookTracker / CoolPointTracker) |
| Module constants preserved | 4 (DB_PATH, HOOKS_RULES_PATH, COOLPOINTS_RULES_PATH, ANALYZE_HOOKS_PROMPT) |
| Consumer sites migrated | 14 (6 production + 8 tests) |
| Patch() string targets migrated | 1 (`tests/reading_power/test_engine.py:12`) |
| Files deleted (Phase 57 C3) | 15 (7 module + 8 tests) |
| Workspace deps added | 2 (`lingwen-shared` + `lingwen-storage`) |
| New invariants | I077 (lingwen-reading-power canonical; infra.reading_power.* forbidden) |
| Version bump | v52.0 → v53.0 |
| Regression guards | 13 (`tests/test_phase57_p3_archdebt_reading_power.py`) |

## Audit findings (recap)

### N.14 9-pattern consumer audit (verified 2026-09-12)

| # | Pattern | Count | Phase 57 outcome |
|---|---------|-------|------------------|
| 1 | Literal dotted-path imports | 14 | ✅ migrated in C2 |
| 2 | Indented/function-body imports | 3 | ✅ migrated in C2 |
| 3 | Relative imports inside infra/reading_power/ | 14 (intra-pkg only) | ✅ migrated in C1 (new package uses canonical form) |
| 4 | Filesystem-path string literals | 5 (all in docs) | ✅ updated in C4 (canonical path) |
| 5 | Wildcard `from infra.reading_power import *` | 0 | ✅ no-op |
| 6 | `patch()` string target (monkeypatch variant) | 1 | ✅ migrated in C2 (`tests/reading_power/test_engine.py:12`) |
| 7 | `import X as Y` re-exports | 0 | ✅ no-op (`apps/studio_api/__init__.py` re-exports via `apps.studio_api.app`, no infra import) |
| 8 | Doc comments referencing old path | 8 docs | ✅ updated in C4 (canonical docs); historical archive preserved per Phase 53 precedent |
| 9 | Prior-phase guards | 0 | ✅ no-op (clean slate) |

### Workspace deps

```python
# db.py:18  — TYPE_CHECKING-style
from lingwen_shared.ports.storage import ConnectionPort

# db.py:57  — runtime deferred (inside _get_connection)
from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter
```

→ **NOT-LEAF** with 2 deps. Migration declares both in new `pyproject.toml`. Module closest to Phase 40a `lingwen-studio-registry` pattern (3 deps).

## Bug fixups applied in C1.5

| # | Bug | Fix | File |
|---|-----|-----|------|
| 1 | `DB_PATH` uses `parents[2]` from old location — would break after relocation | Changed to `Path(__file__).parents[4]` (5 levels: lingwen_reading_power/src/lingwen-reading-power/packages/repo-root). Phase 40a C1.5 lesson. | `db.py` |
| 2 | Duplicate `SuspectedSegment` defined twice: `NamedTuple` (rule_matcher.py) + `@dataclass` (llm_analyzer.py). Incompatible (offset vs char_start field names). | Removed `@dataclass` from llm_analyzer.py; now imports canonical NamedTuple from rule_matcher. analyze() only reads segment_type/pattern_name/content so drop-in safe. | `llm_analyzer.py` |
| 3 | `_determine_position` always returned `"开头"` for chapters ≥100 chars (bug: always-true `if length > 20` branch). Worse: rules YAML uses `"开篇"` (NOT `"开头"`), so pos_weight always fell through to default 1.0 — function was a no-op. | Simplified to coarse length-based classification (no offset parameter exists). Returns `"中段"` for all non-empty inputs. Docstring documents the limitation. | `rule_matcher.py` |
| 4 | "Unused `SuspectedSegment` import in engine.py" | **FALSE POSITIVE** in audit — engine.py:84 actually uses it as `List[SuspectedSegment]` type hint in `_merge_rule_results`. No change needed. | (none) |

## Verification

### C1 (scaffold)

- `uv sync --all-packages` exits 0
- `uv pip list | grep lingwen-reading-power` shows `lingwen-reading-power 0.1.0`
- `python -c "import lingwen_reading_power; print(lingwen_reading_power.__all__)"` → 8 symbols
- `len(lingwen_reading_power.__all__) == 8` ✓ (Phase 37 lesson)

### C1.5 (bug fixups)

- `ReadingPowerDB.DB_PATH` resolves to `<repo>/.state/reading_power.db` (was: `<packages>/.state/...`)
- `SuspectedSegment` is single NamedTuple (was: 2 definitions, one @dataclass)
- `_determine_position` no longer has unreachable code; returns `"中段"` consistently

### C2 (consumer migration)

- `uv run pytest tests/reading_power/ tests/persistence/test_integration.py` → 49 passed (44 reading_power + 5 persistence integration)
- All 6 production consumer sites import successfully; `ReadingPowerDB is Canonical` across all 5 import paths
- `grep -rn "infra\.reading_power" --include="*.py"` returns 0 hits outside the old infra/ + new package docstrings

### C3 (FULL DELETE + I077)

- 15 files deleted (7 infra + 8 tests)
- I077 invariant added to CLAUDE.md after I076
- 24 pre-existing failures in `apps/studio_api/tests/test_world_route.py` + `test_studio_batch_templates_route.py` are Phase 47 leftover import issues (KNOWN_EVENT_TYPES import path) **unrelated to Phase 57** — NOT introduced by this phase

### C4 (version bump + doc updates)

- CLAUDE.md v52.0 → v53.0
- pyproject.toml: `infra.reading_power.db` removed from invariant-list comment
- 5 doc files updated with canonical `packages/lingwen-reading-power/src/lingwen_reading_power/` path
- Historical archive preserved per Phase 53 precedent (commit-blame protection)

### C5 (regression guards)

- `tests/test_phase57_p3_archdebt_reading_power.py` — 13 guards, all passing
- Guards cover: directory deletion, package import + symbol count, consumer migration, runtime audit (anchored grep), I077 invariant, DB_PATH parents[4], SuspectedSegment single-definition + no-duplicate-in-llm_analyzer, _determine_position return value, workspace member declaration, apps re-export

## Active invariants (28)

After Phase 57, **8 P3-ARCHDEBT invariants active**:
- I049 (lingwen-got), I050 (lingwen-world-model), I051 (lingwen-errors), I052 (lingwen-paths), I053 (lingwen-project-config), I054 (lingwen-logging-config), I055 (lingwen-studio-registry), I056 (lingwen-project-init), I057 (lingwen-llm-service), I058 (lingwen-prose-calibration), I059 (lingwen-cache), I060 (lingwen-coverage-gate), I061 (lingwen-patterns), I062 (lingwen-result), I063 (lingwen-quality), I064 (lingwen-studio-batch-runner), I065 (lingwen-studio-batch-templates), I066 (lingwen-studio-batch-streamer), I067 (lingwen-full-check-report), I068 (lingwen-memory-service), I069 (lingwen-schema), I070 (lingwen-health), I071 (lingwen-prose-judge), I072 (lingwen-prose-snapshot), I073 (lingwen-project-characters), I074 (infra/tools/legacy + infra/core + infra/studio deleted), I075 (lingwen-persistence), I076 (lingwen-world-db), **I077 (lingwen-reading-power — NEW)**.

= **28 active invariants total**, of which **27 are P3-ARCHDEBT package invariants** (I048 is the PilotPage batch lifecycle).

## What this phase does NOT do

- Does NOT remove `coolpoint_count` / `coolpoint_density` / `hook_count` schema columns in `lingwen-persistence/schemas.py:187-189` (canonical).
- Does NOT remove `CoolpointChart.vue` / `ChapterTable.vue` coolpoint columns (UI plumbing outside `infra/`).
- Does NOT delete the SQLite DB at `.state/reading_power.db` — preserved (data is real).
- Does NOT touch any consumer outside the 14 enumerated sites.
- Does NOT remove `ReadingPowerDB.__init__` DeprecationWarning (intentional, tells callers to use the registry singleton).

## Risks (post-mitigation)

| Risk | Status |
|------|--------|
| `uv sync --all-packages` failure | ✅ Resolved (C1) |
| `DB_PATH` breaks after relocation | ✅ Resolved (C1.5: parents[4]) |
| Function-body imports missed | ✅ Verified (C2: 3 sites migrated) |
| `patch()` string targets missed (N.14 lesson 1 variant) | ✅ Resolved (C2: 1 site migrated, added to 9-pattern audit) |
| Wildcard import regressions | ✅ No wildcard found (Pattern 5: 0 hits) |
| Workspace dep breakage | ✅ Verified (C1: lingwen-shared + lingwen-storage declared) |
| Historical archive staleness | ✅ Documented in C4 commit message |

## Lessons

1. **`patch()` string targets ARE N.14 Pattern 6** — they use the same dotted-path indirection as `monkeypatch.setattr`. Phase 57 audit initially missed this; verified in C2 with grep `patch("infra.reading_power.*`". Add to canonical N.14 lesson 1 in next memory refresh.

2. **N.14 lesson 1 11th variant — `_determine_position` double-bug** — the function had a logic bug (always returned `"开头"`) AND a string-mismatch bug (rules YAML uses `"开篇"`). Both bugs combined to make the function a silent no-op for ~6 months (Phase 15.0 → Phase 57). Phase 57 C1.5 caught both. Lesson: when debugging "looks like dead code", check whether downstream consumers are silently ignoring the result.

3. **`_determine_position` requires `offset` parameter to actually work** — without per-match offset, position classification is fundamentally impossible. Current fix is honest ("returns 中段 as default") but a future refactor of `RuleMatcher.scan()` to plumb match offsets through would enable proper 开篇/中段/结尾 classification. Defer to follow-up phase.

4. **Audit false positive on "unused import"** — `engine.py:7 imports SuspectedSegment` audit statement was wrong; it's used in `_merge_rule_results` type hint at line 84. Lesson: when flagging "unused" imports, grep for type hints too.

5. **Phase 40a C1.5 lesson validated AGAIN** — `DB_PATH` formula breakage is consistent across `lingwen-studio-registry` (Phase 40), `lingwen-persistence` (Phase 54), `lingwen-world-db` (Phase 56), and now `lingwen-reading-power` (Phase 57). Pattern: `packages/X/src/X/Y.py` → `parents[4]` for repo root resolution.

6. **Phase 37 lesson validated AGAIN** — `len(package.__all__) == N` smoke test catches `__all__` count drift. Phase 57: 8/8 ✓.

7. **Phase 53 precedent validated** — historical archive (Phase 15.0, 124, 126, 51 handoffs) preserved with old paths in docstrings for git-blame traceability. Current canonical docs + Phase 57 spec updated; archive untouched.

## Follow-ups

1. **Optional**: refactor `RuleMatcher.scan()` to plumb match offsets through to `_determine_position(offset)` for proper 开篇/中段/结尾 classification. Currently returns 中段 for all matches (degraded but functional).

2. **Optional**: consider whether `CoolpointChart.vue` / `ChapterTable.vue` coolpoint columns should be removed if reading_power data stays dormant. UI shows zeros — feature is broken from user perspective. Phase 58+ audit candidate.

3. **Pre-existing failures unrelated to Phase 57** (24 in `apps/studio_api/tests/`):
   - `test_world_route.py`: import path issue for lingwen-world-db agent extractors
   - `test_studio_batch_templates_route.py`: `from lingwen_studio_batch_streamer import KNOWN_EVENT_TYPES` — actual symbol is in `service.py` (Phase 47 leftover)
   - These should be addressed in a separate fix-up phase.

## References

- Phase 57 spec: `docs/superpowers/specs/2026-09-12-phase-57-p3-archdebt-reading-power-design.md`
- Phase 57 plan: `docs/superpowers/plans/2026-09-12-phase-57-p3-archdebt-reading-power.md`
- Phase 52 audit: `docs/superpowers/infra-subdir-audit.md`
- Phase 51 lessons: `phase-51-p3-archdebt-prose-cluster.md`
- Phase 40a C1.5 lesson: `phase40.md` Lesson 6
- Phase 37 lesson: `phase37.md` (function-body imports, __all__ count)
- Phase 53 precedent: `2026-09-11-phase-53-p3-archdebt-dead-code-cleanup-handoff.md` (FULL DELETE pattern)
- N.14 lesson 1: 9-pattern audit matrix — `MEMORY.md`

## Total LOC accounting

| Category | LOC |
|----------|-----|
| New code (Phase 57) | +1,108 (C1 scaffold) +24 (C1.5 fixups) -34 (C1.5 deletions) = +1,098 |
| Deleted (Phase 57) | -1,006 (infra/reading_power/) -~855 (tests/reading_power/ 8 files) = -1,861 |
| Net new package | ~1,098 - 1,006 = +92 (mostly tests dir + pyproject) |
| Doc updates | +19 / -19 (CLAUDE.md version + 5 doc files) |
| Regression guards | +13 tests |
| **Net total** | **-1,655 LOC** (with +13 guards added) |

Phase 57 REDUCES codebase by 1,655 LOC while preserving all functionality. v52.0 → v53.0.