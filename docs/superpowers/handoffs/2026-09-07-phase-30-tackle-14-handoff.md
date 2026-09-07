# Phase 30 — TACKLE-14-FAILURES Handoff

> **Branch:** `worktree-phase-30-tackle-14` (8 commits ahead of `master`)
> **Date:** 2026-09-07
> **Spec:** `docs/superpowers/specs/2026-09-07-phase-30-tackle-14-failures-design.md`
> **Plan:** `docs/superpowers/plans/2026-09-07-phase-30-tackle-14-failures.md`
> **Goal:** Close the 14 remaining pre-existing failures from v29.0 P2-MC-WRITING baseline so `tests/agent_system` reaches 0 failed.

---

## Final verification gates

| Gate | Command | v29.0 baseline | Phase 30 final | Delta |
|------|---------|----------------|----------------|-------|
| G1 (`tests/agent_system` full) | `.venv/bin/python -m pytest tests/agent_system -q --tb=no` | **14 failed, 466 passed, 20 skipped** | **0 failed, 480 passed, 20 skipped** | **-14 / +14 / 0** |
| G2 (`tests/got`) | `.venv/bin/python -m pytest tests/got -q --tb=no` | 156 passed | 156 passed | 0 |
| G3a (`packages/lingwen-core/tests/`) | `.venv/bin/python -m pytest packages/lingwen-core/tests/ -q` | 68 passed | 68 passed | 0 |
| G3b (ruff) | `ruff check packages/lingwen-core/src/lingwen_core/agents/` | clean | clean | 0 |

**Net result: -14 failed (14 → 0).** All other gates unchanged. No new failures introduced.

---

## Phase 30 commit log (T1–T5 + docs)

| Task | Commit | Subject | Type | Effect |
|------|--------|---------|------|--------|
| Design | `3f07c532` | docs: design phase 30 tackle-14-failures | docs | n/a |
| Plan | `910d3454` | docs: phase 30 implementation plan | docs | n/a |
| T1 | `4d298d6a` | test(stub-factory): inject WorkflowState.empty() after __new__() bypass | test-only | -7 failures |
| T5 | `4030a43c` | test(master-controller): use make_master_with_router() instead of bare MasterController() | test-only | -2 failures |
| T4 | `9f2322ad` | feat(cost-persistence): add record_at() public helper for explicit-timestamp inserts | test + tiny prod | -2 failures |
| T2 | `04906367` | test(decision-integration): migrate to WorkflowRunner._harvest_decision_specs | test-only | -1 failure |
| T3 | `acd8e013` | fix(audit-chapter): add try/except resilience for LLM failures | real prod + 1 test assertion fix | -2 failures |

**Total cleared: 14 of 14 baseline failures.**

---

## Files touched (7 source files + 2 docs)

| File | Lines | Type |
|------|-------|------|
| `packages/lingwen-core/src/lingwen_core/agents/mc_writing.py` | +20 / -4 | prod (T3 try/except + logging import) |
| `packages/lingwen-core/src/lingwen_core/agents/cost_persistence.py` | +29 / 0 | prod (T4 `record_at` public helper) |
| `tests/agent_system/test_decision_integration.py` | +6 / -3 | test (T1 _state init + T2 WorkflowRunner migration) |
| `tests/agent_system/test_master_controller_workflow.py` | +5 / 0 | test (T1 _state init) |
| `tests/agent_system/test_master_controller.py` | +44 / -50 | test (T5 env-var → make_master_with_router + assertion fix) |
| `tests/agent_system/test_cost_persistence.py` | +23 / -16 | test (T4 record_at migration) |
| `tests/agent_system/test_master_controller_with_usage.py` | +5 / -3 | test (T3 stale `chapter` assertion fix) |
| `docs/superpowers/specs/2026-09-07-phase-30-tackle-14-failures-design.md` | new (114) | docs |
| `docs/superpowers/plans/2026-09-07-phase-30-tackle-14-failures.md` | new (261) | docs |

