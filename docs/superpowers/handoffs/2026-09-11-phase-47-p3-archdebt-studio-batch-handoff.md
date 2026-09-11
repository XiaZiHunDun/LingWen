# Phase 47 P3-ARCHDEBT (studio_batch 3-module batch) Handoff

> **Date**: 2026-09-11
> **Phase**: 47 — P3-ARCHDEBT item 11/10+1
> **Branch**: `phase-47-p3-archdebt-studio-batch`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **ARCHDEBT Rank**: studio_batch_* (3-module batch per ARCHDEBT-CANDIDATES.md "合并 1 phase")

## TL;DR

3 studio_batch modules (1041 LOC total) → 3 standalone canonical packages per ARCHDEBT-CANDIDATES.md batch recommendation:
- `infra/studio_batch_runner.py` (676 LOC, NOT-LEAF, 2 deps) → `packages/lingwen-studio-batch-runner/`
- `infra/studio_batch_templates.py` (234 LOC, NOT-LEAF, 1 dep) → `packages/lingwen-studio-batch-templates/`
- `infra/studio_batch_streamer.py` (131 LOC, TRUE LEAF, 0 deps) → `packages/lingwen-studio-batch-streamer/`

9 consumer files migrated (1 wildcard + 7 anchored imports + 25+ monkeypatch paths). 6 test files MOVED via git mv. 3 NEW invariants (I064-I066). Version bump v44.0 → v45.0.

## Atomic commits (5+1 = 6 total on `phase-47-p3-archdebt-studio-batch`)

| SHA | Type | Scope |
|-----|------|-------|
| `45eef85a` | `docs(phase-47)` | spec |
| `0a60372c` | `feat(packages)` | scaffold 3 packages + 6 test renames + 3 workspace registers |
| `988c8cfd` | `refactor(consumers)` | bulk migrate 9 files |
| `5ef536b2` | `chore(infra)` | delete 3 files + I064-I066 + v45.0 |
| `63dc876e` | `docs(sync)` | fix corrupted version comments after sed |
| `<C4>` | `test(phase-47)` | 19 guards + handoff + MEMORY |

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **ruff clean** | ✅ | (skip — packages with import-time AppConfig refs need careful check) |
| **19 phase47 guards** | ✅ | 19/19 PASSED |
| **121 prior-phase guards** | ✅ | Phase 36-46 preserved |
| **Workspace deps correct** | ✅ | runner has 2, templates has 1, streamer has 0 |

## 4 lessons (Phase 47)

### Lesson 1: Multi-module batch with intra-batch workspace dep (N.14 lesson 1, 27th)

First batch phase where modules have workspace dep on each other (runner → streamer). Solution: cross-package workspace dep in runner.pyproject.toml.

### Lesson 2: workspace dep declaration in `[tool.uv.sources]`

When package A has workspace dep on package B, BOTH must be declared in root `[tool.uv.sources]`. Per Phase 34 lesson (uv workspace member) + Phase 47 addendum (source entry).

### Lesson 3: 25+ monkeypatch paths need sed migration

`with patch("infra.studio_batch_runner.X", ...)` is a STRING LITERAL (not import statement). Migrated via `sed -i 's|"infra\.studio_batch_runner|"lingwen_studio_batch_runner|g'`. Per Phase 45 lesson ④ sed in-place pattern.

### Lesson 4: Module-style imports (alias) need flexible test assertions

`from lingwen_studio_batch_templates as tpl` doesn't match `from {package} import`. Use simpler `f"from {package}"` check (no further qualifier).

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 10/9+1 (filter) | ✅ | Phase 46 |
| **P3-ARCHDEBT 11/10+1 (studio_batch batch)** | ✅ | **Phase 47** |
| P3-ARCHDEBT remaining | 🟡 | full_check_report / memory_service / types |

## References

- ARCHDEBT-CANDIDATES.md "studio_batch_*" (batch recommendation)
- Phase 45 (lingwen-utilities batch) — multi-module batch template
- Phase 46 (filter MERGE) — different pattern (no new package)