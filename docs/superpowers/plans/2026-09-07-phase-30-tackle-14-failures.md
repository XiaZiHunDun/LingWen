# Phase 30 — TACKLE-14-FAILURES Implementation Plan

> **Branch:** `worktree-phase-30-tackle-14`
> **Spec:** `docs/superpowers/specs/2026-09-07-phase-30-tackle-14-failures-design.md`
> **Baseline:** master `2de95a80` (14 failed / 466 passed / 20 skipped in `tests/agent_system`)
> **Target:** 0 failed / 480+ passed / 20 skipped

---

## Task order

Tasks are sequenced by **risk**: test-only cleanups first (T1, T5, T4, T2), real prod change last (T3). Each task is one atomic commit.

| # | Description | Type | Files touched | Tests fixed |
|---|-------------|------|---------------|-------------|
| T1 | Stub factory `_state` injection | test-only | 2 | 7 |
| T5 | env-var tests rewrite | test-only | 1 | 2 |
| T4 | CostTracker `record_at` API + test migration | test + tiny prod | 1 prod + 1 test | 2 |
| T2 | `_harvest_decision_specs` test migration | test-only | 1 | 1 |
| T3 | `_impl_audit_chapter` try/except | real prod | 1 prod | 2 |

After each task: re-run G1, confirm target count drops by the expected amount.

---

## T1 — Stub factory `_state` injection (7 tests)

**Files:**
- `tests/agent_system/test_decision_integration.py` (`_make_controller_with_stubs` helper, ~line 30)
- `tests/agent_system/test_master_controller_workflow.py` (similar helper)

**Change (each file):**

```python
controller = mc_mod.MasterController.__new__(mc_mod.MasterController)
+ from lingwen_core.agents.workflow_state import WorkflowState
+ controller._state = WorkflowState.empty()
  stub = _StubMaster()
  ...
```

For `test_master_controller_workflow.py`, the helper may live in a shared location (verify by grep). If `_make_controller_with_stubs` is reused, single edit suffices.

**Verify:** `.venv/bin/python -m pytest tests/agent_system/test_decision_integration.py tests/agent_system/test_master_controller_workflow.py -q` → 7 fewer failures.

**Commit:** `test(stub-factory): inject WorkflowState.empty() after __new__() bypass`

---

## T5 — env-var tests rewrite (2 tests)

**File:** `tests/agent_system/test_master_controller.py`

**Change:** Rewrite `test_master_controller_write_chapter` (line 55) and `test_master_controller_audit_chapter` (line 89) to use `make_master_with_router()` from `tests/agent_system/_e2e_helpers.py:110` instead of `MasterController()`.

**Pattern (from existing passing tests in same file):**
```python
from tests.agent_system._e2e_helpers import make_master_with_router
master = make_master_with_router(tmp_path)  # or similar signature
result = master.write_chapter(...)
```

Confirm exact signature of `make_master_with_router` in `_e2e_helpers.py:110`.

**Verify:** `.venv/bin/python -m pytest tests/agent_system/test_master_controller.py::test_master_controller_write_chapter tests/agent_system/test_master_controller.py::test_master_controller_audit_chapter -q` → 2 fewer failures.

**Commit:** `test(master-controller): use make_master_with_router() instead of bare MasterController()`

---

## T4 — CostTracker `record_at` + test migration (2 tests)

**Prod file:** `packages/lingwen-core/src/lingwen_core/agents/cost_persistence.py`

**Prod change:** Add public `record_at(timestamp, scenario, tier, in, out) -> CostRecord` method after `record()` (around line 138). Same internal logic as `record()` but uses the explicit `timestamp` instead of `datetime.now()`.

```python
def record_at(
    self,
    timestamp: datetime,
    scenario: str,
    tier: ModelTier,
    input_tokens: int,
    output_tokens: int,
) -> CostRecord:
    """记录一次 LLM 调用 with explicit timestamp.
    
    Same as record() but allows caller to specify timestamp.
    Useful for seeding historical data, migrations, test fixtures.
    """
    self.init_db()
    cost = compute_cost(input_tokens, output_tokens, tier)
    rec = CostRecord(
        scenario=scenario,
        tier=tier,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        timestamp=timestamp,
    )
    def _do(conn) -> None:
        conn.execute(
            """INSERT INTO cost_records
               (scenario, tier, input_tokens, output_tokens, cost_usd, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (rec.scenario, rec.tier.value, rec.input_tokens, rec.output_tokens,
             rec.cost_usd, rec.timestamp.isoformat()),
        )
    self._storage.with_transaction(_do)
    return rec
```

**Test changes:** `tests/agent_system/test_cost_persistence.py:202-223` and `:246-264`

Replace `with db._connect() as conn: conn.executemany(...)` with three `db.record_at(datetime.fromisoformat(...), scenario, ModelTier.X, in, out)` calls.

