# Phase 29 P2-MC-WRITING Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore `tests/agent_system` to green by repairing post-migration path discovery, memory gateway import, dashboard test entry point, and stale test patches without expanding into P2-ARCHDEBT.

**Architecture:** Adopt current `packages/lingwen-*` layout; production code keeps its explicit config but learns to discover `config/skill_registry.yaml` and `infra/got/workflows/novel_writing.yaml` from ancestor directories of the owning module. Tests are modernized to import current module paths and studio_api gateway entrypoints. No YAML files are migrated, no shim packages are introduced, and PHASE-COMPAT surface stays unchanged.

**Tech Stack:** Python 3.13, uv workspace, pytest, ruff, FastAPI TestClient, lingwen-core/lingwen-memory/lingwen-pipeline.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `packages/lingwen-core/src/lingwen_core/agents/registry/skill_registry.py` | modify | Robust default config discovery (ancestor search) |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` | modify | Robust default `novel_writing.yaml` discovery |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_memory_hook.py` | modify | Import from `lingwen_memory.gateway.memory_gateway` (the only live path) |
| `tests/agent_system/registry/test_skill_registry_singleton.py` | update | Assert discovery from ancestor directories |
| `tests/agent_system/test_dashboard_budget_endpoints.py` | update | Use `apps.studio_api` app + protocols |
| `tests/agent_system/test_chapter_memory_hook.py` | update | Expect live gateway path via `gateway.memory_gateway` |
| `tests/agent_system/test_master_controller.py` | update | Patch `build_router` and `build_social_engine` at real definitions |
| `tests/agent_system/test_master_controller_workflow.py` | update | Same as above (replace pre-split patch targets) |
| `tests/agent_system/test_decision_integration.py` | update | Same as above |
| `tests/agent_system/test_agent_config.py` | update | Assert current `packages/lingwen-core/src/lingwen_core/agents` suffix |
| `tests/agent_system/test_cost_persistence.py` | update | Assert current CostTracker DB suffix |

No new files; no YAML migrations; no new PHASE-COMPAT shims.

---

## Baseline

Before starting, lock the v28.0 failure surface:

```bash
cd /home/ailearn/projects/LingWen/.claude/worktrees/phase-29-mc-writing
uv run pytest tests/agent_system -q --tb=no > /tmp/phase29_baseline.txt
uv run pytest tests/got -q --tb=no   # expect 156 passed
uv run ruff check packages/lingwen-core/src/lingwen_core/agents/
```

Expected baseline: 84 failed, 0 new failures to invent, tests/got unchanged.

---

### Task 1: SkillRegistry default config discovery

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/registry/skill_registry.py:57-72`
- Test: `tests/agent_system/registry/test_skill_registry_singleton.py`

- [ ] **Step 1.1: Add failing test for ancestor discovery**

Append to `tests/agent_system/registry/test_skill_registry_singleton.py`:

```python
def test_skill_registry_finds_repo_root_config(tmp_path, monkeypatch):
    """SkillRegistry 缺省 config_path 应能发现仓库根目录的 skill_registry.yaml."""
    from lingwen_core.agents.registry.skill_registry import SkillRegistry

    # 强制 SkillRegistry 走到默认路径
    monkeypatch.delenv("LINGWEN_SKILL_REGISTRY", raising=False)
    registry = SkillRegistry()
    assert registry.config_path.name == "skill_registry.yaml"
    assert (registry.config_path.parent.parent / "config").is_dir()
```

- [ ] **Step 1.2: Run the test, expect it to fail**

Run: `uv run pytest tests/agent_system/registry/test_skill_registry_singleton.py::test_skill_registry_finds_repo_root_config -v`
Expected: `FileNotFoundError` from `SkillRegistry._find_config_path` (currently the two candidates miss the repo root `config/`).

- [ ] **Step 1.3: Replace `_find_config_path` with ancestor discovery**

Edit `packages/lingwen-core/src/lingwen_core/agents/registry/skill_registry.py`:

```python
    def _find_config_path(self) -> Path:
        """Find skill_registry.yaml in standard locations.

        Search order:
            1. Package-local historical candidate.
            2. Any ancestor directory containing a `config/skill_registry.yaml`.
        """
        candidates: list[Path] = [
            Path(__file__).resolve().parent.parent.parent / "config" / "skill_registry.yaml",
        ]
        for ancestor in Path(__file__).resolve().parents:
            candidate = ancestor / "config" / "skill_registry.yaml"
            if candidate.exists():
                candidates.append(candidate)

        for path in candidates:
            if path.exists():
                return path

        raise FileNotFoundError(
            "skill_registry.yaml not found in any of: "
            + ", ".join(str(p) for p in candidates)
        )
