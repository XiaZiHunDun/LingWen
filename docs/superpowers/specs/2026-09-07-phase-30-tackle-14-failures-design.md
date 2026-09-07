# Phase 30 — TACKLE-14-FAILURES Design

> **Branch:** `worktree-phase-30-tackle-14`
> **Date:** 2026-09-07
> **Baseline:** master `2de95a80` (v29.0 P2-MC-WRITING 收尾 + state sync)
> **Goal:** Close the 14 remaining pre-existing failures in `tests/agent_system` (categorized in `docs/superpowers/handoffs/2026-09-04-phase-29-mc-writing-handoff.md`) so the directory reaches 0 failed / 480+ passed / 20 skipped baseline.

---

## Background

v29.0 P2-MC-WRITING reduced `tests/agent_system` from 84 → 14 failed. The remaining 14 are not stale imports or wrong-path tests — they trace to **5 distinct root causes**, all pre-dating Phase 29:

| Root cause | Test count | Surface |
|---|---|---|
| (A) `MasterController.__new__()` stubs miss `_state` initialization | 7 | Test-only (stub factory) |
| (B) `_collect_decision_specs_from_graph` missing re-export | 1 | Test-only (test migration) |
| (C) `_impl_audit_chapter` lacks try/except resilience | 2 | **Real prod contract** (mc_writing.py) |
| (D) `CostTrackerDB._connect()` removed by v16.5 #N.3 | 2 | Test-only (with new prod helper) |
| (E) `MasterController()` no-args requires API key env vars | 2 | Test-only (use `make_master_with_router`) |

All 5 are well-defined and bounded; total scope ~30 lines of prod changes + ~50 lines of test rewrites.

---

## Design decisions

### T1 — Stub factory `_state` injection (test-only)

`_make_controller_with_stubs()` in both `test_decision_integration.py:30` and `test_master_controller_workflow.py` uses `MasterController.__new__(MasterController)` to bypass `__init__`. The Phase 26 v26.0 P2-WFSTATE refactor moved `_last_*` fields into `self._state: WorkflowState` (set on `master_controller.py:111`). When `WorkflowRunner.run()` reads `controller._state.with_updates(...)` (workflow_runner.py:79), it raises `AttributeError`.

**Decision:** Add `controller._state = WorkflowState.empty()` immediately after `__new__()` in both stub factories. One-line fix each.

**Alternative considered:** Guard `workflow_runner.py:79` against missing `_state`. Rejected — this would hide future stubs that forget to init `_state`, undermining the v26.0 refactor guard.

### T2 — `_collect_decision_specs_from_graph` export (test-only)

`test_decision_integration.py:330` imports `_collect_decision_specs_from_graph` from `lingwen_pipeline.master_controller`, but production inlined the helper into `mc_workflow._harvest_decision_specs` (v25.9 P2-HUMAN-REVIEW refactor).

**Decision:** Migrate the test to call `mc_workflow._harvest_decision_specs` directly. Less surface area than re-exporting a helper that's intentionally inlined.

### T3 — `_impl_audit_chapter` resilience (real prod contract)

`mc_writing.py:155-178` (`_impl_audit_chapter`) has no try/except on the `record_usage=True` path. Test `test_master_controller_with_usage.py:167` asserts (with docstring-documented contract):

> 韧性契约: audit LLM 抛错 → try/except 兜底返正常 audit report, usage 0.
> 跟 record_usage=False 路径语义一致 — audit 失败非致命, 规则检查结果保留,
> workflow 不中断 (跟 test_audit_chapter_failure_does_not_crash_workflow 一致).