**Verify:** `.venv/bin/python -m pytest tests/agent_system/test_cost_persistence.py::TestCostTrackerDBCostByDay::test_cost_by_day_groups_by_utc_date tests/agent_system/test_cost_persistence.py::TestCostTrackerDBCostByDayPerTier::test_cost_by_day_per_tier_groups_by_day_and_tier -q` → 2 fewer failures.

**Commit:** `feat(cost-persistence): add record_at() public helper for explicit-timestamp inserts`

---

## T2 — `_harvest_decision_specs` test migration (1 test)

**File:** `tests/agent_system/test_decision_integration.py:330` (or whichever line imports `_collect_decision_specs_from_graph`)

**Change:** Replace `from lingwen_pipeline.master_controller import _collect_decision_specs_from_graph` (or wherever it's imported) with `from lingwen_core.agents.mc_workflow import _harvest_decision_specs`. Update the call site to use the new function name.

**Verify:** `.venv/bin/python -m pytest tests/agent_system/test_decision_integration.py::test_decision_node_creates_pending_decision -q` → 1 fewer failure.

**Commit:** `test(decision-integration): migrate to mc_workflow._harvest_decision_specs`

---

## T3 — `_impl_audit_chapter` try/except (2 tests, real prod change)

**Prod file:** `packages/lingwen-core/src/lingwen_core/agents/mc_writing.py:155-178`

**Change:** Wrap both `record_usage=True` and `record_usage=False` paths in try/except.

```python
import logging

logger = logging.getLogger(__name__)

def _impl_audit_chapter(
    self,
    chapter_num: int,
    content: str,
    characters: List[Dict],
    timeline: List[Dict],
    use_llm: bool,
    record_usage: bool,
):
    if use_llm:
        try:
            if record_usage:
                result, usage = self.auditor.audit_chapter_with_usage(
                    chapter_num, content, characters, timeline
                )
                return {
                    "issues": result.get("issues", []),
                    "suggestions": result.get("suggestions", []),
                }, usage
            result = self.auditor.audit_chapter(chapter_num, content, characters, timeline)
            return {
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", []),
            }
        except Exception:
            logger.warning(
                "audit_chapter failed at chapter_num=%s; returning empty audit report",
                chapter_num,
                exc_info=True,
            )
            if record_usage:
                return (
                    {"issues": [], "suggestions": []},
                    {"input_tokens": 0, "output_tokens": 0},
                )
            return {"issues": [], "suggestions": []}
    return {"issues": [], "suggestions": []}
```

**Note on `result.get("issues", [])` and `result.get("suggestions", [])`:** Existing code does the same; no change. Just wrapping.

**Verify:** `.venv/bin/python -m pytest tests/agent_system/test_master_controller_with_usage.py::TestMasterControllerWithUsage::test_audit_with_usage_propagates_exception tests/agent_system/test_phase7_1_production_fixes.py::test_audit_chapter_failure_does_not_crash_workflow -q` → 2 fewer failures.

**Commit:** `fix(audit-chapter): add try/except resilience for LLM failures (workflow non-interruption contract)`

---

## Final verification gates

After all 5 tasks committed, run from worktree root:

```bash
# G1
.venv/bin/python -m pytest tests/agent_system -q --tb=no
# Expected: 0 failed, 480 passed (or 480+x), 20 skipped

# G2
.venv/bin/python -m pytest tests/got -q --tb=no
# Expected: 156 passed

# G3a
.venv/bin/python -m pytest packages/lingwen-core/tests/ -q --tb=no
# Expected: 68 passed

# G3b
ruff check packages/lingwen-core/src/lingwen_core/agents/
# Expected: All checks passed

# Regression spot-check (full test infra)
.venv/bin/python -m pytest tests/cross_volume tests/got tests/agent_system packages/lingwen-core/tests/ -q --tb=no 2>&1 | tail -5
# Expected: no new failures
```

---

## Handoff commit

After all gates pass:

```
docs(phase-30): tackle-14-failures handoff

- 5 atomic tasks (T1-T5), test-only + 2 small prod changes (T3 try/except, T4 record_at helper)
- 14 → 0 failed in tests/agent_system
- All other gates unchanged

Co-Authored-By: Claude <noreply@anthropic.com>
```

Save to `docs/superpowers/handoffs/2026-09-07-phase-30-tackle-14-handoff.md`.

---

## Merge + push

```bash
# In master worktree:
git checkout master
git merge --ff-only worktree-phase-30-tackle-14
git push origin master
git worktree remove --force .claude/worktrees/phase-30-tackle-14
git branch -D worktree-phase-30-tackle-14
```

---

## Risk register (update after each task)

| Task | Pre-fail | Post-fail | Notes |
|------|----------|-----------|-------|
| T1   | 14       | 7         | -7 stub factory fix |
| T5   | 7        | 5         | -2 env-var rewrite |
| T4   | 5        | 3         | -2 record_at migration |
| T2   | 3        | 2         | -1 export migration |
| T3   | 2        | 0         | -2 try/except resilience |
| **Final** | **14** | **0**  | **-14 total** |