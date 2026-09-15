# Phase 84 P3-ARCHDEBT Design — `infra/tools/workflow/lib` → `packages/lingwen-workflow`

> **版本**: 草稿 v1 (C0 spec + 9-pattern audit + §A test files migration plan)
> **日期**: 2026-09-15
> **承接**: Phase 83 P3-ARCHDEBT infra/config → packages/lingwen-config (v54.15, ARCHDEBT-CANDIDATES.md Top 5 闭环)
> **模式**: ARCHDEBT-REAL 第六例 (Phase 79 story-contracts + Phase 80 subplot + Phase 81 di + Phase 82 util + Phase 83 config + **Phase 84 workflow**)
> **引用模板**: `@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md` (I079 invariant enforced)

---

## §1. 背景

### §1.1 触发条件

Phase 83 ff-merge 后 master 已是 v54.15 (Phase 82 tip + Phase 83 work)，ARCHDEBT-CANDIDATES.md Top 5 全部闭环。

### §1.2 残留发现

本 phase 由「infra/tools/ 残留审查」触发 — Phase 41+++ mini audit (`docs/superpowers/infra-residual-audit.md`) 后 Phase 78 ARCHDEBT-MINI saturation (Phases 53-78 cluster) 处理了大部分，但 `infra/tools/workflow/lib/` 子目录有 12 active consumers (2 production + 4 tests + 4 monkeypatch + 2 docstring)，是 ARCHDEBT-REAL cycle 的自然下一步。

### §1.3 模式延续

Phase 79-83 全部为 ARCHDEBT-REAL 模式 (真迁移到 packages/)：
- Phase 79: story-contracts (LEAF, 10 symbols)
- Phase 80: subplot (NOT-LEAF, 15 symbols)
- Phase 81: di (TRUE LEAF, 8 symbols)
- Phase 82: util (NOT-LEAF, 6 symbols)
- Phase 83: config (TRUE LEAF + pyyaml, 1 symbol)
- **Phase 84: workflow (NOT-LEAF + lingwen-storage, 28 symbols)** ← NEW

---

## §2. 9-pattern 审计 (per N.14 lesson 1)

### §2.1 P1 — 字面 dotted-path imports