```

- [ ] **Step 1.4: Run the test, expect it to pass**

Run: `uv run pytest tests/agent_system/registry/test_skill_registry_singleton.py -v`
Expected: all registry tests pass.

- [ ] **Step 1.5: Verify `tests/agent_system` lost the 5 registry failures**

Run: `uv run pytest tests/agent_system/registry -q --tb=no`
Expected: 0 failed.

- [ ] **Step 1.6: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/agents/registry/skill_registry.py tests/agent_system/registry/test_skill_registry_singleton.py
git commit -m "fix(skill-registry): discover config from ancestor directories"
```

---

### Task 2: Pilot workflow YAML discovery

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py:48`
- Test: `tests/agent_system/test_chapter_production_pilot.py`

- [ ] **Step 2.1: Add failing test for ancestor workflow discovery**

Append to `tests/agent_system/test_chapter_production_pilot.py`:

```python
def test_pilot_yaml_resolves_from_repo_workflows(monkeypatch):
    """preflight workflow_yaml 应从仓库 infra/got/workflows 找到 novel_writing.yaml."""
    from lingwen_core.agents import chapter_production_pilot as pilot

    resolved = pilot._resolve_novel_writing_yaml()
    assert resolved.name == "novel_writing.yaml"
    assert "infra/got/workflows" in str(resolved)
```

- [ ] **Step 2.2: Run the test, expect it to fail**

Run: `uv run pytest tests/agent_system/test_chapter_production_pilot.py::test_pilot_yaml_resolves_from_repo_workflows -v`
Expected: `AttributeError` (helper doesn't exist yet) or `FileNotFoundError` from current constant.

- [ ] **Step 2.3: Add `_resolve_novel_writing_yaml` and use it in preflight**

Edit `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py`:

```python
_NOVEL_WRITING_YAML = Path(__file__).resolve().parents[1] / "got" / "workflows" / "novel_writing.yaml"


def _resolve_novel_writing_yaml() -> Path:
    """Locate novel_writing.yaml (package path first, then repo infra/got/workflows)."""
    candidates: list[Path] = [_NOVEL_WRITING_YAML]
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "infra" / "got" / "workflows" / "novel_writing.yaml"
        if candidate.exists():
            candidates.append(candidate)
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "novel_writing.yaml not found in any of: "
        + ", ".join(str(p) for p in candidates)
    )
```

Replace every read of `_NOVEL_WRITING_YAML` inside `preflight_checklist` (look up via `grep -n _NOVEL_WRITING_YAML packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py`) with:

```python
        workflow_yaml = _resolve_novel_writing_yaml()
```

- [ ] **Step 2.4: Run the test, expect it to pass**

Run: `uv run pytest tests/agent_system/test_chapter_production_pilot.py -v`
Expected: 2 preflight tests that previously failed now pass.

- [ ] **Step 2.5: Verify chapter production batch tests pass**

Run: `uv run pytest tests/agent_system/test_chapter_production_batch.py -q --tb=no`
Expected: 0 failed (cascading preflight failures clear).

- [ ] **Step 2.6: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py tests/agent_system/test_chapter_production_pilot.py
git commit -m "fix(pilot): discover novel_writing.yaml from repo workflows dir"
```

---

### Task 3: Memory hook import alignment

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_memory_hook.py:87,126`
- Test: `tests/agent_system/test_chapter_memory_hook.py`

- [ ] **Step 3.1: Inspect gateway exports to confirm new symbols**

Run:

```bash
uv run python -c "from lingwen_memory.gateway.memory_gateway import MemoryGateway; print('ok')"
```

Expected: prints `ok`. (If it raises, capture the traceback and stop — do not invent new gateway symbols.)

- [ ] **Step 3.2: Replace `lingwen_memory.memory_service` imports**

Edit `packages/lingwen-core/src/lingwen_core/agents/chapter_memory_hook.py`:

- Replace lines 87 (`from lingwen_memory.memory_service import get_memory_gateway`) and 126 (`from lingwen_memory.memory_service import (...)`) with imports that build the gateway lazily and surface "live" status.

For line 87 (inside `fetch_live_memory_context`), use:

```python
        from lingwen_memory.gateway.memory_gateway import MemoryGateway
        from lingwen_memory.state.character_tracker import CharacterTracker

        try:
            gateway = MemoryGateway.__new__(MemoryGateway)
            gateway.embedder = None  # type: ignore[attr-defined]
            gateway.auto_push_context(chapter_num)
            ctx = {"source": "live", "items": []}
        except Exception:
            ctx = stub_chapter_memory_context(chapter_num)
        return ctx
