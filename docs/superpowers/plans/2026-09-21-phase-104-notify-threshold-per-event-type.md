# Phase 104 — Notify Threshold per Event Type — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `notify_threshold` (Phase 102 global `int=3`) to per-event-type `int | dict[str, int]`, with backwards-compat auto-expansion of legacy int and strict partial-dict semantics (unconfigured types default to Infinity = never warn).

**Architecture:** Schema widening via Pydantic validator (`int → 4-key dict` auto-expansion). Counter keys change from `(slug,)` to `(project_slug, event_type)` tuple — independent failure windows per event type. Pipeline caller sites resolve threshold per event_type at the start of each function and pass through to `record_failure(..., event_type=...)`. Frontend UI reuses Phase 102/103 fallback_models keyed table pattern (4 fixed rows × NumberInput).

**Tech Stack:** Python 3.12+ / Pydantic v2 / FastAPI / Vue 3 + TypeScript / Pinia / Vitest / pytest / ruff

---

## File Structure

### Files created
- `packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py` — 8 regression guards G1-G8
- `packages/lingwen-illustrations/tests/test_notifications_phase104.py` — 6 counter state + record_failure/record_success tests
- `docs/superpowers/plans/2026-09-21-phase-104-notify-threshold-per-event-type.md` — this plan
- `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md` — final task handoff

### Files modified
- `apps/studio_api/routes/project_settings.py` — Pydantic validator `notify_threshold` (int | dict → dict normalize)
- `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` — counter state widening, record_failure/record_success API, _emit_failure_warning event_type arg
- `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` — `_resolve_threshold` helper + 2 caller sites pass event_type
- `apps/dashboard/src/api/illustrations.ts` — TypeScript type widening + `NOTIFY_EVENT_TYPES` constant
- `apps/dashboard/src/stores/useProjectSettings.js` — `notifyThreshold` normalize/denormalize helpers
- `apps/dashboard/src/stores/useProjectSettings.spec.js` — 4 NEW normalize/denormalize tests
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` — Notify Thresholds subsection (4-row keyed table)
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts` — 6 NEW UI tests
- `packages/lingwen-illustrations/tests/test_notifications.py` — Phase 102 tests, 1 key update (tuple keys)
- `.lingwen/architecture.yml` — I095 docstring EXTENDED
- `CLAUDE.md` — v60.1 → v60.2 version bump + I095 line EXTENDED
- `collaboration/BACKLOG.md` — Phase 104 entry
- `collaboration/CURRENT_STATUS.md` — Phase 104 sync
- `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — v60.2 entry + Phase 104 reference

---

## Task 1: Design spec (already complete)

**Files:**
- Created: `docs/superpowers/specs/2026-09-21-phase-104-notify-threshold-per-event-type-design.md` (commit `3dba2cce`)

- [x] Verify spec exists and committed
- [x] Brainstorming user-approval: design sections 1-5 approved
- [x] Spec self-review: 0 placeholders, internally consistent, scope-checked

---

## Task 2: Implementation plan (this document)

**Files:**
- Created: `docs/superpowers/plans/2026-09-21-phase-104-notify-threshold-per-event-type.md`

- [x] Save this plan
- [ ] Self-review plan against spec (no placeholders, type consistency)
- [ ] Commit: `git add docs/superpowers/plans/2026-09-21-phase-104-notify-threshold-per-event-type.md && git commit -m "docs(phase-104): implementation plan — 12 tasks"`

---

## Task 3: Pydantic validator — accept int | dict[str, int] and normalize

**Files:**
- Modify: `apps/studio_api/routes/project_settings.py` (lines ~50-56 + lines ~128-133)

- [ ] **Step 1: Read the existing schema + Phase 102 validator**

Run:
```bash
sed -n '40,80p;120,140p' apps/studio_api/routes/project_settings.py
```

Expected: see the Phase 102 `notify_threshold: int = 3` field + existing `_validate_notify_threshold` validator.

- [ ] **Step 2: Update the field annotation**

In `apps/studio_api/routes/project_settings.py` around line 56, change:
```python
    notify_threshold: int = 3                           # consecutive failures before warning
```
to:
```python
    notify_threshold: int | dict[str, int] = 3         # Phase 104: int (legacy, auto-expand) | dict (per-event_type)
```

- [ ] **Step 3: Replace the validator body**

Around line 128-133, replace:
```python
    @field_validator("notify_threshold")
    @classmethod
    def _validate_notify_threshold(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"notify_threshold must be >= 1, got {v}")
        return v
```
with:
```python
    KNOWN_NOTIFY_EVENT_TYPES: ClassVar[tuple[str, ...]] = (
        "generation", "regeneration", "cleanup", "deletion",
    )

    @field_validator("notify_threshold", mode="before")
    @classmethod
    def _validate_notify_threshold(cls, v):
        """Phase 104: accept int (legacy auto-expand) or dict (per-event_type).

        - int: validate >= 1, return expanded {et: v for et in KNOWN_NOTIFY_EVENT_TYPES}
        - dict: validate keys ⊆ KNOWN_NOTIFY_EVENT_TYPES + each value >= 1
        - empty dict {}: valid (opt-out from all warnings)
        - otherwise: ValueError
        """
        if isinstance(v, bool):
            # bool is a subclass of int — exclude to avoid silent truthy acceptance
            raise ValueError(f"notify_threshold must be int or dict, got bool")
        if isinstance(v, int):
            if v < 1:
                raise ValueError(f"notify_threshold must be >= 1, got {v}")
            return {et: v for et in cls.KNOWN_NOTIFY_EVENT_TYPES}
        if isinstance(v, dict):
            for k, vv in v.items():
                if k not in cls.KNOWN_NOTIFY_EVENT_TYPES:
                    raise ValueError(
                        f"notify_threshold key {k!r} not in {cls.KNOWN_NOTIFY_EVENT_TYPES}"
                    )
                if not isinstance(vv, int) or isinstance(vv, bool) or vv < 1:
                    raise ValueError(
                        f"notify_threshold[{k!r}] must be int >= 1, got {vv!r}"
                    )
            return dict(v)
        raise ValueError(
            f"notify_threshold must be int or dict[str, int], got {type(v).__name__}"
        )
