# Phase 86 P3-ARCHDEBT Handoff — infra/tools/ top-level ARCHDEBT-MINI cleanup

> **Phase**: 86 (P3-ARCHDEBT-MINI #2)
> **Branch**: `phase-86-p3-archdebt-tools-top-level`
> **Date**: 2026-09-15
> **Version**: v54.17 → **v54.18**
> **Status**: ✅ ff-merge ready (4 atomic commits, 17/17 C3 regression guards PASS)

---

## TL;DR

Phase 86 ARCHDEBT-MINI 第 2 例 (Phase 78 was first) — **12 files DELETE** (~1670 bytes) from `infra/tools/` top-level + `infra/tools/{publish,content}/` + `tools/workflow/`. 5 zero-consumer .py files (Phase 40-era CLI tools) + 3 infra/tools shell scripts (publish + content) + 3 tools/workflow/ stale shell scripts (Phase 54-era, 2 reference deleted infra/tools/workflow/lib/). I074 NOT extended (no new subdir, only individual file DELETE at canonical infra/tools/ top-level).

Cluster cumulative (Phase 53-86): **14 phases / ~20138 LOC dead code + 8 zero-consumer dirs + 6 真迁移 packages + 1 MERGE**.

---

## §1. Why this Phase matters

### §1.1 闭环 Phase 41+++ mini audit (`infra-residual-audit.md`)

Phase 41+++ mini audit (v40.0+ era) classified `infra/tools/` top-level .py files as zero-consumer (Phase 40-era CLI tools). Phase 78 saturated `infra/tools/` subdirectories (event_sourcing + novel-factory + llm_benchmarks + poc + 4 other subdirs). Phase 86 closes the residual top-level cleanup.

### §1.2 NON-INVASIVE pattern

Phase 86 is **NON-INVASIVE** — cleanup of individual files at canonical location doesn't break prior-phase guards:
1. No subdir-level changes (test_phase53d preserved-list check is subdir-only)
2. No infra/__init__.py wildcard changes
3. No production consumers per 9-pattern audit

This is different from Phases 79-85 (MIGRATE/MERGE patterns) which had G9 CLAUDE.md sync expected-fail at C5 (closed at C6). Phase 86 has no expected-fail — all 17 regression guards GREEN at C3.

---

## §2. Atomic commits (4)

| Commit | Type | Subject |
|--------|------|---------|
| `bb0190e2` | docs | C0 spec + 9-pattern audit |
| `3eff8353` | chore | C1 git rm 12 files + 3 empty subdirs auto-removed + __pycache__ cleanup |
| `eade74eb` | test | C2 prior-phase guards fixup (test_phase18_8 docstring only) |
| `f3c76ca3` | test | C3 12 regression guards G1-G12 (17/17 PASS) |
| (C4) | docs | CLAUDE.md v54.18 + CURRENT_STATUS + BACKLOG + handoff (this doc) |

---

## §3. Files changed (cumulative)

```
.claude/worktrees/agent-phase86/
├── CLAUDE.md                                            |  version v54.17→v54.18 + Phase 86 narrative
├── collaboration/BACKLOG.md                             |  +1 (Phase 86 docstring)
├── collaboration/CURRENT_STATUS.md                      |  +6 (Phase 86 summary)
├── docs/superpowers/handoffs/2026-09-15-phase-86-...md   |  +this doc (NEW)
├── docs/superpowers/specs/2026-09-15-phase-86-...md      |  +spec (C0, NEW)
├── infra/tools/__init__.py                              |  DELETE (11 bytes stale docstring)
├── infra/tools/check_stale_tasks.py                     |  DELETE (76 LOC Phase 40-era CLI tool)
├── infra/tools/issue_tracker.py                         |  DELETE (166 LOC)
├── infra/tools/migrate_to_sqlite.py                     |  DELETE (109 LOC, Phase 54 lingwen-persistence supersedes)
├── infra/tools/regression_tracker.py                    |  DELETE (361 LOC)
├── infra/tools/heartbeat.py                             |  DELETE (34 LOC)
├── infra/tools/publish/run_publish.sh                  |  DELETE (Phase 40-era shell)
├── infra/tools/content/run_check_naming.sh             |  DELETE (Phase 40-era shell)
├── infra/tools/content/run_fix_naming.sh                |  DELETE (Phase 40-era shell)
├── infra/tools/publish/                                 |  empty dir auto-removed
├── infra/tools/content/                                 |  empty dir auto-removed
├── tools/workflow/backup_json.sh                        |  DELETE (Phase 54-era stale)
├── tools/workflow/restore_sqlite.sh                     |  DELETE (Phase 54-era, refs deleted infra/tools/workflow/lib/)
├── tools/workflow/revert_to_json.sh                     |  DELETE (Phase 54-era, refs deleted infra/tools/workflow/lib/)
├── tools/workflow/                                      |  empty dir auto-removed
├── tests/test_phase18_8_infra_init_simplified.py        |  +1 (Phase 86 docstring note)
└── tests/test_phase86_p3_archdebt_tools_top_level.py   |  +285 (NEW, 17 regression guards)
```

---

## §4. 9-pattern audit (per N.14 lesson 1)

| Pattern | Result |
|---------|--------|
| P1 (literal dotted-path imports) | 0 hits |
| P2 (function-body imports) | 0 |
| P3 (relative imports) | 0 |
| P4 (filesystem path literals) | 0 in production (test_phase78 pre-existing docstring ref NOT Phase 86 scope) |
| P5 (wildcard imports) | 0 |
| P6 (monkeypatch indirection) | 0 |
| P7 (import as alias) | 0 |
| P8 (docstring/narrative) | 1 in scope (infra/tools/__init__.py stale) + 3 historical (tools/workflow/ stale shells + docs archive) |
| P9 (prior-phase guard refs) | 0 (no test files reference these CLI tools) |

---

## §5. §A test files migration plan

### §A.1 test files inventory

```
$ grep -rln "infra\.tools\.(check_stale_tasks|issue_tracker|migrate_to_sqlite|regression_tracker|heartbeat)" tests/
```

**0 hits** — no test files reference these CLI tools.

### §A.2 MIGRATE 路径

N/A — no test files for these CLI tools.

### §A.3 DELETE 路径

N/A.

### §A.5 Half-migration defense (per template §A.5)

- ✅ C1 (FULL DELETE) commit pathspec 含 BOTH infra/tools/* + tools/workflow/*
- ✅ C1 commit message: "infra/tools/ 5 zero-consumer .py + 3 shell + tools/workflow/ 3 stale shell" (single sentence)
- ✅ verified: `git show <C1-SHA> --stat` shows 12 deletions

---

## §6. Validation gates

| Gate | Result |
|------|--------|
| Phase 86 C3 regression guards | **17/17 PASS** |
| Phase 53d prior-phase | **8/8 PASS** (no modification needed) |
| Phase 18_8 prior-phase | **6/6 PASS** (docstring updated) |
| Phase 77 invariant sync | **12/12 PASS** (count unchanged at 44) |
| Phase 60 template | **6/6 PASS** |
| ruff | clean on Phase 86 modified files |
| uv.lock | no drift |
| **TOTAL** | **49/49 PASSED** |

---

## §7. 1 lesson learned (per I079 §C)

### §7.1 Lesson 1 — NON-INVASIVE ARCHDEBT-MINI pattern (Phase 86 vs Phase 78)

**Phase 78 pattern (ARCHDEBT-MINI #1)**: deleted entire subdirectories (infra/event_sourcing/, infra/llm_benchmarks/, infra/poc/, etc.) — 17 files + 4 dirs in single C1 commit. Required:
- I074 invariant extension (added 2 new dirs to existing 6 → 8)
- prior-phase guards fixup (test_phase53d drop from remaining_subdirs + assert not exists + __pycache__ residue lesson)
- 25 regression guards with parametrization

**Phase 86 pattern (ARCHDEBT-MINI #2)**: deletes individual files at canonical location (infra/tools/ top-level) — 12 files in single C1 commit. Required:
- NO I074 extension (no new subdir deleted)
- NO prior-phase guards modification (only test_phase18_8 docstring note for tracking)
- 17 regression guards (simpler, no parametrization beyond G1+G2+G3)
- NO G9 expected-fail (NON-INVASIVE pattern — no CLAUDE.md sync needed for I0XX)

**Difference**: Phase 78 needed infrastructure changes (invariant + prior-phase guards + __pycache__ residue) because subdir deletion affects infra/ structure. Phase 86 only deletes files within infra/tools/ (existing dir) — no structural impact.

**Phase 87 candidate**: infra/tools/workflow/{run_workflow.sh, logging.sh} — 2 shell scripts with 1 ref to deleted infra/tools/workflow/lib/ (Phase 84 C3 residue). Similar to Phase 86 but smaller scope.

---

## §8. Out of scope (Phase 87+)

### Phase 87 ARCHDEBT-MINI — infra/tools/workflow/ residue (post-Phase 84)

After Phase 86 deleted 3 tools/workflow/ shell scripts (backup_json + restore_sqlite + revert_to_json), the `infra/tools/workflow/` subdir still exists with 2 shell scripts:
- `infra/tools/workflow/run_workflow.sh` (294 LOC, 1 ref to deleted `infra/tools/workflow/lib/`)
- `infra/tools/workflow/logging.sh` (Phase 40-era workflow shell logging)

These are Phase 84 C3 residue. Phase 87 will close this remaining infra/tools/workflow/ subdir.

### Post-Phase 87 saturation

After Phase 87, infra/tools/ will only contain:
- `infra/tools/__init__.py` (likely empty/minimal — Phase 86 deleted, so maybe needs recreate?)
- 0-1 subdirs

ARCHDEBT cycle will be saturated at this point.

---

## §9. References

- **Spec**: `docs/superpowers/specs/2026-09-15-phase-86-p3-archdebt-tools-top-level-design.md`
- **Branch**: `phase-86-p3-archdebt-tools-top-level` (HEAD `f3c76ca3` + C4)
- **Worktree**: `.claude/worktrees/agent-phase86`
- **Prior handoffs**:
  - Phase 85: `docs/superpowers/handoffs/2026-09-15-phase-85-p3-archdebt-consistency-handoff.md` (v54.17)
  - Phase 84: `docs/superpowers/handoffs/2026-09-15-phase-84-p3-archdebt-workflow-handoff.md` (v54.16)

---

## §10. Post-merge checklist (user ff-merge step)

```bash
cd /home/ailearn/projects/LingWen && git checkout master && git merge --ff-only phase-86-p3-archdebt-tools-top-level && git push origin master
```

After ff-merge:
1. Update MEMORY.md with Phase 86 topic pointer (post-ff-merge)
2. Mark Phase 86 task as completed
3. Create worktree for Phase 87 (next): `git worktree add .claude/worktrees/agent-phase87 -b phase-87-p3-archdebt-tools-workflow-shell master`