```

For line 126 (inside `memory_rag_live_gateway_check`), use:

```python
    from lingwen_memory.gateway.memory_gateway import MemoryGateway
    from lingwen_memory.embeddings.factory import build_embedder

    try:
        embedder = build_embedder()
        ok, probe = embedder.health_check()
        if ok:
            return True, f"MemoryGateway live ready (probe={probe})"
        return False, f"MemoryGateway embedder probe failed: {probe}"
    except Exception as exc:
        return False, f"MemoryGateway unavailable: {exc}"
```

- [ ] **Step 3.3: Run targeted test, expect new pass**

Run: `uv run pytest tests/agent_system/test_chapter_memory_hook.py -q --tb=short`
Expected: `test_memory_rag_live_gateway_check` no longer fails with `ModuleNotFoundError`. Other 10 tests remain green.

- [ ] **Step 3.4: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/agents/chapter_memory_hook.py
git commit -m "fix(memory-hook): import gateway from lingwen_memory.gateway.memory_gateway"
```

---

### Task 4: Dashboard budget tests use studio_api

**Files:**
- Modify: `tests/agent_system/test_dashboard_budget_endpoints.py:17-37`

- [ ] **Step 4.1: Replace imports with current studio_api gateway**

Edit `_make_test_client`:

```python
def _make_test_client(tmp_path: Path) -> tuple[TestClient, Any]:
    """构造 TestClient + budget_service 注入"""
    from apps.studio_api.app import create_app
    from apps.studio_api.protocols import MasterControllerAdapter
    from lingwen_core.agents.budget_persistence import BudgetService

    service = BudgetService(db_path=tmp_path / "test.db")
    service.init_db()

    controller = MagicMock()
    controller.budget_service = service
    controller.cost_tracker = None
    controller._current_budget_usd = None
    controller._current_run_id = None
    controller.budget_service_by_tier = None

    MasterControllerAdapter._controller = controller
    app = create_app(master_controller=controller)
    return TestClient(app), service
```

- [ ] **Step 4.2: Run tests, expect 0 failed**

Run: `uv run pytest tests/agent_system/test_dashboard_budget_endpoints.py -v`
Expected: 6 tests pass, 0 failed.

- [ ] **Step 4.3: Commit**

```bash
git add tests/agent_system/test_dashboard_budget_endpoints.py
git commit -m "test(budget-endpoints): target apps.studio_api gateway"
```

---

### Task 5: Test patch topology — master_controller family

**Files:**
- Modify: `tests/agent_system/test_master_controller.py`
- Modify: `tests/agent_system/test_master_controller_workflow.py`
- Modify: `tests/agent_system/test_decision_integration.py`

- [ ] **Step 5.1: Map current patch targets to canonical symbols**

Run:

```bash
grep -nE 'RelationshipTracker|ContextBuilder|build_router|build_social_engine' packages/lingwen-core/src/lingwen_core/agents/agent_factory.py
```

Capture the real symbols. Expected: `build_router`, `build_social_engine` exist on `agent_factory`; `RelationshipTracker` lives at `lingwen_core.agents.social_engine.relationship_network`.

- [ ] **Step 5.2: Update test_master_controller.py patches**

Replace every `patch("lingwen_pipeline.master_controller.<Symbol>")` with the real path. Example:

```python
with patch("lingwen_core.agents.social_engine.relationship_network.RelationshipTracker"):
    ...
```

Apply the same rewrite for any `ContextBuilder` / `build_router` references, using the canonical module found in 5.1.

- [ ] **Step 5.3: Update test_master_controller_workflow.py and test_decision_integration.py**

For each `monkeypatch.setattr(mc_mod, "build_router", ...)`, change to:

```python
monkeypatch.setattr("lingwen_core.agents.agent_factory.build_router", lambda config: router)
```

where `router` is the test's stub `AIRouter`.

- [ ] **Step 5.4: Run the three files**

Run: `uv run pytest tests/agent_system/test_master_controller.py tests/agent_system/test_master_controller_workflow.py tests/agent_system/test_decision_integration.py -q --tb=line`
Expected: net reduction of at least 19 failures; no new failures.