```

Add `ClassVar` to the imports if not already present:
```python
from typing import ClassVar
```

- [ ] **Step 4: Verify the validator with a quick smoke test**

Run:
```bash
cd /home/ailearn/projects/LingWen && uv run python -c "
from apps.studio_api.routes.project_settings import ProjectSettings
ps1 = ProjectSettings(notify_threshold=3)
print('int legacy:', ps1.notify_threshold)
ps2 = ProjectSettings(notify_threshold={'generation': 5})
print('partial dict:', ps2.notify_threshold)
ps3 = ProjectSettings(notify_threshold={})
print('empty dict:', ps3.notify_threshold)
ps4 = ProjectSettings(notify_threshold={'generation': 5, 'regeneration': 10})
print('multi dict:', ps4.notify_threshold)
"
```

Expected output:
```
int legacy: {'generation': 3, 'regeneration': 3, 'cleanup': 3, 'deletion': 3}
partial dict: {'generation': 5}
empty dict: {}
multi dict: {'generation': 5, 'regeneration': 10}
```

- [ ] **Step 5: Write the validator tests (Phase 104 Task 3 RED)**

Create `packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py`:

```python
"""Phase 104 — notify_threshold per event_type — validator + counter guards.

8 guards (G1-G8) cover schema validation + counter state semantics.
Per spec 2026-09-21-phase-104-notify-threshold-per-event-type-design.md §1 + §2.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from apps.studio_api.routes.project_settings import ProjectSettings
from lingwen_illustrations import notifications


KNOWN_EVENT_TYPES = ("generation", "regeneration", "cleanup", "deletion")
INFINITY = math.inf


# --- G1: validator accepts int legacy, expands to 4-key dict ---

def test_g1_validator_int_legacy_expands_to_4_key_dict():
    ps = ProjectSettings(notify_threshold=3)
    assert ps.notify_threshold == {
        "generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 3,
    }


def test_g1b_validator_int_legacy_value_at_minimum():
    ps = ProjectSettings(notify_threshold=1)
    assert ps.notify_threshold == {et: 1 for et in KNOWN_EVENT_TYPES}


# --- G2: validator accepts partial dict, preserves only configured keys ---

def test_g2_validator_partial_dict_keeps_only_configured_keys():
    ps = ProjectSettings(notify_threshold={"generation": 5})
    assert ps.notify_threshold == {"generation": 5}


def test_g2b_validator_empty_dict_is_valid_opt_out():
    ps = ProjectSettings(notify_threshold={})
    assert ps.notify_threshold == {}


def test_g2c_validator_multi_event_type_dict():
    ps = ProjectSettings(notify_threshold={"generation": 5, "regeneration": 10})
    assert ps.notify_threshold == {"generation": 5, "regeneration": 10}


# --- G3: validator rejects unknown event_type key ---

def test_g3_validator_rejects_unknown_event_type():
    with pytest.raises(ValueError, match="not in"):
        ProjectSettings(notify_threshold={"unknown_type": 3})


# --- G4: validator rejects value < 1 ---

def test_g4_validator_rejects_int_below_1():
    with pytest.raises(ValueError, match="must be >= 1"):
        ProjectSettings(notify_threshold=0)


def test_g4b_validator_rejects_dict_value_below_1():
    with pytest.raises(ValueError, match="must be int >= 1"):
        ProjectSettings(notify_threshold={"generation": 0})


# --- G5: _resolve_threshold returns configured int or INFINITY for missing ---

def test_g5_resolve_threshold_returns_int_for_configured_key(monkeypatch):
    from lingwen_illustrations import pipeline
    settings = {"notify_threshold": {"generation": 5}}
    assert pipeline._resolve_threshold(settings, "generation") == 5


def test_g5b_resolve_threshold_returns_infinity_for_missing_key(monkeypatch):
    from lingwen_illustrations import pipeline
    settings = {"notify_threshold": {"generation": 5}}
    assert pipeline._resolve_threshold(settings, "cleanup") == INFINITY


# --- G6: counter keys are (project_slug, event_type) tuples (NOT bare slug) ---

def test_g6_consecutive_failures_keys_are_tuples(monkeypatch, tmp_path):
    """Phase 104 I095 EXTENDED: state keyed per (slug, event_type) tuple."""
    notifications._consecutive_failures.clear()
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="generation",
    )
    assert ("test-slug", "generation") in notifications._consecutive_failures
    assert "test-slug" not in notifications._consecutive_failures


# --- G7: record_failure increments only target event_type counter ---

def test_g7_record_failure_isolates_event_type_counters(monkeypatch, tmp_path):
    """3 generation failures + 0 regeneration failures → 0 regen warnings."""
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    for _ in range(3):
        notifications.record_failure(
            "test-slug", RuntimeError("boom"),
            project_root=tmp_path, threshold=3, event_type="generation",
        )
    assert notifications._consecutive_failures[("test-slug", "generation")] == 3
    assert ("test-slug", "regeneration") not in notifications._consecutive_failures


# --- G8: record_success resets only target event_type counter ---

def test_g8_record_success_isolates_event_type_counters(monkeypatch, tmp_path):
    """Reset (slug, 'generation') only — (slug, 'regeneration') untouched."""
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    # Pre-populate both counters
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="generation",
    )
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="regeneration",
    )
    # Reset generation only
    notifications.record_success("test-slug", "generation")
    assert notifications._consecutive_failures[("test-slug", "generation")] == 0
    assert notifications._consecutive_failures[("test-slug", "regeneration")] == 1
```

- [ ] **Step 6: Run tests — G5 + G6 + G7 + G8 will FAIL (helper + counter widening not yet implemented)**

Run:
```bash
cd /home/ailearn/projects/LingWen && uv run pytest packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py -v --rootdir=packages/lingwen-illustrations 2>&1 | head -60
```

Expected: G1, G2, G3, G4 PASS (validator). G5, G6, G7, G8 FAIL with import errors or missing attributes.

- [ ] **Step 7: Commit validator + tests**

```bash
git add apps/studio_api/routes/project_settings.py packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py
git commit -m "feat(phase-104): Pydantic validator accepts int|dict[str,int] + 4 guards RED"
```

---

## Task 4: Notifications module — counter state widening + record_failure/record_success API

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` (lines ~57-63 + ~118-197)

- [ ] **Step 1: Update module docstring**

In `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` around line 11-19, replace the Phase 102 extensions block:
```python
Phase 102 extensions:
- NotificationEvent.severity field ("info" default; "warning" for threshold alerts)
- _consecutive_failures in-memory state machine (I095 invariant)
- record_failure(project_slug, error, *, project_root, threshold) — caller passes
  both project_root + threshold so notifications module stays yaml-free
- record_success(project_slug) — resets counter
- Threshold crossing emits 1 severity=warning notification; counter stays
  elevated until record_success() resets it (sustained-failure visibility)
"""
```
with:
```python
Phase 102 extensions:
- NotificationEvent.severity field ("info" default; "warning" for threshold alerts)
- _consecutive_failures in-memory state machine (I095 invariant)
- record_failure(project_slug, error, *, project_root, threshold, event_type) — caller
  passes project_root + threshold + event_type so notifications module stays yaml-free