**Production files touched: 2** (mc_writing.py + cost_persistence.py)
**Test files touched: 5**
**Doc files added: 2**

---

## T3 — the only design-decision task

`_impl_audit_chapter` (mc_writing.py:155-178) needed try/except for LLM failures. The contract (per both test docstrings) is "audit LLM 抛错 → try/except 兜底返正常 audit report, usage 0". Implemented:

- **Broad `Exception` catch** (not narrow `requests.RequestException`) because:
  - LLM library exceptions are diverse (502, timeout, rate limit, AttributeError from shape drift)
  - Historical contract (test_phase7_1_production_fixes.py:116-117) explicitly notes AttributeError must be swallowed
  - Narrow catch would miss LLM-library-specific exceptions
- **`logger.warning(..., exc_info=True)`** on failure so ops can see (no silent swallow)
- **`record_usage=True` path** returns `({"issues":[], "suggestions":[]}, {input_tokens:0, output_tokens:0})` on failure
- **`record_usage=False` path** returns `{"issues":[], "suggestions":[]}` on failure
- **Use-llm-False path** unchanged (`{"issues":[], "suggestions":[]}` — no LLM call, no try/except needed)

Also fixed stale assertion in `test_master_controller_with_usage.py`: `assert "chapter" in result` was for an older contract; current `_impl_audit_chapter` strips the auditor's response to `{issues, suggestions}` only. Updated to assert `result["issues"] == []` and `result["suggestions"] == []`.

---

## Carryover to Phase 31+

1. **P2-ARCHDEBT** (deferred from v25.9 / v27 / v29):
   - `infra.got.*` migrate to ` packages/lingwen-got/` + `allowed_imports`
   - `chapter_golden_path.py` reverse-import `apps.studio_api.*` fix
   - HANDOFF docs `latest_decision_queue` wording
   - 4 thin proxies → `OrchestratorProxyMixin`
   - PHASE-COMPAT shim deletion
2. **Phase 114 prod preview regression** (accepted debt — do NOT attempt).

---

## Branch state — ready for ff-merge

```
Branch:  worktree-phase-30-tackle-14
Ahead:   8 commits ahead of master (clean working tree)
Commits: 2de95a80 chore(phase-29): state sync   ← master HEAD
         3f07c532 docs: design phase 30 tackle-14-failures
         910d3454 docs: phase 30 implementation plan
         4d298d6a test(stub-factory): inject WorkflowState.empty()
         4030a43c test(master-controller): use make_master_with_router()
         9f2322ad feat(cost-persistence): add record_at() public helper
         04906367 test(decision-integration): migrate to WorkflowRunner
         acd8e013 fix(audit-chapter): add try/except resilience
         (this handoff commit)
```

**Per project workflow rule (2026-09-01):** "No more PRs; for future phases: work in worktree, commit atomically per task, push branch directly, merge locally, push master." Human approval is required to run `git checkout master && git merge --ff-only worktree-phase-30-tackle-14 && git push origin master`. This handoff document does not run that command.

---

## Baseline vs final state

| Metric | v29.0 baseline | Phase 30 final | Delta |
|--------|----------------|----------------|-------|
| `tests/agent_system` failed | 14 | **0** | **-14** |
| `tests/agent_system` passed | 466 | **480** | **+14** |
| `tests/agent_system` skipped | 20 | 20 | 0 |
| `tests/got` passed | 156 | 156 | 0 |
| `packages/lingwen-core/tests/` passed | 68 | 68 | 0 |
| ruff check (`packages/lingwen-core/src/lingwen_core/agents/`) | clean | clean | 0 |
| Production files touched | n/a | **2** | +2 |
| Test files touched | n/a | 5 | +5 |
| Doc files added | n/a | 2 (design + plan) + 1 (handoff) | +3 |

Phase 30 delivered the targeted 14-failure reduction with 2 tightly-scoped production changes (T3 try/except resilience + T4 `record_at` public helper) and 5 test-only cleanups.