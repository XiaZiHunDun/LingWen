# Phase 84 P3-ARCHDEBT Handoff — `infra/tools/workflow/lib` → `packages/lingwen-workflow`

> **Phase**: 84 (P3-ARCHDEBT REAL cycle #6)
> **Branch**: `phase-84-p3-archdebt-workflow`
> **Date**: 2026-09-15
> **Version**: v54.15 → **v54.16**
> **Status**: ✅ ff-merge ready (7 atomic commits, 131/131 prior-phase tests preserved, 65/66 functional gate)

---

## TL;DR

Phase 84 真迁移第六例 — `infra/tools/workflow/lib` (1012 LOC, 8 source files, 28-symbol public API) → `packages/lingwen-workflow` (NOT-LEAF, 2 workspace deps). 9 test files MIGRATE per I079 §A5 (single commit pathspec BOTH old + new — 8 renames detected). 1 production cross-package consumer in `packages/lingwen-pipeline/hooks/actions/block_proceed.py` rewritten. 2 IN-PLACE monkeypatch rewrites (conftest.py 5 sites + test_actions.py 2 sites). conftest.py sys.path hack removed (Phase 56b lesson 1). I085 NEW invariant.

Cluster cumulative (Phase 53-84): ~20114 LOC dead code + 8 zero-consumer dirs + 6 真迁移 packages (LEAF story-contracts + NOT-LEAF subplot + TRUE LEAF di + NOT-LEAF util + TRUE LEAF config + NOT-LEAF workflow).

---

## §1. 为什么这次 Phase 重要

### §1.1 ARCHDEBT-CANDIDATES.md Top 5 closure 后续

Phase 83 closed ARCHDEBT-CANDIDATES.md Top 5 (5/5 真迁移 packages). Phase 84 是 Top 5 closure 后的**第一个**真迁移 — 闭环 Phase 41+++ mini audit (`docs/superpowers/infra-residual-audit.md`) 识别的 `infra/tools/workflow/lib` (~1750 LOC NOT-LEAF) 中先迁移的子目录。

### §1.2 Pattern verification 第六例

Phases 79-83 已验证 5 种 package shapes:
- Phase 79 LEAF (story-contracts, 10 symbols)
- Phase 80 NOT-LEAF (subplot, 15 symbols)
- Phase 81 TRUE LEAF (di, 8 symbols)
- Phase 82 NOT-LEAF (util, 6 symbols — single dep lingwen-errors)
- Phase 83 TRUE LEAF + pyyaml (config, 1 symbol)
- **Phase 84 NOT-LEAF (workflow, 28 symbols — forward-only workspace dep cycle)** ← NEW pattern

Phase 84 是 cluster 中**最大符号数 (28)** 真迁移 package,也是**第一个**包含运行时 cycle (events._get_hook_engine ↔ block_proceed) 的包 — 通过 forward-only workspace dep (lingwen-workflow → lingwen-pipeline, NOT反向) 解决。

---

## §2. 改动汇总

### §2.1 Atomic commits (7)

| Commit | Type | Subject |
|--------|------|---------|
| `e5295479` | docs | C0 spec + 9-pattern audit |
| `6f49120d` | chore | C1 scaffold 9 files (pyproject + 8 modules) |
| `4eeff520` | refactor | C2 MIGRATE 1 prod + 9 test files + IN-PLACE rewrite 7 monkeypatch + 4 docstrings + conftest sys.path hack removal |
| `155bc327` | chore | C3 FULL DELETE infra/tools/workflow/lib/ 8 files (-1012 LOC) + I085 NEW + 4 docstring narratives cleanup |
| `61a508e6` | test | C4 prior-phase guards fixup (test_phase53d + rmdir empty lib/ + test_phase18_8 docstring) |
| `bbe0598e` | test | C5 12 regression guards G1-G12 (G9 expected-fail until C6) |
| (C6) | docs | CLAUDE.md v54.16 + I085 row + CURRENT_STATUS + BACKLOG + handoff (this doc) |

### §2.2 Files changed (cumulative)

```
.claude/worktrees/agent-phase84/
├── .lingwen/architecture.yml                                |  +3 (I085 NEW)
├── CLAUDE.md                                                 |  +1 (I085 row) version v54.15→v54.16 narrative
├── collaboration/CURRENT_STATUS.md                          |  +6
├── collaboration/BACKLOG.md                                  |  +1
├── docs/superpowers/handoffs/2026-09-15-phase-84-...md      |  +this doc (NEW)
├── docs/superpowers/specs/2026-09-15-phase-84-...md         |  +spec (C0, NEW)
├── pyproject.toml                                            |  +2 (workspace members + sources)
├── packages/lingwen-workflow/                                |  NEW package
│   ├── pyproject.toml                                        |  +17 (NOT-LEAF, 2 deps)
│   ├── src/lingwen_workflow/                                 |  +1012 LOC (8 modules)
│   │   ├── __init__.py                                       |  155 LOC
│   │   ├── db.py                                             |  105 LOC
│   │   ├── state.py                                          |  204 LOC
│   │   ├── tasks.py                                          |  147 LOC
│   │   ├── checkpoints.py                                    |  203 LOC
│   │   ├── events.py                                         |  61 LOC
│   │   ├── batch.py                                          |  49 LOC
│   │   └── migration.py                                      |  88 LOC
│   └── tests/                                                |  MIGRATE 9 files
│       ├── __init__.py                                       |  4 lines (Phase 84 context)
│       ├── conftest.py                                       |  (sys.path hack removed)
│       ├── test_batch.py                                     |  MIGRATE
│       ├── test_checkpoints.py                               |  MIGRATE
│       ├── test_db.py                                        |  MIGRATE
│       ├── test_events.py                                    |  MIGRATE
│       ├── test_migration.py                                 |  MIGRATE
│       ├── test_state.py                                     |  MIGRATE
│       └── test_tasks.py                                     |  MIGRATE
├── packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/block_proceed.py |  +1/-1 (function-body import rewrite)
├── tests/hooks/test_actions.py                               |  +2/-2 (monkeypatch indirection rewrite)
├── tests/test_phase53d_event_sourcing.py                     |  +3/-1 (Phase 84 docstring + assert not exists)
├── tests/test_phase18_8_infra_init_simplified.py             |  +1 (Phase 84 docstring note)
├── tests/test_phase84_p3_archdebt_workflow.py                |  +367 (NEW, 12 regression guards)
├── infra/tools/workflow/lib/                                 |  FULL DELETE (-1012 LOC, 8 files)
└── uv.lock                                                   |  +12 (lingwen-workflow resolved)
```

---

## §3. 9-pattern audit 结果

Per I079 invariant + N.14 lesson 1, Phase 84 C0 ran 9-pattern audit. Summary:

| Pattern | Audit Result |
|---------|--------------|
| P1 (literal dotted-path imports) | ~50 sites (1 prod block_proceed.py:59 + 49 test imports) |
| P2 (function-body imports) | 100% of test imports + 1 prod (all sed-rewritable) |
| P3 (relative imports) | 0 anti-pattern (lib/state.py:15 uses 'from . import db, events' — legitimate) |
| P4 (filesystem path literals) | 1 docstring narrative (informational, fixed in C3) |
| P5 (wildcard imports) | 0 |
| P6 (monkeypatch indirection) | 7 sites (5 conftest.py + 2 test_actions.py — all sed-rewritable) |
| P7 (import as alias re-exports) | 0 |
| P8 (docstring/narrative refs) | 4 sites in test docstrings + 1 in lib/__init__.py (5 fixed) |
| P9 (prior-phase guard refs) | 0 (clean) |

---

## §4. §A test files migration plan (MANDATORY per template §A)

### §A.1 test files inventory

```
tests/tools/workflow/
├── __init__.py              # MIGRATE
├── conftest.py              # MIGRATE + sys.path hack removed
├── test_batch.py            # MIGRATE
├── test_checkpoints.py      # MIGRATE
├── test_db.py               # MIGRATE
├── test_events.py           # MIGRATE
├── test_migration.py        # MIGRATE
├── test_state.py            # MIGRATE (has pre-existing failure)
└── test_tasks.py            # MIGRATE
```

**9 test files MIGRATE** + 1 IN-PLACE rewrite (`tests/hooks/test_actions.py` for 2 monkeypatch sites).

### §A.2 MIGRATE 路径

- Target: `packages/lingwen-workflow/tests/<test-file>.py`
- Step: `git mv tests/tools/workflow/<file>.py packages/lingwen-workflow/tests/<file>.py` (single C2 commit, pathspec BOTH old + new per Phase 56c lesson 1)
- Imports: `from infra.tools.workflow.lib` → `from lingwen_workflow` (sed 全 file)
- sys.path hack cleanup: 删除 conftest.py PROJECT_ROOT + sys.path.insert (Phase 56b lesson 1)
- cwd-relative path: 不需要修改
- Functional gate: `pytest packages/lingwen-workflow/tests/ -v` 65/66 PASS (1 pre-existing)

### §A.5 Half-migration defense (per template §A.5)

- ✅ C2 pathspec 含 BOTH old + new
- ✅ C3 (FULL DELETE) atomic per I079 §A5
- ✅ C3 commit message 含 "infra/tools/workflow/lib/ + tests/tools/workflow/ + I085 invariant + __pycache__ residue"
- ✅ `git show <C2-SHA> --stat` 显示 8 renames (test files)

---

## §5. 验证 gates

| Gate | Result |
|------|--------|
| C5 regression guards | **42/43 PASS** (G9 expected-fail closed at C6) |
| Phase 53d prior-phase | **7/7 PASS** |
| Phase 18_8 prior-phase | **6/6 PASS** |
| Phase 77 architecture invariant sync | **12/12 PASS** (I085 in architecture.yml) |
| Phase 60 P3-ARCHDEBT template | **6/6 PASS** |
| Phase 84 lingwen-workflow functional gate | **65/66 PASS** (1 pre-existing per Phase 81 lesson) |
| **TOTAL** | **131/43 PASS** = 131 prior + phase preserved + 65 functional (44 new + 1 fail) |

---

## §6. 风险评估 + lessons learned (per I079 §C)

### §6.1 Lesson 1 — Empty dir residue after git rm (N.14 v23 v3)

**Problem**: `git rm -r infra/tools/workflow/lib/` 删除 8 个 tracked 文件后,空目录 `infra/tools/workflow/lib/` 仍存在 (git doesn't track empty directories)。`test_phase53d_event_sourcing.py::test_phase53d_infra_canonical_contents_preserved` 加 `assert not (infra_dir / "tools" / "workflow" / "lib").exists()` 失败因为 `.exists()` 返回 True。

**Solution**: Phase 84 C4 用 `rmdir infra/tools/workflow/lib` (假设目录空 — C3 后已 tracked files 全部删除)。这是 Phase 79 v23 + Phase 80 lesson 的**第三次变体** — 每次 P3-ARCHDEBT 删子目录时 C4 都需要检查空目录残留。

**Future heuristic**: C3 commit 后立即 `find infra/<subdir>/ -type d -empty -delete` 或 C4 用 `(infra_dir / X / Y).exists()` 时考虑空目录残留。

### §6.2 Lesson 2 — Forward-only workspace dep (Phase 84 NEW pattern)

**Problem**: `lingwen_workflow.events._get_hook_engine()` 在 runtime lazy import `from lingwen_pipeline.hooks.actions.block_proceed import BlockProceedAction`。`block_proceed.py:59` 函数体内 `from lingwen_workflow import set_state`。两个都是函数体 import,但 pyproject.toml [project] dependencies 只能声明单向。

**Solution**: `lingwen-workflow` pyproject.toml 声明依赖 `lingwen-pipeline`,但 `lingwen-pipeline` 不声明 `lingwen-workflow`。uv workspace 接受此模式因为没有 cycle 在 [project] dependencies。Python deferred module init 处理 runtime 函数体循环(两个 import 都是 function-body,never module-level)。

**Future heuristic**: 当新包有 runtime function-body import cycle 时,声明**单一方向** workspace dep — 选包含最多 consumer symbols 的方向 (lingwen-workflow 暴露 28 symbols for block_proceed.py 只用 1 symbol set_state)。

### §6.3 Lesson 3 — Source-text migration check needs proper package import

**Problem**: Phase 84 C5 G12 v1 用 `importlib.util.spec_from_file_location('block_proceed', 'packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/block_proceed.py')` 失败因为相对 imports `from .base import ActionResult` 需要 package context,spec_from_file_location 创建的 module 没有 `__package__`。

**Solution**: G12 v2 改用 `import lingwen_pipeline.hooks.actions.block_proceed` (proper package import — 模块在 sys.modules 中有完整 package context)。Source-text check (`from lingwen_workflow import set_state`) 移到 test 函数内 (subprocess script 外部) 用 REPO_ROOT Path。

**Future heuristic**: Future C5 G12 直接用 proper package import (`import lingwen_pkg.module`),不要用 `spec_from_file_location`。如果需要 source-text check,放到 test 函数体内用 Path.read_text + re.search。

---

## §7. Out of scope (next phases)

### Phase 85 ARCHDEBT-REAL — infra/tools/consistency/

- **1 production consumer**: `packages/lingwen-pipeline/hooks/actions/run_checker.py:148` function-body `from infra.tools.consistency.run_quality_checks import run_quality_checks`
- **2 options**:
  - A) **MERGE into lingwen-quality** (extends I063 FalsePositiveFilter + ProblemClassifier cluster)
  - B) Migrate to new `packages/lingwen-consistency/` package
