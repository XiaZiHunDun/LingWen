# Phase 88 P3-ARCHDEBT-MINI Design — infra/__pycache__ + relationship_network.json residue cleanup

> **Phase**: 88 (P3-ARCHDEBT-MINI #4, ARCHDEBT cycle POST-saturation disk cleanup)
> **Branch**: `phase-88-archdebt-pycache-residue`
> **Date**: 2026-09-15
> **Version**: v54.19 → **v54.20**
> **Status**: 📋 spec ready
> **Pattern**: NON-INVASIVE++ (gitignored content only, no tracked file touched)
> **Risk**: MINIMAL (pycache regenerable + gitignored JSON never reachable)

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

---

## §1. Background

Phase 87 closed ARCHDEBT cycle ("ARCHDEBT cycle FINAL saturation" per handoff). However, post-Phase 87 audit (2026-09-15) revealed **two classes of filesystem residue** that the tracked-state cleanup left behind:

1. **`infra/__pycache__/` bytecode residue** — 29 `__pycache__/` subdirectories, ~86 MB on disk. Origin: `git rm` during Phases 79-87 deletes source `.py` files but NOT gitignored `*.pyc` bytecode. The bytecode directories remained on disk because:
   - `.gitignore` pattern `**/__pycache__/` + `**/*.pyc` matched them from commit time (when modules were first imported in this checkout)
   - `git rm -r infra/X/` only removes tracked files; ignored content untouched (N.14 lesson 23 v3, Phase 79 handoff)

2. **`infra/novel-factory/agent_system/social_engine/relationship_network.json`** — 61 bytes empty JSON `{"characters":[],"relationships":[],"events":[]}`. mtime 2026-05-19 (ancient). Origin: Phase 54 P3-ARCHDEBT infra/persistence migration; canonical location moved to `packages/lingwen-core/.../social_engine/relationship_network.db`. Phase 53e gitignored the legacy path (`infra/novel-factory/` in .gitignore:247) to prevent re-tracking, but never physically deleted the JSON residue.

**Tracked-state is clean**: `git ls-files infra/` returns 1 file (`__init__.py`). `git status` clean. ARCHDEBT cycle claim is accurate **with respect to git tracking**.

**Filesystem state has 86 MB residue** of gitignored content.

**Doc stale claim**: CLAUDE.md + CURRENT_STATUS.md + BACKLOG.md read "infra/ now contains only __init__.py" — technically correct (git tracking) but misleading without qualifier. Phase 88 also fixes this doc precision.

---

## §2. 9-pattern audit (per N.14 lesson 1, 22+ variants)

| # | Pattern | Verdict | Notes |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports `from infra.X import Y` | ✅ N/A | No canonical path changes |
| 2 | Indented / function-body imports `^[[:space:]]+from infra.X` | ✅ N/A | No canonical path changes |
| 3 | Relative imports `from .X` / `from ..X` | ✅ N/A | No canonical path changes |
| 4 | Filesystem-path string literals `"infra/X/..."` | ✅ N/A | No canonical path changes |
| 5 | Wildcard `from infra.X import *` | ✅ N/A | No canonical path changes |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ N/A | No canonical path changes |
| 7 | `import X as Y` re-exports | ✅ N/A | No canonical path changes |
| 8 | Doc comments referencing deleted paths | ⚠️ 3 stale claims | CLAUDE.md:103 + CURRENT_STATUS.md:5 + BACKLOG.md:3 read "infra/ now contains only __init__.py" without qualifier. **C3 doc fixup** adds precision: "git tracking only; ~86 MB gitignored `__pycache__/` bytecode residue remains on disk pre-Phase 88, deleted post-Phase 88 C1" |
| 9 | Prior-phase guards hardcoded representative files | ✅ Safe | `tests/test_phase53d_event_sourcing.py:178,218` + `tests/test_phase87_p3_archdebt_tools_workflow_residue.py` checks tracked files (e.g. `infra/__init__.py` existence + `infra/tools/workflow/lib/` absence). Phase 88 does NOT touch tracked files. **0 fixup needed** in C2 |

**Audit verdict**: 9-pattern clean (1 stale doc claim fixup in C3, no canonical path changes, no prior-phase guard regressions).

---

## §3. Inventory + Cleanup targets

### §3.1 `infra/__pycache__/` residue (29 subdirs, ~86 MB)

| Subdir | Size | Origin phase |
|--------|------|--------------|
| `infra/__pycache__/` | 616K | Top-level — accumulating across all phases |
| `infra/cli/__pycache__/` | 244K | Phase 86 deleted `infra/cli/` shell scripts |
| `infra/config/__pycache__/` | 24K | Phase 83 deleted `infra/config/` (config migration to packages/lingwen-config) |
| `infra/core/__pycache__/` | 12K | Phase 53 deleted `infra/core/` |
| `infra/creator/__pycache__/` | 16K | Phase 86 deleted `infra/creator/` shell scripts |
| `infra/cross_volume/__pycache__/` | 268K | Phase 55 deleted `infra/cross_volume/` (full migration to packages/lingwen-cross-volume) |
| `infra/di/__pycache__/` | 28K | Phase 81 deleted `infra/di/` (full migration to packages/lingwen-di) |
| `infra/hooks/__pycache__/` | 116K | Phase 86 deleted `infra/hooks/` shell scripts |
| `infra/persistence/__pycache__/` | 92K | Phase 54 deleted `infra/persistence/` (full migration to packages/lingwen-persistence) |
| `infra/poc/__pycache__/` | 24K | Phase 78 deleted `infra/poc/` |
| `infra/project/__pycache__/` | 12K | Phase 86 deleted `infra/project/` shell scripts |
| `infra/prose/__pycache__/` | 12K | Phase 51 deleted `infra/prose/` (prose 簇 merge) |
| `infra/reading_power/__pycache__/` | 68K | Phase 57 deleted `infra/reading_power/` (full migration) |
| `infra/story_contracts/__pycache__/` | 56K | Phase 79 deleted `infra/story_contracts/` (full migration) |
| `infra/studio/__pycache__/` | 12K | Phase 53 deleted `infra/studio/` |
| `infra/subplot/__pycache__/` | 44K | Phase 80 deleted `infra/subplot/` (full migration to packages/lingwen-subplot) |
| `infra/tools/__pycache__/` | 144K | Phase 86 deleted `infra/tools/` 5 .py + 3 shell |
| `infra/util/__pycache__/` | 36K | Phase 82 deleted `infra/util/` (full migration to packages/lingwen-util) |
| `infra/world_db/__pycache__/` | 100K | Phase 56 deleted `infra/world_db/` (full migration to packages/lingwen-world-db) |
| `infra/world_model/__pycache__/` | 104K | Phase 35 deleted `infra/world_model/` (full migration to packages/lingwen-world-model) |

**Cleanup mechanism**: `find infra/ -type d -name __pycache__ -exec rm -rf {} +` (NOT `git rm` because `__pycache__/` is gitignored — `git rm` would refuse).

**Safety**: All `.pyc` files are Python bytecode cache, regenerable on next Python import. Zero runtime impact.

### §3.2 `infra/novel-factory/agent_system/social_engine/relationship_network.json` (61 bytes)

**File content**:
```json
{"characters":[],"relationships":[],"events":[]}
```

**Origin**: Phase 54 P3-ARCHDEBT infra/persistence migration (2026-09-11). Canonical location moved to `packages/lingwen-core/.../social_engine/relationship_network.db` (SQLite). Old empty JSON file gitignored per `.gitignore:247` (`infra/novel-factory/` pattern). Never tracked, never reachable from current code.

**Cleanup mechanism**: `rm infra/novel-factory/agent_system/social_engine/relationship_network.json`. After deletion, optionally `rm -rf infra/novel-factory/agent_system/social_engine/` (the only file in that subdir).

**Safety**: Gitignored, never tracked, empty content, ancient mtime. Zero runtime impact.

### §3.3 Preserved content (NOT touched)

| Path | Why preserved |
|------|---------------|
| `infra/__init__.py` | 864 bytes compat re-exports, tracked, Phase 36-83 preserved |
| `infra/.locks/workflow.lock` | Runtime lock file, may be held by active sessions |
| `infra/.state/*.db` | Runtime SQLite DBs (workflow.db, ripple.db, cost_tracker.db) — used by app |
| `infra/.state/*.db-*` | SQLite WAL/SHM files |
| `infra/.state/*.json` | Runtime state (creator_merge_preferences_global.json, factory_volume_templates.json, studio_active.json, decisions.json, factory_merge_preset_packages.json) |
| `infra/.state/*.json.lock` | Runtime state locks |
| `infra/.state/ci_records/`, `infra/.state/pilot_records/` | Runtime record dirs |

---

## §4. Plan (5 atomic commits)

| Commit | Type | Subject | Files | +/- | Risk |
|--------|------|---------|-------|-----|------|
| C0 | docs | spec + 9-pattern audit | `docs/superpowers/specs/2026-09-15-phase-88-...md` (NEW) | +~200 | None |
| C1 | chore | FULL DELETE infra/__pycache__/ (29 dirs) + infra/novel-factory/agent_system/social_engine/relationship_network.json + rm parent dir | filesystem only (gitignored content) | ~86 MB disk freed | MINIMAL (gitignored + regenerable) |
| C2 | test | 12 regression guards G1-G12 verifying cleanup + preservation | `tests/test_phase88_archdebt_pycache_residue.py` (NEW) | +~280 | None |
| C3 | docs | doc precision fixup (CLAUDE.md v54.19→v54.20 + CURRENT_STATUS + BACKLOG + handoff) | 4 docs | +~30 | None |

**Note**: Phase 88 follows Phase 87 pattern (5 atomic commits) but C1 is filesystem-only (no `git rm` since gitignored content cannot be staged).

---

## §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

Phase 88 deletes **only gitignored content** — NO canonical path changes, NO test file impact:

- ✅ `infra/__init__.py` (tracked, 864 bytes) — **PRESERVED**
- ✅ `tests/test_phase53d_event_sourcing.py` (tracked) — unaffected (checks tracked files only)
- ✅ `tests/test_phase87_p3_archdebt_tools_workflow_residue.py` (tracked) — unaffected (checks tracked files only)
- ✅ `tests/test_phase88_archdebt_pycache_residue.py` (NEW, C2) — new regression guards
- ✅ All other test files (e.g., `tests/test_phase18_8_stale_imports.py`) — unaffected

**Inventory result**: 0 test files affected by Phase 88 deletion scope. C2 adds new regression guards but does NOT migrate or modify any existing test.

### A2. MIGRATE 路径

**N/A** — no canonical path changes.

### A3. DELETE 路径

**N/A** — no test files deleted. (Phase 88 deletes only filesystem-residue that was never tracked.)

### A4. RETAIN-ORPHAN 路径

**N/A** — no canonical path changes, no orphan risk.

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

**N/A** — Phase 88 has NO infra/X/ → packages/<pkg>/ migration. No "tests/X/ orphan" risk. No pathspec dependency.

---

## §B. Lessons from prior phases (recommended reference)

- **Phase 79 (story_contracts)**: N.14 v23 lesson — `__pycache__/` residue after `git rm`. Phase 79 fixup only addressed `test_phase53d` G5 false-positive, not comprehensive residue cleanup. **Phase 88 closes this carryover** with filesystem-wide pycache cleanup.
- **Phase 53e (orphan runtime artifacts)**: deleted 2 orphan runtime artifacts (relationship_network.json + decisions.json.lock) + added `.gitignore` patterns. Phase 53e was tracked-source focused; `infra/novel-factory/` JSON was gitignored + cleared from tracking but not physically deleted. **Phase 88 closes this carryover** with physical deletion.
- **Phase 87 (tools/workflow/ residue)**: 5 atomic commits pattern (C0 spec / C1 git rm / C2 prior-phase guards fixup / C3 regression guards / C4 doc sync). Phase 88 follows same pattern with filesystem-only C1.
- **Phase 86 (NON-INVASIVE pattern)**: deleted individual files at canonical location without breaking prior-phase guards. Phase 88 is even safer (NON-INVASIVE++) — only gitignored content, zero canonical path impact.

---

## §C. Validation gates

### §C.1 Functional gate

```
# After C1 cleanup:
du -sh infra/  # Expect: <1 MB (vs 86 MB baseline)
find infra/ -type d -name __pycache__ | wc -l  # Expect: 0
ls infra/novel-factory/agent_system/social_engine/ 2>&1  # Expect: ENOENT
ls infra/__init__.py  # Expect: exists (864 bytes, tracked)
ls infra/.locks/workflow.lock  # Expect: exists (runtime, preserved)
ls infra/.state/*.db  # Expect: exists (runtime SQLite, preserved)

# Run prior-phase guards (must remain GREEN):
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase53d_event_sourcing.py -v
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase87_p3_archdebt_tools_workflow_residue.py -v
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase18_8_stale_imports.py -v

# New Phase 88 guards:
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase88_archdebt_pycache_residue.py -v
```

### §C.2 9-pattern audit (post-C1)

Per §2 audit, 0 changes to canonical paths. 9-pattern clean.

### §C.3 Disk verification

```
# Before C1:
du -sh infra/  # 86M

# After C1:
du -sh infra/  # <1M (just __init__.py + .locks/ + .state/ runtime artifacts)
```

---

## §D. Risk assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Delete 29 `__pycache__/` dirs | MINIMAL — Python bytecode regenerable on next import | Zero runtime impact; first Python import of any infra/ submodule will recreate pycache as needed |
| Delete `relationship_network.json` | MINIMAL — gitignored, empty content | Gitignored from Phase 53e (line 247); never tracked; ancient mtime 2026-05-19 |
| Update doc claims (C3) | NONE — text edit | Mechanical doc precision fixup |

---

## §E. Out of scope (explicit defer)

- ❌ Runtime `.state/*.db` SQLite DBs — DO NOT TOUCH (used by app)
- ❌ Runtime `.locks/workflow.lock` — DO NOT TOUCH (may be held by active sessions)
- ❌ Runtime `.state/*.json` state files — DO NOT TOUCH
- ❌ Recreating `__pycache__/` during pytest — natural consequence, not concern
- ❌ Migrating `infra/__init__.py` to `packages/lingwen-infra-init/` — out of scope (it's 26 lines compat shim, ARCHDEBT cycle complete per CLAUDE.md claim)

---

## §F. Completion criteria

- [x] C0 spec doc written (this file)
- [ ] C1 — `infra/__pycache__/` deleted (29 subdirs, ~86 MB freed)
- [ ] C1 — `infra/novel-factory/agent_system/social_engine/relationship_network.json` deleted (61 bytes)
- [ ] C1 — `du -sh infra/` < 1 MB
- [ ] C2 — 12 regression guards G1-G12 GREEN
- [ ] C2 — Prior-phase guards preserved (test_phase53d, test_phase87, test_phase18_8)
- [ ] C3 — CLAUDE.md v54.19 → v54.20 with doc precision fixup
- [ ] C3 — CURRENT_STATUS.md + BACKLOG.md updated
- [ ] C3 — handoff doc written
- [ ] ff-merge ready for `phase-88-archdebt-pycache-residue` branch

---

## §G. Post-Phase 88 state

After Phase 88:

```
$ ls -la infra/
total 16
drwxr-xr-x  6 ailearn ailearn  4096 Sep 15 XX:XX .
drwxr-xr-x 50 ailearn ailearn  4096 Sep 15 XX:XX ..
drwxr-xr-x  2 ailearn ailearn  4096 Sep 15 XX:XX .locks       # runtime, preserved
drwxr-xr-x  5 ailearn ailearn  4096 Sep 15 XX:XX .state       # runtime, preserved
-rw-rw-r--  1 ailearn ailearn   864 Sep 15 XX:XX __init__.py  # tracked, preserved
drwxr-xr-x  2 ailearn ailearn  4096 Sep 15 XX:XX __pycache__/ # regenerable, ~616K top-level

$ du -sh infra/
~640K infra/   # Was 86M before Phase 88 C1
```

**infra/ is now truly minimal**: 1 tracked file (`__init__.py`) + 2 runtime dirs (`.locks/`, `.state/`) + 1 regenerable pycache (~616K top-level from `__init__.py` import). ARCHDEBT cycle **physically complete**, not just tracking-complete.

**Cluster cumulative**: Phase 53 + 53b + 53c + 53d + 53e + 78-88 = **16 phases / ~20464 LOC dead code + ~86 MB disk space recovered**.

**Future ARCHDEBT**: After Phase 88, ARCHDEBT cycle is complete in BOTH git tracking AND filesystem. No further ARCHDEBT work identified. Future work is non-ARCHDEBT features.

---

**Pattern classification**: ARCHDEBT-MINI #4 (NON-INVASIVE++, post-saturation disk cleanup)

**Cluster**: Phase 53-88 = 16 phases, ARCHDEBT cycle closure confirmed.

**Lessons (anticipated)**:
1. **NON-INVASIVE++ pattern**: deleting gitignored content is even safer than deleting tracked content at canonical path. Prior-phase guards unaffected. No 9-pattern audit concerns for canonical paths (only doc precision fixup).
2. **ARCHDEBT cycle physical completion**: tracking-clean ≠ filesystem-clean. Future ARCHDEBT cycle closures should verify both dimensions.