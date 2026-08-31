# Phase 126 v16.5 #N.12 — Async Port Conformance Design

> **Date**: 2026-08-31
> **Phase**: 126 v16.5 #N.12 — Async Port Conformance
> **Status**: Design APPROVED, ready for plan creation
> **Carryover from**: N.10 / N.11 (LLMServiceAdapter currently sync facade; LLMServicePort Protocol declares async — mismatch)

## Goal

Make `LLMServiceAdapter` async (matching the `LLMServicePort` Protocol declaration) and migrate all 7+ caller sites to await the async API. Eliminate the sync/async + data-type mismatch between Protocol declaration and concrete implementation.

## Non-Goals

- **NOT** migrating to `TaskSpec` + `LLMResult` (decision per design review). Keep `LLMTask` + `str` return for minimal call-site churn.
- **NOT** making the underlying `LLMService` concrete class async. The async adapter wraps the sync concrete via `asyncio.to_thread` (runs sync I/O in thread pool, doesn't block event loop).
- **NOT** providing a sync `execute_sync()` compat shim. Full migration is the goal — sync shim would encourage ongoing sync usage.
- **NOT** changing provider plugin internals (they handle their own HTTP I/O — out of scope for this Phase).

## Architecture

```
Caller (async) ─→ LLMServiceAdapter (async) ─→ asyncio.to_thread() ─→ LLMService concrete (sync)
                                          │
                                          └─ execute_stream wraps sync Iterator as async generator
```

### Layer responsibilities

| Layer | Module | Async? | I/O pattern |
|-------|--------|--------|-------------|
| Port declaration | `lingwen-shared/ports/llm_service.py` | declare async | n/a (Protocol) |
| Adapter (sync→async bridge) | `lingwen-llm/port_adapter.py` | async | `asyncio.to_thread(sync_call)` + async generator wrapper |
| Concrete service | `infra/llm_service.py` | sync (unchanged) | HTTP via provider plugins |
| Provider plugins | `lingwen_llm/providers/*` | sync (unchanged) | HTTP clients |
| Callers | `apps/*`, `infra/*`, `tools/*` | async (new requirement) | `await service.execute(task)` |

### Why `asyncio.to_thread` (not full async concrete)

- Minimal code change — providers stay sync
- `LLMService.execute` is already non-blocking-from-CPU-perspective (it just makes HTTP calls); `to_thread` puts it on the threadpool executor so it doesn't block the event loop
- Future async providers can override by making the concrete class async (adapter doesn't change)
- Matches the "facade over sync concrete" pattern already used by `StoragePort` (v16.5 #N.1)

## Component Changes

### 1. `LLMServicePort` Protocol (lingwen-shared)

**File**: `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py`

**Current** (mismatch):
```python
class LLMServicePort(Protocol):
    async def execute(self, task: TaskSpec) -> LLMResult: ...       # TaskSpec wrong
    async def execute_stream(self, task: TaskSpec) -> AsyncIterator[str]: ...  # TaskSpec wrong
    def parse_json_response(self, response: LLMResult, schema: type) -> Any: ...  # LLMResult wrong
    def is_available(self) -> bool: ...
```

**New** (matches adapter + LLMTask convention):
```python
from lingwen_shared.contracts.python.llm import LLMTask

class LLMServicePort(Protocol):
    async def execute(self, task: LLMTask) -> str: ...
    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]: ...
    def parse_json_response(self, response: str) -> Any: ...
    def is_available(self) -> bool: ...
```

**Imports cleanup**: Remove `TaskSpec` + `LLMResult` from `lingwen-shared/ports/__init__.py` (never used outside Protocol declaration). Keep `LLMServicePort` re-export.

### 2. `LLMServiceAdapter` async rewrite

**File**: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py`

**New shape**:
```python
import asyncio
from typing import Any, AsyncIterator, Optional

from lingwen_shared.contracts.python.llm import LLMTask, TaskType


class LLMServiceAdapter:
    """Async facade matching LLMServicePort Protocol.
    
    Wraps the concrete LLMService singleton via factory; provides async
    surface by routing sync concrete calls through asyncio.to_thread.
    """
    
    def __init__(self, service: Any = None) -> None:
        if service is None:
            if _DEFAULT_FACTORY is None:
                raise RuntimeError("LLMServiceAdapter default factory not registered...")
            service = _DEFAULT_FACTORY()
        self._service = service
    
    @property
    def provider_name(self) -> str:
        return self._service.provider_name
    
    async def execute(self, task: LLMTask) -> str:
        """Execute an LLM task in a thread (so sync HTTP doesn't block event loop)."""
        return await asyncio.to_thread(self._service.execute, task)
    
    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]:
        """Stream an LLM task, yielding text chunks.
        
        Wraps the sync iterator as an async generator. We don't move the
        underlying HTTP iteration to a thread because streaming semantics
        should preserve the same chunk-by-chunk behavior as the concrete.
        """
        for chunk in self._service.execute_stream(task):
            yield chunk
    
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str = "default",
        **kwargs: Any,
    ) -> str:
        """Async convenience method (was sync in v16.5 #N.6)."""
        task = LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=int(kwargs.get("max_tokens", 2000)),
            temperature=float(kwargs.get("temperature", 0.3)),
        )
        return await self.execute(task)
    
    def parse_json_response(self, response: str) -> Any:
        """Sync — pure function, no I/O. No change from v16.5 #N.6."""
        return self._service.parse_json_response(response)
    
    def is_available(self) -> bool:
        """Sync — health check. No change from v16.5 #N.6."""
        return self._service.is_available()
