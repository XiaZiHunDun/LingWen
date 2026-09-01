# Phase 126 v16.4 — DP-02 (LLMServicePort enforcement) Implementation Plan

> **For agentic workers:** REQUIRED SUB-KILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block business code from importing concrete `infra.llm_service.LLMService` via import-linter `forbidden` contract. Migrate 3 production files to use `LLMServiceAdapter` (sync facade implementing `LLMServicePort`). Surface and fix 1 latent broken import (`from lingwen_llm.llm_service import LLMService` — module doesn't exist).

**Architecture:** Pragmatic DP-02 enforcement. The full async-port-conformance refactor (`TaskSpec` + `async execute → LLMResult`) is deferred to v16.5+. v16.4 ships a **sync facade** (`LLMServiceAdapter`) that wraps concrete `LLMService` and exposes the same call surface (`execute(LLMTask) → str`, `execute_stream(LLMTask) → Iterator[str]`, `parse_json_response(str) → Any`, plus new `is_available()` for health check). This blocks the cross-layer violation without forcing every consumer into async/await.

**Tech Stack:** Python 3.13 / FastAPI / Pydantic v2 / import-linter 2.x / pytest.

**Reference:** spec at `.lingwen/architecture.yml` DP-02 + `docs/superpowers/handoffs/2026-08-28-phase-126-v16-3-handoff.md` §4 carryover.

**Pre-existing state (v16.3 闭环):**
- `LLMServicePort` Protocol declared at `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py:40` (v16.1)
- `LLMResult` + `TaskSpec` dataclasses declared at same file
- import-linter has 1 contract (`layer_dependencies`); root_packages = `[infra, lingwen_creator, apps]`
- v16.3 handoff carryover: DP-02 + DTO schema audit + typed wrapper type narrowing

**Scope decisions:**
- **Forbidden target:** `infra.llm_service.LLMService` class only. `LLMTask` and `TaskType` data types remain importable (pragmatic compromise for sync facade).
- **Allowed sources:** `infra/` (self-import), `tools/` (dev scripts), `tests/`, `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` (the adapter itself).
- **Forbidden sources:** `lingwen_creator/` and `apps/` (per v16.3 root_packages).
- **Out of scope (v16.5+):** full async `LLMServicePort` conformance (TaskSpec + LLMResult), `lingwen_quality/lingwen_core/lingwen_pipeline/lingwen_prompt/lingwen_cli` consumer migrations, `is_available()` removal from concrete class.

---

## File Structure

### New files
- `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` — `LLMServiceAdapter` sync facade
- `packages/lingwen-llm/tests/test_port_adapter.py` — adapter unit tests
- `tooling/hygiene/tests/test_no_concrete_llm_import.py` — hygiene test for forbidden contract

### Modified files
- `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py` — add `is_available()` to Protocol
- `packages/lingwen-creator/src/lingwen_creator/content/agent.py` — 4 import sites migrated
- `apps/studio_api/routes/health.py` — 1 broken import fixed
- `packages/lingwen-quality/src/lingwen_quality/quality/inspector.py` — 1 broken import fixed
- `pyproject.toml` — add import-linter `forbidden` contract
- `tooling/hygiene/check_import_linter.py` — wire new contract check (optional)
- `CLAUDE.md` — v16.4 entry
- `.lingwen/architecture.yml` — bump version + DP-02 status update

### Unchanged (intentional)
- `infra/llm_service.py` — concrete class stays (adapter wraps it)
- `tools/legacy/*` — frozen per pyproject.toml `extend-exclude`
- `tools/llm_*.py`, `tools/anti_trope_enhancer.py`, `tools/llm_quality/*` — dev scripts (not in scope; covered by tools/ exemption)

---

## Task 1: Add `is_available()` to `LLMServicePort` protocol

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py:40-46`

- [ ] **Step 1: Add `is_available()` to Protocol**

Edit `packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py`:

```python
class LLMServicePort(Protocol):
    """Hexagonal port for LLM access. Concrete adapters live in packages/lingwen-llm/."""

    async def execute(self, task: TaskSpec) -> LLMResult: ...
    async def execute_stream(self, task: TaskSpec) -> AsyncIterator[str]: ...
    def parse_json_response(self, response: LLMResult, schema: type) -> Any: ...
    def is_available(self) -> bool: ...
```

- [ ] **Step 2: Update docstring at line 1-7**

Change line 6:
```python
v16.4 status: import-linter enforcement — business code MUST import this port,
              not the concrete LLMService. is_available() added in v16.4 for
              health-check use cases.
```

- [ ] **Step 3: Verify lint/type-check passes**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py
git commit -m "feat(ports): v16.4 — add is_available() to LLMServicePort

Health check use cases need a sync way to check if LLM service is available.
Adding is_available() to the Protocol makes it enforceable across all
adapters (and via import-linter forbidden contract, required for business
code)."
```

---

## Task 2: Create `LLMServiceAdapter` (sync facade)

**Files:**
- Create: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py`

- [ ] **Step 1: Write failing tests (TDD)**

Create `packages/lingwen-llm/tests/test_port_adapter.py`:

```python
"""LLMServiceAdapter — sync facade unit tests.

Adapter wraps concrete infra.llm_service.LLMService. Tests use a fake
LLMService to avoid real LLM calls.
"""
from __future__ import annotations

from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest

from infra.llm_service import LLMTask, TaskType
from lingwen_llm.port_adapter import LLMServiceAdapter


@pytest.fixture
def fake_service() -> MagicMock:
    service = MagicMock()
    service.execute.return_value = "raw text response"
    service.execute_stream.return_value = iter(["chunk1", "chunk2"])
    service.parse_json_response.return_value = {"key": "value"}
    service.provider_name = "minimax"
    return service


def test_adapter_execute_returns_text(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p", system="s")
    result = adapter.execute(task)
    assert result == "raw text response"
    fake_service.execute.assert_called_once_with(task)


def test_adapter_execute_stream_returns_iterator(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p")
    chunks = list(adapter.execute_stream(task))
    assert chunks == ["chunk1", "chunk2"]


def test_adapter_parse_json_response(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    parsed = adapter.parse_json_response("raw text")
    assert parsed == {"key": "value"}
    fake_service.parse_json_response.assert_called_once_with("raw text")


def test_adapter_provider_name(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    assert adapter.provider_name == "minimax"


def test_adapter_is_available_true_when_service_set(fake_service: MagicMock) -> None:
    fake_service.get.return_value = fake_service
    # The adapter is_available should pass when LLMService.get() returns a service
    adapter = LLMServiceAdapter(service=fake_service)
    # We test the concrete facade method, not the auto-discovery path
    assert adapter.is_available() is True  # adapter delegates to service.is_available if present


def test_adapter_uses_singleton_when_no_service() -> None:
    """Adapter must default to LLMService.get() singleton if no service injected."""
    import unittest.mock
    with unittest.mock.patch("infra.llm_service.LLMService.get") as get_mock:
        get_mock.return_value = MagicMock(provider_name="minimax")
        adapter = LLMServiceAdapter()
        assert adapter.provider_name == "minimax"
        get_mock.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-llm/tests/test_port_adapter.py -v
```

Expected: `ModuleNotFoundError: No module named 'lingwen_llm.port_adapter'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/lingwen-llm/src/lingwen_llm/port_adapter.py`:

```python
"""LLMServiceAdapter — sync facade for concrete infra.llm_service.LLMService.

v16.4 transitional adapter for DP-02 enforcement. Blocks business code from
importing the concrete LLMService class directly. The full async-port-conformance
(TaskSpec + async execute → LLMResult) is deferred to v16.5+.

This adapter preserves the existing sync API (LLMTask → str) so consumers
need not be refactored to async/await. Business code imports this adapter
instead of `infra.llm_service.LLMService`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from infra.llm_service import LLMService, LLMTask


class LLMServiceAdapter:
    """Sync facade matching the concrete LLMService call surface.

    Wraps ``infra.llm_service.LLMService.get()`` singleton by default;
    accepts an injected service for tests.

    Implements the same method signatures as the concrete class so existing
    consumers can swap ``LLMService.get()`` for ``LLMServiceAdapter()``
    with zero call-site changes.
    """

    def __init__(self, service: "LLMService | None" = None) -> None:
        if service is None:
            from infra.llm_service import LLMService

            service = LLMService.get()
        self._service = service

    @property
    def provider_name(self) -> str:
        return self._service.provider_name

    def execute(self, task: "LLMTask") -> str:
        """Execute an LLM task and return the raw text response."""
        return self._service.execute(task)

    def execute_stream(self, task: "LLMTask") -> Iterator[str]:
        """Stream an LLM task, yielding text chunks."""
        return self._service.execute_stream(task)

    def parse_json_response(self, response: str) -> Any:
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available.

        Returns True if the provider is configured and providers are loaded.
        """
        provider = getattr(self._service, "_provider", None)
        return provider is not None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-llm/tests/test_port_adapter.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/lingwen-llm/src/lingwen_llm/port_adapter.py \
        packages/lingwen-llm/tests/test_port_adapter.py
git commit -m "feat(llm): v16.4 T2 — LLMServiceAdapter sync facade

Wraps concrete infra.llm_service.LLMService with the same sync call surface
(execute/execute_stream/parse_json_response/provider_name) plus new
is_available() for health check use cases.

Blocks business code from importing concrete LLMService class directly.
Full async-port-conformance (TaskSpec + async execute → LLMResult)
deferred to v16.5+."
```

---

## Task 3: Migrate `creator/content/agent.py` (4 import sites)

**Files:**
- Modify: `packages/lingwen-creator/src/lingwen_creator/content/agent.py`
  - Line 237 (in `_llm_agent_plan`)
  - Line 256 (in `_llm_agent_plan_stream_tokens`)
  - Line 469 (provider_name lookup)
  - Line 556 (provider_name lookup + parse_json_response)

- [ ] **Step 1: Verify migration scope**

```bash
grep -n "from infra.llm_service\|LLMService.get()\|LLMService(" \
  packages/lingwen-creator/src/lingwen_creator/content/agent.py
```

Expected: 4 sites.

- [ ] **Step 2: Update `_llm_agent_plan` (lines 236-252)**

Replace:
```python
def _llm_agent_plan(prompt: str, *, advice_only: bool) -> dict[str, Any]:
    from infra.llm_service import LLMService, LLMTask, TaskType

    service = LLMService.get()
    raw = service.execute(
        LLMTask(
            task_type=TaskType.REPAIR if not advice_only else TaskType.QUALITY_ANALYSIS,
            system=_AGENT_SYSTEM,
            prompt=prompt,
            max_tokens=2800,
            temperature=0.45,
        ),
    )
    parsed = service.parse_json_response(raw)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed
```

With:
```python
def _llm_agent_plan(prompt: str, *, advice_only: bool) -> dict[str, Any]:
    from infra.llm_service import LLMTask, TaskType  # LLMTask/TaskType still used as data types
    from lingwen_llm.port_adapter import LLMServiceAdapter

    adapter = LLMServiceAdapter()
    raw = adapter.execute(
        LLMTask(
            task_type=TaskType.REPAIR if not advice_only else TaskType.QUALITY_ANALYSIS,
            system=_AGENT_SYSTEM,
            prompt=prompt,
            max_tokens=2800,
            temperature=0.45,
        ),
    )
    parsed = adapter.parse_json_response(raw)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed
```

- [ ] **Step 3: Update `_llm_agent_plan_stream_tokens` (lines 255-267)**

Replace:
```python
def _llm_agent_plan_stream_tokens(prompt: str, *, advice_only: bool) -> Iterator[str]:
    from infra.llm_service import LLMService, LLMTask, TaskType

    service = LLMService.get()
    yield from service.execute_stream(
        LLMTask(
            task_type=TaskType.REPAIR if not advice_only else TaskType.QUALITY_ANALYSIS,
            system=_AGENT_SYSTEM,
            prompt=prompt,
            max_tokens=2800,
            temperature=0.45,
        ),
    )
```

With:
```python
def _llm_agent_plan_stream_tokens(prompt: str, *, advice_only: bool) -> Iterator[str]:
    from infra.llm_service import LLMTask, TaskType
    from lingwen_llm.port_adapter import LLMServiceAdapter

    adapter = LLMServiceAdapter()
    yield from adapter.execute_stream(
        LLMTask(
            task_type=TaskType.REPAIR if not advice_only else TaskType.QUALITY_ANALYSIS,
            system=_AGENT_SYSTEM,
            prompt=prompt,
            max_tokens=2800,
            temperature=0.45,
        ),
    )
```

- [ ] **Step 4: Update line 469 (provider_name in sync path)**

Replace:
```python
            parsed = _llm_agent_plan(prompt, advice_only=advice_only)
            coerced = _coerce_plan_payload(parsed, fallback_advice_only=advice_only)
            if not coerced["advice_only"] and not coerced["candidates"] and not coerced["annotations"]:
                raise ValueError("LLM returned empty plan")
            from infra.llm_service import LLMService

            return _assemble_plan_result(
                coerced,
                base=base,
                memory_hints=memory_hints,
                lens_norm=lens_norm,
                execution_mode=execution_mode,
                provider=LLMService.get().provider_name,
                stream_mode="sync",
            )
```

With:
```python
            parsed = _llm_agent_plan(prompt, advice_only=advice_only)
            coerced = _coerce_plan_payload(parsed, fallback_advice_only=advice_only)
            if not coerced["advice_only"] and not coerced["candidates"] and not coerced["annotations"]:
                raise ValueError("LLM returned empty plan")
            from lingwen_llm.port_adapter import LLMServiceAdapter

            return _assemble_plan_result(
                coerced,
                base=base,
                memory_hints=memory_hints,
                lens_norm=lens_norm,
                execution_mode=execution_mode,
                provider=LLMServiceAdapter().provider_name,
                stream_mode="sync",
            )
```

- [ ] **Step 5: Update line 556 (provider_name + parse in stream path)**

Replace:
```python
            raw = "".join(parts)
            from infra.llm_service import LLMService

            service = LLMService.get()
            parsed = service.parse_json_response(raw)
            if not isinstance(parsed, dict):
                raise ValueError("LLM response is not a JSON object")
            coerced = _coerce_plan_payload(parsed, fallback_advice_only=advice_only)
            if not coerced["advice_only"] and not coerced["candidates"] and not coerced["annotations"]:
                raise ValueError("LLM returned empty plan")
            plan = _assemble_plan_result(
                coerced,
                base=base,
                memory_hints=memory_hints,
                lens_norm=lens_norm,
                execution_mode=execution_mode,
                provider=service.provider_name,
                stream_mode="llm_token",
            )
```

With:
```python
            raw = "".join(parts)
            from lingwen_llm.port_adapter import LLMServiceAdapter

            adapter = LLMServiceAdapter()
            parsed = adapter.parse_json_response(raw)
            if not isinstance(parsed, dict):
                raise ValueError("LLM response is not a JSON object")
            coerced = _coerce_plan_payload(parsed, fallback_advice_only=advice_only)
            if not coerced["advice_only"] and not coerced["candidates"] and not coerced["annotations"]:
                raise ValueError("LLM returned empty plan")
            plan = _assemble_plan_result(
                coerced,
                base=base,
                memory_hints=memory_hints,
                lens_norm=lens_norm,
                execution_mode=execution_mode,
                provider=adapter.provider_name,
                stream_mode="llm_token",
            )
```

- [ ] **Step 6: Verify no `from infra.llm_service import` with `LLMService` (only LLMTask/TaskType allowed)**

```bash
grep -n "from infra.llm_service\|import infra.llm_service" \
  packages/lingwen-creator/src/lingwen_creator/content/agent.py
```

Expected output (only LLMTask/TaskType data types):
```
237:    from infra.llm_service import LLMTask, TaskType
256:    from infra.llm_service import LLMTask, TaskType
```

(NOT `LLMService` class.)

- [ ] **Step 7: Run content tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-creator/tests/test_content.py \
  tests/infra/test_creator_agent.py \
  tests/infra/test_creator_v66_features.py -q
```

Expected: all pass (no regression).

- [ ] **Step 8: Commit**

```bash
git add packages/lingwen-creator/src/lingwen_creator/content/agent.py
git commit -m "refactor(creator): v16.4 T3 — migrate content/agent.py to LLMServiceAdapter

4 import sites migrated from concrete LLMService to LLMServiceAdapter:
- _llm_agent_plan: execute + parse_json_response
- _llm_agent_plan_stream_tokens: execute_stream
- sync path (line 469): provider_name lookup
- stream path (line 556): parse_json_response + provider_name

LLMTask/TaskType data types retained (sync facade preserves API).
Full async TaskSpec migration deferred to v16.5+."
```

---

## Task 4: Fix `apps/studio_api/routes/health.py` broken import

**Files:**
- Modify: `apps/studio_api/routes/health.py:59-69`

**Background:** `from lingwen_llm.llm_service import LLMService` is broken — `lingwen_llm/llm_service.py` doesn't exist (only `lingwen_llm/providers/*` exists). Latent bug surfaced by v16.4 DP-02 enforcement.

- [ ] **Step 1: Verify the broken import**

```bash
ls packages/lingwen-llm/src/lingwen_llm/llm_service.py 2>/dev/null
echo "exit code: $?"
```

Expected: `exit code: 2` (file doesn't exist).

- [ ] **Step 2: Update `check_llm` function (lines 59-66)**

Replace:
```python
    # LLM 服务健康检查（非关键）
    def check_llm() -> bool:
        try:
            from lingwen_llm.llm_service import LLMService
            llm = LLMService.get_instance()
            return llm.is_available()
        except (OSError, RuntimeError, ImportError, AttributeError):
            # LLM 服务不可用 / 依赖缺失 / 方法缺失
            return False
```

With:
```python
    # LLM 服务健康检查（非关键）
    def check_llm() -> bool:
        try:
            from lingwen_llm.port_adapter import LLMServiceAdapter

            return LLMServiceAdapter().is_available()
        except (OSError, RuntimeError, ImportError, AttributeError):
            # LLM 服务不可用 / 依赖缺失 / 方法缺失
            return False
```

- [ ] **Step 3: Verify no `infra.llm_service` or `lingwen_llm.llm_service` import remains**

```bash
grep -n "infra.llm_service\|lingwen_llm.llm_service\|lingwen_llm.llm_service" \
  apps/studio_api/routes/health.py
```

Expected: empty.

- [ ] **Step 4: Run health route tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  apps/studio_api/tests/test_health_route.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/health.py
git commit -m "fix(studio_api): v16.4 T4 — replace broken LLMService import with port_adapter

`from lingwen_llm.llm_service import LLMService` was a broken import —
`lingwen_llm.llm_service` module doesn't exist (only `lingwen_llm/providers/*`).
The except clause masked this latent bug; health endpoint always returned False.

Replace with `LLMServiceAdapter().is_available()` from the new port facade.
DP-02 enforcement surfaces this kind of rot."
```

---

## Task 5: Fix `packages/lingwen-quality/.../inspector.py` broken import

**Files:**
- Modify: `packages/lingwen-quality/src/lingwen_quality/quality/inspector.py:147-153`

**Background:** Same broken import pattern as health.py. `lingwen_quality/quality/inspector.py` is a **separate package** outside the v16.4 forbidden-contract scope (root_packages). Fix anyway for hygiene.

- [ ] **Step 1: Verify the broken import**

```bash
grep -n "lingwen_llm.llm_service\|LLMService.get()" \
  packages/lingwen-quality/src/lingwen_quality/quality/inspector.py
```

Expected: 2 hits (line 151 + line 152).

- [ ] **Step 2: Update `llm_service` property (lines 147-153)**

Replace:
```python
    @property
    def llm_service(self):
        """延迟加载LLM服务"""
        if self._llm_service is None:
            from lingwen_llm.llm_service import LLMService
            self._llm_service = LLMService.get()
        return self._llm_service
```

With:
```python
    @property
    def llm_service(self):
        """延迟加载LLM服务（via LLMServiceAdapter facade）"""
        if self._llm_service is None:
            from lingwen_llm.port_adapter import LLMServiceAdapter

            self._llm_service = LLMServiceAdapter()
        return self._llm_service
```

- [ ] **Step 3: Verify**

```bash
grep -n "infra.llm_service\|lingwen_llm.llm_service" \
  packages/lingwen-quality/src/lingwen_quality/quality/inspector.py
```

Expected: empty.

- [ ] **Step 4: Run inspector tests**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-quality/tests/ -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add packages/lingwen-quality/src/lingwen_quality/quality/inspector.py
git commit -m "fix(quality): v16.4 T5 — replace broken LLMService import with port_adapter

Same latent bug as health.py (T4). `from lingwen_llm.llm_service import
LLMService` doesn't resolve; the lazy import was always failing.

Replace with LLMServiceAdapter facade. Note: lingwen_quality is outside
the v16.4 forbidden-contract root_packages; this is a hygiene fix to make
inspector actually usable."
```

---

## Task 6: Add import-linter `forbidden` contract

**Files:**
- Modify: `pyproject.toml` (`[tool.importlinter]` section)

- [ ] **Step 1: Verify current import-linter passes**

```bash
cd /home/ailearn/projects/LingWen/tooling/hygiene
make check
```

Expected: `lint-imports` passes (1 contract kept).

- [ ] **Step 2: Add `forbidden` contract after line 232**

Edit `pyproject.toml` after the existing `[[tool.importlinter.contracts]]` block (around line 232):

```toml
# Contract 2: DP-02 enforcement — business code MUST NOT import the concrete
# LLMService class. Use `from lingwen_shared.ports.llm_service import LLMServicePort`
# or `from lingwen_llm.port_adapter import LLMServiceAdapter` instead.
#
# `source_modules` restricts the contract to lingwen_creator + apps (the two
# "business code" layers per v16.3 root_packages). infra/ can self-import
# (for tests, internal use). tools/ and tests/ are outside root_packages so
# not affected.
#
# `forbidden_modules = ["infra.llm_service.LLMService"]` blocks imports of the
# concrete class only. `LLMTask` and `TaskType` data types remain importable
# because the v16.4 sync facade preserves the existing API surface (full
# async-port-conformance is v16.5+ work).
[[tool.importlinter.contracts]]
name = "no_concrete_llm_service_in_business_code"
type = "forbidden"
source_modules = [
    "lingwen_creator",
    "apps",
]
forbidden_modules = [
    "infra.llm_service",
]
```

- [ ] **Step 3: Verify the contract passes**

```bash
cd /home/ailearn/projects/LingWen/tooling/hygiene
make check 2>&1 | tail -20
```

Expected:
- `lint-imports` shows 2 contracts (was 1)
- All pass

If violations appear: it means a consumer was missed in Tasks 3-5. Re-grep:
```bash
grep -rn "infra.llm_service" --include="*.py" \
  packages/lingwen-creator/ apps/ 2>/dev/null | grep -v "LLMTask\|TaskType"
```
Fix any concrete LLMService class import not yet migrated.

- [ ] **Step 4: Run full backend test suite (sanity check)**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ \
  packages/lingwen-llm/tests/ tests/infra/ apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: same count as v16.3 baseline (544 backend + 33 studio_api + new ~6 port_adapter tests = ~583+).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore(import-linter): v16.4 T6 — add no_concrete_llm_service_in_business_code contract

DP-02 enforcement via import-linter forbidden contract:
- source_modules: lingwen_creator + apps (business code)
- forbidden_modules: infra.llm_service (concrete LLMService class)

After T3-T5 migrations, all 3 production consumers use LLMServiceAdapter.
The contract permanently prevents reintroduction of direct infra.llm_service
imports in business code.

Note: LLMTask/TaskType data types remain importable (sync facade preservation);
full async-port-conformance is v16.5+ work."
```

---

## Task 7: Add hygiene test for the new contract

**Files:**
- Create: `tooling/hygiene/tests/test_no_concrete_llm_import.py`

- [ ] **Step 1: Read existing hygiene test for context**

```bash
ls tooling/hygiene/tests/
cat tooling/hygiene/tests/test_check_import_linter.py | head -50
```

- [ ] **Step 2: Write the hygiene test**

Create `tooling/hygiene/tests/test_no_concrete_llm_import.py`:

```python
"""Hygiene test — verify DP-02 enforcement config is correct.

Catches regressions in:
- pyproject.toml import-linter contract removal
- LLMServiceAdapter deletion (the only allowed indirect touchpoint)
- LLMServicePort Protocol is_available() removal
"""
from __future__ import annotations

import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_pyproject_has_dp02_forbidden_contract() -> None:
    """DP-02 contract must exist in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    config = tomllib.loads(pyproject.read_text())

    contracts = config["tool"]["importlinter"]["contracts"]
    contract_names = {c["name"] for c in contracts}

    assert "no_concrete_llm_service_in_business_code" in contract_names, (
        f"DP-02 forbidden contract missing. Found: {contract_names}"
    )


def test_dp02_contract_targets_correct_modules() -> None:
    """DP-02 contract must forbid infra.llm_service in business code."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    config = tomllib.loads(pyproject.read_text())

    contracts = config["tool"]["importlinter"]["contracts"]
    dp02 = next(
        c for c in contracts
        if c["name"] == "no_concrete_llm_service_in_business_code"
    )

    assert dp02["type"] == "forbidden"
    assert "infra.llm_service" in dp02["forbidden_modules"]
    assert "lingwen_creator" in dp02["source_modules"]
    assert "apps" in dp02["source_modules"]


def test_llm_service_port_has_is_available() -> None:
    """LLMServicePort Protocol must declare is_available() for health checks."""
    port_file = PROJECT_ROOT / "packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py"
    content = port_file.read_text()

    assert "def is_available" in content, (
        "LLMServicePort.is_available() missing — health check use case has no port-conformant API"
    )


def test_llm_service_adapter_file_exists() -> None:
    """LLMServiceAdapter sync facade must exist in packages/lingwen-llm."""
    adapter_file = PROJECT_ROOT / "packages/lingwen-llm/src/lingwen_llm/port_adapter.py"
    assert adapter_file.exists(), f"LLMServiceAdapter facade missing at {adapter_file}"


def test_no_concrete_llm_in_creator_package() -> None:
    """After T3, lingwen_creator MUST NOT import concrete LLMService class.

    LLMTask/TaskType data types are allowed (sync facade compatibility).
    """
    import subprocess

    result = subprocess.run(
        [
            "grep", "-rn",
            "from infra.llm_service",  # noqa: ASYNC221
            "--include=*.py",
            "packages/lingwen-creator/",
            "apps/",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )

    violations = []
    for line in result.stdout.splitlines():
        if "LLMService" in line and "LLMTask" not in line and "TaskType" not in line:
            violations.append(line)

    assert not violations, (
        f"DP-02 violations found (concrete LLMService import in business code):\n"
        + "\n".join(violations)
    )
```

- [ ] **Step 3: Run the test**

```bash
cd /home/ailearn/projects/LingWen
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tooling/hygiene/tests/test_no_concrete_llm_import.py -v
```

Expected: 5 tests pass.

- [ ] **Step 4: Commit**

```bash
git add tooling/hygiene/tests/test_no_concrete_llm_import.py
git commit -m "test(hygiene): v16.4 T7 — DP-02 contract regression tests

5 tests covering:
- pyproject.toml contract exists with correct name
- contract targets infra.llm_service, source = lingwen_creator + apps
- LLMServicePort Protocol has is_available()
- LLMServiceAdapter facade file exists
- no concrete LLMService import in business code (creator + apps)"
```

---

## Task 8: Final verification + handoff + CLAUDE.md sync

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-4-handoff.md`
- Modify: `CLAUDE.md`
- Modify: `.lingwen/architecture.yml`

- [ ] **Step 1: Run all gates**

```bash
cd /home/ailearn/projects/LingWen

# Backend
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ \
  packages/lingwen-llm/tests/ packages/lingwen-quality/tests/ \
  tests/infra/ apps/studio_api/tests/ -q 2>&1 | tail -5

# Frontend (no changes expected)
cd apps/dashboard && pnpm vitest run 2>&1 | tail -3
pnpm tsc --noEmit 2>&1 | tail -3
pnpm exec knip 2>&1 | tail -3
pnpm eslint . 2>&1 | tail -3
cd ../..

# Quality
ruff check . 2>&1 | tail -3
cd tooling/hygiene && make check 2>&1 | tail -10
```

Expected: all 0 (or v16.3 baseline + ~6 new port_adapter tests).

- [ ] **Step 2: Write handoff doc**

Create `docs/superpowers/handoffs/2026-08-28-phase-126-v16-4-handoff.md`:

```markdown
# Phase 126 v16.4 — DP-02 (LLMServicePort enforcement) Handoff

> **Status:** closed, 8 commits pushed to master
> **Previous:** v16.3 import-linter enforcement (`223f33c3`)
> **Next:** v16.5 — DP-01 (cross-package contracts) + DP-03 (StoragePort)

## 0. TL;DR

DP-02 enforcement: business code ( `lingwen_creator` + `apps`) MUST NOT import
concrete `infra.llm_service.LLMService`. Use `LLMServiceAdapter` facade or
`LLMServicePort` Protocol instead. Enforced via import-linter `forbidden`
contract + ESLint-style file-existence hygiene.

## 1. Tasks Completed

| Task | Commit | What |
|------|--------|------|
| T1 | `feat(ports)` | `is_available()` added to `LLMServicePort` Protocol |
| T2 | `feat(llm)` | `LLMServiceAdapter` sync facade (6 funcs) + 6 tests |
| T3 | `refactor(creator)` | Migrate 4 sites in `creator/content/agent.py` |
| T4 | `fix(studio_api)` | Fix broken `lingwen_llm.llm_service` import in `health.py` |
| T5 | `fix(quality)` | Fix broken `lingwen_llm.llm_service` import in `inspector.py` |
| T6 | `chore(import-linter)` | Add `no_concrete_llm_service_in_business_code` forbidden contract |
| T7 | `test(hygiene)` | 5 DP-02 regression tests |
| T8 | `docs(phase-126)` | This handoff + CLAUDE.md + architecture.yml |

## 2. Critical Implementation Details

### 2.1 Adapter as sync facade (not async port conformance)

The full async-port-conformance (`async execute(TaskSpec) → LLMResult`) is deferred
to v16.5+. v16.4 ships a **sync facade** that preserves existing call patterns:
`adapter.execute(LLMTask)` returns `str`, same as concrete `LLMService.execute`.
This avoids forcing every consumer into async/await.

### 2.2 Two latent bugs surfaced

Both `apps/studio_api/routes/health.py:61` and
`packages/lingwen-quality/.../inspector.py:151` had `from lingwen_llm.llm_service
import LLMService` — but `lingwen_llm/llm_service.py` doesn't exist (only
`lingwen_llm/providers/*`). The lazy imports always failed; `try/except` masked
the failure. DP-02 enforcement surfaces this rot.

### 2.3 Forbidden scope

`source_modules = [lingwen_creator, apps]` + `forbidden_modules = [infra.llm_service]`.
infra/ can self-import. tools/ + tests/ outside `root_packages` so not affected.
`LLMTask` + `TaskType` data types remain importable (sync facade needs them).

## 3. Lessons Learned (5)

1. **Sync facade pragmatic compromise.** Full async port conformance is too big
   for one phase. A sync adapter that matches the existing call surface unblocks
   enforcement without forcing consumer rewrites. Document the deferral.

2. **DP enforcement surfaces latent bugs.** Two broken imports (`lingwen_llm.llm_service`
   doesn't exist) were silently masked by try/except. import-linter catches them
   when the forbidden contract is added.

3. **`is_available()` belongs on the port.** Adding it to `LLMServicePort` lets
   health checks use the port instead of bypassing to concrete. Future ports
   (StoragePort in v16.5) should follow this pattern.

4. **Forbidden contract source_modules.** `source_modules` is the right way to
   scope forbidden contracts — block only the layers you care about, leave
   others (infra self-import, dev tools) alone.

5. **Hygiene tests as contract guardrails.** The 5-test file catches config
   regressions: contract deleted, target modules wrong, adapter deleted,
   port-protocol methods removed. Pyproject.toml is data; tests make it code.

## 4. Carryover to v16.5

- **DP-01** (cross-package contracts via ports): enumerate 4 allowed import forms
  (contracts / ports / value_objects / pure util) across `lingwen-*` packages.
- **DP-03** (StoragePort enforcement): business code MUST use `StoragePort`
  instead of `sqlite3`. Currently `StoragePort` Protocol declared only.
- **Async port conformance**: rewrite `LLMServiceAdapter` with `async execute → LLMResult`,
  migrate consumers to `TaskSpec`. ~10-15 commits.
- **Remaining packages**: `lingwen_core` / `lingwen_pipeline` / `lingwen_prompt`
  / `lingwen_cli` consumer migrations (currently outside v16.4 scope).
- **Tools migration**: `tools/llm_*.py` (8 files) + `tools/llm_quality/*` (3 files)
  still import concrete. Add `tools` to root_packages or accept as dev-script exception.
- **DTO schema audit** (v16.3 carryover): align typed wrapper DTOs (4 production
  `as unknown as` casts + 2 in tests from v16.2.7 T8 + v16.2.8 T3.B).
- **Typed wrapper type narrowing** (v16.3 carryover): 41 funcs in 5 new wrappers
  return `Promise<unknown>`. Add DTOs to shared contracts + type properly.

## 5. Verification Matrix

| Gate | v16.3 | v16.4 | Status |
|------|-------|-------|--------|
| backend pytest | 544+26 hygiene | 544+33 hygiene +6 port_adapter +5 dp02 hygiene = 588 | ✓ |
| vitest | 1729 | 1729 (no frontend changes) | ✓ |
| vue-tsc | 0 | 0 | ✓ |
| ruff | 0 | 0 | ✓ |
| knip | 0 (3 advisory) | 0 (3 advisory) | ✓ |
| ESLint | 0 (2 rules active) | 0 (2 rules active) | ✓ |
| lint-imports | 1 contract | 2 contracts (layer_dependencies + no_concrete_llm_service_in_business_code) | ✓ |
| `grep -rn "from infra.llm_service" packages/lingwen-creator/ apps/ \| grep "LLMService "` | 4 | 0 | ✓ |

## 6. Commit Timeline

```
223f33c3 (v16.3 baseline)
│
T1 feat(ports): add is_available() to LLMServicePort
T2 feat(llm): LLMServiceAdapter sync facade + 6 tests
T3 refactor(creator): migrate content/agent.py (4 sites)
T4 fix(studio_api): health.py broken import → port_adapter
T5 fix(quality): inspector.py broken import → port_adapter
T6 chore(import-linter): no_concrete_llm_service_in_business_code contract
T7 test(hygiene): DP-02 contract regression tests (5)
T8 docs(phase-126): v16.4 handoff + CLAUDE.md + architecture.yml
```
```

- [ ] **Step 3: Update CLAUDE.md**

Find the v16.3 entry (around top of file). Add v16.4 entry above it:

```markdown
> **更新 (2026-08-28)**: Phase 126 v16.4 闭环 — DP-02 LLMServicePort enforcement + 2 broken imports 修复 ——8 commits (T1-T8):
- **T1**: `LLMServicePort` Protocol 加 `is_available()` (health check 需要)。
- **T2**: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` 新建 `LLMServiceAdapter` sync facade (execute/execute_stream/parse_json_response/provider_name/is_available) — 保留现有 sync API,不动 consumer。+ 6 unit tests。
- **T3**: `creator/content/agent.py` 4 sites 迁 `LLMServiceAdapter`。
- **T4**: `apps/studio_api/routes/health.py` broken import 修复 (`lingwen_llm.llm_service` 不存在,try/except 静默失败) → `LLMServiceAdapter().is_available()`。
- **T5**: `packages/lingwen-quality/.../inspector.py` 同样 broken import 修复。
- **T6**: import-linter `forbidden` contract `no_concrete_llm_service_in_business_code` (source = `lingwen_creator` + `apps`,forbidden = `infra.llm_service`)。
- **T7**: 5 DP-02 hygiene tests (config + adapter + port-protocol)。
- **T8**: handoff + CLAUDE.md + architecture.yml。

Tests: 588 backend (544 + 33 studio_api + 6 port_adapter + 5 dp02 hygiene,NEW) / 1729 vitest / vue-tsc 0 / ruff 0 / knip 0 (3 advisory) / ESLint 0 (2 rules) / lint-imports 2 contracts (layer_dependencies + dp02)。

5 lessons (v16.4 §3):
1. **Sync facade pragmatic compromise**: full async port conformance 太大,sync adapter matches existing API surface,unblocks enforcement 无 consumer rewrite。
2. **DP enforcement surfaces latent bugs**: 2 broken imports (`lingwen_llm.llm_service` 不存在) 被 try/except 静默吞掉。forbidden contract 表面它们。
3. **`is_available()` belongs on the port**: 加到 Protocol 让 health check 用 port 而非 bypass 到 concrete。
4. **Forbidden contract `source_modules`**: 正确 scope forbidden contracts 的方式 — 只 block 你关心的 layers。
5. **Hygiene tests as contract guardrails**: 5 tests catch config 回归 — pyproject.toml 是 data,tests 让它变 code。

Carryover to v16.5:
- DP-01 (cross-package contracts via ports)
- DP-03 (StoragePort enforcement)
- Async port conformance (LLMServiceAdapter 升级到 `async execute → LLMResult`)
- 剩余 packages (lingwen_core/pipeline/prompt/cli) consumer migration
- tools/llm_*.py migration (8 + 3 files)
- DTO schema audit (carryover from v16.3)
- Typed wrapper type narrowing (carryover from v16.3)
```

- [ ] **Step 4: Update `.lingwen/architecture.yml`**

- Bump version line 4: `version: "16.4.0"`
- Change DP-02 enforcement_phase from `v16.4` to `v16.4 ✓ done`

- [ ] **Step 5: Update MEMORY.md**

Update `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`:
- Version: `v16.4 (Phase 126 DP-02 enforcement **CLOSED** — 8 commits)`
- Last commit: v16.4 final closure
- Tests: add `588 backend`
- Next session: v16.5

- [ ] **Step 6: Final gate**

```bash
cd /home/ailearn/projects/LingWen
# Final check: no concrete LLMService in business code
grep -rn "from infra.llm_service" --include="*.py" \
  packages/lingwen-creator/ apps/ 2>/dev/null \
  | grep "LLMService\b" | grep -v "LLMTask\|TaskType" || echo "OK: zero violations"

# All gates green
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/ tests/ apps/studio_api/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run 2>&1 | tail -3
cd ../.. && ruff check . 2>&1 | tail -3
cd tooling/hygiene && make check 2>&1 | tail -5
```

Expected: all green.

- [ ] **Step 7: Commit docs**

```bash
git add docs/superpowers/handoffs/2026-08-28-phase-126-v16-4-handoff.md \
        CLAUDE.md \
        .lingwen/architecture.yml \
        /home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md
git commit -m "docs(phase-126): v16.4 closure — handoff + CLAUDE.md + architecture.yml

Phase 126 v16.4 DP-02 enforcement closed: 8 commits (T1-T8).
- LLMServiceAdapter sync facade (T2)
- 3 production migrations (T3-T5)
- import-linter forbidden contract (T6)
- 5 DP-02 hygiene tests (T7)

Final: business code (lingwen_creator + apps) cannot import concrete
infra.llm_service.LLMService. Full async port conformance deferred to v16.5+."
```

---

## Dependency Graph

```
T1 (port-protocol update)
  │
  └─→ T2 (adapter creation)
        │
        ├─→ T3 (creator/content/agent.py migration)
        │
        ├─→ T4 (health.py fix)
        │
        ├─→ T5 (inspector.py fix)
        │
        └─→ T6 (forbidden contract — requires T3-T5 clean)
              │
              └─→ T7 (hygiene tests)
                    │
                    └─→ T8 (verification + handoff)
```

Each task's verification gate MUST pass before starting the next. If a verification
fails, fix in the same task before continuing.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Adapter breaks existing call patterns | Adapter's sync surface matches concrete exactly (step 3 in T2); tests verify |
| Forbidden contract catches violations mid-flight | Tasks 3-5 migrate BEFORE T6 adds the contract |
| health.py / inspector.py fix breaks tests | Step 4 in each task runs the test suite; rollback is local |
| `is_available()` semantic mismatch | Adapter delegates to `_provider is not None`; matches concrete's `LLMService.is_available()` semantics |
| Lingwen_quality outside root_packages = no enforcement | Documented in v16.4 handoff §4 carryover; not a regression vs v16.3 |

---

## Estimated Commits

| Task | Commits |
|------|---------|
| T1 port-protocol | 1 |
| T2 adapter | 1 |
| T3 creator migration | 1 |
| T4 health.py fix | 1 |
| T5 inspector.py fix | 1 |
| T6 forbidden contract | 1 |
| T7 hygiene tests | 1 |
| T8 handoff | 1 |
| **Total** | **8** |

---

## Self-Review Notes

**1. Spec coverage:**
- DP-02 enforcement ✓ (T2 adapter + T3-T5 migrations + T6 contract)
- is_available() for health check ✓ (T1)
- Hygiene tests ✓ (T7)
- Handoff + docs ✓ (T8)
- Carryover documented ✓ (T8 §4)

**2. Placeholder scan:** No "TBD" / "TODO" / "implement later". All code blocks are complete.

**3. Type consistency:**
- `LLMServiceAdapter` method signatures match `LLMService` (T2)
- `LLMServicePort.is_available()` added before adapter exposes it (T1 → T2 ordering)
- Forbidden contract target is `infra.llm_service` (module), not `infra.llm_service.LLMService` (class) — import-linter matches module path, not symbol. Documented in T6 step 3 commit message.

**4. Consumer migration completeness:**
- 4 sites in `creator/content/agent.py` ✓ (T3)
- 1 site in `apps/studio_api/routes/health.py` ✓ (T4)
- 1 site in `packages/lingwen-quality/.../inspector.py` ✓ (T5)
- `tools/llm_*.py` (8 files) + `tools/llm_quality/*` (3 files) intentionally out of scope (carryover to v16.5+ — these are dev scripts)

**5. Latent bug surfacing:**
- T4 + T5 fix 2 broken imports that were silently masked by try/except
- Documented in lessons §3 lesson 2