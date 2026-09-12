# Phase 57 — Implementation Plan

## Commit sequence (7 atomic commits)

| # | Commit hash (TBD) | Subject | Files touched | Lines | Verify |
|---|-------------------|---------|---------------|-------|--------|
| C0 | `docs(phase-57)` | spec for lingwen-reading-power | 1 file created | +400 | None (docs only) |
| C1 | `feat(packages)` | scaffold lingwen-reading-power (8 src files + tests dir + pyproject + workspace member declaration) | 19 new files + 1 pyproject edit | +1300 | `uv sync --all-packages` succeeds, `lingwen-reading-power` visible in `uv pip list` |
| C1.5 | `fix(reading-power)` | 4 bug fixups (DB_PATH parents[4], SuspectedSegment dedup, _determine_position, unused import) | 4 src files | +5 / -15 | `pytest packages/lingwen-reading-power/tests/` all green |
| C2 | `refactor(consumers)` | migrate 16 consumer sites | 14 files | +24 / -24 | `grep -rn "infra\.reading_power" --include="*.py"` returns 0 hits |
| C3 | `chore(infra)` | FULL DELETE infra/reading_power/ + tests/reading_power/ + I077 invariant | 15 files deleted + CLAUDE.md edit | -1030 / +20 | Path-deleted guard green |
| C4 | `docs(arch)` | version bump v52.0 → v53.0 + update 8 doc references | CLAUDE.md + 5 doc files | +50 / -50 | Version consistency check |
| C5 | `test(phase-57)` | regression guards + handoff + MEMORY.md | 1 new test file + 1 handoff + MEMORY.md edit | +300 | New guards green |

## Checkpoints

### C0 → C1
- [ ] Spec committed
- [ ] Branch is clean
- [ ] pyproject.toml workspace members listed (Phase 54 has the format)

### C1 → C1.5
- [ ] `uv sync --all-packages` exits 0
- [ ] `uv pip list | grep lingwen-reading-power` shows 0.1.0
- [ ] `python -c "import lingwen_reading_power"` works
- [ ] All 8 symbols importable from canonical path
- [ ] Original `infra/reading_power/` still intact (untouched)

### C1.5 → C2
- [ ] DB_PATH now resolves to `infra/.state/reading_power.db` from new location (parents[4])
- [ ] `SuspectedSegment` is single class (NamedTuple form)
- [ ] `_determine_position` no longer has unreachable code
- [ ] `engine.py` no longer has unused import
- [ ] `pytest packages/lingwen-reading-power/tests/` all green

### C2 → C3
- [ ] All 16 consumer sites migrated
- [ ] `grep -rn "from infra\.reading_power"` returns 0
- [ ] `grep -rn "import infra\.reading_power"` returns 0
- [ ] Function-body imports verified (Pattern 2)
- [ ] Apps re-export checked (`apps/studio_api/__init__.py:5`)
- [ ] Original `infra/reading_power/` + `tests/reading_power/` still intact (about to delete in C3)

### C3 → C4
- [ ] `infra/reading_power/` deleted (7 files, 1006 LOC)
- [ ] `tests/reading_power/` deleted (8 files, ~26 KB)
- [ ] I077 invariant added to CLAUDE.md
- [ ] Path-deleted regression guard green
- [ ] `uv run pytest tests/ -v` baseline preserved

### C4 → C5
- [ ] Version bumped v52.0 → v53.0 in CLAUDE.md
- [ ] 8 doc references to `infra/reading_power/` updated
- [ ] MEMORY.md Phase 52 entry preserved
- [ ] New Phase 57 entry to be added in C5

### C5 → Done
- [ ] `tests/test_phase57_lingwen_reading_power.py` created with 8+ guards
- [ ] `docs/superpowers/handoffs/2026-09-12-phase-57-p3-archdebt-reading-power-handoff.md` written
- [ ] MEMORY.md appended with Phase 57 pointer
- [ ] All 9 validation gates GREEN
- [ ] Branch pushed: `git push -u origin phase-57-p3-archdebt-reading-power`
- [ ] User runs ff-merge: `cd /home/ailearn/projects/LingWen && git checkout master && git merge --ff-only phase-57-p3-archdebt-reading-power && git push origin master`

## Pre-flight verification checklist (run before C1)

- [ ] Git status clean
- [ ] On correct branch (`phase-57-p3-archdebt-reading-power`)
- [ ] `uv --version` working
- [ ] `python --version` is 3.11+
- [ ] Recent baseline: `pytest tests/infra/ apps/studio_api/tests/ packages/lingwen-persistence/tests/ -q` all green

## Critical reminders from prior phases

- **N.14 lesson 1, 11th variant**: 9-pattern audit. Already done in C0.
- **Phase 38 lesson 3**: function-body imports — use unanchored grep `grep -rn "from infra\.reading_power"` (catches indented imports).
- **Phase 40a C1.5 lesson**: `parents[4]` for DB_PATH from `packages/X/src/lingwen_X/Y.py` → reach repo root.
- **Phase 34 N.14 lesson 1**: workspace member declaration MUST be in C1 pyproject.toml edit, not C7.
- **Phase 37 lesson**: `__all__` count must match spec — verify `len(package.__all__) == 8` (current `__all__` has 8 names).
- **Phase 41 mini lesson 3**: bash backticks in commit messages — use heredoc `<<'EOF'`.
- **Worktree python env-sync**: use `uv run` (NOT conda).

## Open questions for user

None — all decisions made in Phase 57-B (audit + decide).

## Total estimated wall-clock

~30-45 min for 7 commits (assuming ~5 min/commit average).