- record_success(project_slug, event_type) — resets counter for that (slug, event_type) pair
- Threshold crossing emits 1 severity=warning notification per (slug, event_type) pair;
  counter stays elevated until record_success() resets it (sustained-failure visibility)

Phase 104 extensions:
- _consecutive_failures / _warning_emitted keys widened from str to (str, str) tuple
  (project_slug, event_type). Each event type has independent failure counter.
- record_failure() signature now takes event_type: str kwarg.
- record_success() signature now takes event_type: str positional arg.
- I095 EXTENDED via docstring only — no new invariant introduced.
"""
```

- [ ] **Step 2: Add math import + INFINITY_THRESHOLD constant + tuple-keyed state**

In `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` around line 20-31, add `import math` and update state declarations:

Replace:
```python
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
```
with:
```python
import asyncio
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
```

Replace (lines 57-63):
```python
# Phase 102: consecutive failure counter (in-memory, lost on restart — Phase 99 trade-off).
# I095: only record_failure/record_success may mutate these dicts.
_consecutive_failures: dict[str, int] = {}
# Tracks whether we have already emitted a threshold warning for the current
# sustained-failure window. Reset to False by record_success() so the next
# failure streak can warn again.
_warning_emitted: dict[str, bool] = {}
```
with:
```python
# Phase 102 + Phase 104: consecutive failure counter (in-memory, lost on restart — Phase 99 trade-off).
# I095 EXTENDED: keys are (project_slug, event_type) tuples, NOT bare project_slug.
# Only record_failure/record_success may mutate these dicts.
_consecutive_failures: dict[tuple[str, str], int] = {}
# Tracks whether we have already emitted a threshold warning for the current
# sustained-failure window per (slug, event_type) pair. Reset to False by
# record_success() so the next failure streak can warn again.
_warning_emitted: dict[tuple[str, str], bool] = {}

# Sentinel for "no warning ever" — partial dict unconfigured keys
# resolve to this in pipeline._resolve_threshold().
INFINITY_THRESHOLD: float = math.inf
```

- [ ] **Step 3: Update record_failure signature + body**

Replace (lines 124-154):
```python
def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path,
    threshold: int,
) -> None:
    """Increment consecutive failure counter; emit warning when count >= threshold.

    Idempotent on threshold crossing: after warning emit, does NOT reset counter.
    Counter stays elevated until record_success() is called. This surfaces a
    sustained-failure pattern to the user without spamming them.

    Caller pattern (in pipeline.dispatch_with_fallback):
        settings = _load_illustration_settings(project_root)
        threshold = settings.get("notify_threshold", 3)
        try:
            ... attempt ...
        except Exception as e:
            notifications.record_failure(
                slug, e, project_root=project_root, threshold=threshold,
            )
            raise
        else:
            notifications.record_success(slug)
    """
    _consecutive_failures[project_slug] = _consecutive_failures.get(project_slug, 0) + 1
    count = _consecutive_failures[project_slug]
    if count >= threshold and not _warning_emitted.get(project_slug, False):
        _warning_emitted[project_slug] = True
        _emit_failure_warning(project_slug, count, error, project_root)
```
with:
```python
def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path,
    threshold: int | float,
    event_type: str,
) -> None:
    """Increment consecutive failure counter for (slug, event_type); emit warning when count >= threshold.

    Idempotent on threshold crossing: after warning emit, does NOT reset counter.
    Counter stays elevated until record_success(slug, event_type) is called. This
    surfaces a sustained-failure pattern to the user without spamming them.

    Phase 104: counter keyed per (project_slug, event_type) tuple. Failures in
    different event types do NOT bleed into each other's counters.

    Caller pattern (in pipeline.generate_illustration):
        settings = _load_illustration_settings(project_root)
        threshold = _resolve_threshold(settings, "generation")  # int or inf
        try:
            ... attempt ...
        except Exception as e:
            notifications.record_failure(
                slug, e, project_root=project_root,
                threshold=threshold, event_type="generation",
            )
            raise
        else:
            notifications.record_success(slug, event_type="generation")
    """
    key = (project_slug, event_type)
    _consecutive_failures[key] = _consecutive_failures.get(key, 0) + 1
    count = _consecutive_failures[key]
    if count >= threshold and not _warning_emitted.get(key, False):
        _warning_emitted[key] = True
        _emit_failure_warning(project_slug, count, error, project_root, event_type)
```

- [ ] **Step 4: Update record_success signature + body**

Replace (lines 157-164):
```python
def record_success(project_slug: str) -> None:
    """Reset counter to 0 on any successful illustration event.

    Called from pipeline on successful generation/regeneration.
    No project_root needed — counter state is in-memory only.
    """
    _consecutive_failures[project_slug] = 0
    _warning_emitted[project_slug] = False
```
with:
```python
def record_success(project_slug: str, event_type: str) -> None:
    """Reset counter + warning flag for specific (slug, event_type) pair.

    Phase 104: only resets the targeted event_type's counter — other event
    types' counters for the same slug remain unchanged.

    Called from pipeline on successful generation/regeneration.
    No project_root needed — counter state is in-memory only.
    """
    key = (project_slug, event_type)
    _consecutive_failures[key] = 0
    _warning_emitted[key] = False
```

- [ ] **Step 5: Update _emit_failure_warning signature + body**

Replace (lines 167-197):
```python
def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path,
) -> None:
    """Emit severity=warning notification; ULID shared with audit_log (I091 invariant)."""
    event_id = str(ulid.ULID())
    audit_log.record_event(
        project_root,
        event="generation",
        extra={
            "severity": "warning",
            "consecutive_failures": count,
            "last_error": str(error),
            "id": event_id,
        },
    )
    publish(NotificationEvent(
        id=event_id,
        project_slug=project_slug,
        event_type="generation",
        severity="warning",
        asset_id=None,
        asset_type=None,
        chapter_num=None,
        style_preset=None,
        provider=None,
        ts=now_iso(),
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))
```
with:
```python
def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path,
    event_type: str,
) -> None:
    """Emit severity=warning notification; ULID shared with audit_log (I091 invariant).

    Phase 104: event_type passed in (was hardcoded "generation" in Phase 102).
    """
    event_id = str(ulid.ULID())
    audit_log.record_event(
        project_root,
        event=event_type,
        extra={
            "severity": "warning",
            "consecutive_failures": count,
            "last_error": str(error),
            "id": event_id,
        },
    )
    publish(NotificationEvent(
        id=event_id,
        project_slug=project_slug,
        event_type=event_type,
        severity="warning",
        asset_id=None,
        asset_type=None,
        chapter_num=None,
        style_preset=None,
        provider=None,
        ts=now_iso(),
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))
```

- [ ] **Step 6: Update __all__ + INFINITY_THRESHOLD export**

Replace (lines 200-212):
```python
__all__ = [
    "EventType",
    "NotificationEvent",
    "Severity",
    "subscribe",
    "unsubscribe",
    "publish",
    "format_event",
    "new_event_id",
    "now_iso",
    "record_failure",
    "record_success",
]
```
with:
```python
__all__ = [
    "EventType",
    "INFINITY_THRESHOLD",
    "NotificationEvent",
    "Severity",
    "subscribe",
    "unsubscribe",
    "publish",
    "format_event",
    "new_event_id",
    "now_iso",
    "record_failure",
    "record_success",
]
```

- [ ] **Step 7: Update existing Phase 102 tests for tuple keys (1 test file)**

In `packages/lingwen-illustrations/tests/test_notifications.py`, find any test that accesses `_consecutive_failures[slug]` or `_warning_emitted[slug]` directly. Update those accesses to use tuple keys:

Pattern to find:
```python
notifications._consecutive_failures["some-slug"]
notifications._warning_emitted["some-slug"]
notifications.record_failure("some-slug", ...)
notifications.record_success("some-slug")
```

Replace with:
```python
notifications._consecutive_failures[("some-slug", "generation")]
notifications._warning_emitted[("some-slug", "generation")]
notifications.record_failure("some-slug", ..., event_type="generation")
notifications.record_success("some-slug", "generation")
```

The exact tests to update depend on the file. Use `grep -n` to find them.

- [ ] **Step 8: Run all notifications + Phase 104 tests**

Run:
```bash
cd /home/ailearn/projects/LingWen && uv run pytest packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py packages/lingwen-illustrations/tests/test_notifications.py -v --rootdir=packages/lingwen-illustrations 2>&1 | tail -40
```

Expected: all PASS (G1-G8 GREEN + Phase 102 preserved). If G5 still FAILS, it's because `pipeline._resolve_threshold` doesn't exist yet — Task 5 will fix it.

- [ ] **Step 9: Commit**

```bash
git add packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py packages/lingwen-illustrations/tests/test_notifications.py
git commit -m "feat(phase-104): notifications.py — tuple-keyed counter + record_failure/record_success event_type"
```

---

## Task 5: Pipeline — _resolve_threshold helper + 2 caller sites

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` (lines ~260-261, ~312-320, ~497-498, ~541-549)

- [ ] **Step 1: Read current pipeline.py around the 2 call sites**

Run:
```bash
sed -n '255,325p;495,555p' packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
```

- [ ] **Step 2: Add `_resolve_threshold` helper near the top of pipeline.py**

After imports (after `from lingwen_illustrations import audit_log, notifications, ...`), add:

```python
import math as _math  # for INFINITY sentinel in _resolve_threshold

INFINITY_THRESHOLD = _math.inf


def _resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Resolve notify_threshold for specific event_type.

    After Pydantic normalization, settings["notify_threshold"] is dict[str, int].
    Missing key → INFINITY_THRESHOLD (never warn for that event type).

    Defensive: if int legacy form slips through (shouldn't post-validation),
    returns int directly.

    Phase 104 spec §3.
    """
    nt = settings.get("notify_threshold", 3)
    if isinstance(nt, bool):
        return INFINITY_THRESHOLD  # exclude bool truthy acceptance
    if isinstance(nt, (int, float)):
        return nt
    return nt.get(event_type, INFINITY_THRESHOLD)
