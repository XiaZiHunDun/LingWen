# Phase 78 — P3-ARCHDEBT llm_benchmarks + poc dead code cleanup

> **Phase**: 78 (ARCHDEBT-MINI cleanup)
> **Branch**: `phase-57-p3-archdebt-reading-power` (continuing work)
> **承接**: Phase 77 (`d70cede2`, v54.9 architecture invariant sync) — Phase 52 audit `infra-subdir-audit.md` 剩余 low-priority subdirs long-tail cleanup
> **目标**: 删除 2 个零生产消费者子目录 + 配套 test files + 4 处 stale 引用 + I074 扩展为 8 目录
> **预计**: ~1854 LOC dead code (9 source files + 8 test files + config entries), 4 atomic commits, v54.9 → v54.10

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

---

## 1. 背景

Phase 77 (`d70cede2`, 2026-09-14) 闭环了 v54.8 carryover (architecture.yml missing I071-I078 + I079 orphan-scope bug)。Phase 78 是 v54.8 era 后的第一个 **next-actionable** phase。

**触发**: `docs/superpowers/infra-subdir-audit.md` Phase 52 audit 识别出 21 个 infra/ 子目录中 5 个是 dead code 候选。其中:
- `infra/tools/legacy/` (4976 LOC) — Phase 53b/53c 闭环
- `infra/event_sourcing/` (992 LOC) — Phase 53d 闭环
- `infra/core/` + `infra/studio/` + `infra/novel-factory/` — Phase 39 + 40 + 53e 闭环

**未闭环的 2 个**:
- `infra/llm_benchmarks/` (751 LOC) — Phase 52 audit 标 "基准测试" (低 ROI)
- `infra/poc/` (439 LOC) — Phase 52 audit 标 "POC 验证代码 — 可能全 dead"

**Phase 52 audit §3 "低优先级建议" 明确指出**:
> 立即可执行 (本期 Phase 53 预告): 删 `infra/poc/` (审计后, 可能 439 LOC)

后续 Phase 53 + 53b/c/d/e + 54 + 55 + 56 + 57 + 57b 优先处理了 P3-ARCHDEBT 真迁移（persistence/cross_volume/world_db/reading_power）和 ARCHDEBT-MINI cleanup，但 `llm_benchmarks` + `poc` long-tail 一直 defer。

## 2. 9-pattern 审计结果 (per N.14 lesson 1)

### 2.1 `infra/llm_benchmarks/`

| # | Pattern | Verdict | 详情 |
|---|---------|---------|------|
| 1 | Literal dotted-path imports `infra.llm_benchmarks` | ✅ ZERO production | grep -rln 仅 intra-package + tests + architecture.yml |
| 2 | Indented/function-body imports | ✅ ZERO | 无 |
| 3 | Relative imports | ✅ ZERO | intra-package only |
| 4 | Filesystem path string literals | ⚠️ 1 site (safe) | `.gitignore:247` `infra/llm_benchmarks/results/` (gitignore 自身要删) |
| 5 | Wildcard imports `from X import *` | ✅ ZERO | 无 |
| 6 | `monkeypatch.setattr` / `patch` indirection | ✅ ZERO | 无 |
| 7 | `import X as Y` re-exports | ⚠️ 1 (architecture) | `.lingwen/architecture.yml:280-287` llm_benchmarks entry (要删) |
| 8 | Doc comments referencing old path | ✅ ZERO production | 仅 handoff/audit docs (历史存档) |
| 9 | Prior-phase guard hardcoded representative | ⚠️ 2 sites | `tests/test_phase53d_event_sourcing.py:152` docstring + `:168` preserved list (要 update) |

**Production consumers**: **0** (none)
**Test consumers**: 6 files in `tests/infra/llm_benchmarks/` (570 LOC, all exclusively test `infra.llm_benchmarks.X` symbols)
**Architecture consumers**: 1 entry (`.lingwen/architecture.yml:280-287`)
**Gitignore consumers**: 1 line (`.gitignore:247`)

### 2.2 `infra/poc/`

