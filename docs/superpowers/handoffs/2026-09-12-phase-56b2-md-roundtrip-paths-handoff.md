# Phase 56b2 P3-ARCHDEBT — cwd-independent test paths handoff

> **Date**: 2026-09-12
> **Branch**: `phase-57-p3-archdebt-reading-power` (continuing Phase 56b branch)
> **Master HEAD before**: `a8b48ae4` (Phase 56b C4 doc-sync)
> **Version**: v54.1 (no bump — Phase 56b2 is a 1-line test fix, doesn't merit version)

## Why

Phase 56b C2 (commit `4e22667f`) restored `packages/lingwen-world-db/tests/test_markdown_roundtrip.py`
from Phase 58 commit `0f3239f4^`. The restored file used cwd-relative paths:

```python
SAMPLE_DIR = Path("docs/character-bible")
# ... Path("docs/faction-design.md") ...
# ... Path("docs/lore-registry.md") ...
# ... src_dir = Path("docs") ...
```

These only resolve when pytest is invoked from the repo root. From any other
cwd (`cd packages/lingwen-world-db && pytest tests/`, or from CI in a
sandbox where pytest's rootdir detection misbehaves), they fail with
`FileNotFoundError`.

Phase 56b handoff lesson 4 (handoff lines 145-150) explicitly flagged this
as deferred scope. Phase 56b2 closes that gap.

## What changed

### C1 — cwd-relative path refactor (`f74c1af3`)

**File**: `packages/lingwen-world-db/tests/test_markdown_roundtrip.py`

Replaced cwd-relative `Path()` literals with file-relative anchors:

```python
# Before
SAMPLE_DIR = Path("docs/character-bible")
src = Path("docs/faction-design.md").read_text(...)
src = Path("docs/lore-registry.md").read_text(...)
src_dir = Path("docs")

# After
REPO_ROOT = Path(__file__).resolve().parents[3]   # tests → <pkg> → packages → repo
DOCS_DIR = REPO_ROOT / "docs"
SAMPLE_DIR = DOCS_DIR / "character-bible"
src = (DOCS_DIR / "faction-design.md").read_text(...)
src = (DOCS_DIR / "lore-registry.md").read_text(...)
src_dir = DOCS_DIR
```

Layout documented inline so future readers don't re-derive the `parents[3]`
arithmetic:

```python
# Resolve fixture paths relative to repo root (cwd-independent — pytest
# collection runs may have any cwd). Layout:
#   tests/ → lingwen-world-db/ → packages/ → <repo_root>
```

`test_timeline_serialize` is unchanged (pure unit test, no file fixtures).

### C2 — 2 regression guards (`d2f3e604`)

**File**: `tests/test_phase56b2_p3_archdebt_md_roundtrip_paths.py` (new, 87 LOC)

| ID | Test | Asserts |
|----|------|---------|
| G6 | `test_no_cwd_relative_path_literals_in_md_roundtrip` | No `Path("docs/...")` / `Path('docs/...')` literals in `test_markdown_roundtrip.py` (comments/docstrings exempt) |
| G7 | `test_md_roundtrip_uses_file_relative_path_pattern` | `Path(__file__).resolve().parents[N]` pattern + module-level `DOCS_DIR` constant present |

## Validation

### Test results

| Invocation cwd | Result |
|----------------|--------|
| repo root: `pytest packages/lingwen-world-db/tests/` | **27 passed** in 0.98s |
| package dir: `cd packages/lingwen-world-db && pytest tests/` | **27 passed** in 0.18s |
| tests dir: `cd packages/lingwen-world-db/tests && pytest .` | **27 passed** in 0.96s |

All 3 invocation paths now produce identical green results — cwd-independence proven.

### Regression guards

| Suite | Result |
|-------|--------|
| Phase 56b (G1-G5, restoration) | 5/5 GREEN |
| Phase 56b2 (G6-G7, this phase) | 2/2 GREEN |
| Phase 5x cumulative (`tests/test_phase5*.py`) | 155/155 GREEN |

## Lessons

(Detailed in `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase-56b2-p3-archdebt-md-roundtrip-paths.md`)

1. **Cwd-relative `Path("X/...")` is a test-fixture smell** — prefer
   `Path(__file__).resolve().parents[N]` for package-local tests.
2. **`parents[N]` math depends on file depth** — document the layout
   inline (tests/ → <pkg> → packages → repo).
3. **Run tests from MULTIPLE cwds to verify cwd-independence** —
   a single invocation hides bugs. Phase 56b2 verified 3 cwds.
4. **Phases can be "follow-up to follow-up"** — each gets its own handoff +
   guards. Don't cram "1-line fix" into parent phase.

## Side discovery

While investigating why Phase 56b wasn't ff-merged (master was still at
Phase 55 `f5a34173`), discovered the "daemon" the previous session thought
would auto-merge (`/tmp/lingwen-auto-merge.sh`) is a **downstream sync daemon**
that pulls origin/master into local master. It does NOT push worktree branches
to master. The actual ff-merge mechanism is `scripts/ff-merge-to-master.sh
<branch>` (explicit invocation, sandbox-allowed via `git push origin BRANCH:master`).

Phase 56b was finally ff-merged manually via this script (commit `a8b48ae4` →
origin/master).

## Atomic commits

| SHA | Phase | Description |
|-----|-------|-------------|
| `f74c1af3` | C1 | fix(world-db): cwd-independent paths in test_markdown_roundtrip |
| `d2f3e604` | C2 | test(world-db): 2 regression guards for cwd-independent paths |
| (this handoff) | C3 | doc-sync: MEMORY.md + topic file + CLAUDE.md |

## Next-actionable candidates

(a) Continue Phase 56b follow-ups — audit `infra/tools/` for similar cwd-
    dependent test patterns (Phase 53c).

(b) Fix 32 cross_volume test collection errors (CLAUDE.md noted 16; actual
    count is 32 per `pytest --collect-only`). Root cause likely in
    `tests/cross_volume/conftest.py` or import path resolution.

(c) Investigate why `auto-merge.sh` daemon doesn't push worktree branches.
    Either expand the daemon to handle this, or document the manual
    `ff-merge-to-master.sh` workflow more prominently.

(d) Switch to product feature work.