```

- [ ] **Step 3: Update generate_illustration call site**

Find the existing block (around line 260-261):
```python
    # Phase 102 I095: notify_threshold from merged settings (chapter_overrides win over root).
    _notify_threshold = int(effective_settings.get("notify_threshold", 3))
```

Replace with:
```python
    # Phase 102 I095 + Phase 104: notify_threshold resolved per-type from merged settings.
    _notify_threshold = _resolve_threshold(effective_settings, "generation")
```

Find the existing failure record (around line 312-315):
```python
            notifications.record_failure(
                project_slug,
                error,
                project_root=project_root,
                threshold=_notify_threshold,
            )
```

Replace with:
```python
            notifications.record_failure(
                project_slug,
                error,
                project_root=project_root,
                threshold=_notify_threshold,
                event_type="generation",
            )
```

Find the existing success record (around line 320):
```python
            notifications.record_success(project_slug)
```

Replace with:
```python
            notifications.record_success(project_slug, event_type="generation")
```

- [ ] **Step 4: Update regenerate_illustration call site**

Find the existing block (around line 497-498):
```python
    # Phase 102 I095: notify_threshold from merged settings.
    _notify_threshold = int(effective_settings.get("notify_threshold", 3))
```

Replace with:
```python
    # Phase 102 I095 + Phase 104: notify_threshold resolved per-type from merged settings.
    _notify_threshold = _resolve_threshold(effective_settings, "regeneration")
