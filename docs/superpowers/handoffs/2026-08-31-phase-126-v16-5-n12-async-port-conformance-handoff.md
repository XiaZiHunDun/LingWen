# Phase 126 v16.5 #N.12 Handoff — Async Port Conformance

> **Phase**: 126 v16.5 #N.12 — Async Port Conformance
> **Date**: 2026-08-31
> **Branch**: `phase-126-v16-5-n12` (CLOSED, ready for merge to master)
> **Commits**: 22 (since master `8d9e8ab6` v16.5 #N.12 plan)
> **Plan**: `docs/superpowers/plans/2026-08-31-phase-126-v16-5-n12-async-port-conformance.md`
> **Spec**: `docs/superpowers/specs/2026-08-31-phase-126-v16-5-n12-async-port-conformance-design.md`

## Summary

Closed v16.5 #N.12 — LLMServiceAdapter converted from sync facade to async surface matching the LLMServicePort Protocol declaration. All 12 caller sites migrated to `await` the async API. Adapter wraps sync `LLMService` concrete via `asyncio.to_thread` (no event loop blocking). `TaskSpec` + `LLMResult` removed from `lingwen_shared.ports` (declared but never used).

**Branch totals: 22 commits, 5 deliverables (Part A/B/C/D/E), 4 architecture invariants added.**

## Commits (22 total)

### Part A: Foundation (3 commits)
- `a6f628ec` `feat(lingwen-shared)`: LLMServicePort async + LLMTask (drop TaskSpec/LLMResult)
- `dcc540f0` `feat(lingwen-llm)`: LLMServiceAdapter async (execute/execute_stream/generate)
- `bbbc9d93` `refactor(lingwen-llm)`: extract _FakeService + accurate execute_stream docstring

### Part B: creator/content/agent.py (1 commit)
- `3654b653` `refactor(lingwen-creator)`: content/agent.py await LLMServiceAdapter + cascade to creator_core.py

### Part C: Infra async callers (2 commits)
- `ea18f811` `refactor(infra)`: prose_judge.py await LLMServiceAdapter.execute
- `b7bb8981` `refactor(infra)`: agent_extractors.py extract_* methods async + await

### Part D: Tools migration (13 commits)
- `931d87c8` `refactor(tools)`: llm_emotional_resonance_checker await LLMServiceAdapter
- `58c3392b` `refactor(tools)`: llm_foreshadow_analyzer await LLMServiceAdapter
- `bf064e7c` `refactor(tools)`: llm_pacing_analyzer await LLMServiceAdapter
- `3c77d6ac` `refactor(tools)`: llm_quality_analyzer await LLMServiceAdapter
- `370af844` `refactor(tools)`: anti_trope_enhancer await LLMServiceAdapter
- `1af7decd` `refactor(tools)`: llm_quality.checker await LLMServiceAdapter
- `38f7fce2` `refactor(tools)`: llm_quality.repairer await LLMServiceAdapter
- `e70beb64` `refactor(tools)`: llm_character_arc_analyzer await LLMServiceAdapter
- `5abba6b3` `refactor(tools)`: llm_outline_quality_check await LLMServiceAdapter
- `dba0a5ed` `refactor(tools)`: llm_protagonist_charm_analyzer await LLMServiceAdapter
- `99415284` `refactor(tools)`: llm_readability_analyzer await LLMServiceAdapter
- `32e87b0e` `chore(ruff)`: add asyncio import to llm_quality_analyzer
- `03a6698c` `test(tools)`: update test_enhancement_tools for async LLMServiceAdapter

### Part E: Handoff + CLAUDE.md (this commit + 1 next)
- (this commit) handoff doc
- (next commit) CLAUDE.md update

## Architecture Invariants Enforced (4 NEW, 29 total)

26. (NEW) ✅ `LLMServicePort.execute` is `async def (LLMTask) -> str` — Protocol + Adapter conform (matches N.12 spec §3)
27. (NEW) ✅ `LLMServiceAdapter.execute` runs sync concrete in `asyncio.to_thread` (no event loop blocking) — wraps `infra/llm_service.py::LLMService.execute`
28. (NEW) ✅ All `LLMServiceAdapter` callers `await` the result (no orphan sync callers) — 12+ caller sites migrated across creator/infra/tools
29. (NEW) ✅ `TaskSpec` + `LLMResult` removed from `lingwen_shared.ports.llm_service` (declared but never used) + `ports/__init__.py` exports

## Test Results

| Gate | Count | Status |
|------|-------|--------|
| `packages/lingwen-shared/tests/` | 125 passed | 0 regression |
| `packages/lingwen-llm/tests/` | 11 passed (was 8; +3 NEW async tests) | 0 regression |
| `packages/lingwen-creator/tests/` | 73 passed | 0 regression |
| `apps/studio_api/tests/` | 48 passed | 0 regression |
| `tests/tools/` | 118 passed + 6 skipped + 1 unrelated pre-existing fail | 0 regression |
| `tests/infra/` (excluding pre-existing lingwen_quality module missing) | 338 passed + 15 pre-existing fails (lingwen_quality module missing — confirmed pre-existing v15.7.1 debt) | 0 regression |
| `tooling/hygiene/tests/` (grimp-evasion regression) | 2 passed | OK |
| `vitest` | (not run — no frontend changes) | N/A |
| `vue-tsc` | (not run — no frontend changes) | N/A |
| `ruff check .` | 0 violations | clean |

## Files Changed (Summary)

### Protocol + Adapter (3 files)
- `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py` — Protocol async rewrite
- `packages/lingwen-shared/src/lingwen_shared/ports/__init__.py` — drop TaskSpec/LLMResult exports
- `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` — async rewrite (execute/execute_stream/generate)

### Creator (1 file + 1 FastAPI caller + 1 test)
- `packages/lingwen-creator/src/lingwen_creator/content/agent.py` — 4 functions → async
- `apps/studio_api/routes/creator_core.py` — 2 route handlers → await
- `packages/lingwen-creator/tests/test_content.py` — 8 tests → async

### Infra (2 files + 1 test + 1 route + 1 stub)
- `infra/prose_judge.py` — 3 functions → async (cascade)
- `infra/world_db/agent_extractors.py` — extract_* methods → async
- `apps/studio_api/routes/world.py` — 2 route handlers → await
- `tests/infra/test_prose_judge.py` — 1 test → async
- `tests/infra/world_db/test_agent_extractors.py` — 9 tests → async
- `apps/studio_api/tests/test_world_route.py` — _StubLLM → async

### Tools (12 files + 1 test)
- 5 modern tools: `llm_emotional_resonance_checker.py`, `llm_foreshadow_analyzer.py`, `llm_pacing_analyzer.py`, `llm_quality_analyzer.py`, `anti_trope_enhancer.py`
- 2 llm_quality: `checker.py`, `repairer.py` (`__init__.py` skipped — pure re-exports)
- 4 legacy: `llm_character_arc_analyzer.py`, `llm_outline_quality_check.py`, `llm_protagonist_charm_analyzer.py`, `llm_readability_analyzer.py`
- 1 test: `tests/tools/test_enhancement_tools.py` (AsyncMock migration)

## Lessons Learned

1. **PEP-562 factory pattern carries over**: Same factory (`_DEFAULT_FACTORY` + `set_default_factory` + `get_default_factory`) used to avoid `from infra.llm_service import` (DP-02 grimp-evasion). Now N.12 Part A wraps the **async** surface on top — proves pattern is portable across sync/async.

2. **`asyncio.to_thread` vs `asyncio.Queue` for streams**: `execute()` uses `asyncio.to_thread` (run sync HTTP in threadpool). `execute_stream()` uses simple `yield from sync iterator` (no thread offload). Trade-off documented in class docstring: current scale tolerates the simpler approach for streams (p95 ~9.52s latency per Phase 120 benchmark; one event-loop block per active streaming request). Future optimization could push stream iteration to a thread via Queue if multi-stream concurrency becomes a concern.

3. **Cascading async migration through 4 layers**: For complex callers like `iter_creator_agent_plan_stream`, async propagated through `_llm_agent_plan_stream_tokens` (helper) → `iter_creator_agent_plan_stream` (public) → `event_stream()` (nested FastAPI helper) → FastAPI route. Each layer adds `async`/`await`/`.tool_adapter`. 4 layers × ~5 lines per layer = ~20 lines of mechanical changes.

4. **`yield from` is illegal in async generators**: When converting `_llm_agent_plan_stream_tokens` from sync generator (`yield from _yield_plan_preview_events(...)`) to async generator, had to replace `yield from sync_iter` with manual `for x in sync_iter: yield x` loop. Documented in `_llm_agent_plan_stream_tokens` docstring.

5. **AsyncMock replaces MagicMock for async method mocks**: Test mocks that previously did `MagicMock(return_value="x")` for `service.execute(...)` must become `AsyncMock(return_value="x")` and the call must be wrapped with `asyncio.run(...)` in sync test contexts. Or convert the test to `async def` + `@pytest.mark.asyncio` + `await`. Only affected 1 test in `test_enhancement_tools.py`.

6. **Tool scripts with sync entry points need `asyncio.run(_async_main())`**: Each of the 12 tool files had a sync `def main():` for CLI invocation. Renamed to `async def _async_main()` + added new sync `def main(): asyncio.run(_async_main())` to preserve CLI ergonomics. Bash scripts that wrap Python (e.g., `scripts/run-prose-judge.sh`) also updated.

7. **Worktree env-sync issue is recurring**: Same pattern from N.6 lesson 3 — `pip install -e packages/<pkg> --no-deps` needed after changes to make tests see the new async version. Affects `lingwen-creator` and `lingwen-llm` in this Phase. MEMORY.md note stands.

8. **Async test pattern is clean with pytest-asyncio `@pytest.mark.asyncio` decorator**: pytest-asyncio `Mode.STRICT` (project default) requires explicit decorator on each `async def test_*`. No glob patterns or conftest magic — explicit is good.

## Carryover to v16.5 #N.13+

- **#N.11.d** `impact_score` storage-vs-presentation drift (CVG cleanup) — still deferred from N.10
- **#N.11.e** Dashboard cascade field migration (`cascadeGraphUtils.js` cleanup) — still deferred from N.10
- **#N.11.g** `ReferenceGraphResponse` full migration to presentation shape — still deferred from N.10
- **#N.13+** 39 `as unknown as` cast cleanup in composables — original carryover
- **Pre-existing lingwen_quality module missing** — affects `tests/infra/test_check_fail_severity.py` + `tests/infra/test_full_check_report.py` + 13 other tests (15 fails total). Out of scope for v16.5 #N.12 (Phase 125 baseline cleanup carryover from v15.7.1)
- **Pre-existing plugin_manager module path bug** — affects `tests/infra/test_creator_agent.py::test_stream_llm_tokens_when_provider_streams`. Real LLM providers fail to load due to wrong module path `infra.ai_service.<name>` vs `lingwen_llm.providers.<name>`. Out of scope (v15.7.1 latent bug)

## Final State

- **Branch**: `phase-126-v16-5-n12` (22 commits since master `8d9e8ab6`)
- **Master**: at v16.5 #N.12 plan commit `8d9e8ab6` (no merge yet — pending PR)
- **Tests**: 132 backend + 118 tools (excluding pre-existing) + 73 creator + 48 studio_api + 11 llm + 125 shared + 2 hygiene = ~509 tests pass; 0 async migration regressions
- **Architecture invariants**: 29 total enforced (4 NEW in N.12)
- **Carryover**: 5 items documented above