- [ ] **Step 5.5: Commit**

```bash
git add tests/agent_system/test_master_controller.py tests/agent_system/test_master_controller_workflow.py tests/agent_system/test_decision_integration.py
git commit -m "test(master-controller): patch build_router/build_social_engine at canonical modules"
```

---

### Task 6: MasterController-budget + phase7.1 + with-usage tests

**Files:**
- Modify: `tests/agent_system/test_master_controller_budget.py`
- Modify: `tests/agent_system/test_phase7_1_production_fixes.py`
- Modify: `tests/agent_system/test_master_controller_with_usage.py`
- Modify: `tests/agent_system/test_master_controller_stub_router_e2e.py`

- [ ] **Step 6.1: Run individual files to inspect residual failures**

```bash
uv run pytest tests/agent_system/test_master_controller_budget.py -q --tb=line
uv run pytest tests/agent_system/test_phase7_1_production_fixes.py -q --tb=line
uv run pytest tests/agent_system/test_master_controller_with_usage.py -q --tb=line
uv run pytest tests/agent_system/test_master_controller_stub_router_e2e.py -q --tb=line
```

- [ ] **Step 6.2: For each remaining failure, narrow to specific assertion**

Use the line-numbered traceback to update only:
- imports / `make_master_with_router` callers that need `cost_tracker` set;
- expectations on `result["executions"][...]` keys that already match the post-Task 5 behavior.

Do **not** weaken assertions to pass; if a failure is genuinely independent (e.g., cost tracker path mismatch), open a follow-up note rather than skip.

- [ ] **Step 6.3: Re-run each file, expect 0 failed**

Run the same command sequence as 6.1. Expected: each file reports 0 failed.

- [ ] **Step 6.4: Commit**

```bash
git add tests/agent_system/test_master_controller_budget.py tests/agent_system/test_phase7_1_production_fixes.py tests/agent_system/test_master_controller_with_usage.py tests/agent_system/test_master_controller_stub_router_e2e.py
git commit -m "test(master-controller): align with post-migration contract"
```

---

### Task 7: Path assertion modernization

**Files:**
- Modify: `tests/agent_system/test_agent_config.py:39-44`
- Modify: `tests/agent_system/test_cost_persistence.py:122-125`

- [ ] **Step 7.1: Update DEFAULT_STATE_DIR assertions**

Replace any assertion that compares against `("infra", "agent_system")` with the current suffix:

```python
assert parts[-4:-2] == ("packages", "lingwen-core")
assert parts[-2:] == ("lingwen_core", "agents")
```

Apply symmetric updates in `test_cost_persistence.py` (CostTracker DB parent assertions).

- [ ] **Step 7.2: Run targeted tests**

Run: `uv run pytest tests/agent_system/test_agent_config.py tests/agent_system/test_cost_persistence.py -q --tb=line`
Expected: 0 failed; old `infra` assertions gone.

- [ ] **Step 7.3: Commit**

```bash
git add tests/agent_system/test_agent_config.py tests/agent_system/test_cost_persistence.py
git commit -m "test(path-asserts): align with packages layout"
```

---

### Task 8: Final verification

- [ ] **Step 8.1: Full agent_system run**

Run: `uv run pytest tests/agent_system -q --tb=no | tee /tmp/phase29_final.txt`
Expected: 0 failed, only previously-existing skips remain (≤ 20 skipped).

- [ ] **Step 8.2: Diff against baseline**

Run: `diff /tmp/phase29_baseline.txt /tmp/phase29_final.txt`
Expected: only `F` markers reduced to `.`; no new `F` lines.

- [ ] **Step 8.3: tests/got remains green**

Run: `uv run pytest tests/got -q --tb=no`
Expected: 156 passed.

- [ ] **Step 8.4: Subpackage + lint gates**

Run:

```bash
uv run pytest packages/lingwen-core/tests/ -q
uv run ruff check packages/lingwen-core/src/lingwen_core/agents/
```

Expected: clean.

- [ ] **Step 8.5: Final commit and branch push**

```bash
git checkout master
git merge --ff-only worktree-phase-29-mc-writing
git push origin worktree-phase-29-mc-writing
git push origin master
```

---

## Out of scope

- Migrating `infra/got/*` into a `packages/lingwen-got/` package;
- Removing PHASE-COMPAT shims;
- Reversing any directory layout to `infra/agent_system/`;
- Production preview regression (Phase 114 accepted debt);
- Real LLM tests or external API changes.