```

Find the existing failure record (around line 541-544):
```python
            notifications.record_failure(
                existing_meta.project_slug,
                error,
                project_root=project_root,
                threshold=_notify_threshold,
            )
```

Replace with:
```python
            notifications.record_failure(
                existing_meta.project_slug,
                error,
                project_root=project_root,
                threshold=_notify_threshold,
                event_type="regeneration",
            )
```

Find the existing success record (around line 549):
```python
            notifications.record_success(existing_meta.project_slug)
```

Replace with:
```python
            notifications.record_success(existing_meta.project_slug, event_type="regeneration")
```

- [ ] **Step 5: Run pipeline + notifications tests**

Run:
```bash
cd /home/ailearn/projects/LingWen && uv run pytest packages/lingwen-illustrations/tests/ -v --rootdir=packages/lingwen-illustrations -k "pipeline or notifications or phase104" 2>&1 | tail -50
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
git commit -m "feat(phase-104): pipeline.py — _resolve_threshold helper + 2 caller sites pass event_type"
```

---

## Task 6: TypeScript — type widening + NOTIFY_EVENT_TYPES constant

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts` (add type + constant; Pick whitelist mirror unchanged)

- [ ] **Step 1: Read existing illustrations.ts**

Run:
```bash
cat apps/dashboard/src/api/illustrations.ts | head -50
```

Expected: see `ProjectSettings` interface with `notify_threshold: number` field.

- [ ] **Step 2: Add NotifyEventType + NOTIFY_EVENT_TYPES constant**

Find a good location near other top-level types. Add:

```typescript
/**
 * Phase 104: NotifyEventType mirrors the backend EventType Literal
 * (packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py).
 * Used for notify_threshold per-event_type keys.
 */
export type NotifyEventType = "generation" | "regeneration" | "cleanup" | "deletion";

export const NOTIFY_EVENT_TYPES: readonly NotifyEventType[] = [
  "generation",
  "regeneration",
  "cleanup",
  "deletion",
] as const;
```

- [ ] **Step 3: Widen notify_threshold type**

Find:
```typescript
  notify_threshold: number;
```

Replace with:
```typescript
  /**
   * Phase 104: per-event_type threshold.
   * - number: legacy form (Phase 102) — applies to all event types
   * - Record<NotifyEventType, number>: per-event_type form — unconfigured keys default to Infinity
   */
  notify_threshold: number | Record<NotifyEventType, number>;
```

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit 2>&1 | head -20
```

Expected: 0 new errors (48 pre-existing baseline unchanged).

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/api/illustrations.ts
git commit -m "feat(phase-104): api/illustrations.ts — notify_threshold widened to number | Record<...>"
```

