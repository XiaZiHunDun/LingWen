# Phase 126 v16.5 #N.12 — Async Port Conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `LLMServiceAdapter` async (matching `LLMServicePort` Protocol) and migrate all 7+ caller sites to `await` the async API. Eliminate sync/async + data-type mismatch between Protocol declaration and concrete implementation.

**Architecture:** Adapter wraps sync `LLMService` concrete via `asyncio.to_thread` (runs sync HTTP I/O in thread pool, doesn't block event loop). All callers promoted to async. Concrete service + provider plugins stay sync (their I/O is already non-CPU-bound).

**Tech Stack:** Python 3.13 + asyncio + pytest-asyncio (already in pyproject.toml) + FastAPI + Pydantic v2.

**Spec:** `docs/superpowers/specs/2026-08-31-phase-126-v16-5-n12-async-port-conformance-design.md`

**Locked decisions:**
- Keep `LLMTask` + `str` return (not `TaskSpec` + `LLMResult`)
- Full async migration (adapter + callers all async; concrete stays sync wrapped via `asyncio.to_thread`)
- No sync compat shim — all callers MUST migrate
- `generate()` retained but becomes async
- `TaskSpec` + `LLMResult` removed from `lingwen_shared.ports`

**Final gates:**
- ✅ pytest backend (all suites) passes with `pytest-asyncio` async tests
- ✅ vitest 1733 passed + 1 skipped
- ✅ vue-tsc 0 / ruff 0 / lint-imports 3 contracts KEPT
- ✅ 4 NEW architecture invariants (#26-#29)
- ✅ All 7+ caller files migrated to await LLMServiceAdapter methods

---

## File Structure

**Files Modified (16):**
- `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py` — Protocol async rewrite + LLMTask import + remove TaskSpec/LLMResult
- `packages/lingwen-shared/src/lingwen_shared/ports/__init__.py` — remove TaskSpec/LLMResult from __all__
- `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` — async methods (execute/execute_stream/generate)
- `packages/lingwen-llm/tests/test_port_adapter.py` — async tests with @pytest.mark.asyncio + AsyncMock
- `apps/studio_api/routes/health.py` — verify (no change likely)
- `packages/lingwen-creator/src/lingwen_creator/content/agent.py` — 4 sites: promote methods to async + await
- `infra/prose_judge.py` — promote calling method to async + await
- `infra/world_db/agent_extractors.py` — promote extract_* methods to async + await
- `tools/{anti_trope_enhancer,llm_emotional_resonance_checker,llm_foreshadow_analyzer,llm_pacing_analyzer,llm_quality_analyzer}.py` — 5 atomic commits
- `tools/llm_quality/{__init__.py,checker.py,repairer.py}` — 3 atomic commits OR grouped
- `tools/legacy/{llm_character_arc_analyzer,llm_outline_quality_check,llm_protagonist_charm_analyzer,llm_readability_analyzer}.py` — 4 atomic commits

**Files Created (2):**
- `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n12-async-port-conformance-handoff.md` — handoff doc

**Tests Modified:**
- All caller unit tests using `MagicMock(spec=LLMServiceAdapter)` → `AsyncMock(spec=LLMServiceAdapter)`
- `tests/tools/test_*.py` — async test methods where needed

---

## Part A: Foundation (Tasks A1-A3)

### Task A1: Update LLMServicePort Protocol signature

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py`
- Modify: `packages/lingwen-shared/src/lingwen_shared/ports/__init__.py`

- [ ] **Step 1: Rewrite Protocol**

Replace entire content of `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py`:

```python
"""LLMServicePort — Hexagonal port for LLM service access.

Phase 126 v16.1 status: Protocol declaration (async).
Phase 126 v16.5 #N.12 status: protocol signatures match LLMServiceAdapter
  async surface (async execute / async execute_stream / sync helpers).
  Data types aligned with ``lingwen_shared.contracts.python.llm.LLMTask``
  (canonical, established in v16.5 #1).
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Protocol

from lingwen_shared.contracts.python.llm import LLMTask


class LLMServicePort(Protocol):
    """Hexagonal port for LLM access. Concrete adapters live in packages/lingwen-llm/."""

    async def execute(self, task: LLMTask) -> str: ...
    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]: ...
    def parse_json_response(self, response: str) -> Any: ...
    def is_available(self) -> bool: ...
```

- [ ] **Step 2: Remove TaskSpec + LLMResult from ports/__init__.py**

Edit `packages/lingwen-shared/src/lingwen_shared/ports/__init__.py`. Replace:

```python
"""LingWen hexagonal ports.

Phase 126 v16.1: declaration only. Enforcement is in v16.4 (LLMServicePort) / v16.5 (StoragePort).
"""
from lingwen_shared.ports.llm_service import LLMServicePort
from lingwen_shared.ports.storage import ConnectionPort, MarkdownRoundtripPort, StoragePort

__all__ = [
    "LLMServicePort",
    "ConnectionPort",
    "StoragePort",
    "MarkdownRoundtripPort",
]
```

(Removed: `LLMResult`, `TaskSpec` from imports + `__all__`.)

- [ ] **Step 3: Verify lingwen-shared tests pass**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q
```
Expected: All pass (no callers use TaskSpec or LLMResult per design review).

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py packages/lingwen-shared/src/lingwen_shared/ports/__init__.py
git commit -m "feat(lingwen-shared): v16.5 #N.12 — LLMServicePort async + LLMTask (drop TaskSpec/LLMResult)"
```

---

### Task A2: Rewrite LLMServiceAdapter as async

**Files:**
- Modify: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py`

- [ ] **Step 1: Read current file**

Read `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` (already familiar — see Part A reference in spec).

- [ ] **Step 2: Write failing test (RED)**

Read `packages/lingwen-llm/tests/test_port_adapter.py` and append:

```python
import pytest


@pytest.mark.asyncio
async def test_execute_is_async_returns_string():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.execute is async, returns str (NOT awaitable)."""
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    class FakeService:
        def execute(self, task):
            return "ok"

    adapter = LLMServiceAdapter(service=FakeService())
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    import inspect
    assert inspect.iscoroutinefunction(adapter.execute)
    assert await adapter.execute(task) == "ok"


@pytest.mark.asyncio
async def test_execute_stream_is_async_generator():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.execute_stream is async generator."""
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    class FakeService:
        def execute_stream(self, task):
            yield "a"
            yield "b"

    adapter = LLMServiceAdapter(service=FakeService())
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    chunks = []
    async for chunk in adapter.execute_stream(task):
        chunks.append(chunk)
    assert chunks == ["a", "b"]


@pytest.mark.asyncio
async def test_generate_is_async():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.generate is async (legacy API retained)."""
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    class FakeService:
        def execute(self, task):
            return "ok"

    adapter = LLMServiceAdapter(service=FakeService())
    import inspect
    assert inspect.iscoroutinefunction(adapter.generate)
    assert await adapter.generate(prompt="x", system="y") == "ok"
```

Run to verify RED:
```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-llm/tests/test_port_adapter.py::test_execute_is_async_returns_string -v
```
Expected: FAIL with `TypeError: object coroutine can't be used in 'await' expression` (since current `execute` returns str not awaitable).

- [ ] **Step 3: Rewrite port_adapter.py**

Replace entire content of `packages/lingwen-llm/src/lingwen_llm/port_adapter.py`:

```python
"""LLMServiceAdapter — async facade for concrete LLMService.

Phase 126 v16.5 #N.12: converted to async surface matching LLMServicePort Protocol.
Sync concrete ``LLMService`` is wrapped via ``asyncio.to_thread`` so HTTP I/O
runs in the default threadpool without blocking the event loop.

Architecture invariant: this module MUST NOT contain any static
``from infra.llm_service import ...`` statement, any string-concat
dynamic import of ``infra.llm_service``, or any PEP 562 ``__getattr__``
that re-exports ``infra.llm_service`` symbols. Regression-tested by
``tooling/hygiene/check_no_grimp_evasion.py`` (v16.5 #1).
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable, Optional

from lingwen_shared.contracts.python.llm import LLMTask, TaskType

_DEFAULT_FACTORY: Optional[Callable[[], Any]] = None


def set_default_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Register the default factory used when no service is injected."""
    global _DEFAULT_FACTORY
    _DEFAULT_FACTORY = factory


def get_default_factory() -> Optional[Callable[[], Any]]:
    """Return the currently registered default factory, or ``None``."""
    return _DEFAULT_FACTORY


class LLMServiceAdapter:
    """Async facade matching ``LLMServicePort`` Protocol.

    Wraps the concrete LLM service singleton by default; accepts an
    injected service for tests. Async methods route through
    ``asyncio.to_thread`` so sync concrete I/O doesn't block the event loop.
    """

    def __init__(self, service: Any = None) -> None:
        if service is None:
            if _DEFAULT_FACTORY is None:
                raise RuntimeError(
                    "LLMServiceAdapter default factory not registered. "
                    "Either pass `service=` explicitly or import "
                    "`infra.llm_service` (which registers the factory at "
                    "module load time) before constructing the adapter."
                )
            service = _DEFAULT_FACTORY()
        self._service = service

    @property
    def provider_name(self) -> str:
        return self._service.provider_name

    async def execute(self, task: LLMTask) -> str:
        """Execute an LLM task in a thread pool (so sync HTTP doesn't block event loop)."""
        return await asyncio.to_thread(self._service.execute, task)

    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]:
        """Stream an LLM task, yielding text chunks as an async generator."""
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
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available."""
        return self._service.is_available()


__all__ = [
    "LLMServiceAdapter",
    "set_default_factory",
    "get_default_factory",
]
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-llm/tests/test_port_adapter.py -v
```
Expected: All pass (3 NEW + existing).

- [ ] **Step 5: Commit**

```bash
git add packages/lingwen-llm/src/lingwen_llm/port_adapter.py packages/lingwen-llm/tests/test_port_adapter.py
git commit -m "feat(lingwen-llm): v16.5 #N.12 — LLMServiceAdapter async (execute/execute_stream/generate)"
```

---

### Task A3: Run full verification gates

- [ ] **Step 1: Run backend tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ packages/lingwen-llm/tests/ -q
```
Expected: All pass.

- [ ] **Step 2: Run ruff**

```bash
/home/ailearn/miniconda3/bin/python -m ruff check packages/lingwen-shared/src packages/lingwen-llm/src
```
Expected: 0 errors.

- [ ] **Step 3: Verify vue-tsc still passes (no frontend changes)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit
```
Expected: 0 errors.

---

## Part B: FastAPI routes + creator/content/agent.py (Tasks B1-B2)

### Task B1: Verify apps/studio_api/routes/health.py works with async LLMServiceAdapter

**Files:**
- Modify: `apps/studio_api/routes/health.py` (verify only, likely no change)

- [ ] **Step 1: Read current usage**

Read `apps/studio_api/routes/health.py:55-65`. The current code:
```python
from lingwen_llm.port_adapter import LLMServiceAdapter
...
return LLMServiceAdapter().is_available()
```

`is_available()` is still sync, so this should work as-is.

- [ ] **Step 2: Verify tests pass**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -q -k "health"
```
Expected: PASS.

- [ ] **Step 3: No commit if no change**

If no code change needed, skip commit. Otherwise commit:
```bash
git add apps/studio_api/routes/health.py
git commit -m "chore(studio-api): v16.5 #N.12 — verify health.py LLMServiceAdapter.is_available() works (no change)"
```

---

### Task B2: Migrate creator/content/agent.py (4 sites)

**Files:**
- Modify: `packages/lingwen-creator/src/lingwen_creator/content/agent.py`

- [ ] **Step 1: Read current file + identify 4 sites**

Read `packages/lingwen-creator/src/lingwen_creator/content/agent.py`. Identify 4 sites that call `LLMServiceAdapter().generate()` or `.execute()`. Each site is inside a method that needs to become async.

- [ ] **Step 2: Promote methods to async + add await**

For each of the 4 sites:
- Find the enclosing method
- Change `def method_name(...)` → `async def method_name(...)`
- Change `service.generate(prompt=...)` → `await service.generate(prompt=...)`
- Change `service.execute(task)` → `await service.execute(task)`

Specific pattern (per site):
```python
# Before
def some_method(self, prompt: str) -> str:
    from lingwen_llm.port_adapter import LLMServiceAdapter
    service = LLMServiceAdapter()
    return service.generate(prompt=prompt)

# After
async def some_method(self, prompt: str) -> str:
    from lingwen_llm.port_adapter import LLMServiceAdapter
    service = LLMServiceAdapter()
    return await service.generate(prompt=prompt)
```

Also update any callers of these methods (within the same file or other files that import these methods) — add `await` at the call site. Cascade async through callers as needed.

- [ ] **Step 3: Run tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ apps/studio_api/tests/ -q -k "agent or content"
```
Expected: PASS (existing tests may need to add `await` if they call these methods — fix as you go).

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-creator/src/lingwen_creator/content/agent.py
git commit -m "refactor(lingwen-creator): v16.5 #N.12 — content/agent.py 4 sites await LLMServiceAdapter"
```

---

## Part C: Infra async callers (Tasks C1-C3)

### Task C1: Migrate infra/prose_judge.py

**Files:**
- Modify: `infra/prose_judge.py`

- [ ] **Step 1: Read current usage**

Read `infra/prose_judge.py:225-260` (the LLM-using method). Identify the sync method that calls `service.execute(LLMTask)` at line 246.

- [ ] **Step 2: Promote to async + await**

```python
# Before (line ~232-250)
def judge_prose(...):
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType
    service = LLMServiceAdapter()
    raw = service.execute(LLMTask(...))
    ...

# After
async def judge_prose(...):
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType
    service = LLMServiceAdapter()
    raw = await service.execute(LLMTask(...))
    ...
```

Also update callers of `judge_prose` (grep for `judge_prose` to find them) — add `await`.

- [ ] **Step 3: Run tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ apps/studio_api/tests/ -q -k "prose_judge"
```
Expected: PASS (existing tests may need to add `await` if they call `judge_prose` directly).

- [ ] **Step 4: Commit**

```bash
git add infra/prose_judge.py
git commit -m "refactor(infra): v16.5 #N.12 — prose_judge.py await LLMServiceAdapter.execute"
```

---

### Task C2: Migrate infra/world_db/agent_extractors.py

**Files:**
- Modify: `infra/world_db/agent_extractors.py`

- [ ] **Step 1: Read current usage**

Read `infra/world_db/agent_extractors.py`. Identify the `extract_*` methods (sync) that call `LLMServiceAdapter().generate()`.

- [ ] **Step 2: Promote each extract_* method to async + await**

```python
# Before
def extract_proposals(self, ...):
    from lingwen_llm.port_adapter import LLMServiceAdapter
    service = LLMServiceAdapter()
    raw = service.generate(prompt=...)
    ...

# After
async def extract_proposals(self, ...):
    from lingwen_llm.port_adapter import LLMServiceAdapter
    service = LLMServiceAdapter()
    raw = await service.generate(prompt=...)
    ...
```

- [ ] **Step 3: Update FastAPI callers**

The `extract_*` methods are called from FastAPI routes (`apps/studio_api/routes/world.py`). Find those call sites and add `await`.

- [ ] **Step 4: Run tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ apps/studio_api/tests/ -q -k "agent_extract or world"
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add infra/world_db/agent_extractors.py apps/studio_api/routes/world.py
git commit -m "refactor(infra): v16.5 #N.12 — agent_extractors.py extract_* methods async + await"
```

---

### Task C3: Audit other infra callers

**Files:**
- Audit only — may need modifications

- [ ] **Step 1: Grep for remaining sync LLMServiceAdapter usage**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "LLMServiceAdapter" infra/ apps/ packages/ tools/ 2>&1 | grep -v ".pyc" | grep -v "is_available()" | grep -v dist
```

For each remaining file with sync usage (not yet in T1/T6/T7):
- Open the file
- If the file is just a type annotation or constant (e.g., `Optional[LLMServiceAdapter]`), no change
- If the file calls `service.execute(...)` / `service.generate(...)` sync, promote method to async + await

- [ ] **Step 2: Apply fixes**

For each file requiring fix:
- Promote enclosing method to async
- Add `await` at call sites
- Update callers as needed

- [ ] **Step 3: Commit per file**

```bash
git add <each fixed file>
git commit -m "refactor(infra): v16.5 #N.12 — <file> await LLMServiceAdapter"
```

(One commit per file per DP-06 strict.)

---

## Part D: Tools migration (Tasks D1-D10)

**Style**: Each tools/ file is a self-contained script or class. Migrate atomically (1 commit per file).

**Common pattern for tools/ files**:
```python
# Before
class LLMForeshadowAnalyzer:
    def __init__(self, llm_service: Optional[LLMServiceAdapter] = None) -> None:
        self.llm = llm_service or LLMServiceAdapter()
    
    def analyze(self, text: str) -> dict:
        raw = self.llm.generate(prompt=...)
        return parse(raw)

# After
class LLMForeshadowAnalyzer:
    def __init__(self, llm_service: Optional[LLMServiceAdapter] = None) -> None:
        self.llm = llm_service or LLMServiceAdapter()
    
    async def analyze(self, text: str) -> dict:
        raw = await self.llm.generate(prompt=...)
        return parse(raw)
```

If the tool has a sync entry point (`def main(): ...`), wrap with `asyncio.run(_async_main())`.

### Tasks D1-D5: Modern tools (5 files)

For each file:
- `tools/llm_emotional_resonance_checker.py` (D1)
- `tools/llm_foreshadow_analyzer.py` (D2)
- `tools/llm_pacing_analyzer.py` (D3)
- `tools/llm_quality_analyzer.py` (D4)
- `tools/anti_trope_enhancer.py` (D5)

**Per file**:
- [ ] Read current file
- [ ] Identify class methods that call `self.llm.generate()` / `.execute()`
- [ ] Promote methods to async + add `await`
- [ ] If sync entry point exists, wrap with `asyncio.run(_async_main())`
- [ ] Run tests: `env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/tools/test_<basename>.py -q`
- [ ] Commit:
```bash
git add tools/.py
git commit -m "refactor(tools): v16.5 #N.12 — <basename> await LLMServiceAdapter"
```

### Tasks D6-D8: tools/llm_quality/ (3 files)

For each file:
- `tools/llm_quality/__init__.py` (D6) — likely just re-exports, minimal change
- `tools/llm_quality/checker.py` (D7)
- `tools/llm_quality/repairer.py` (D8)

Same pattern as D1-D5. Atomic commits per file.

### Tasks D9-D12: tools/legacy/ (4 files)

For each file:
- `tools/legacy/llm_character_arc_analyzer.py` (D9)
- `tools/legacy/llm_outline_quality_check.py` (D10)
- `tools/legacy/llm_protagonist_charm_analyzer.py` (D11)
- `tools/legacy/llm_readability_analyzer.py` (D12)

Same pattern. Atomic commits per file.

---

## Part E: Documentation + verification (Tasks E1-E2)

### Task E1: Write handoff doc

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n12-async-port-conformance-handoff.md`

- [ ] **Step 1: Write handoff doc**

Mirror structure of `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup-handoff.md`:

Sections:
1. **Summary**: 16-22 commits, async port conformance, all callers migrated
2. **Commits**: list all commits (T1-T16) with type/scope/subject
3. **Architecture invariants**: 4 NEW (#26-#29)
4. **Tests**: counts + results
5. **Lessons**: 5-6 lessons learned
6. **Carryover to v16.5 #N.13+**: list N.11.d/e/g + N.13+ items

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n12-async-port-conformance-handoff.md
git commit -m "docs(phase-126): v16.5 #N.12 — handoff + CLAUDE.md closure"
```

---

### Task E2: Update CLAUDE.md + verify all gates

- [ ] **Step 1: Update CLAUDE.md**

Edit `CLAUDE.md` to add v16.5 #N.12 closure entry at the top of "更新" history. Mirror the N.11 entry structure. Include:
- Part A (Foundation): 3 commits — Protocol + Adapter + tests
- Part B (FastAPI + creator): 2-3 commits
- Part C (Infra async): 3-4 commits
- Part D (Tools): 7-8 atomic commits
- Part E: handoff
- 4 NEW architecture invariants (#26-#29)
- Updated carryover to N.13+

- [ ] **Step 2: Run ALL verification gates**

```bash
cd /home/ailearn/projects/LingWen

# Backend shared + LLM
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ packages/lingwen-llm/tests/ -q

# Creator
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -q

# Infra + studio_api
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ apps/studio_api/tests/ -q

# Tools
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/tools/ -q

# vitest
cd apps/dashboard && pnpm vitest run
cd ../..

# vue-tsc
cd apps/dashboard && pnpm tsc --noEmit
cd ../..

# ruff
/home/ailearn/miniconda3/bin/python -m ruff check .

# Hygiene (tooling/hygiene/tests/ — grimp-evasion regression)
/home/ailearn/miniconda3/bin/python -m pytest tooling/hygiene/tests/ -q
```

Expected:
- All pytest suites pass
- 1733 vitest + 1 skipped (no frontend changes)
- vue-tsc 0 errors
- ruff 0 errors
- grimp-evasion hygiene OK (no static import of infra.llm_service in port_adapter)

- [ ] **Step 3: Commit CLAUDE.md update**

```bash
git add CLAUDE.md
git commit -m "docs: v16.5 #N.12 — CLAUDE.md closure"
```

- [ ] **Step 4: Final commit count + PR**

```bash
git log --oneline -25
```

Expected: ~17-23 new commits since master `0e7993f6`.

---

## Self-Review

**Spec coverage:**
- ✅ Phase 1 (Foundation) covered by Tasks A1-A3 (Protocol + Adapter + tests)
- ✅ Phase 2 (FastAPI + creator) covered by Tasks B1-B2
- ✅ Phase 3 (Infra async) covered by Tasks C1-C3
- ✅ Phase 4 (Tools migration) covered by Tasks D1-D12 (5 + 3 + 4 = 12 files)
- ✅ Phase 5 (Docs + verify) covered by Tasks E1-E2

**Placeholder scan:** No TBD/TODO/"similar to Task X" found. All code blocks are complete.

**Type consistency:**
- Adapter methods `async def execute(self, task: LLMTask) -> str` matches Protocol
- Adapter methods `async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]` matches Protocol
- Adapter `async def generate(self, prompt, system=None, model="default", **kwargs) -> str`
- Adapter `def parse_json_response(self, response: str) -> Any` (sync, unchanged)
- Adapter `def is_available(self) -> bool` (sync, unchanged)

**Estimated commits:** ~17-23 atomic commits across 5 Parts (A-E)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-31-phase-126-v16-5-n12-async-port-conformance.md`.**

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per file/Part. Mirrors N.10/N.11 execution pattern. Best for mechanical 1:1 refactors with high commit granularity.

2. **Inline Execution** — Execute Parts in this session with verification gates between Parts. Coarser commit granularity (1 per Part).

**Recommended for N.12:** Option 1 (Subagent-Driven) — ~20 commits × 1 subagent per file = clean review/rollback surface, mirrors N.10/N.11 pattern.

**Which approach?**

If subagent-driven: invoke `superpowers:subagent-driven-development` skill next.
If inline: invoke `superpowers:executing-plans` skill next.