| # | Pattern | Verdict | 详情 |
|---|---------|---------|------|
| 1 | Literal dotted-path imports `infra.poc` | ✅ ZERO production | only `tests/poc/test_end_to_end.py` |
| 2 | Indented/function-body imports | ⚠️ 1 site (test) | `tests/poc/test_end_to_end.py:22,28,36,43,49,59,69,78,88` (function-body lazy import, Phase 57b lesson 6 闭环) |
| 3 | Relative imports | ⚠️ 1 (intra-pkg) | `infra/poc/__init__.py:5` `from .run_volume_1 import` |
| 4 | Filesystem path string literals | ⚠️ 1 site (safe) | `tests/test_phase35_world_model.py:264` `REPO_ROOT / "infra" / "poc" / "run_volume_1.py"` (early-return guard, safe) |
| 5 | Wildcard imports | ✅ ZERO | 无 |
| 6 | `monkeypatch.setattr` / `patch` indirection | ✅ ZERO | 无 |
| 7 | `import X as Y` re-exports | ✅ ZERO production | 无 |
| 8 | Doc comments referencing old path | ⚠️ 1 site (historical) | `docs/superpowers/infra-subdir-audit.md:18,124,133,153` (历史 audit doc, no functional impact) |
| 9 | Prior-phase guard hardcoded representative | ✅ ZERO | test_phase53d_event_sourcing.py 不 list poc (audit-only doc 提及) |

**Production consumers**: **0** (none)
**Test consumers**: 1 file `tests/poc/test_end_to_end.py` (94 LOC, exclusively tests `infra.poc.run_volume_1`)
**Architecture consumers**: 0 (not in architecture.yml)
**Gitignore consumers**: 0

### 2.3 配套 stale refs

| Site | 内容 | Action |
|------|------|--------|
| `.lingwen/architecture.yml:280-287` | llm_benchmarks full entry | DELETE |
| `.gitignore:247` | `infra/llm_benchmarks/results/` | DELETE |
| `tests/test_phase53d_event_sourcing.py:152` | docstring "config / di / llm_benchmarks / poc / story_contracts / subplot / tools / util" | UPDATE → drop llm_benchmarks/poc |
| `tests/test_phase53d_event_sourcing.py:168` | `remaining_subdirs = [..., "llm_benchmarks", "poc", ...]` | UPDATE → drop llm_benchmarks/poc from preserved list |
| `tests/test_phase35_world_model.py:263-264` | `def test_poc_consumer_migrated(): p = REPO_ROOT / "infra" / "poc" / "run_volume_1.py" if not p.exists(): return` | KEEP (early-return guard auto-handles Phase 78 deletion) |

### 2.4 Doc 历史 references (no functional impact, leave alone)

| File | Lines | Why leave |
|------|-------|-----------|
| `docs/superpowers/infra-subdir-audit.md` | 18, 124, 133, 153 | Phase 52 historical audit doc — append Phase 78 closure note at top |
| `docs/superpowers/handoffs/2026-09-12-phase-58-defect-closure-handoff.md` | 36, 64, 67 | Historical handoff — leave (commit blame protection) |
| `docs/superpowers/specs/2026-08-26-phase-120-llm-provider-benchmark-design.md` | (full) | Source spec — historical, leave |
| `docs/superpowers/plans/2026-08-10-phase16.7-discovery-and-decision.md` | (full) | Historical plan — leave |
| `docs/superpowers/plans/2026-08-26-phase-120-llm-provider-benchmark.md` | (full) | Historical plan — leave |

## 3. 计划 (4 atomic commits)

| Commit | Subject | Files | +/- | Risk |
|--------|---------|-------|-----|------|
| **C0** | `docs(phase-78): spec + 9-pattern audit` | 1 file | +200 | LOW (doc-only) |
| **C1** | `chore(archdebt): git rm infra/llm_benchmarks + tests + infra/poc + tests` (pathspec BOTH infra + tests per §A5) | 4 dirs (17 files) | -1854 | MEDIUM (large deletion; A5 defense: pathspec includes BOTH infra + tests per §A) |
| **C2** | `chore(archdebt): update test_phase53d + .lingwen/architecture.yml + .gitignore + I074 extension` (4 stale refs cleanup) | 4 files | ±10 | LOW |
| **C3** | `test(phase-78): 10 regression guards (G1-G10) for llm_benchmarks/poc deletion` | 1 file | +200 | LOW (test-only) |
| **C4** | `docs(phase-78): CURRENT_STATUS + BACKLOG + handoff sync + I074 doc update` | 4 files | +300 | LOW (doc-only) |

**Total: 5 atomic commits**, version v54.9 → **v54.10** (long-stale version bump reflecting ARCHDEBT-MINI cluster cumulative)

## 4. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