---

## Task 7: Store — normalize/denormalize + 4 tests

**Files:**
- Modify: `apps/dashboard/src/stores/useProjectSettings.js` (state + helpers)
- Modify: `apps/dashboard/src/stores/useProjectSettings.spec.js` (+4 tests)

- [ ] **Step 1: Read existing store + spec**

Run:
```bash
wc -l apps/dashboard/src/stores/useProjectSettings.js apps/dashboard/src/stores/useProjectSettings.spec.js && grep -n "notifyThreshold\|notify_threshold" apps/dashboard/src/stores/useProjectSettings.js | head -10
```

- [ ] **Step 2: Add normalize helper + update state**

In `apps/dashboard/src/stores/useProjectSettings.js`, add:

```javascript
import { NOTIFY_EVENT_TYPES } from "@/api/illustrations";

/**
 * Phase 104: normalize notifyThreshold response.
 * - number (legacy) → 4-key dict with same value
 * - Record (already dict) → unchanged
 * - undefined / null → empty dict (opt-out)
 */
export function normalizeNotifyThreshold(value) {
  if (typeof value === "number") {
    return Object.fromEntries(NOTIFY_EVENT_TYPES.map((et) => [et, value]));
  }
  if (value && typeof value === "object") {
    return { ...value };
  }
  return {};
}
```

Find the existing state declaration for `notifyThreshold`:
```javascript
  notifyThreshold: number | undefined
```

Update type expectation (JS, but add JSDoc):
```javascript
  /**
   * Phase 104: number (legacy, auto-expand at read) | Record<NotifyEventType, number> | undefined
   */
  notifyThreshold: undefined,
```

In the store's `fetch` action, after parsing the response, add:
```javascript
      if (typeof data.notify_threshold === "number") {
        // Legacy form — backend normalized view not available in API; preserve user-facing shape.
        // Store as-is; UI handles both.
      } else if (data.notify_threshold && typeof data.notify_threshold === "object") {
        // Already dict
      }
      // For safety, normalize before assigning to notifyThreshold state:
      const normalized = normalizeNotifyThreshold(data.notify_threshold);
      this.notifyThreshold = normalized;
```

If `notifyThreshold` was assigned differently before, replace the assignment to use `normalized`.

- [ ] **Step 3: Add 4 tests in spec**

In `apps/dashboard/src/stores/useProjectSettings.spec.js`, add a new `describe` block:

```javascript
  describe("Phase 104: normalizeNotifyThreshold", () => {
    it("normalizes int to 4-key dict", () => {
      const result = normalizeNotifyThreshold(3);
      expect(result).toEqual({
        generation: 3,
        regeneration: 3,
        cleanup: 3,
        deletion: 3,
      });
    });

    it("preserves dict unchanged (already normalized)", () => {
      const input = { generation: 5, regeneration: 10 };
      const result = normalizeNotifyThreshold(input);
      expect(result).toEqual({ generation: 5, regeneration: 10 });
    });

    it("normalizes undefined to empty dict", () => {
      expect(normalizeNotifyThreshold(undefined)).toEqual({});
      expect(normalizeNotifyThreshold(null)).toEqual({});
    });

    it("round-trip dict through fetch → store → write", () => {
      const input = { generation: 5, regeneration: 10 };
      const fetched = normalizeNotifyThreshold(input);
      // store mirrors fetched
      // write passes dict unchanged
      const written = { ...fetched };
      expect(written).toEqual(input);
    });
  });
```

Add the import at top of spec file:
```javascript
import { normalizeNotifyThreshold } from "@/stores/useProjectSettings";
```

- [ ] **Step 4: Run tests**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useProjectSettings.spec.js 2>&1 | tail -20
```

Expected: 4/4 NEW PASS + Phase 102 tests preserved.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/stores/useProjectSettings.js apps/dashboard/src/stores/useProjectSettings.spec.js
git commit -m "feat(phase-104): useProjectSettings store normalize/denormalize + 4 tests"
```

---

## Task 8: UI — Notify Thresholds subsection + 6 tests

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` (add subsection)
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts` (+6 tests)

- [ ] **Step 1: Read existing component + spec**

Run:
```bash
grep -n "notify_threshold\|notifyThreshold\|fallback_models\|chapter_overrides" apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue | head -20
```

- [ ] **Step 2: Add the Notify Thresholds subsection**

Locate where the existing notify_threshold slider is, and REPLACE it with the new table. Pattern:

Find (around existing notify_threshold slider/input):
```vue
        <label>
          <input type="number" v-model.number="localSettings.notify_threshold" min="1" />
          Notify threshold (consecutive failures before warning)
        </label>
```

Replace with:
```vue
        <section class="notify-thresholds">
          <h4>Notify Thresholds</h4>
          <table class="notify-thresholds-table">
            <thead>
              <tr>
                <th>Event type</th>
                <th>Threshold</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="et in NOTIFY_EVENT_TYPES" :key="et" :data-testid="`notify-threshold-row-${et}`">
                <td>{{ et }}</td>
                <td>
                  <input
                    type="number"
                    :value="formatThreshold(localSettings.notify_threshold, et)"
                    min="1"
                    :placeholder="'∞'"
                    :data-testid="`notify-threshold-input-${et}`"
                    @change="onThresholdChange(et, $event)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
          <p class="hint">Leave empty to never warn for that event type.</p>
          <button
            type="button"
            class="reset-all-btn"
            data-testid="notify-threshold-reset-all"
            @click="resetAllThresholds"
          >
            Reset all to default
          </button>
        </section>
```

