# Phase 85 P3-ARCHDEBT Handoff — `infra/tools/consistency/run_quality_checks.py` → MERGE into `packages/lingwen-quality`

> **Phase**: 85 (P3-ARCHDEBT MIXED #2)
> **Branch**: `phase-85-p3-archdebt-consistency`
> **Date**: 2026-09-15
> **Version**: v54.16 → **v54.17**
> **Status**: ✅ ff-merge ready (5 atomic commits, 31/31 prior + phase tests GREEN)

---

## TL;DR

Phase 85 ARCHDEBT-MIXED 第二例 (Phase 50 was first) — `infra/tools/consistency/run_quality_checks.py` (185 LOC, file-level integrity check no-op stub from Phase 53 rewrite) → **MERGE** into `packages/lingwen-quality/src/lingwen_quality/consistency/` (NOT-LEAF I063 extension). 8 supporting files DELETE (~22KB dead code, all zero consumers verified per P1 audit). 3 in-place consumer fixups (1 prod + 2 test monkeypatch + 1 historical ref + 1 docstring). I086 NEW invariant (extends I063 cluster).

Cluster cumulative (Phase 53-85): ~20136 LOC dead code + 8 zero-consumer dirs + 6 真迁移 packages + 1 MERGE (lingwen-quality consistency/ extension).

---

## §1. 为什么这次 Phase 重要

### §1.1 MERGE vs NEW package 决策

**Decision**: **MERGE** into existing `packages/lingwen-quality/src/lingwen_quality/consistency/` subdir.

Rationale:
- `packages/lingwen-quality` 已有 `consistency/` 子目录 (3 files: ai_tells_blacklist.py + checker_feedback.py + creative_whitelist.py = 876 LOC, LLM-related)
- `infra/tools/consistency/run_quality_checks.py` (185 LOC) 是 file-level integrity check — 名字含 "quality_checks" 与 `lingwen-quality.consistency` 同语义簇
- I063 was extended in Phase 46 (filter MERGE) — 同样模式 (小 module 进入 lingwen-quality)
- NEW package `lingwen-consistency` 会增加 maintenance overhead — MERGE 减少 1 个 package
- Total LOC MERGE 范围 ~6KB — 小到不需要独立 package

### §1.2 ARCHDEBT-MIXED pattern (second example after Phase 50)

Phase 85 combines MIGRATE (1 file to existing package subdir) + DELETE (8 supporting files). This is the 2nd time in ARCHDEBT history that Phase combines MERGE + DELETE in single phase (Phase 50 utilities batch v2 was 1st).

Pattern:
- 1 file MERGE (verbatim copy to target location)
- 8 files DELETE (zero consumers per P1 audit + orphan docs/shell/data)
- No pyproject.toml changes (existing package already has workspace deps)
- No __init__.py changes (direct module path import works without __all__ entry)

---

## §2. 改动汇总

### §2.1 Atomic commits (5)

| Commit | Type | Subject |
|--------|------|---------|
| `a9b824af` | docs | C0 spec + 9-pattern audit |
| `9505c446` | chore | C1 MERGE target scaffold (verbatim copy 179 LOC) |
| `7e70ab60` | refactor | C2 IN-PLACE rewrite 4 sites + ruff --fix |
| `??` (C3) | chore | FULL DELETE infra/tools/consistency/ 11 files + I086 NEW |
| `53c16b70` | test | C4 prior-phase guards fixup |
| `17ba9be9` | test | C5 12 regression guards G1-G12 |
| (C6) | docs | CLAUDE.md v54.17 + I086 row + CURRENT_STATUS + BACKLOG + handoff (this doc) |

### §2.2 Files changed (cumulative)

```
.claude/worktrees/agent-phase85/
├── .lingwen/architecture.yml                                    |  +3 (I086 NEW after I085)
├── CLAUDE.md                                                    |  +1 (I086 row in invariant table) + version v54.16→v54.17 narrative
├── collaboration/BACKLOG.md                                    |  +1
├── collaboration/CURRENT_STATUS.md                             |  +6
├── docs/superpowers/handoffs/2026-09-15-phase-85-...md         |  +this doc (NEW)
├── docs/superpowers/specs/2026-09-15-phase-85-...md            |  +spec (C0, NEW)
├── packages/lingwen-quality/src/lingwen_quality/consistency/run_quality_checks.py | NEW (185 LOC MERGED)
├── infra/tools/consistency/                                    |  FULL DELETE (-22KB, 11 files)
├── packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/run_checker.py | +1/-1 (function-body import rewrite)
├── tests/hooks/test_actions.py                                 |  +4/-4 (monkeypatch indirection rewrite + docstring)
├── tests/test_phase53_p3_archdebt_dead_code_cleanup.py         |  +3/-1 (historical ref update)
├── tests/test_phase18_8_infra_init_simplified.py               |  +1 (Phase 85 docstring note)
├── tests/test_phase53d_event_sourcing.py                       |  +5/-1 (consistency/ assert not exists + docstring)
├── tests/test_phase77_architecture_invariant_sync.py           |  +3/-3 (count 43→44 + I048-I086 range)
└── tests/test_phase85_p3_archdebt_consistency.py               |  +274 (NEW, 13 regression guards)
```

---

## §3. 9-pattern audit 结果

| Pattern | Result |
|---------|--------|
| P1 (literal dotted-path imports) | 5 sites (1 prod + 1 historical ref + 3 monkeypatch) |
| P2 (function-body imports) | 100% of production (run_checker.py:148 function-body) |
| P3 (relative imports) | 0 |
| P4 (filesystem path literals) | 0 |
| P5 (wildcard imports) | 0 |
| P6 (monkeypatch indirection) | 2 sites (test_actions.py:234 + 241) |
| P7 (import as alias) | 0 |
| P8 (docstring/narrative) | 2 test docstring sites (test_actions.py:222 + test_phase53 historical line 5) |
| P9 (prior-phase guard refs) | 1 site (test_phase53 historical Phase 53 reference) |

---

## §4. §A test files migration plan

### §A.1 test files inventory

| File | Action |
|------|--------|
| `tests/hooks/test_actions.py` | IN-PLACE rewrite (2 monkeypatch sites + 1 docstring) |
| `tests/test_phase53_p3_archdebt_dead_code_cleanup.py` | IN-PLACE rewrite (line 5 docstring + line 173 importlib) |
| `tests/test_phase53d_event_sourcing.py` | IN-PLACE update (add assert not exists for consistency/) |
| `tests/test_phase18_8_infra_init_simplified.py` | IN-PLACE update (add Phase 85 docstring note) |
| `tests/test_phase77_architecture_invariant_sync.py` | IN-PLACE update (count 43→44 + I048-I086 range) |
| `tests/test_phase85_p3_archdebt_consistency.py` | NEW (12 regression guards) |

**0 files MIGRATE** (no dedicated tests for run_quality_checks.py — Phase 53 made it a no-op stub, no functional tests). 5 files IN-PLACE rewrite + 1 NEW file.

### §A.2 IN-PLACE rewrite 路径

- sed `infra\.tools\.consistency\.run_quality_checks` → `lingwen_quality\.consistency\.run_quality_checks` (all sites)
- `tests/hooks/test_actions.py`: 2 monkeypatch sites (string-based patch target + dict key) + 1 docstring
- `tests/test_phase53_p3_archdebt_dead_code_cleanup.py`: 1 docstring (line 5 mentions Phase 53 rewrite) + 1 importlib site (line 173)
- Manual edit for test_phase53d (add new assert block) + test_phase18_8 (add docstring note) + test_phase77 (count + range update)

### §A.5 Half-migration defense

- ✅ C2 IN-PLACE rewrite in single commit (preserves blame for production + test sites)
- ✅ C3 FULL DELETE atomic per I079 §A5
- ✅ C3 commit message 含 "infra/tools/consistency/run_quality_checks.py MIGRATE + 8 supporting files DELETE + I063 extension"

---

## §5. 验证 gates

| Gate | Result |
|------|--------|
| Phase 85 C5 regression guards | **13/13 PASS** (G9 closed at C6) |
| Phase 53d prior-phase | **8/8 PASS** (added new assert for consistency/) |
| Phase 18_8 prior-phase | **6/6 PASS** |
| Phase 77 invariant sync | **12/12 PASS** (G1 count 44, G2 I086 in both CLAUDE.md + architecture.yml) |
| Phase 60 P3-ARCHDEBT template | **6/6 PASS** |
| **TOTAL** | **45/45 PASSED** (G9 closed at C6 + G2 closed at C6) |

---

## §6. 1 lesson learned (per I079 §C)

### §6.1 Lesson 1 — MERGE pattern is different from MIGRATE pattern (Phase 85 vs Phase 79-84)

**MIGRATE pattern (Phases 79-84)**: Creates NEW package from scratch:
- New pyproject.toml + __init__.py + N modules
- Workspace member declaration in root pyproject.toml
- Direct module path import OR __init__.py + __all__ entry
- uv lock sync (Phase 83 systemic lesson)

**MERGE pattern (Phase 85)**: Relocates file into EXISTING package subdir:
- NO pyproject.toml changes (existing package already has workspace deps)
- NO __init__.py changes (direct module path import `from lingwen_quality.consistency.run_quality_checks import ...` works)
- NO uv lock sync (no new workspace member)
- Verbatim copy of file content (no rename, no dep changes)
- Pre-C1 audit: `grep '^from infra\.tools\.consistency\.' infra/tools/consistency/` = 0 hits (no intra-package absolute imports, no pre-C1 fixup needed)

**Decision criteria for MERGE vs MIGRATE vs NEW package**:
- MIGRATE: creates new package, typically NOT-LEAF with workspace deps (Phase 79-84)
- MERGE: file moves to existing package subdir, semantic match (Phase 85 + Phase 46)
- NEW package: file moves to brand new package, distinct from existing (Phase 49 lingwen-memory-service)

**Phase 85 chose MERGE** because:
1. lingwen-quality already has `consistency/` subdir (3 LLM-related files)
2. run_quality_checks is file-level integrity check matching consistency/ semantic
3. Total scope ~6KB too small for standalone package
4. Maintenance overhead reduction (no new package to maintain)

---

## §7. Out of scope (Phase 86)

### Phase 86 ARCHDEBT-MINI — infra/tools/ top-level cleanup

After Phase 84-85, remaining infra/tools/ subdirs:
- 5 zero-consumer .py files at top-level: `check_stale_tasks.py` (76 LOC) + `issue_tracker.py` (166) + `migrate_to_sqlite.py` (109) + `regression_tracker.py` (361) + `heartbeat.py` (34) = 746 LOC
- 3 shell scripts: `publish/run_publish.sh` + `content/run_check_naming.sh` + `content/run_fix_naming.sh`
- 2 stale tools/workflow/ shell scripts: `restore_sqlite.sh` + `revert_to_json.sh` (Phase 54 era, predates lingwen-persistence)
- `infra/tools/__init__.py` with stale narrative mentioning deleted subdirs

Total scope: ~750 LOC + 5 shell scripts.

---

## §8. References

- **Spec**: `docs/superpowers/specs/2026-09-15-phase-85-p3-archdebt-consistency-design.md`
- **Branch**: `phase-85-p3-archdebt-consistency` (HEAD `17ba9be9` + C6)
- **Worktree**: `.claude/worktrees/agent-phase85`
- **Architecture**: `.lingwen/architecture.yml` (I086 NEW line 177, extends I063)
- **Prior handoffs**:
  - Phase 84: `docs/superpowers/handoffs/2026-09-15-phase-84-p3-archdebt-workflow-handoff.md` (v54.16)
  - Phase 83: `docs/superpowers/handoffs/2026-09-14-phase-83-p3-archdebt-config-handoff.md` (v54.15)

---

## §9. Post-merge checklist (user ff-merge step)

```bash
cd /home/ailearn/projects/LingWen && git checkout master && git merge --ff-only phase-85-p3-archdebt-consistency && git push origin master
```

After ff-merge:
1. Update MEMORY.md with Phase 85 topic pointer (post-ff-merge)
2. Mark Phase 85 task as completed
3. Create worktree for Phase 86 (next): `git worktree add .claude/worktrees/agent-phase86 -b phase-86-p3-archdebt-tools-top-level master`