| Source file | LOC | Consumers | Plan |
|------------|-----|-----------|------|
| `tests/infra/llm_benchmarks/__init__.py` | 1 | (self) | **DELETE** (only service infra/llm_benchmarks) |
| `tests/infra/llm_benchmarks/test_fixtures.py` | 44 | `infra.llm_benchmarks.fixtures` | **DELETE** |
| `tests/infra/llm_benchmarks/test_metrics.py` | 203 | `infra.llm_benchmarks.metrics` | **DELETE** |
| `tests/infra/llm_benchmarks/test_providers.py` | 48 | `infra.llm_benchmarks.providers` | **DELETE** |
| `tests/infra/llm_benchmarks/test_render.py` | 56 | `infra.llm_benchmarks.render` | **DELETE** |
| `tests/infra/llm_benchmarks/test_results.py` | 72 | `infra.llm_benchmarks.results` | **DELETE** |
| `tests/infra/llm_benchmarks/test_run.py` | 52 | `infra.llm_benchmarks.run` | **DELETE** |
| `tests/poc/__init__.py` (N/A — no __init__.py) | 0 | n/a | n/a |
| `tests/poc/test_end_to_end.py` | 94 | `infra.poc.run_volume_1` | **DELETE** |

**Total DELETE**: 9 test files, ~570 LOC (`tests/infra/llm_benchmarks/` 570 LOC + `tests/poc/` 94 LOC, no `tests/poc/__init__.py` exists per audit)

### A2. MIGRATE 路径

**None** — all test files exclusively service deleted infra/X/ modules with NO cross-cutting value.

### A3. DELETE 路径

Per A1, all 9 test files are DELETE.

- ✅ Each test file imports ONLY from `infra.llm_benchmarks.X` or `infra.poc.run_volume_1` (verified via `grep -h "from infra" tests/infra/llm_benchmarks/*.py tests/poc/*.py | sort -u`)
- ✅ No `monkeypatch.setattr` indirection (Phase 57b N.14 lesson 6 verified)
- ✅ No cross-package fixtures / shared conftest / Path("infra/llm_benchmarks") cross-deps

### A4. RETAIN-ORPHAN 路径

**None** — no justification for leaving test files at tests/X/ while infra/X/ deleted (Phase 56c lesson 3 explicit "defer = never" anti-pattern).

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

**C1 pathspec MUST include BOTH `infra/X/` AND `tests/X/<test-files>`**:

```bash
git rm -r infra/llm_benchmarks/ infra/poc/ tests/infra/llm_benchmarks/ tests/poc/
```

Single `git rm -r` command covers all 4 directories. Single C1 commit ensures git tracks all deletions atomically (Phase 56c lesson 1).

**C1 commit message MUST explicitly list**:
> "deleted infra/llm_benchmarks (7 files, 751 LOC) + tests/infra/llm_benchmarks (7 files, 570 LOC) + infra/poc (2 files, 439 LOC) + tests/poc/test_end_to_end.py (1 file, 94 LOC); extended I074 invariant (Phase 78 ARCHDEBT-MINI dead code cleanup); total -1854 LOC across 17 files in 4 dirs"

**Verification**:
- `git show <C1-SHA> --stat | grep -c "^.*deleted"` MUST show 17 file deletions
- `git show <C1-SHA> --stat | grep -E "(infra/(llm_benchmarks|poc)/|tests/(infra/llm_benchmarks|poc)/)"` MUST list ALL 4 directories

## 5. 验证 gates

| Gate | Description | Pass criteria |
|------|-------------|---------------|
| **ruff** | `ruff check infra/ tests/ apps/ packages/ .` | 0 new errors (Phase 53c baseline preserved) |
| **Phase 77 guards** | `pytest tests/test_phase61_architecture_invariant_sync.py tests/test_phase53d_event_sourcing.py tests/test_phase35_world_model.py` | 12 + 10 + ... preserved |
| **Phase 78 guards** | `pytest tests/test_phase78_archdebt_llm_benchmarks_poc.py` | 10/10 GREEN |
| **9-pattern audit** | `grep -rln "infra\.llm_benchmarks\|infra\.poc" --include="*.py" .` | 0 hits (excluding test_phase78 itself) |
| **Functional gate** | `pytest apps/studio_api/tests/ packages/lingwen-core/tests/ packages/lingwen-got/tests/ packages/lingwen-world-model/tests/ -v` | baseline preserved (no new failures) |