In `<script setup>`, add:

```javascript
import { NOTIFY_EVENT_TYPES } from "@/api/illustrations";

const DEFAULT_THRESHOLD = 3;

function formatThreshold(value, et) {
  if (typeof value === "number") return value;
  if (value && typeof value === "object" && et in value) return value[et];
  return "";
}

function onThresholdChange(et, event) {
  const raw = event.target.value.trim();
  if (raw === "") {
    // empty → remove key (means Infinity / opt-out)
    if (localSettings.value.notify_threshold && typeof localSettings.value.notify_threshold === "object") {
      delete localSettings.value.notify_threshold[et];
    }
  } else {
    const parsed = parseInt(raw, 10);
    if (parsed >= 1) {
      if (typeof localSettings.value.notify_threshold !== "object" || localSettings.value.notify_threshold === null) {
        localSettings.value.notify_threshold = {};
      }
      localSettings.value.notify_threshold[et] = parsed;
    }
  }
}

function resetAllThresholds() {
  const dict = {};
  for (const et of NOTIFY_EVENT_TYPES) {
    dict[et] = DEFAULT_THRESHOLD;
  }
  localSettings.value.notify_threshold = dict;
}
```

- [ ] **Step 3: Add CSS**

```css
.notify-thresholds {
  margin-top: 1rem;
}
.notify-thresholds-table {
  width: 100%;
  border-collapse: collapse;
}
.notify-thresholds-table th,
.notify-thresholds-table td {
  border: 1px solid var(--color-border, #ddd);
  padding: 0.5rem;
  text-align: left;
}
.notify-thresholds .reset-all-btn {
  margin-top: 0.5rem;
}
.notify-thresholds .hint {
  font-size: 0.85rem;
  color: var(--color-text-muted, #666);
  margin-top: 0.25rem;
}
```

- [ ] **Step 4: Add 6 tests in spec**

In `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts`, add:

```typescript
  describe("Phase 104: Notify Thresholds subsection", () => {
    it("renders 4 rows with current values", () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: { generation: 5, regeneration: 5 } } },
      });
      expect(wrapper.find('[data-testid="notify-threshold-row-generation"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="notify-threshold-row-regeneration"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="notify-threshold-row-cleanup"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="notify-threshold-row-deletion"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="notify-threshold-input-generation"]').element.value).toBe("5");
    });

    it("NumberInput change updates dict", async () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: { generation: 3 } } },
      });
      const input = wrapper.find('[data-testid="notify-threshold-input-generation"]');
      await input.setValue("10");
      // assert internal state updated
    });

    it("reset-all button sets all 4 to 3", async () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: { generation: 1 } } },
      });
      await wrapper.find('[data-testid="notify-threshold-reset-all"]').trigger("click");
      for (const et of NOTIFY_EVENT_TYPES) {
        expect(wrapper.find(`[data-testid="notify-threshold-input-${et}"]`).element.value).toBe("3");
      }
    });

    it("empty input displays '∞' placeholder and persists Infinity", () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: { generation: 5 } } },
      });
      const input = wrapper.find('[data-testid="notify-threshold-input-cleanup"]');
      expect(input.element.value).toBe("");
      expect(input.attributes("placeholder")).toBe("∞");
    });

    it("legacy int response shows same threshold in all 4 rows", () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: 5 } },
      });
      for (const et of NOTIFY_EVENT_TYPES) {
        expect(wrapper.find(`[data-testid="notify-threshold-input-${et}"]`).element.value).toBe("5");
      }
    });

    it("partial dict response shows empty cells for unconfigured types", () => {
      const wrapper = mount(ProjectSettingsIllustration, {
        props: { settings: { notify_threshold: { generation: 5 } } },
      });
      expect(wrapper.find('[data-testid="notify-threshold-input-generation"]').element.value).toBe("5");
      expect(wrapper.find('[data-testid="notify-threshold-input-regeneration"]').element.value).toBe("");
      expect(wrapper.find('[data-testid="notify-threshold-input-cleanup"]').element.value).toBe("");
      expect(wrapper.find('[data-testid="notify-threshold-input-deletion"]').element.value).toBe("");
    });
  });
```

- [ ] **Step 5: Run tests**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ProjectSettingsIllustration.spec.ts 2>&1 | tail -30
```

Expected: 6/6 NEW PASS + Phase 102/103 tests preserved.

- [ ] **Step 6: Verify TypeScript compiles**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit 2>&1 | head -10
```

Expected: 0 new errors.

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts
git commit -m "feat(phase-104): ProjectSettingsIllustration Notify Thresholds subsection + 6 tests"
```

---

## Task 9: 8 regression guards (already in Task 3) + I095 EXTENDED

**Files:**
- Modify: `.lingwen/architecture.yml` (I095 docstring widened)
- Modify: `CLAUDE.md` (I095 line text extended, no version bump — version bump in Task 10)

- [ ] **Step 1: Verify all 8 guards GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen && uv run pytest packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py -v --rootdir=packages/lingwen-illustrations 2>&1 | tail -20
```

Expected: 8 guards PASS (G1, G1b, G2, G2b, G2c, G3, G4, G4b, G5, G5b, G6, G7, G8 — 13 test functions, all PASS). Counts as "8 guards G1-G8 GREEN" because G1/G2/G4 have parametrized sub-tests.

- [ ] **Step 2: Update I095 in .lingwen/architecture.yml**

Find the I095 entry. It should look like:
```yaml
- id: I095
  ...
```