```

### 3. Caller migration patterns

**Pattern A — FastAPI route handler (already async context)**:
```python
@app.get("/api/llm-health")
async def check_llm():
    from lingwen_llm.port_adapter import LLMServiceAdapter
    return {"available": LLMServiceAdapter().is_available()}  # is_available stays sync
```

**Pattern B — FastAPI route that calls LLM**:
```python
@app.post("/api/agent-extract")
async def extract(payload: Request):
    service = LLMServiceAdapter()
    raw = await service.execute(task)  # NEW: await added
    ...
```

**Pattern C — Sync method calling LLM (must be promoted to async)**:
```python
# Before (sync)
def evaluate_prose(text: str) -> dict:
    service = LLMServiceAdapter()
    raw = service.generate(prompt=...)
    return parse(raw)

# After (async)
async def evaluate_prose(text: str) -> dict:
    service = LLMServiceAdapter()
    raw = await service.generate(prompt=...)
    return parse(raw)
```

**Pattern D — Script / tool entry point (standalone)**:
```python
def main():  # entry point stays sync
    result = asyncio.run(_main())  # bridge at top-level

async def _main():
    tool = LLMForeshadowAnalyzer()
    result = await tool.analyze(...)  # tool.analyze is now async
    print(result)
```

### 4. Files migrated (8 caller file groups, 11 total files)

| Caller file | Usage | Migration pattern |
|-------------|-------|-------------------|
| `apps/studio_api/routes/health.py` | `.is_available()` (sync) | Add no-op `await` if needed (probably none — stays sync) |
| `infra/prose_judge.py` | `service.execute(LLMTask)` in sync method | Promote method to async + await |
| `infra/world_db/agent_extractors.py` | `LLMServiceAdapter().generate()` in sync `extract_*` methods | Promote to async + await |
| `packages/lingwen-creator/src/lingwen_creator/content/agent.py` | 4 sites `LLMServiceAdapter().generate()` in sync methods | Promote to async + await |
| `tools/anti_trope_enhancer.py` | `LLMServiceAdapter()` constructor + `self.llm.generate()` | Class async conversion |
| `tools/llm_emotional_resonance_checker.py` | Same | Same |
| `tools/llm_foreshadow_analyzer.py` | Same | Same |
| `tools/llm_pacing_analyzer.py` | Same | Same |
| `tools/llm_quality_analyzer.py` | Same | Same |
| `tools/llm_quality/__init__.py` | Likely re-export | Verify |
| `tools/llm_quality/checker.py` | `LLMServiceAdapter().generate()` | Promote |
| `tools/llm_quality/repairer.py` | Same | Same |
| `tools/legacy/llm_*.py` (4 files) | Likely similar | Same per file |

**Total**: 8 + 11 ≈ 14-16 atomic 1-file commits (some may group logically)

### 5. Test migration

**Unit tests** (`packages/lingwen-llm/tests/test_port_adapter.py`):
- Add `pytest-asyncio` dependency (already in pyproject for other tests)
- Convert `def test_*` → `async def test_*` with `@pytest.mark.asyncio`
- Mock `LLMService.execute` with `unittest.mock.AsyncMock` (auto-await)
- Test `execute_stream` as async generator (iterate with `async for chunk in adapter.execute_stream(task): ...`)

**Mock patterns in caller tests** (`tests/tools/test_*.py`, `tests/infra/test_*.py`):
- Replace `MagicMock(spec=LLMServiceAdapter)` with `AsyncMock(spec=LLMServiceAdapter)`
- Test methods that call LLM become async + await mocks

**conftest.py** (`tests/tools/conftest.py`):
- Update factory bootstrap if needed (current code does `from infra.llm_service import ...` to register factory — no change needed since infra.llm_service stays sync)

## Migration Phases (commits)

### Phase 1: Foundation (3 commits)
- **T1**: Update `LLMServicePort` Protocol — async signatures + LLMTask + str; remove `TaskSpec` + `LLMResult` from ports `__init__.py` exports
- **T2**: Rewrite `LLMServiceAdapter` as async — `asyncio.to_thread` + async generator for execute_stream; factory pattern unchanged
- **T3**: Update `test_port_adapter.py` to use `pytest-asyncio` + `AsyncMock`; verify all existing tests still pass (or migrate)

### Phase 2: FastAPI routes + helpers (2-3 commits)
- **T4**: `apps/studio_api/routes/health.py` — confirm `is_available()` works in async context (no change needed since it stays sync)
- **T5**: `packages/lingwen-creator/src/lingwen_creator/content/agent.py` — 4 sites: promote calling methods to async + add `await`

### Phase 3: Infra async callers (3-4 commits)
- **T6**: `infra/prose_judge.py` — promote calling method to async + add `await`
- **T7**: `infra/world_db/agent_extractors.py` — promote `extract_*` methods to async + add `await`
- **T8**: Audit other infra callers (grep for `LLMServiceAdapter` usage not in T6/T7)

### Phase 4: Tools migration (7-8 commits)
- **T9-T12**: `tools/{llm_emotional_resonance_checker,llm_foreshadow_analyzer,llm_pacing_analyzer,llm_quality_analyzer}.py` — 4 atomic 1-file commits (DP-06 strict)
- **T13**: `tools/anti_trope_enhancer.py` — separate atomic commit
- **T14**: `tools/llm_quality/{__init__,checker,repairer}.py` — 3 atomic commits OR grouped if needed
- **T15**: `tools/legacy/llm_*.py` (4 files) — 4 atomic commits OR grouped

### Phase 5: Documentation + verification (1-2 commits)
- **T16**: Handoff doc + CLAUDE.md update + final verification gates (pytest + vitest + vue-tsc + ruff)

**Total**: ~16-22 commits (matches carryover estimate of "~16-25 commits")

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Forgotten caller (sync code calling async adapter) → `TypeError: object coroutine can't be used as awaitable` | Audit grep before each commit; import-linter + ruff gate catch mismatches |
| AsyncMock not used in test mocks → magic mock returns coroutine, test silently passes without checking behavior | Replace `MagicMock(spec=LLMServiceAdapter)` with `AsyncMock(spec=...)` per test file |
| `execute_stream` async generator in sync `for chunk in ...:` context → `TypeError: 'async_generator' object can't be iterated` | All callers using `execute_stream` must be in async context; verify with grep |
| Provider plugins' HTTP clients (sync) called from `asyncio.to_thread` — contextvars / asyncio state | Verify with integration test that doesn't hang in event loop |
| Tools with sync entry point (`def main()` calling `LLMServiceAdapter.execute()`) | Wrap with `asyncio.run(_async_main())` pattern |