## 6. 风险评估

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Prior-phase guard false-positive on `test_phase53d` `remaining_subdirs` list | **HIGH** (已知 Phase 53d N.14 lesson 1 v22 variant) | C2 explicitly updates the preserved list BEFORE running Phase 78 guards |
| `test_phase35_world_model.py:264` `test_poc_consumer_migrated` early-return fails on file-missing state | LOW (early-return `if not p.exists(): return` already handles this) | Verified — no fixup needed |
| `.gitignore` `infra/llm_benchmarks/results/` orphan | LOW (no `infra/llm_benchmarks/results/` dir exists) | C2 removes `.gitignore:247` line |
| Architecture invariant drift — Phase 78 deletes llm_benchmarks but I074 doesn't cover it | MEDIUM | C2 extends I074 rule text |
| User-visible regression (anything depended on infra.llm_benchmarks or infra.poc) | LOW (zero production consumers verified by 9-pattern audit) | Phase 78 takes defensive measurement: `git grep` audit pre-C1 |

## 7. 不在范围 (deferred / not this phase)

- ❌ **Not touching**: `infra/story_contracts/` (848 LOC, 8 consumers) — NOT-LEAF P3-ARCHDEBT, needs proper package migration (Phase 79+ candidate)
- ❌ **Not touching**: `infra/subplot/` (508 LOC, 10 consumers) — same as above
- ❌ **Not touching**: `infra/util/` (338 LOC) — active via `infra/__init__.py` exports
- ❌ **Not touching**: `infra/di/` (309 LOC) — active via `tests/test_infra_modules.py::TestDI`
- ❌ **Not touching**: `infra/config/` (77 LOC) — active via `infra/__init__.py` + tools
- ❌ **Not touching**: `infra/tools/` (subdirs workflow/consistency/legacy all Phase 53-53c closed; remaining is just infra/tools/ root)
- ❌ **Not touching**: Historical doc references in `infra-subdir-audit.md` + handoffs (commit blame protection)

## 8. Lessons from prior phases (per I079 §C reference)

- **Phase 53c (top-level tools/legacy/)**: same pattern — dead code + tests cleanup, 5 atomic commits, 26 guards, I074 cluster invariant
- **Phase 53d (event_sourcing/)**: 4 commits, 7 guards, 992 LOC; demonstrated `test_phase53d_event_sourcing.py` orphan watch pattern (now Phase 53d G5 preserves canonical infra/ subdirs)
- **Phase 53e (orphan runtime artifacts)**: `infra/.state/*.json.lock` + `infra/novel-factory/agent_system/relationship_network.json` (61 bytes empty JSON), 2 new .gitignore patterns
- **Phase 56b/56c/57b (test-migration 3x recurrence)**: all 3 phases had test files left orphan after `infra/X/` deletion. Phase 78 implements **preemptive §A plan** to delete both atomically
- **N.14 lesson 1 (9-pattern audit matrix)**: v22 variant — prior-phase guard hardcoded representative files (`test_phase53d` preserved list)

## 9. Anti-patterns (must NOT do) — per I079 §D

- ❌ C1 commit message 只写 "deleted dead code" 而不列具体 dirs/files (Phase 56c lesson 1)
- ❌ 用 `git rm` 旧路径 + `git add` 新路径 (分开 commit, blame 丢失) — Phase 78 zero new paths, all DELETE, no split risk
- ❌ Spec 缺 §A test files migration plan (本 template 强制) — Phase 78 §4 has full A1-A5
- ❌ "defer test migration to followup" — Phase 78 C1 pathspec covers BOTH infra + tests atomically
- ❌ Skip prior-phase guard update (`test_phase53d` preserved list) — C2 fixes this

## 10. 完工标准

- [ ] C0 spec doc committed
- [ ] C1 git rm 4 directories committed (pathspec includes BOTH infra + tests per §A5)
- [ ] C2 prior-phase guards + architecture.yml + .gitignore + I074 extension committed
- [ ] C3 10 regression guards committed (G1-G10)
- [ ] C4 CURRENT_STATUS + BACKLOG + handoff + MEMORY sync committed
- [ ] All 5 commits ff-merged to master
- [ ] v54.10 version bump applied to CLAUDE.md + architecture.yml
- [ ] Phase 78 handoff `docs/superpowers/handoffs/2026-09-14-phase-78-archdebt-llm-benchmarks-poc-handoff.md` written
- [ ] MEMORY.md `phase-78-archdebt-llm-benchmarks-poc.md` topic file created

---

**Estimated**: 5 commits × 5-15 min = ~1 hour. Phase 78 + 53d + 53c + 53e + 53b ARCHDEBT-MINI cluster total ≈ 17,000 LOC dead code eliminated from infra/.