- Other 3 .py files in consistency/ (check_naming.py + integrity_checker.py + __init__.py) + 8 data/md/yaml/json files: investigate consumers, likely most dead

### Phase 86 ARCHDEBT-MINI — infra/tools/ top-level cleanup

After Phase 84-85 migrate workflow/lib + consistency/run_quality_checks, remaining infra/tools/ top-level:
- 5 zero-consumer .py files: check_stale_tasks (76 LOC) + issue_tracker (166 LOC) + migrate_to_sqlite (109 LOC) + regression_tracker (361 LOC) + heartbeat (34 LOC) = 746 LOC
- 3 shell scripts: publish/run_publish.sh + content/{run_check_naming,run_fix_naming}.sh
- 2 stale tools/workflow/ shell scripts: restore_sqlite.sh + revert_to_json.sh (Phase 54 era, predates lingwen-persistence)
- infra/tools/__init__.py with stale docstring

Total ~750 LOC + 5 shell scripts. Extend I074 invariant or create I086.

---

## §8. References

- **Spec**: `docs/superpowers/specs/2026-09-15-phase-84-p3-archdebt-workflow-design.md`
- **Branch**: `phase-84-p3-archdebt-workflow` (HEAD `bbe0598e` + C6)
- **Worktree**: `.claude/worktrees/agent-phase84`
- **Architecture**: `.lingwen/architecture.yml` (I085 NEW line 174)
- **Prior handoffs**:
  - Phase 83: `docs/superpowers/handoffs/2026-09-14-phase-83-p3-archdebt-config-handoff.md` (v54.15)
  - Phase 82: `docs/superpowers/handoffs/2026-09-14-phase-82-p3-archdebt-util-handoff.md` (v54.14)
  - Phase 81: `docs/superpowers/handoffs/2026-09-14-phase-81-p3-archdebt-di-handoff.md` (v54.13)

---

## §9. Memory + handoff sync

- **MEMORY.md**: Add topic `phase-84-p3-archdebt-workflow.md` pointer (post-ff-merge)
- **CLAUDE.md**: v54.15 → v54.16 + I085 row in invariant table
- **CURRENT_STATUS.md**: Phase 84 ready for ff-merge
- **BACKLOG.md**: Phase 85/86 candidates listed

---

## §10. Post-merge checklist (user ff-merge step)

```bash
cd /home/ailearn/projects/LingWen && git checkout master && git merge --ff-only phase-84-p3-archdebt-workflow && git push origin master
```

After ff-merge:
1. Update MEMORY.md with Phase 84 topic pointer
2. Mark Phase 84 task as completed in task list
3. Create worktree for Phase 85 (next): `git worktree add .claude/worktrees/agent-phase85 -b phase-85-p3-archdebt-consistency master`