| Site | File | Line | Style |
|------|------|------|-------|
| Production | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/block_proceed.py` | 59 | function-body (`\s+from`) |
| Test | `tests/tools/workflow/test_checkpoints.py` | 14, 26, 36, 46, 64, 71, 89, 105, 114, 130, 158, 167 | function-body |
| Test | `tests/tools/workflow/test_events.py` | 15, 21 | function-body |
| Test | `tests/tools/workflow/test_state.py` | 58, 66, 73, 80, 87, 95+ | function-body |
| Test | `tests/tools/workflow/test_migration.py` | 14, 25, 33, 44, 53 | function-body |
| Test | `tests/tools/workflow/test_batch.py` | 12, 22, 33, 41, 50 | function-body |
| Test | `tests/tools/workflow/test_db.py` | TBD | function-body |
| Test | `tests/tools/workflow/test_tasks.py` | TBD | function-body |

**Verdict**: ~50 sites total (1 prod + ~49 test). sed with `\1` whitespace prefix per Phase 51 N.14 lesson 2.

### §2.2 P2 — 函数体内 indented imports

100% of test imports are function-body (lazy init pattern from conftest.py mock_env fixture). Production import in `block_proceed.py` is also function-body.

### §2.3 P3 — relative imports

**0 sites**. `lib/state.py:15` uses `from . import db, events` (legitimate intra-package relative). No pre-existing anti-pattern to fix.

### §2.4 P4 — filesystem path string literals

**1 site** (informational, not runtime path):
- `infra/tools/workflow/lib/__init__.py:10` docstring: "本包是从原 infra/tools/workflow/lib.py (814 行) 拆分而来"

No code-level filesystem path literal. Project uses `Path(__file__).parent.parent.parent.parent` in `db.py:14` (preserved as-is during migration — same depth works in `packages/lingwen-workflow/src/lingwen_workflow/db.py`).

### §2.5 P5 — wildcard imports

**0 sites**. `from X import *` not used.

### §2.6 P6 — monkeypatch indirection

| Site | File:Line | Target |
|------|-----------|--------|
| Tests | `tests/tools/workflow/conftest.py:33` | `infra.tools.workflow.lib.db.PROJECT_ROOT` |
| Tests | `tests/tools/workflow/conftest.py:34` | `infra.tools.workflow.lib.db.WORKFLOW_FILE` |
| Tests | `tests/tools/workflow/conftest.py:35` | `infra.tools.workflow.lib.db.DB_DIR` |
| Tests | `tests/tools/workflow/conftest.py:36` | `infra.tools.workflow.lib.db.DB_PATH` |
| Tests | `tests/tools/workflow/conftest.py:37` | `infra.tools.workflow.lib.db.LOCKFILE` |
| Tests | `tests/hooks/test_actions.py:490` | `infra.tools.workflow.lib.set_state` |
| Tests | `tests/hooks/test_actions.py:508` | `infra.tools.workflow.lib.set_state` |

**Verdict**: 7 sites. sed needs to handle both `infra.tools.workflow.lib.db.*` (conftest) and `infra.tools.workflow.lib.set_state` (test_actions).

### §2.7 P7 — `import X as Y` re-exports

**0 sites**. No aliased imports.

### §2.8 P8 — docstring / narrative references

| Site | File:Line | Quote |
|------|-----------|-------|
| Doc | `infra/tools/workflow/lib/__init__.py:10` | "本包是从原 infra/tools/workflow/lib.py (814 行) 拆分而来" |
| Test | `tests/tools/workflow/test_db.py:19` | "改的 infra.tools.workflow.lib.db.DB_PATH 不会反映到 lib.DB_PATH" |
| Test | `tests/tools/workflow/test_batch.py:1` | "Tests for infra.tools.workflow.lib.batch (batch_dispatch_writer, batch_dispatch_reviewer)" |
| Test | `tests/tools/workflow/test_state.py:1,3,7` | Docstring references to infra.tools.workflow.lib.* |

**Verdict**: 4 docstring sites. IN-PLACE update during C2 (not high priority but should fix for consistency).

### §2.9 P9 — prior-phase guard references

**0 sites** in active prior-phase test files. `test_phase53_p3_archdebt_dead_code_cleanup.py` doesn't reference infra.tools.workflow (only infra.tools.legacy/core/studio/etc which Phase 53 handled).

`test_phase18_8_infra_init_simplified.py` doesn't reference workflow either.

---

## §3. API surface (canonical 28 symbols)

From `infra/tools/workflow/lib/__init__.py` `__all__`:

| Category | Symbols | Source Module |
|----------|---------|---------------|
| Constants | `DB_DIR`, `DB_PATH`, `LOCKFILE`, `PROJECT_ROOT`, `WORKFLOW_FILE` | `db.py` |
| DB | `init_sqlite` | `db.py` |
| Locks | `_acquire_lock`, `_release_lock` | `db.py` |
| State | `advance_step`, `get_json`, `get_state`, `set_state` | `state.py` |
| Tasks | `dispatch_task`, `get_task_status`, `list_tasks`, `verify_task` | `tasks.py` |
| Checkpoints | `create_checkpoint`, `delete_checkpoint`, `list_checkpoints`, `restore_checkpoint` | `checkpoints.py` |
| Events | `_get_hook_engine`, `_trigger_event`, `trigger_event` | `events.py` |
| Batch | `batch_dispatch_reviewer`, `batch_dispatch_writer` | `batch.py` |
| Migration | `migrate_json_to_sqlite` | `migration.py` |

**Verdict**: 28 symbols, stable API surface preserved in canonical package `__all__`. No drift.

---

## §4. 配套 stale refs (per template §B)

### §4.1 `infra/__init__.py` wildcard

**0 wildcard**. `infra/__init__.py` has no `from infra.tools.workflow` re-export. No C3 cleanup needed.

### §4.2 ALLOWLIST / static lists

- None in current repo.

### §4.3 `__pycache__` residue

Per Phase 53d/78/79/80 lesson, C3 must `rm -rf infra/tools/workflow/lib/__pycache__/` to avoid G1 false-positive.

### §4.4 pre-C1 fixups (intra-package absolute imports)

`infra/tools/workflow/lib/__init__.py` uses `from .batch import ...` (relative — fine). No pre-C1 fixups needed.

---

## §5. Plan — 5-column commit table (per template §B)

| Commit | Subject | Files | +/- | Risk |
|--------|---------|-------|-----|------|
| **C0** | spec + 9-pattern audit | `docs/superpowers/specs/2026-09-15-phase-84-...md` (new) | +~250 / 0 | none |
| **C1** | scaffold `packages/lingwen-workflow/` (NOT-LEAF + 1 dep lingwen-storage) | `pyproject.toml` (root + new pkg) + `packages/lingwen-workflow/pyproject.toml` + `packages/lingwen-workflow/src/lingwen_workflow/__init__.py` + 7 module files copied | +1300 / 0 | low |
| **C2** | MIGRATE 1 prod consumer + 8 test files (per I079 §A5) + IN-PLACE rewrite 7 monkeypatch sites + 4 docstring fixes + conftest.py sys.path hack removal | `block_proceed.py` + `tests/tools/workflow/*` (8 files + conftest + __init__) + `tests/hooks/test_actions.py` | +50 / -50 | medium |
| **C3** | FULL DELETE infra/tools/workflow/lib/ + `__pycache__` + I085 NEW invariant | `infra/tools/workflow/lib/` (8 files) + `.lingwen/architecture.yml` + remove __pycache__ residue | +1 / -1500 | low (post-§A verification) |
| **C4** | prior-phase guards fixup (test_phase53d drop workflow from remaining_subdirs + test_phase18_8 docstring) — N.14 v22 lesson defense | `tests/test_phase53d_event_sourcing.py` + `tests/test_phase18_8_infra_init_simplified.py` | +5 / -3 | low |
| **C5** | 12 regression guards G1-G12 | `tests/test_phase84_p3_archdebt_workflow.py` (new) | +250 / 0 | low |
| **C6** | CLAUDE.md v54.16 + I085 row + CURRENT_STATUS + BACKLOG + handoff sync | `CLAUDE.md` + `collaboration/CURRENT_STATUS.md` + `collaboration/BACKLOG.md` + `docs/superpowers/handoffs/2026-09-15-phase-84-p3-archdebt-workflow-handoff.md` (new) | +200 / -3 | low |
| **C7** | uv.lock sync (systemic fix from Phase 83 lesson) | `uv.lock` | +12 / 0 | low (already proven pattern) |

**Total**: 8 atomic commits, +~2058 / -~1556 lines net (consolidating 28-symbol workflow lib into canonical package, deleting infra duplicate).

---

## §6. §A. test files migration plan (MANDATORY per template §A)

### §A.1 test files inventory

```
$ grep -rln "infra\.tools\.workflow\.lib" tests/
tests/hooks/test_actions.py
tests/tools/workflow/__init__.py
tests/tools/workflow/conftest.py
tests/tools/workflow/test_batch.py
tests/tools/workflow/test_checkpoints.py
tests/tools/workflow/test_db.py
tests/tools/workflow/test_events.py
tests/tools/workflow/test_migration.py
tests/tools/workflow/test_state.py
tests/tools/workflow/test_tasks.py
```

| File | LOC | MIGRATE / DELETE / RETAIN |
|------|-----|---------------------------|
| `tests/hooks/test_actions.py` (2 patch sites) | ~600 | **IN-PLACE rewrite** (test file has many other concerns; only 2 patches need rewrite) |
| `tests/tools/workflow/__init__.py` | ~10 | **MIGRATE** |
| `tests/tools/workflow/conftest.py` | ~80 | **MIGRATE** (also drop sys.path hack — Phase 56b lesson 1) |
| `tests/tools/workflow/test_batch.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_checkpoints.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_db.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_events.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_migration.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_state.py` | TBD | **MIGRATE** |
| `tests/tools/workflow/test_tasks.py` | TBD | **MIGRATE** |

**Total**: 9 files MIGRATE to `packages/lingwen-workflow/tests/` + 1 IN-PLACE rewrite (`tests/hooks/test_actions.py`).

### §A.2 MIGRATE 路径

- **目标位置**: `packages/lingwen-workflow/tests/<test-file>.py`
- **迁移步骤**: `git mv tests/tools/workflow/<file>.py packages/lingwen-workflow/tests/<file>.py` (single C2 commit, pathspec BOTH old + new for blame preservation — Phase 56c lesson 1)
- **Imports 迁移**: `from infra.tools.workflow.lib` → `from lingwen_workflow` (sed 全 file)
- **sys.path hack cleanup**: 删除 `tests/tools/workflow/conftest.py:13-14` `PROJECT_ROOT = Path(__file__).parent.parent.parent.parent; sys.path.insert(0, str(PROJECT_ROOT))` (Phase 56b lesson 1) — 不再需要因为 lingwen_workflow 通过 uv workspace editable install 可用
- **cwd-relative path**: `lib_module.sys = sys` (conftest.py:43) — 保留 (lib.db.PROJECT_ROOT monkeypatch 仍指向同一个 infra 路径直到 C3, C3 后删除)
- **Functional gate**: `pytest packages/lingwen-workflow/tests/ -v` 必须 100% pass (C5 gate)

### §A.3 DELETE 路径

N/A — all test files are MIGRATE.

### §A.4 RETAIN-ORPHAN 路径

**0 sites**. No orphan tests allowed (per template §A.4 strong recommendation).

### §A.5 Half-migration defense (per template §A.5)

- ✅ **C2 commit pathspec 含 BOTH** `infra/tools/workflow/lib/` source files + `tests/tools/workflow/` test files MIGRATE (single commit, blame preserved)
- ✅ **C3 (FULL DELETE) commit pathspec 含 BOTH** `infra/tools/workflow/lib/` source files + `__pycache__/` residue cleanup
- ✅ **C3 commit message 必须包含**: "infra/tools/workflow/lib/ + tests/tools/workflow/ + I085 invariant + __pycache__ residue" (single sentence summary)
- ✅ **验证**: `git show <C3-SHA> --stat` 必须显示 8 source files 在 deletions + __pycache__ removed

---

## §7. 验证 gates (per template §B)

| Gate | Command | Expected |
|------|---------|----------|
| pytest functional | `pytest packages/lingwen-workflow/tests/ -v` | 100% pass (expected ~30-40 tests) |
| pytest lingwen-pipeline regression | `pytest packages/lingwen-pipeline/tests/ -v` | 100% pass (block_proceed.py migrated) |
| ruff | `ruff check packages/lingwen-workflow/ packages/lingwen-pipeline/ tests/tools/workflow/ tests/hooks/test_actions.py` | clean |
| 9-pattern audit | `grep -rn "infra\.tools\.workflow" --include="*.py" apps/ packages/ tests/ tools/` | 0 hits (except archive) |
| Phase 84 regression guards | `pytest tests/test_phase84_p3_archdebt_workflow.py -v` | 12/12 PASS |
| Phase 53d/18_8/77/60 prior-phase | `pytest tests/test_phase53d_event_sourcing.py tests/test_phase18_8_infra_init_simplified.py tests/test_phase77_architecture_invariant_sync.py tests/test_phase60_p3_archdebt_template.py -v` | All preserved |
| Phase 79-83 ARCHDEBT-REAL guards | `pytest tests/test_phase79_p3_archdebt_story_contracts.py tests/test_phase80_p3_archdebt_subplot.py tests/test_phase81_p3_archdebt_di.py tests/test_phase82_p3_archdebt_util.py tests/test_phase83_p3_archdebt_config.py -v` | All preserved |

---

## §8. 风险评估 (per template §B)

| 风险 | 等级 | 缓解 |
|------|------|------|
| `tests/tools/workflow/` MIGRATE 9 files 时 git blame 丢失 | medium | single C2 commit with BOTH pathspec per Phase 56c lesson 1 |
| `conftest.py` sys.path hack 残留破坏 pytest collection | low | Phase 56b lesson 1: explicit removal in C2 |
| `tests/hooks/test_actions.py` 2 patch indirection sites 漏掉 | medium | §2.6 listed all 7 monkeypatch sites (5 conftest + 2 test_actions) — comprehensive C2 audit |
| `infra/tools/workflow/lib/state.py` `from . import db, events` 在新 package location 仍正确 | low | relative imports keep working regardless of new parent dir name |
| `lingwen_storage.sqlite_storage_adapter` 5 lazy imports 在新 package location 仍工作 | low | workspace dep unchanged |
| `__pycache__` residue after C3 | low | explicit `rm -rf infra/tools/workflow/lib/__pycache__/` per Phase 78 lesson |
| run_workflow.sh 残留 (1 ref to lib/) | low | OUT OF SCOPE for Phase 84 — Phase 86 ARCHDEBT-MINI will handle |
| I085 invariant grammar / scope (Phase 60 orphan bug recurrence) | low | explicit parsed-value test in Phase 77 G3 family + Phase 60 template enforces |

---

## §9. 不在范围 (per template §B)

- ❌ `infra/tools/workflow/{run_workflow.sh,logging.sh}` — shell scripts, Phase 86 ARCHDEBT-MINI scope (alongside other dead shell scripts)
- ❌ `infra/tools/consistency/` (Phase 85 ARCHDEBT-REAL candidate — separate spec)
- ❌ `infra/tools/{check_stale_tasks.py,issue_tracker.py,migrate_to_sqlite.py,regression_tracker.py,heartbeat.py}` — top-level zero-consumer CLI tools, Phase 86 ARCHDEBT-MINI scope
- ❌ `infra/tools/publish/` + `infra/tools/content/` shell scripts — Phase 86 scope
- ❌ `tools/workflow/{restore_sqlite.sh,revert_to_json.sh}` — Phase 54 era stale shell scripts, Phase 86 scope

---

## §10. 完工标准 (per template §B)

- [ ] C0 spec committed with `@template:` reference + §A plan
- [ ] C1 scaffold creates 9 files (pyproject + 8 modules)
- [ ] C2 MIGRATE 1 prod + 9 test files + IN-PLACE rewrite 7 monkeypatch + 4 docstring + conftest sys.path hack removed
- [ ] C3 FULL DELETE infra/tools/workflow/lib/ + __pycache__ + I085 NEW (atomic, pathspec verified)
- [ ] C4 prior-phase guards fixup (test_phase53d + test_phase18_8 — N.14 v22 defense)
- [ ] C5 12 regression guards G1-G12 (functional pytest gate + I085 in architecture.yml + no infra refs)
- [ ] C6 CLAUDE.md v54.16 + I085 row + handoff doc sync
- [ ] C7 uv.lock sync (systemic lesson from Phase 83 — runs at C7 not C3)
- [ ] All 7 validation gates GREEN
- [ ] 0 ruff errors
- [ ] 0 9-pattern audit hits
- [ ] No test file left as orphan (per §A.5)

---

## §11. Lessons from prior phases (per template §C)

**Phase 79** (story-contracts): LEAF pattern + 5 test files MIGRATE
**Phase 80** (subplot): NOT-LEAF pattern + intra-package absolute imports `infra.subplot.X` pre-C1 fixup → `lingwen_subplot.X`
**Phase 81** (di): TRUE LEAF + 14 pre-existing failures baseline
**Phase 82** (util): NOT-LEAF + `lingwen_util/__init__.py` intra-package absolute import (infra.util.retry → lingwen_util.retry) C3.5 fixup lesson
**Phase 83** (config): TRUE LEAF + pyyaml third-party dep + uv.lock systemic carryover (4 missing packages)
**Phase 56b/56c/57b** (3rd recurrence): test files MUST MIGRATE in same phase, NOT defer

---

## §12. Anti-patterns (per template §D)

- ❌ 在 C2 MIGRATE 用 `git rm` + `git add` (分开 commit, blame 丢失) — single commit pathspec BOTH required
- ❌ 留下 `tests/tools/workflow/` orphan after C3 — `git mv` then sed rewrite then C3
- ❌ C3 跳过 `__pycache__` 清理 — Phase 78/79/80/82 lesson
- ❌ 漏掉 monkeypatch indirection (P6) — `infra.tools.workflow.lib.X` 在 conftest.py 和 test_actions.py 都出现
- ❌ 漏掉 docstring 引用 (P8) — 4 sites in test docstrings
- ❌ 假设 lingwen-storage 自动可用 — pyproject.toml workspace dep declaration mandatory in C1
- ❌ "defer test migration to followup" — Phase 56c lesson 3: defer = never