Test `test_phase7_1_production_fixes.py:112` asserts the same contract for `record_usage=False` path (audit failures don't crash workflow).

**Decision:** Wrap both `record_usage=True` and `record_usage=False` paths in try/except. On exception: return `({"issues": [], "suggestions": []}, {"input_tokens": 0, "output_tokens": 0})` (or `{"issues": [], "suggestions": []}` for the no-usage path). Log a warning so the failure isn't silent.

**Resilience boundary:** Catch **broad** (`Exception`) because:
- LLM exceptions (502, timeout, rate limit) need swallowing
- Programming errors (TypeError, AttributeError from LLM library shape changes) — these were also caught historically per `test_phase7_1_production_fixes.py:113-117` docstring ("修复前: llm_audit AttributeError 被 master.audit_chapter except 吞")
- Workflow non-interruption is the contract — narrow except (`requests.RequestException`) would miss LLM-library-specific exceptions

**Why not just `record_usage=True`:** Test `test_phase7_1_production_fixes.py:112` covers `record_usage=False` (audit failure in `run_workflow` path). Both paths must be wrapped.

### T4 — `CostTrackerDB._connect()` migration (test + tiny prod helper)

`test_cost_persistence.py:209,249` calls `db._connect()` (private context-manager API) to insert records with specific timestamps. The v16.5 #N.3 migration to `SqliteStorageAdapter` removed `_connect`; the test wasn't migrated.

**Decision:** Add a public `record_at(timestamp, scenario, tier, in, out)` method on `CostTrackerDB`. It's a real additive API (useful for seeding historical data, migrations, restoring backups) — not just for tests. Then rewrite the 2 tests to call `db.record_at(...)` instead of `db._connect()`.

**Why not expose `with_transaction(fn)` directly on `CostTrackerDB`:** That would leak the storage abstraction. `record_at` is the right semantic API.

### T5 — env-var tests rewrite (test-only)

`test_master_controller.py:55,89` constructs `MasterController()` with no args, which triggers `load_default_config()` requiring `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `MINIMAX_API_KEY` (per `agent_config.py:130`). When all three are unset, it raises "No AI provider configured".

**Decision:** Rewrite both tests to use `make_master_with_router()` (from `tests/agent_system/_e2e_helpers.py:110`) which injects a stub router. The other tests in the same file already use this pattern.

**Alternative considered:** Set `OPENAI_API_KEY=stub` env var in conftest. Rejected — `make_master_with_router()` is the established pattern and the test intent is to test `MasterController` behavior, not config loading.

---

## What is NOT in scope

- **P2-ARCHDEBT** (`infra.got.*` migration, `chapter_golden_path.py` reverse-import fix, 5 thin proxies → `OrchestratorProxyMixin`, PHASE-COMPAT shim deletion). Deferred to Phase 31+.
- **Phase 114 prod preview regression** (accepted debt, do NOT attempt).
- **Re-exposing `_connect` on `CostTrackerDB`** (rejected in T4).
- **Re-exporting `_collect_decision_specs_from_graph` from `lingwen_pipeline.master_controller`** (rejected in T2).

---

## Expected gates after Phase 30

| Gate | Baseline (v29.0) | Phase 30 final | Delta |
|------|-------------------|----------------|-------|
| G1 `tests/agent_system` failed | 14 | **0** | -14 |
| G1 `tests/agent_system` passed | 466 | **480+** | +14 |
| G1 `tests/agent_system` skipped | 20 | 20 | 0 |
| G2 `tests/got` passed | 156 | 156 | 0 |
| G3a `packages/lingwen-core/tests/` passed | 68 | 68 | 0 |
| G3b `ruff check packages/lingwen-core/src/lingwen_core/agents/` | clean | clean | 0 |

---

## Risk assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| T3 try/except swallows a programming error that should propagate | Low | Log warning with `logger.warning(...)` so ops can see; both test docstrings document the broad-catch contract |
| T4 `record_at` API naming clutters the surface | Very low | Real use case (seeding, migration, restore) — not a test-only shim |
| Stub factory change breaks other tests that share the helper | Low | The 7 failing tests are the only consumers; grep confirms no other callers |
| `_harvest_decision_specs` signature drift between `mc_workflow` and the test's expected args | Low | Test already calls it with the right signature in test setup; just need to swap the import target |

---

## Out-of-scope followups (carryover to Phase 31+)

Same as Phase 29 carryover (P2-ARCHDEBT) plus any new contract gaps discovered during Phase 30 implementation.