## Open Decisions Locked In

1. **Data model**: Keep `LLMTask` + `str` return (not `TaskSpec` + `LLMResult`)
2. **Async strategy**: Full async migration (adapter + callers all async); concrete `LLMService` stays sync wrapped via `asyncio.to_thread`
3. **No sync compat shim**: All callers MUST migrate (no `execute_sync()` backdoor)
4. **Generate() retained but async**: legacy convenience method stays, becomes async
5. **TaskSpec + LLMResult removal**: Both removed from `lingwen_shared.ports.llm_service` and `ports/__init__.py` (declared but unused)

## Verification Gates (after each phase + at end)

| Gate | Command |
|------|---------|
| Backend tests | `env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ packages/lingwen-llm/tests/ packages/lingwen-creator/tests/ apps/studio_api/tests/ tests/infra/ tests/tools/ -v` |
| Frontend | `cd apps/dashboard && pnpm vitest run && pnpm tsc --noEmit` |
| Lint | `/home/ailearn/miniconda3/bin/python -m ruff check .` |
| Imports | (existing lint-imports 3 contracts must still pass) |

## Architecture Invariants Enforced (after completion)

1. (NEW) ✅ `LLMServicePort.execute` is `async def (LLMTask) -> str` — Protocol + Adapter + concrete all conform
2. (NEW) ✅ `LLMServiceAdapter.execute` is async; runs sync concrete in `asyncio.to_thread` (event loop not blocked)
3. (NEW) ✅ All `LLMServiceAdapter` callers `await` the result (no orphan sync callers)
4. (NEW) ✅ `LLMServicePort` no longer references `TaskSpec` or `LLMResult` (cleaned up unused declarations)

## Carryover to v16.5 #N.13+

- N.11.d (impact_score drift) — still deferred from N.11
- N.11.e (dashboard cascade field migration) — still deferred from N.11
- N.11.g (ReferenceGraphResponse full migration) — still deferred from N.11
- N.13+ (39 `as unknown as` cast cleanup) — sweeps across apps/dashboard/src/composables/

## Spec Self-Review

- **Placeholder scan**: No TBD/TODO/empty sections. ✓
- **Internal consistency**: Architecture → Components → Migration → Risks are mutually consistent. ✓
- **Scope check**: Single-phase implementation (16-22 commits, all related to async conformance). ✓
- **Ambiguity check**: "Sync vs async concrete" resolved via `asyncio.to_thread`; "Data model" resolved via keep-LLMTask decision. ✓
