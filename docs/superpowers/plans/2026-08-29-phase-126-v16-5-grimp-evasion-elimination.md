# v16.5 #1: Eliminate Grimp-Evasion Hack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the v16.4 grimp-evasion hack in `lingwen_llm/port_adapter.py` by relocating `LLMTask`/`TaskType` to `lingwen_shared` and using a factory pattern for the default service.

**Architecture:**
- **Canonical source**: `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` — `TaskType` (Enum) + `LLMTask` (dataclass).
- **Back-compat**: `infra/llm_service.py` re-exports both symbols (zero behavioral change for tools/, tests/, infra/core/__init__.py star-imports).
- **Factory pattern**: `infra/llm_service.py` registers `LLMService.get` as the default factory for `LLMServiceAdapter` at module load time. `port_adapter.py` calls the factory (no static import of `infra.llm_service` → grimp can't see the transitive chain).
- **Consumer migration**: `creator/content/agent.py` + `infra/prose_judge.py` + `infra/world_db/agent_extractors.py` import `LLMTask`/`TaskType` directly from `lingwen_shared` (no more "re-export for DP-02" wrapper).

**Tech Stack:** Python 3.12+ dataclass + Enum (no Pydantic — internal data types, not DTOs). import-linter 2.x for grimp-based forbidden contract.

---

## Context: Why this matters

v16.4 T6.5b added grimp-evasion hack to `port_adapter.py` because grimp follows transitive imports. The chain `lingwen_creator.content.agent → lingwen_llm.port_adapter → infra.llm_service` triggered the DP-02 forbidden contract. The hack used string-concat + PEP 562 `__getattr__` to hide the import from grimp.

**Problems with the hack:**
- Static analysis is circumvented — future refactors can silently break
- If `infra.llm_service` is renamed, the string-concat silently breaks
- Architectural intent (data types in infra/) contradicts enforcement goal (no infra.llm_service imports in business code)

**Solution:** Move the data types OUT of `infra.llm_service` and INTO `lingwen_shared`. Then `port_adapter.py` doesn't need to import from infra.llm_service for the data types. The default service singleton is wired via factory registration at startup (infra.llm_service registers itself when imported).

---

## File Structure

| File | Responsibility |
|------|---------------|
| `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` | **NEW** — canonical `TaskType` + `LLMTask` |
| `packages/lingwen-shared/src/lingwen_shared/contracts/python/__init__.py` | Re-export from `llm` module |
| `packages/lingwen-shared/tests/test_llm_dto.py` | **NEW** — verify data types |
| `infra/llm_service.py` | Remove local defs, import + re-export from lingwen_shared, register factory |
| `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` | Remove grimp-evasion, use factory + clean imports |
| `packages/lingwen-llm/tests/test_port_adapter.py` | Update imports + factory test pattern |
| `packages/lingwen-creator/src/lingwen_creator/content/agent.py` | Change 2 LLMTask/TaskType import sites |
| `infra/prose_judge.py` | Change LLMTask/TaskType import site |
| `infra/world_db/agent_extractors.py` | Confirm LLMServiceAdapter import unchanged |
| `tooling/hygiene/check_no_grimp_evasion.py` | **NEW** — regression test asserting no string-concat or PEP 562 in port_adapter.py |

---

## Task 1: Create lingwen_shared LLM contracts (canonical source)

**Files:**
- Create: `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`
- Test: `packages/lingwen-shared/tests/test_llm_dto.py`

- [ ] **Step 1.1: Write the failing test**

Create `packages/lingwen-shared/tests/test_llm_dto.py`:

```python
"""Tests for lingwen_shared.contracts.python.llm canonical data types.

v16.5: LLMTask and TaskType relocated from infra.llm_service to
lingwen_shared so the LLMServiceAdapter can import them without
crossing into infra.llm_service (which would re-trigger the DP-02
forbidden contract via grimp transitive analysis).
"""
from __future__ import annotations

import pytest

from lingwen_shared.contracts.python.llm import LLMTask, TaskType


def test_task_type_values_match_infra_baseline() -> None:
    """TaskType enum must expose the six task kinds used by infra.llm_service."""
    assert TaskType.WORLDVIEW_CHECK.value == "worldview_check"
    assert TaskType.CHARACTER_CHECK.value == "character_check"
    assert TaskType.LOGIC_CHECK.value == "logic_check"
    assert TaskType.AI_TRACE_CHECK.value == "ai_trace_check"
    assert TaskType.QUALITY_ANALYSIS.value == "quality_analysis"
    assert TaskType.REPAIR.value == "repair"


def test_llm_task_required_fields() -> None:
    """LLMTask must require task_type + prompt; everything else has defaults."""
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="hello")
    assert task.task_type is TaskType.QUALITY_ANALYSIS
    assert task.prompt == "hello"
    assert task.max_tokens == 2000
    assert task.temperature == 0.3
    assert task.system is None


def test_llm_task_override_fields() -> None:
    """All fields are settable via constructor kwargs."""
    task = LLMTask(
        task_type=TaskType.REPAIR,
        prompt="fix it",
        max_tokens=3000,
        temperature=0.7,
        system="you are a careful editor",
    )
    assert task.task_type is TaskType.REPAIR
    assert task.prompt == "fix it"
    assert task.max_tokens == 3000
    assert task.temperature == 0.7
    assert task.system == "you are a careful editor"


def test_llm_task_equality() -> None:
    """LLMTask is a dataclass — two tasks with same fields compare equal."""
    a = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    b = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    assert a == b


def test_llm_task_is_dataclass_not_pydantic() -> None:
    """LLMTask stays a stdlib dataclass (no Pydantic overhead — internal type)."""
    import dataclasses

    assert dataclasses.is_dataclass(LLMTask)


def test_module_importable_via_package_root() -> None:
    """Symbols re-exported from lingwen_shared.contracts.python (T2)."""
    from lingwen_shared.contracts.python import LLMTask as RootTask
    from lingwen_shared.contracts.python import TaskType as RootType

    assert RootTask is LLMTask
    assert RootType is TaskType
```

- [ ] **Step 1.2: Run test to verify it fails**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-shared/tests/test_llm_dto.py --rootdir=packages/lingwen-shared -q
```

Expected: `ModuleNotFoundError: No module named 'lingwen_shared.contracts.python.llm'`

- [ ] **Step 1.3: Create the module**

Create `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`:

```python
"""LLM data-type contracts (TaskType enum + LLMTask dataclass).

v16.5 relocation: moved from ``infra.llm_service`` to ``lingwen_shared``
so that ``lingwen_llm.port_adapter`` can import the data types without
crossing into ``infra.llm_service`` (which would re-trigger the DP-02
forbidden contract via grimp transitive analysis).

These are infrastructure-level types, not DTOs crossing the wire. They use
``@dataclass`` + ``class Enum`` for low-overhead runtime construction —
no Pydantic v2 validation needed (they're consumed inside Python only).

Back-compat: ``infra.llm_service`` re-exports ``LLMTask`` and ``TaskType``
via ``from lingwen_shared.contracts.python.llm import LLMTask, TaskType``,
so existing consumers in ``tools/`` and ``tests/`` that import from
``infra.llm_service`` keep working unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """LLM task types.

    Matches the original TaskType in ``infra.llm_service`` (v15.7+) so
    existing serialized task-type string values (e.g. stored in DB or
    passed across process boundaries) remain stable.
    """

    WORLDVIEW_CHECK = "worldview_check"      # 世界观检测
    CHARACTER_CHECK = "character_check"      # 角色一致性检测
    LOGIC_CHECK = "logic_check"              # 逻辑矛盾检测
    AI_TRACE_CHECK = "ai_trace_check"       # AI痕迹检测
    QUALITY_ANALYSIS = "quality_analysis"    # 质量综合分析
    REPAIR = "repair"                        # 修复任务


@dataclass
class LLMTask:
    """LLM task descriptor.

    Plain dataclass (not Pydantic) because it is an internal Python-only
    type that does not cross any wire boundary. Validation happens at the
    provider layer.
    """

    task_type: TaskType
    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.3
    system: str | None = None


__all__ = ["LLMTask", "TaskType"]
```

- [ ] **Step 1.4: Run test to verify it passes**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-shared/tests/test_llm_dto.py --rootdir=packages/lingwen-shared -q
```

Expected: `6 passed`

- [ ] **Step 1.5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py \
        packages/lingwen-shared/tests/test_llm_dto.py
git commit -m "feat(shared): v16.5 — relocate LLMTask/TaskType to lingwen_shared

v16.4 placed these types in infra.llm_service, forcing grimp-evasion
hack in port_adapter.py. v16.5 relocates the canonical definition to
lingwen_shared so the LLMServiceAdapter can import them cleanly.

infra.llm_service will keep re-exporting both symbols for back-compat
in a follow-up commit."
```

---

## Task 2: Re-export from lingwen_shared.contracts.python root

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/__init__.py`

- [ ] **Step 2.1: Add re-export to __init__.py**

Read current `__init__.py` (one-line docstring), then replace with:

```python
"""lingwen_shared.contracts.python — Pydantic v2 source-of-truth DTO.

Plus v16.5: plain dataclass/enum LLM data types (LLMTask, TaskType).
"""
from lingwen_shared.contracts.python.llm import LLMTask, TaskType

__all__ = ["LLMTask", "TaskType"]
```

- [ ] **Step 2.2: Run test to verify root import works**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-shared/tests/test_llm_dto.py --rootdir=packages/lingwen-shared -q
```

Expected: `6 passed` (test_module_importable_via_package_root now passes too)

- [ ] **Step 2.3: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/__init__.py
git commit -m "feat(shared): v16.5 — re-export LLMTask/TaskType from contracts.python"
```

---

## Task 3: Update infra/llm_service.py — remove local defs, import from lingwen_shared

**Files:**
- Modify: `infra/llm_service.py:1-55` (remove TaskType + LLMTask class defs) and `infra/llm_service.py:97-102, 277-290` (update type annotations)

- [ ] **Step 3.1: Verify back-compat: existing infra tests still pass**

Run baseline before changes:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/infra/test_llm_service.py apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: 33 tests pass (already verified).

- [ ] **Step 3.2: Replace TaskType class with import + re-export**

In `infra/llm_service.py`, replace lines 25-54 (the `class TaskType` + `class LLMTask` definitions) with:

```python
# v16.5 relocation: TaskType + LLMTask moved to lingwen_shared.contracts.python.llm.
# Re-export here so tools/, tests/, infra/core/__init__.py star-imports keep working.
from lingwen_shared.contracts.python.llm import LLMTask, TaskType

__all__ = [
    "LLMService",
    "LLMTask",
    "TaskType",
    "get_llm_service",
    "create_task",
]
```

- [ ] **Step 3.3: Run infra + studio_api tests to verify back-compat**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/infra/test_llm_service.py apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: All tests pass (back-compat works via re-export).

- [ ] **Step 3.4: Run lint + import-linter**

Run:
```bash
ruff check infra/llm_service.py
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  lint-imports 2>&1 | tail -10
```

Expected: ruff clean, import-linter still reports 2 contracts KEPT.

- [ ] **Step 3.5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add infra/llm_service.py
git commit -m "refactor(infra): v16.5 — import LLMTask/TaskType from lingwen_shared

Back-compat re-export preserves tools/, tests/, infra/core/__init__.py
star-imports. Canonical definition now lives in lingwen_shared so the
LLMServiceAdapter can stop using grimp-evasion hack."
```

---

## Task 4: Register LLMServiceAdapter default factory in infra/llm_service.py

**Files:**
- Modify: `infra/llm_service.py` — append factory registration after class definition

- [ ] **Step 4.1: Append factory registration at end of file**

Read current end of `infra/llm_service.py` (after `create_task` function). Add:

```python


# v16.5: Register LLMService.get as the default factory for LLMServiceAdapter.
# This eliminates the v16.4 grimp-evasion hack in port_adapter.py (which used
# string-concat to hide ``importlib.import_module("infra.llm_service")``).
#
# Side effect on import: importing ``infra.llm_service`` anywhere in the process
# wires up ``LLMServiceAdapter()`` default behavior. Tests that mock the adapter
# can either inject ``service=`` explicitly or rely on this registration.
from lingwen_llm.port_adapter import set_default_factory


def _default_service_factory() -> "LLMService":
    """Factory returning the LLMService singleton (lazy)."""
    return LLMService.get()


set_default_factory(_default_service_factory)
```

- [ ] **Step 4.2: Verify no circular import**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -c \
  "import infra.llm_service; print('OK'); from lingwen_llm.port_adapter import LLMServiceAdapter; a = LLMServiceAdapter(); print(a.is_available())"
```

Expected: `OK` then `True` (or `False` if no API key — both acceptable).

- [ ] **Step 4.3: Run all infra + studio_api tests**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/infra/ apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: 392 passed, 5 skipped (unchanged from baseline).

- [ ] **Step 4.4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add infra/llm_service.py
git commit -m "feat(infra): v16.5 — register LLMService as LLMServiceAdapter default factory

Eliminates the need for the grimp-evasion hack in port_adapter.py.
infra.llm_service registers itself at module load time so any subsequent
LLMServiceAdapter() call resolves to the singleton without crossing
back into infra.llm_service via dynamic import."
```

---

## Task 5: Refactor port_adapter.py — remove all grimp-evasion hacks

**Files:**
- Modify: `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` — full rewrite

- [ ] **Step 5.1: Replace port_adapter.py with factory-pattern version**

Replace the entire content of `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` with:

```python
"""LLMServiceAdapter — sync facade for concrete LLMService.

v16.5: removed all string-concat + PEP 562 workarounds (v16.4 hack).
Data types (``LLMTask``, ``TaskType``) now imported directly from
``lingwen_shared.contracts.python.llm``. The default service is resolved
via a factory registered at startup by ``infra.llm_service`` — this
ensures the import graph never crosses from ``lingwen_llm`` into
``infra.llm_service`` (which would re-trigger the DP-02 forbidden
contract via grimp transitive analysis).

Architecture invariant: this module MUST NOT contain any static
``from infra.llm_service import ...`` statement, any string-concat
dynamic import of ``infra.llm_service``, or any PEP 562 ``__getattr__``
that re-exports ``infra.llm_service`` symbols. Regression-tested by
``tooling/hygiene/check_no_grimp_evasion.py`` (Task 10).
"""
from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

from lingwen_shared.contracts.python.llm import LLMTask, TaskType


_DEFAULT_FACTORY: Optional[Callable[[], Any]] = None


def set_default_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Register the default factory used when no service is injected.

    Called once at module load time by ``infra.llm_service`` to wire the
    concrete ``LLMService`` singleton into the adapter's default behavior.
    Passing ``None`` clears the registration (useful in tests).

    The factory MUST be a zero-argument callable returning the service
    instance (or any object matching the surface used by ``LLMServiceAdapter``).
    """
    global _DEFAULT_FACTORY
    _DEFAULT_FACTORY = factory


def get_default_factory() -> Optional[Callable[[], Any]]:
    """Return the currently registered default factory, or ``None``.

    Exposed for introspection (tests, debugging). Not used by the adapter
    itself — it reads the module-level variable directly.
    """
    return _DEFAULT_FACTORY


class LLMServiceAdapter:
    """Sync facade matching the concrete ``LLMService`` call surface.

    Wraps the concrete LLM service singleton by default; accepts an
    injected service for tests. Implements the same method signatures as
    the concrete class so existing consumers can swap direct calls for
    the adapter with zero call-site changes.

    Constructing without arguments requires the default factory to be
    registered (importing ``infra.llm_service`` does this). To use the
    adapter in an isolated test, either inject ``service=fake`` explicitly
    or call ``set_default_factory(lambda: fake)`` before constructing.
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

    def execute(self, task: LLMTask) -> str:
        """Execute an LLM task and return the raw text response."""
        return self._service.execute(task)

    def execute_stream(self, task: LLMTask) -> Iterator[str]:
        """Stream an LLM task, yielding text chunks."""
        return self._service.execute_stream(task)

    def parse_json_response(self, response: str) -> Any:
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str = "default",
        **kwargs: Any,
    ) -> str:
        """Convenience method mirroring the concrete ``generate`` API.

        Wraps ``prompt``/``system`` into an ``LLMTask`` and delegates to
        ``execute``. Used by code paths that pre-date the task-based API.
        """
        task = LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=int(kwargs.get("max_tokens", 2000)),
            temperature=float(kwargs.get("temperature", 0.3)),
        )
        return self._service.execute(task)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available.

        Returns True if the provider is configured and providers are loaded.
        """
        return self._service.is_available()


__all__ = [
    "LLMServiceAdapter",
    "set_default_factory",
    "get_default_factory",
]
```

- [ ] **Step 5.2: Run port_adapter tests**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-llm/tests/test_port_adapter.py --rootdir=packages/lingwen-llm -v 2>&1 | tail -20
```

Expected: 6 of 7 tests pass. The `test_adapter_uses_singleton_when_no_service` test fails because it mocks `infra.llm_service.LLMService.get` directly. The factory is now stored as `_DEFAULT_FACTORY` module variable — fix the test in Task 6.

- [ ] **Step 5.3: Run lint + import-linter**

Run:
```bash
ruff check packages/lingwen-llm/src/lingwen_llm/port_adapter.py
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  lint-imports 2>&1 | tail -10
```

Expected: ruff clean, import-linter still 2 contracts KEPT (port_adapter no longer triggers the chain).

- [ ] **Step 5.4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add packages/lingwen-llm/src/lingwen_llm/port_adapter.py
git commit -m "feat(llm): v16.5 — replace grimp-evasion hack with factory pattern

The v16.4 hack used string-concat + PEP 562 __getattr__ to hide
``infra.llm_service`` imports from grimp. v16.5 eliminates it by:

1. Importing LLMTask/TaskType directly from lingwen_shared (no infra
   dependency for data types).
2. Resolving the default service via a factory registered at startup
   by infra.llm_service (no static import of infra.llm_service here).

The DP-02 forbidden contract still passes — grimp can no longer see
the lingwen_creator → lingwen_llm → infra.llm_service chain because
port_adapter no longer statically imports infra.llm_service."
```

---

## Task 6: Update test_port_adapter.py — use new factory pattern

**Files:**
- Modify: `packages/lingwen-llm/tests/test_port_adapter.py`

- [ ] **Step 6.1: Update imports**

In `packages/lingwen-llm/tests/test_port_adapter.py`:
- Replace `from infra.llm_service import LLMTask, TaskType` (line 11) with `from lingwen_shared.contracts.python.llm import LLMTask, TaskType`
- Keep `from lingwen_llm.port_adapter import LLMServiceAdapter`

- [ ] **Step 6.2: Update singleton test to use factory pattern**

Find and replace the `test_adapter_uses_singleton_when_no_service` function. The test currently mocks `infra.llm_service.LLMService.get` and constructs `LLMServiceAdapter()` (which used to call `LLMService.get()` directly). With the factory pattern, the adapter calls the registered factory, which was set by `infra.llm_service` at module load.

The cleanest fix: explicitly set the factory in the test (no dependency on infra.llm_service import order):

```python
def test_adapter_uses_registered_factory_when_no_service() -> None:
    """Adapter must call the registered default factory when no service is injected."""
    from lingwen_llm.port_adapter import set_default_factory

    fake = MagicMock(provider_name="minimax")
    set_default_factory(lambda: fake)
    try:
        adapter = LLMServiceAdapter()
        assert adapter.provider_name == "minimax"
    finally:
        set_default_factory(None)
```

- [ ] **Step 6.3: Run all port_adapter tests**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-llm/tests/test_port_adapter.py --rootdir=packages/lingwen-llm -v 2>&1 | tail -15
```

Expected: All 7 tests pass.

- [ ] **Step 6.4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add packages/lingwen-llm/tests/test_port_adapter.py
git commit -m "test(llm): v16.5 — update port_adapter tests for factory pattern

LLMTask/TaskType now imported from lingwen_shared (clean path).
Singleton test uses explicit set_default_factory() instead of mocking
infra.llm_service.LLMService.get directly — cleaner test isolation."
```

---

## Task 7: Update creator/content/agent.py — direct import from lingwen_shared

**Files:**
- Modify: `packages/lingwen-creator/src/lingwen_creator/content/agent.py` — lines 237-240 and 260-263

- [ ] **Step 7.1: Replace import site 1 (around line 237)**

Find:
```python
    from lingwen_llm.port_adapter import (  # re-export for DP-02
        LLMServiceAdapter,
        LLMTask,
        TaskType,
    )
```

Replace with:
```python
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType
```

- [ ] **Step 7.2: Replace import site 2 (around line 260)**

Same replacement as Step 7.1 (both sites have identical imports).

- [ ] **Step 7.3: Verify creator tests pass**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-quality/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-creator/tests/ --rootdir=packages/lingwen-creator -q 2>&1 | tail -5
```

Expected: 73 tests pass.

- [ ] **Step 7.4: Verify import-linter still passes**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  lint-imports 2>&1 | tail -5
```

Expected: `2 kept, 0 broken`.

- [ ] **Step 7.5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add packages/lingwen-creator/src/lingwen_creator/content/agent.py
git commit -m "refactor(creator): v16.5 — import LLMTask/TaskType directly from lingwen_shared

Eliminates the \"re-export for DP-02\" wrapper pattern. The data types
now have a canonical home, so consumers don't need to route through
port_adapter for symbol access."
```

---

## Task 8: Update infra/prose_judge.py — direct import from lingwen_shared

**Files:**
- Modify: `infra/prose_judge.py:230-234` — replace import block

- [ ] **Step 8.1: Replace the import block**

Find (around line 230-234):
```python
    from lingwen_llm.port_adapter import (  # re-exported from infra.llm_service for DP-02
        LLMTask,
        TaskType,
    )
```

Replace with:
```python
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType
```

- [ ] **Step 8.2: Verify prose_judge tests pass**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-quality/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/infra/test_prose_judge.py -q 2>&1 | tail -5
```

Expected: All tests pass.

- [ ] **Step 8.3: Verify import-linter still passes**

Run:
```bash
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  lint-imports 2>&1 | tail -5
```

Expected: `2 kept, 0 broken`.

- [ ] **Step 8.4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add infra/prose_judge.py
git commit -m "refactor(infra): v16.5 — prose_judge imports LLMTask/TaskType from lingwen_shared

prose_judge lives in infra/ (not in forbidden source_modules), but for
consistency with content/agent.py the data types now come from the
canonical location."
```

---

## Task 9: Verify world_db/agent_extractors.py needs no change

**Files:**
- Inspect: `infra/world_db/agent_extractors.py`

- [ ] **Step 9.1: Verify no LLMTask/TaskType import**

Run:
```bash
grep -n "LLMTask\|TaskType" /home/ailearn/projects/LingWen/.worktrees/v16-5/infra/world_db/agent_extractors.py
```

Expected: No output (agent_extractors.py only imports `LLMServiceAdapter` from port_adapter, no LLMTask/TaskType usage).

- [ ] **Step 9.2: No commit (skip if no change needed)**

If grep returns nothing, document the finding in the handoff and skip this task.

---

## Task 10: Add hygiene regression test for grimp-evasion absence

**Files:**
- Create: `tooling/hygiene/check_no_grimp_evasion.py`
- Create: `tests/hygiene/test_check_no_grimp_evasion.py`

- [ ] **Step 10.1: Create the hygiene script**

Create `tooling/hygiene/check_no_grimp_evasion.py`:

```python
"""Regression check: lingwen_llm.port_adapter MUST NOT contain any
grimp-evasion patterns (v16.5 invariant).

What we forbid:
- Static ``from infra.llm_service import ...`` (would re-trigger DP-02)
- String-concat dynamic imports of infra.llm_service (e.g. ``"infra" + "." + "llm" + "_service"``)
- PEP 562 ``__getattr__`` that re-exports infra.llm_service symbols

Why: v16.4 introduced these patterns as a workaround for grimp's
transitive-import detection. v16.5 eliminates them by relocating
LLMTask/TaskType to lingwen_shared and using a factory for the default
service. Future regressions that reintroduce any of these patterns
should fail this check.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


PORT_ADAPTER = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "lingwen-llm"
    / "src"
    / "lingwen_llm"
    / "port_adapter.py"
)


def _read() -> str:
    return PORT_ADAPTER.read_text(encoding="utf-8")


def check_static_import() -> list[str]:
    """Fail if any static ``from infra.llm_service import`` exists."""
    text = _read()
    pattern = re.compile(r"^\s*from\s+infra\.llm_service\s+import\s+", re.MULTILINE)
    return [
        f"port_adapter.py:{m.start()}: forbidden static import "
        f"`from infra.llm_service import ...`"
        for m in pattern.finditer(text)
    ]


def check_string_concat_evasion() -> list[str]:
    """Fail if ``infra.llm_service`` appears via string concatenation."""
    text = _read()
    # Match patterns like "infra" + "." + "llm" + "_service"
    # or any string that builds the module name at runtime.
    pattern = re.compile(
        r'["\']infra["\']\s*\+\s*["\'][^"\']*["\']|"infra[^"\']*"\s*\+|"llm"\s*\+\s*"_service"',
        re.MULTILINE,
    )
    return [
        f"port_adapter.py:{m.start()}: forbidden string-concat "
        f"dynamic import of infra.llm_service"
        for m in pattern.finditer(text)
    ]


def check_pep562_re_export() -> list[str]:
    """Fail if a PEP 562 ``__getattr__`` re-exports infra symbols."""
    text = _read()
    # If port_adapter defines module-level __getattr__, it must not
    # dynamically resolve infra.llm_service attributes.
    has_getattr = "__getattr__" in text
    if not has_getattr:
        return []
    pattern = re.compile(r"infra\s*\.\s*llm_service")
    return [
        f"port_adapter.py:{m.start()}: forbidden PEP 562 re-export of "
        f"infra.llm_service (got rid of __getattr__ in v16.5)"
        for m in pattern.finditer(text)
    ]


def main() -> int:
    findings = (
        check_static_import()
        + check_string_concat_evasion()
        + check_pep562_re_export()
    )
    if findings:
        print("FAIL: grimp-evasion regression detected in port_adapter.py:")
        for f in findings:
            print(f"  {f}")
        return 1
    print("OK: port_adapter.py is grimp-evasion-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 10.2: Create the test**

Create `tests/hygiene/test_check_no_grimp_evasion.py`:

```python
"""Unit tests for the grimp-evasion hygiene check."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "tooling"
    / "hygiene"
    / "check_no_grimp_evasion.py"
)


def test_check_passes_on_clean_port_adapter() -> None:
    """Current port_adapter.py (v16.5) must pass the check."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Hygiene check failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "grimp-evasion-free" in result.stdout


def test_check_detects_static_import(tmp_path: Path) -> None:
    """Insert a forbidden static import and verify the check catches it."""
    # Skip — this is a manual verification test that requires writing to
    # port_adapter.py. Marked skip-by-default to avoid touching prod code
    # in unit tests.
    pytest.skip("Manual verification: edit port_adapter.py and re-run check_no_grimp_evasion.py")
```

- [ ] **Step 10.3: Run the hygiene check**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
python tooling/hygiene/check_no_grimp_evasion.py
```

Expected: `OK: port_adapter.py is grimp-evasion-free`

- [ ] **Step 10.4: Run the hygiene test**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/hygiene/test_check_no_grimp_evasion.py -v 2>&1 | tail -10
```

Expected: 1 passed, 1 skipped.

- [ ] **Step 10.5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add tooling/hygiene/check_no_grimp_evasion.py tests/hygiene/test_check_no_grimp_evasion.py
git commit -m "test(hygiene): v16.5 — regression check for grimp-evasion absence

Forbids static ``from infra.llm_service import``, string-concat
dynamic imports, and PEP 562 re-exports in port_adapter.py. Catches
future regressions that would reintroduce the v16.4 hack."
```

---

## Task 11: Final verification — all gates green

- [ ] **Step 11.1: Run all backend tests**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-quality/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/infra/ apps/studio_api/tests/ tests/hygiene/ \
  --rootdir=. -q 2>&1 | tail -5
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-creator/tests/ --rootdir=packages/lingwen-creator -q 2>&1 | tail -5
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -5
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:$PYTHONPATH \
  env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-llm/tests/ --rootdir=packages/lingwen-llm -q 2>&1 | tail -5
```

Expected totals:
- infra + studio_api + hygiene: 392 + ~5 = ~397 passed
- creator pkg: 73 passed
- shared pkg: 79 + 6 = 85 passed
- llm pkg: 7 passed

- [ ] **Step 11.2: Run import-linter**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
PYTHONPATH=/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-creator/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-llm/src:/home/ailearn/projects/LingWen/.worktrees/v16-5/packages/lingwen-shared/src:$PYTHONPATH \
  lint-imports 2>&1 | tail -5
```

Expected: `2 kept, 0 broken`.

- [ ] **Step 11.3: Run ruff**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
ruff check infra/ packages/lingwen-llm/src/ packages/lingwen-shared/src/ packages/lingwen-creator/src/ apps/ 2>&1 | tail -5
```

Expected: `All checks passed!`

- [ ] **Step 11.4: Run frontend gates (no changes, but verify)**

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5/apps/dashboard
pnpm vitest run 2>&1 | tail -5
pnpm tsc --noEmit 2>&1 | tail -3
pnpm exec knip 2>&1 | tail -3
```

Expected: 1729 vitest, 0 vue-tsc errors, 0 knip issues (unchanged from baseline).

- [ ] **Step 11.5: Commit (no code change — skip if nothing to add)**

If any gate fails, fix and commit. Otherwise document the verification result in the handoff.

---

## Task 12: Write handoff doc + update CLAUDE.md + update architecture.yml

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-29-phase-126-v16-5-handoff.md`
- Modify: `CLAUDE.md` — add v16.5 section
- Modify: `.lingwen/architecture.yml` — update DP-02 status

- [ ] **Step 12.1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-08-29-phase-126-v16-5-handoff.md`:

```markdown
# Phase 126 v16.5 #1 — Grimp-Evasion Hack Elimination Handoff

> **Status:** closed, ~10 commits pushed to `phase-126-v16-5` branch (ready for merge to master + push)
> **Previous:** v16.4 DP-02 LLMServicePort enforcement (`4bc88d41`)
> **Next:** v16.5 #2..#7 (DP-01 cross-package contracts + DP-03 StoragePort + async port + remaining packages + tools + DTO audit)

## 0. TL;DR

Eliminated the v16.4 grimp-evasion hack in `lingwen_llm/port_adapter.py` by:
1. Relocating `LLMTask` + `TaskType` from `infra/llm_service.py` to `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`.
2. Replacing string-concat dynamic imports with a factory pattern: `infra.llm_service.py` registers `LLMService.get` as the default factory at module load time; `LLMServiceAdapter` calls the factory when no service is injected.
3. Back-compat: `infra.llm_service.py` re-exports `LLMTask` + `TaskType` so `tools/`, `tests/`, `infra/core/__init__.py` star-imports keep working unchanged.

## 1. Architecture Invariant

`lingwen_llm/port_adapter.py` MUST NOT contain any:
- Static `from infra.llm_service import ...`
- String-concat dynamic import of `infra.llm_service`
- PEP 562 `__getattr__` re-exporting `infra.llm_service` symbols

Regression-tested by `tooling/hygiene/check_no_grimp_evasion.py` (Task 10).

## 2. Tasks Completed

(table filled in at end of implementation)

## 3. Lessons Learned

(filled at end)

## 4. Carryover to v16.6+ (the rest of v16.5)

- DP-01 (cross-package contracts via ports)
- DP-03 (StoragePort enforcement)
- Async port conformance
- Remaining packages migration (lingwen_core/pipeline/prompt/cli)
- Tools migration (tools/llm_*.py — 11 files)
- DTO schema audit + typed wrapper narrowing
```

- [ ] **Step 12.2: Update CLAUDE.md v16.5 section**

Append to the version history in `CLAUDE.md`:

```markdown
> **更新 (2026-08-29)**: Phase 126 v16.5 #1 闭环 — eliminate grimp-evasion hack——10 commits:
- **T1**: 新建 `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` — `TaskType` (Enum) + `LLMTask` (dataclass) canonical source。
- **T2**: Re-export `LLMTask` + `TaskType` from `lingwen_shared.contracts.python.__init__.py`。
- **T3**: `infra/llm_service.py` 删除 local `TaskType` + `LLMTask` 定义,改为 `from lingwen_shared.contracts.python.llm import LLMTask, TaskType` (back-compat re-export via `__all__`)。
- **T4**: `infra/llm_service.py` 末尾注册 `set_default_factory(LLMService.get)` — 替代 v16.4 dynamic import。
- **T5**: `lingwen_llm/port_adapter.py` 完整重写 — 删除所有 string-concat + PEP 562 hack,改为 factory pattern + 直接 import from `lingwen_shared`。
- **T6**: `test_port_adapter.py` 更新 — `LLMTask`/`TaskType` 从 `lingwen_shared` import + singleton test 改用 `set_default_factory()`。
- **T7**: `creator/content/agent.py` 2 处 LLMTask/TaskType import site 直接从 `lingwen_shared` import (不再 "re-export for DP-02")。
- **T8**: `infra/prose_judge.py` LLMTask/TaskType import site 直接从 `lingwen_shared` import。
- **T9**: `infra/world_db/agent_extractors.py` 无 LLMTask/TaskType usage,无 change。
- **T10**: `tooling/hygiene/check_no_grimp_evasion.py` 新建 — regression test 禁止 static import / string-concat / PEP 562 re-export。

Lessons:
1. Factory pattern 比 dynamic import 干净 — 不需要 string-concat 躲避 grimp detection。
2. Back-compat re-export via `__all__` 让 `infra/core/__init__.py` star-import + tools/ + tests/ 零修改通过。
3. PEP 562 `__getattr__` 是 grimp 不可见但 runtime 正确 — 但 defeat static analysis intent,不如 factory pattern。

Carryover to v16.5 #2..#7:DP-01 / DP-03 / async port conformance / 剩余 packages migration / tools migration / DTO audit。
```

- [ ] **Step 12.3: Update .lingwen/architecture.yml DP-02 status**

Read `.lingwen/architecture.yml`, find the DP-02 section, and update its status to indicate the grimp-evasion hack is removed.

- [ ] **Step 12.4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/v16-5
git add docs/superpowers/handoffs/2026-08-29-phase-126-v16-5-handoff.md CLAUDE.md .lingwen/architecture.yml
git commit -m "docs(phase-126): v16.5 #1 closure — handoff + CLAUDE.md + architecture.yml"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Relocate LLMTask/TaskType to lingwen_shared → T1, T2
- ✅ Update consumers → T7, T8
- ✅ Remove all string-concat + PEP 562 workarounds → T5
- ✅ Verify import-linter passes → T11
- ✅ Handoff doc → T12

**2. Placeholder scan:**
- All test code is complete (not "similar to Task N")
- All commit commands are full `git commit -m "..."` with concrete messages
- All file paths are absolute (under worktree)

**3. Type consistency:**
- `LLMTask` and `TaskType` are spelled consistently across all tasks
- `set_default_factory` / `get_default_factory` API matches between T4 (register site) and T5 (consumer site) and T6 (test site)
- `_DEFAULT_FACTORY` module variable name matches T5 definition and T6 test reset

**Potential issues to verify during execution:**
- T5 Step 5.2 expects 6/7 tests pass — if the singleton test breaks differently than expected, adjust T6 accordingly
- T7 Step 7.3 expects 73 tests — verify against actual count in v16.5 worktree
- T8 Step 8.2 expects prose_judge tests pass — verify

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-29-phase-126-v16-5-grimp-evasion-elimination.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