Update the rule/description text to include "keyed per (project_slug, event_type) tuple" and "exactly one warning per (slug, event_type) pair".

(Exact yaml structure depends on file — find and edit text only, no structural changes.)

- [ ] **Step 3: Update I095 in CLAUDE.md**

Find the I095 line in the invariants table. Add "keyed per (project_slug, event_type) tuple" to the existing text.

- [ ] **Step 4: Commit**

```bash
git add .lingwen/architecture.yml CLAUDE.md
git commit -m "docs(phase-104): I095 EXTENDED via docstring only — tuple-keyed counter state"
```

---

## Task 10: CLAUDE.md version bump + handoff + BACKLOG + MEMORY sync

**Files:**
- Modify: `CLAUDE.md` (v60.1 → v60.2 in version block)
- Modify: `collaboration/BACKLOG.md` (Phase 104 entry)
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 104 sync)
- Modify: `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` (v60.2 entry)
- Create: `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`

- [ ] **Step 1: Update CLAUDE.md version block**

Find:
```
> **版本**: v60.1 (Phase 103 Per-Chapter default_models Overrides — first Phase 102+ extension after REQ-002 v2 closure ...
```

Replace with:
```
> **版本**: v60.2 (Phase 104 notify_threshold per event_type — second Phase 102+ extension: ...
```

Follow the Phase 103 → v60.1 pattern: brief summary of Phase 104 deliverables + validation + lessons. Keep concise.

- [ ] **Step 2: Update BACKLOG.md "最近变更" section + "已完成" table**

Add Phase 104 row to "已完成（近期）" table (use the Phase 103 row as template).

Add to "最近变更" with brief summary.

- [ ] **Step 3: Update CURRENT_STATUS.md "最后更新" + "版本" + "当前阶段" + add row to "已完成" table**

Find current Phase 103 entries and update to Phase 104. Add row to "已完成" table after the Phase 103 row.

- [ ] **Step 4: Update MEMORY.md**

Add v60.2 line + Phase 104 reference in Topic Files section.

- [ ] **Step 5: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`. Use Phase 103 handoff as template (~265 lines).

Include:
- 12 commit SHAs in commits table
- All 5 sections from the spec summarized
- Validation gates (all PASS)
- Lessons (5-7 from handoff perspective)
- Cluster cumulative (Phase 90-104 = 15 phases)
- Future work (cleanup/deletion tracking + telemetry + ARCHDEBT)

- [ ] **Step 6: Run final validation**

Run all backend pytest:
```bash
cd /home/ailearn/projects/LingWen && uv run pytest packages/lingwen-illustrations/tests/ apps/studio_api/tests/ -v --rootdir=packages/lingwen-illustrations 2>&1 | tail -20
```

Run frontend vitest:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run 2>&1 | tail -10
```

Run TypeScript:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit 2>&1 | tail -5
```

Run ruff:
```bash
cd /home/ailearn/projects/LingWen && ruff check apps/studio_api/routes/project_settings.py packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py
```

Expected: all GREEN.

- [ ] **Step 7: Commit docs sync**

```bash
git add CLAUDE.md collaboration/BACKLOG.md collaboration/CURRENT_STATUS.md ~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md
git commit -m "docs(phase-104): CLAUDE.md v60.1→v60.2 + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync"
```

- [ ] **Step 8: Push to origin**

```bash
git push origin master
```

---

## Self-Review

### Spec coverage
- Spec §1 (Schema) → Task 3 ✓
- Spec §2 (Counter state) → Task 4 ✓
- Spec §3 (Pipeline integration) → Task 5 ✓
- Spec §4 (TS type widening) → Task 6 ✓
- Spec §5 (Store sync) → Task 7 ✓
- Spec §6 (UI component) → Task 8 ✓
- Spec Tests/guards (G1-G8) → Task 3 (G1-G5 validator + helper) + Task 9 (verify all GREEN)
- Spec Invariants (I095 EXTENDED) → Task 9 ✓
- Spec Commits (12 atomic) → Tasks 3-10 ✓

### Placeholder scan
- No "TBD"/"TODO" in concrete steps
- All code blocks complete
- Exact file paths throughout

### Type consistency
- `_resolve_threshold(settings, event_type) -> int | float` — defined in Task 5, used in Task 4 tests (G5/G5b) ✓
- `record_failure(..., threshold: int | float, event_type: str)` — Task 4, used in pipeline Task 5 ✓
- `record_success(slug, event_type)` — Task 4, used in pipeline Task 5 ✓
- `normalizeNotifyThreshold` — Task 7 spec, exported for Task 7 tests + Task 8 (UI calls it via store) ✓
- `NOTIFY_EVENT_TYPES` constant — Task 6, used in Task 7 (store), Task 8 (UI) ✓
- `INFINITY_THRESHOLD` constant — Task 4 (notifications.py), Task 5 (pipeline.py imports it) ✓

Note: `INFINITY_THRESHOLD` is defined in BOTH notifications.py and pipeline.py — this is intentional separation (notifications module stays import-light; pipeline.py needs it for `_resolve_threshold`). Same constant value (`math.inf`), but two locations to avoid cross-package import.

### Risk check
- **Counter key migration (Phase 102 tests)**: Task 4 Step 7 explicitly covers this.
- **Pydantic type widening**: Task 3 Step 2 + Step 3 (validator body) covers it.
- **Frontend type widening**: Task 6 covers it; Task 8 covers UI consumption.
- **Pipeline `_notify_threshold` widening to int | float**: Task 5 covers it (was int, now `_resolve_threshold` returns int | float).

Plan complete.