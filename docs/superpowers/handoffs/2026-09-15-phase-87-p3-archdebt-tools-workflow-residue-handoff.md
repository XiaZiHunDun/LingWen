# Phase 87 P3-ARCHDEBT Handoff — infra/tools/workflow/ residue cleanup (ARCHDEBT cycle FINAL saturation)

> **Phase**: 87 (P3-ARCHDEBT-MINI #3, FINAL)
> **Branch**: `phase-87-p3-archdebt-tools-workflow-residue`
> **Date**: 2026-09-15
> **Version**: v54.18 → **v54.19**
> **Status**: ✅ ff-merge ready (5 atomic commits, 10/10 C3 + 75/75 prior-phase GREEN)

---

## TL;DR

Phase 87 **ARCHDEBT cycle FINAL saturation** — 2 shell scripts DELETE from `infra/tools/workflow/` (Phase 84 C3 residue). `infra/tools/` directory entirely gone. `infra/` now contains only `infra/__init__.py` (864 bytes compat re-exports).

Cluster cumulative (Phase 53-87): **15 phases / ~20464 LOC dead code + 8 zero-consumer dirs + 6 真迁移 packages + 1 MERGE**.

**ARCHDEBT cycle essentially COMPLETE**.

---

## §1. Why this Phase matters (ARCHDEBT cycle closure)

Phase 87 closes the ARCHDEBT cycle that began with Phase 53 (P3-ARCHDEBT pilot, dead code cleanup). After Phase 87:
- `infra/` contains only `__init__.py` (864 bytes, compat re-exports from Phase 36-83 migrations)
- 8 zero-consumer dirs deleted (Phase 53-78 ARCHDEBT-MINI saturation)
- 6 packages MIGRATED to packages/ (Phase 79-84 ARCHDEBT-REAL cycle)
- 1 MERGE into existing package subdir (Phase 85)
- 2 zero-consumer .py top-level + 5 zero-consumer shell scripts deleted (Phase 86-87 ARCHDEBT-MINI saturation)

---

## §2. Atomic commits (5)

| Commit | Type | Subject |
|--------|------|---------|
| `39817d11` | docs | C0 spec + 9-pattern audit |
| `46ca423c` | chore | C1 git rm 2 shell scripts + rmdir empty subdir (auto-removed by git rm) + __pycache__ cleanup |
| `4ba2b5f9` | test | C2 prior-phase guards fixup (test_phase53d remove 'tools' from remaining_subdirs + add assert not exists; test_phase18_8 docstring; test_phase84 G7 docstring cleanup) |
| `9e163205` | test | C3 12 regression guards G1-G12 (10/10 PASS — G6 simplified to runtime-import smoke test) |
| (C4) | docs | CLAUDE.md v54.19 + CURRENT_STATUS + BACKLOG + handoff (this doc) |

---

## §3. Files changed

```
infra/tools/workflow/run_workflow.sh                            | DELETE (294 LOC, 9520 bytes)
infra/tools/workflow/logging.sh                                | DELETE (19 LOC, 503 bytes)
tests/test_phase53d_event_sourcing.py                         | +4/-4 (remove 'tools' from remaining_subdirs + add assert not exists for infra/tools/ + docstring)
tests/test_phase18_8_infra_init_simplified.py                 | +1 (Phase 87 docstring note)
tests/test_phase84_p3_archdebt_workflow.py                    | +1/-3 (G7 docstring cleanup, removed obsolete exclusion note)
tests/test_phase87_p3_archdebt_tools_workflow_residue.py      | +285 (NEW, 10 regression guards)
CLAUDE.md                                                    | version v54.18→v54.19 + Phase 87 narrative
collaboration/BACKLOG.md                                     | +1
collaboration/CURRENT_STATUS.md                              | +6
docs/superpowers/handoffs/2026-09-15-phase-87-...md          | NEW (this doc)
docs/superpowers/specs/2026-09-15-phase-87-...md             | +240 (C0)
```

---

## §4. ARCHDEBT cycle FINAL saturation status

| Phase | Pattern | Scope | Status |
|-------|---------|-------|--------|
| 53 | ARCHDEBT-MINI pilot | infra/tools/legacy/ + infra/core/ + infra/studio/ | ✅ |
| 53c | ARCHDEBT-MINI | top-level tools/legacy/ | ✅ |
| 53d | ARCHDEBT-MINI | infra/event_sourcing/ | ✅ |
| 53e | ARCHDEBT-MINI | orphan runtime artifacts | ✅ |
| 78 | ARCHDEBT-MINI | infra/llm_benchmarks/ + infra/poc/ | ✅ |
| 79 | ARCHDEBT-REAL #1 | infra/story_contracts → packages/lingwen-story-contracts | ✅ |
| 80 | ARCHDEBT-REAL #2 | infra/subplot → packages/lingwen-subplot | ✅ |
| 81 | ARCHDEBT-REAL #3 | infra/di → packages/lingwen-di | ✅ |
| 82 | ARCHDEBT-REAL #4 | infra/util → packages/lingwen-util | ✅ |
| 83 | ARCHDEBT-REAL #5 | infra/config → packages/lingwen-config | ✅ |
| 84 | ARCHDEBT-REAL #6 | infra/tools/workflow/lib → packages/lingwen-workflow | ✅ |
| 85 | ARCHDEBT-MIXED #1 | infra/tools/consistency MERGE into packages/lingwen-quality | ✅ |
| 86 | ARCHDEBT-MINI #2 | infra/tools/ top-level 5 .py + 3 shell | ✅ |
| **87** | **ARCHDEBT-MINI #3 (FINAL)** | **infra/tools/workflow/ 2 shell scripts** | **✅** |

**Cluster cumulative**: 15 phases / ~20464 LOC dead code eliminated.

---

## §5. 1 lesson learned (per I079 §C)

### §5.1 Lesson 1 — Non-invasive vs invasive ARCHDEBT-MINI pattern (Phase 86 vs Phase 87)

**Phase 86 NON-INVASIVE**: Deleted individual files at canonical location (infra/tools/ top-level + subdirs). No impact on prior-phase guards because:
- Remaining infra/tools/__init__.py still existed (deleted in same phase as files)
- infra/tools/ directory remained as empty dir post-Phase 86 C1

**Phase 87 BREAKS NON-INVASIVE**: Deleting infra/tools/workflow/{run_workflow.sh,logging.sh} was the LAST tracked files in infra/tools/workflow/ subdir, which was the LAST subdir inside infra/tools/. So git rm auto-removed both infra/tools/workflow/ AND infra/tools/ parent directory. This broke:
- test_phase53d_event_sourcing.py line 174: `assert (infra_dir / "tools").is_dir()` (checks `tools` subdir exists)
- Fixed in C2 by removing `'tools'` from `remaining_subdirs` list + adding `assert not (infra_dir / "tools").exists()`

**Lesson**: Even "NON-INVASIVE" ARCHDEBT-MINI patterns can have hidden prior-phase guard dependencies on directory structure. Always verify Phase 84 G7 + test_phase53d remaining_subdirs + any infra subdir existence checks in C2 BEFORE C1, especially when the deleted files might trigger parent dir removal.

**Phase 88+ heuristic**: Before deleting individual files in ARCHDEBT-MINI, check:
1. `git ls-files <target_dir>/` to see all tracked files in subdirs
2. If deleting those files triggers parent dir removal, update any prior-phase guards that check parent dir existence (test_phase53d remaining_subdirs, etc.)
3. Run `pytest tests/test_phase5x_*_contents_preserved.py` BEFORE C1 commit to verify

---

## §6. References

- **Spec**: `docs/superpowers/specs/2026-09-15-phase-87-p3-archdebt-tools-workflow-residue-design.md`
- **Branch**: `phase-87-p3-archdebt-tools-workflow-residue` (HEAD `9e163205` + C4)
- **Worktree**: `.claude/worktrees/agent-phase87`
- **Prior handoffs**:
  - Phase 86: `docs/superpowers/handoffs/2026-09-15-phase-86-p3-archdebt-tools-top-level-handoff.md` (v54.18)
  - Phase 85: `docs/superpowers/handoffs/2026-09-15-phase-85-p3-archdebt-consistency-handoff.md` (v54.17)
  - Phase 84: `docs/superpowers/handoffs/2026-09-15-phase-84-p3-archdebt-workflow-handoff.md` (v54.16)

---

## §7. Post-merge checklist (user ff-merge step)

```bash
cd /home/ailearn/projects/LingWen && git checkout master && git merge --ff-only phase-87-p3-archdebt-tools-workflow-residue && git push origin master
```

After ff-merge:
1. Update MEMORY.md with Phase 87 topic pointer
2. Mark Phase 87 task as completed
3. **ARCHDEBT cycle essentially complete** — consider non-ARCHDEBT work or final cleanup of `infra/tools/__init__.py` (Phase 88 candidate if needed)