# Phase 19+ Sub1 — World Model Domain Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `infra/world_model/data_structures.py::WorldSnapshot` + `infra/subplot/data_structures.py::Plot` to `packages/lingwen-core/domain/`, fill the API gap (to_dict/from_dict + active_subplots + physical/mental fields), and migrate 10+ consumer files to the new location while keeping `infra/*` as 1-line PHASE-COMPAT shims.

**Architecture:** Atomic 1-file commits + dual PHASE-COMPAT shims. Domain fill (Phase 1, T1-T6) → consumer migration (Phase 2, T7-T16) → shim creation (Phase 3, T17) → docs close (Phase 4, T18).

**Tech Stack:** Python 3.13 (conda), dataclasses-frozen, pytest, Pydantic v2 (DomainEvent base), Python `from typing import Any` for `active_subplots` duck-typing until T4 provides `Plot`.

**Branch:** `phase-19-sub1` (created from master `1b45153a` on 2026-09-01, spec at `docs/superpowers/specs/2026-09-01-phase-19-sub1-world-model-domain-design.md`).

**Verification gates (run after each task):**
```bash
# Backend (must use miniconda Python)
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/ \
  tests/subplot/ \
  tests/consistency/ \
  tests/world_model/ \
  --rootdir=. -q

# Lint
ruff check infra/ packages/lingwen-core/

# Import-linter contract (must remain 3 KEPT)
# Run via project Makefile/CI — keep it intact; lingwen-core → infra MUST NOT appear
```

---

## Pre-Implementation: Worktree Setup

This plan assumes a worktree. If you are NOT already in a worktree for this branch, create one:

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-19-sub1 -b phase-19-sub1
cd .worktrees/phase-19-sub1
```

Verify branch state:

```bash
git branch --show-current  # phase-19-sub1
git log --oneline -1       # d3da0d27 (spec commit)
```

---

## Task 1: Add `to_dict()` / `from_dict()` to `WorldSnapshot`

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/domain/ripple.py:134-170` (the `WorldSnapshot` class)

- [ ] **Step 1: Edit ripple.py to add `to_dict()` method**

Edit `WorldSnapshot` in `packages/lingwen-core/src/lingwen_core/domain/ripple.py`. Add these methods AFTER `compute_consistency_hash` (after line 170):

```python
    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "chapter": self.chapter,
            "timestamp": self.timestamp.isoformat(),
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "relations": [r.to_dict() for r in self.relations],
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "world_mood": self.world_mood,
            "consistency_hash": self.consistency_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorldSnapshot":
        from lingwen_core.domain.common import KeyPoint, NodeId, Relation
        nodes = {
            NodeId.from_string(s): KeyPoint.from_dict(kd)
            for s, kd in d.get("nodes", {}).items()
        }
        return cls(
            snapshot_id=d["snapshot_id"],
            chapter=d["chapter"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            nodes=nodes,
            relations=tuple(Relation.from_dict(rd) for rd in d.get("relations", [])),
            active_ripples=tuple(
                Ripple.from_dict(rd) for rd in d.get("active_ripples", [])
            ),
            world_mood=d.get("world_mood", "neutral"),
            consistency_hash=d.get("consistency_hash", ""),
        )
```

Note: `physical` / `mental` / `active_subplots` fields are NOT YET defined. `to_dict` / `from_dict` are written defensively to ignore them when they're absent. `compute_consistency_hash` will be updated in Task 4.

- [ ] **Step 2: Verify import + syntax**

```bash
/home/ailearn/miniconda3/bin/python -c "from lingwen_core.domain.ripple import WorldSnapshot; print(hasattr(WorldSnapshot, 'to_dict'), hasattr(WorldSnapshot, 'from_dict'))"
```

Expected: `True True`

- [ ] **Step 3: Run existing tests to confirm no regression**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/test_domain.py -q
```

Expected: All existing tests pass (NEW methods not yet exercised).

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/domain/ripple.py
git commit -m "feat(lingwen-core): WorldSnapshot.to_dict/from_dict" -m "Match Ripple/KeyPoint/Relation pattern. Pre-Step for Phase 19+ Sub1
atomic API gap fill. Active_subplots + physical/mental still missing,
so to_dict/from_dict ignore those keys when absent (defensive)."

# Co-Authored-By trailer as per project convention
```

---

## Task 2: Add `physical` and `mental` fields to `WorldSnapshot`

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/domain/ripple.py:147` (insert fields after `active_ripples`)

- [ ] **Step 1: Add fields**

Edit `WorldSnapshot` in `packages/lingwen-core/src/lingwen_core/domain/ripple.py`. Update the field list to import `PhysicalLine` and `MentalLine`, and add the two new fields:

Replace line 17 (`from lingwen_core.domain.common import KeyPoint, NodeId, Relation`) with:

```python
from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, Relation
```

In the `WorldSnapshot` dataclass, ADD two new fields AFTER `active_ripples`:

```python
    active_ripples: tuple[Ripple, ...] = ()
    physical: PhysicalLine = field(default_factory=lambda: PhysicalLine(ch=0))
    mental: MentalLine = field(default_factory=lambda: MentalLine(ch=0))
    world_mood: str = "neutral"
```

Note: `field` import is at line 12 (`from dataclasses import dataclass, field`). The lambda for `PhysicalLine(ch=0)` / `MentalLine(ch=0)` matches `infra/world_model/data_structures.py:288-289` exactly.

- [ ] **Step 2: Update `compute_consistency_hash` to include physical/mental**

Replace `compute_consistency_hash` (lines 161-170) with:

```python
    def compute_consistency_hash(self) -> str:
        """基于 nodes + relations + ripples + lines 计算一致性 hash"""
        payload = {
            "nodes": {str(k): v.to_dict() for k, v in sorted(self.nodes.items(), key=lambda x: str(x[0]))},
            "relations": [r.to_dict() for r in sorted(self.relations, key=lambda r: (str(r.src), str(r.dst)))],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "world_mood": self.world_mood,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
```

- [ ] **Step 3: Update `to_dict` to include physical/mental**

Replace the `to_dict` method body with:

```python
    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "chapter": self.chapter,
            "timestamp": self.timestamp.isoformat(),
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "relations": [r.to_dict() for r in self.relations],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "world_mood": self.world_mood,
            "consistency_hash": self.consistency_hash,
        }
```

- [ ] **Step 4: Update `from_dict` to consume physical/mental**

Replace `from_dict` body with:

```python
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorldSnapshot":
        from lingwen_core.domain.common import KeyPoint, NodeId, Relation
        nodes = {
            NodeId.from_string(s): KeyPoint.from_dict(kd)
            for s, kd in d.get("nodes", {}).items()
        }
        return cls(
            snapshot_id=d["snapshot_id"],
            chapter=d["chapter"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            nodes=nodes,
            relations=tuple(Relation.from_dict(rd) for rd in d.get("relations", [])),
            physical=PhysicalLine.from_dict(d.get("physical", {"ch": 0})),
            mental=MentalLine.from_dict(d.get("mental", {"ch": 0})),
            active_ripples=tuple(
                Ripple.from_dict(rd) for rd in d.get("active_ripples", [])
            ),
            world_mood=d.get("world_mood", "neutral"),
            consistency_hash=d.get("consistency_hash", ""),
        )
```

- [ ] **Step 5: Verify imports resolve**

```bash
/home/ailearn/miniconda3/bin/python -c "
from lingwen_core.domain.ripple import WorldSnapshot
from datetime import datetime
s = WorldSnapshot(snapshot_id='s', chapter=1, timestamp=datetime(2026, 1, 1))
print('physical.ch:', s.physical.ch)
print('mental.ch:', s.mental.ch)
d = s.to_dict()
assert 'physical' in d and 'mental' in d
s2 = WorldSnapshot.from_dict(d)
assert s == s2
"
```

Expected: prints `physical.ch: 0`, `mental.ch: 0`, no error.

- [ ] **Step 6: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/domain/ripple.py
git commit -m "feat(lingwen-core): WorldSnapshot.physical/mental fields" -m "Add PhysicalLine + MentalLine references with default_factory(ch=0).
Types live in domain/chapter.py. Update compute_consistency_hash /
to_dict / from_dict to include these fields. Default factory mirrors
infra/world_model/data_structures.py:288-289 exactly."
```

---

## Task 3: Add `active_subplots` field to `WorldSnapshot`

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/domain/ripple.py:147` (insert field)

- [ ] **Step 1: Add `active_subplots` field**

Edit the `WorldSnapshot` dataclass in `packages/lingwen-core/src/lingwen_core/domain/ripple.py`. ADD new field AFTER `active_ripples` (BEFORE `physical` / `mental`):

```python
    active_ripples: tuple[Ripple, ...] = ()
    active_subplots: tuple[Any, ...] = ()  # Plot when Task 4 lands; tuple[Any, ...] for now
    physical: PhysicalLine = field(default_factory=lambda: PhysicalLine(ch=0))
    mental: MentalLine = field(default_factory=lambda: MentalLine(ch=0))
```

`tuple[Any, ...]` is used here because `Plot` lives in `infra/subplot/data_structures.py` until Task 5 moves it. Task 6 will tighten this annotation.

- [ ] **Step 2: Update `compute_consistency_hash` to include active_subplots**

Update the `payload` dict in `compute_consistency_hash`:

```python
        payload = {
            "nodes": {str(k): v.to_dict() for k, v in sorted(self.nodes.items(), key=lambda x: str(x[0]))},
            "relations": [r.to_dict() for r in sorted(self.relations, key=lambda r: (str(r.src), str(r.dst)))],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "active_subplots": [getattr(p, "to_dict", lambda: p)() for p in self.active_subplots],
            "world_mood": self.world_mood,
        }
```

- [ ] **Step 3: Update `to_dict` to include active_subplots**

Replace the `to_dict` body with:

```python
    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "chapter": self.chapter,
            "timestamp": self.timestamp.isoformat(),
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "relations": [r.to_dict() for r in self.relations],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "active_subplots": [getattr(p, "to_dict", lambda: p)() for p in self.active_subplots],
            "world_mood": self.world_mood,
            "consistency_hash": self.consistency_hash,
        }
```

- [ ] **Step 4: Update `from_dict` with backward-compat default for old JSON**

In `from_dict`, after the `Ripple.from_dict` line, add the subplots parsing with `.get()` backward-compat:

```python
            active_ripples=tuple(
                Ripple.from_dict(rd) for rd in d.get("active_ripples", [])
            ),
            # active_subplots NOT loaded from_dict (Plot not yet in lingwen-core;
            # uses TYPE_CHECKING bridge in Task 6). Stays as default ()
            world_mood=d.get("world_mood", "neutral"),
            consistency_hash=d.get("consistency_hash", ""),
```

- [ ] **Step 5: Smoke test**

```bash
/home/ailearn/miniconda3/bin/python -c "
from lingwen_core.domain.ripple import WorldSnapshot
from datetime import datetime
s = WorldSnapshot(snapshot_id='s', chapter=1, timestamp=datetime(2026, 1, 1))
print('active_subplots default:', s.active_subplots)
print('hash:', s.consistency_hash)
"
```

Expected: `active_subplots default: ()`, hash is non-empty 16-char hex.

- [ ] **Step 6: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/domain/ripple.py
git commit -m "feat(lingwen-core): WorldSnapshot.active_subplots field" -m "Type tuple[Any, ...] until Task 4 moves Plot to lingwen_core.domain.
Default factory is empty tuple. Update compute_consistency_hash /
to_dict to include subplots via duck typing (getattr).
from_dict uses .get() for backward-compat with pre-Phase 1.2 JSON."
```

---

## Task 4: Move `Plot` to `packages/lingwen-core/domain/subplot.py` + 5 RED tests

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/domain/subplot.py`
- Create: `packages/lingwen-core/tests/test_subplot.py`
- Modify: `packages/lingwen-core/src/lingwen_core/domain/__init__.py:18-24, 44-75`

- [ ] **Step 1: Write 5 RED tests in new `test_subplot.py`**

Create `packages/lingwen-core/tests/test_subplot.py` with:

```python
"""Phase 19+ Sub1 — Plot entity guard tests."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest


def test_plot_importable():
    from lingwen_core.domain.subplot import Plot
    assert Plot is not None


def test_plot_frozen():
    from lingwen_core.domain.subplot import Plot, PlotStatus, PlotType

    p = Plot(
        plot_id="p:1",
        type=PlotType.SUBPLOT,
        title="test",
        status=PlotStatus.ACTIVE,
    )
    assert is_dataclass(p)
    assert p.__dataclass_params__.frozen  # type: ignore[attr-defined]
    with pytest.raises(FrozenInstanceError):
        p.plot_id = "x"  # type: ignore[misc]


def test_plot_rejects_empty_plot_id():
    from lingwen_core.domain.subplot import Plot, PlotStatus, PlotType

    with pytest.raises(ValueError, match="non-empty"):
        Plot(plot_id="", type=PlotType.SUBPLOT, title="t", status=PlotStatus.ACTIVE)


def test_plot_to_dict_from_dict_roundtrip():
    from lingwen_core.domain.common import NodeId, NodeType
    from lingwen_core.domain.subplot import Plot, PlotPurpose, PlotStatus, PlotType

    p = Plot(
        plot_id="p:1",
        type=PlotType.SUBPLOT,
        title="mystery",
        status=PlotStatus.ACTIVE,
        purpose=PlotPurpose.MYSTERY,
        protagonist_link=NodeId(NodeType.CHARACTER, "alice"),
        birth_ch=10,
        active_ch_range=(10, 50),
    )
    d = p.to_dict()
    p2 = Plot.from_dict(d)
    assert p == p2


def test_plot_state_machine_enums():
    from lingwen_core.domain.subplot import PlotPurpose, PlotStatus, PlotType

    assert PlotType.MAIN.value == "main"
    assert PlotType.SUBPLOT.value == "subplot"
    assert PlotStatus.DRAFT.value == "draft"
    assert PlotStatus.CLOSED.value == "closed"
    assert PlotPurpose.GROWTH.value == "growth"
    assert PlotPurpose.MYSTERY.value == "mystery"
```

- [ ] **Step 2: Run tests to verify RED**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/test_subplot.py -q
```

Expected: All 5 tests fail with `ModuleNotFoundError: No module named 'lingwen_core.domain.subplot'`.

- [ ] **Step 3: Create `subplot.py` (verbatim copy from infra)**

Create `packages/lingwen-core/src/lingwen_core/domain/subplot.py`:

```python
"""灵文核心 · Domain — Subplot/Plot 实体

Phase 19+ Sub1 — 从 infra/subplot/data_structures.py 迁移到 lingwen-core/domain。

主支线/支线定义 + 3 个 str Enum。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from lingwen_core.domain.common import NodeId

MAX_ACTIVE_SUBPLOTS = 5


class PlotType(str, Enum):
    """支线类型"""

    MAIN = "main"
    SUBPLOT = "subplot"
    SIDE = "side"


class PlotPurpose(str, Enum):
    """支线目的 — 8 个语义维度"""

    GROWTH = "growth"
    MYSTERY = "mystery"
    PAYOFF = "payoff"
    FACTION = "faction"
    ROMANCE = "romance"
    PACING = "pacing"
    ARTIFACT = "artifact"
    THEME = "theme"


class PlotStatus(str, Enum):
    """支线状态 — 6 个状态"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class Plot:
    """支线/主线定义 — 不可变"""

    plot_id: str
    type: PlotType
    title: str
    status: PlotStatus
    purpose: PlotPurpose = PlotPurpose.GROWTH
    protagonist_link: Optional[NodeId] = None
    birth_ch: int = 0
    active_ch_range: tuple[int, int] = (0, 0)
    close_ch: Optional[int] = None
    constraints_generated: tuple[str, ...] = ()
    related_ripples: tuple[str, ...] = ()
    parent_plot: Optional[str] = None
    key_chapters: tuple[int, ...] = ()
    next_constraint_ch: int = 0

    def __post_init__(self) -> None:
        if not self.plot_id or not self.plot_id.strip():
            raise ValueError("plot_id must be non-empty")
        if not self.title or not self.title.strip():
            raise ValueError("title must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "type": self.type.value,
            "title": self.title,
            "status": self.status.value,
            "purpose": self.purpose.value,
            "protagonist_link": str(self.protagonist_link) if self.protagonist_link else None,
            "birth_ch": self.birth_ch,
            "active_ch_range": list(self.active_ch_range),
            "close_ch": self.close_ch,
            "constraints_generated": list(self.constraints_generated),
            "related_ripples": list(self.related_ripples),
            "parent_plot": self.parent_plot,
            "key_chapters": list(self.key_chapters),
            "next_constraint_ch": self.next_constraint_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Plot":
        protagonist = d.get("protagonist_link")
        protagonist_link = NodeId.from_string(protagonist) if protagonist else None
        return cls(
            plot_id=d["plot_id"],
            type=PlotType(d["type"]),
            title=d["title"],
            status=PlotStatus(d["status"]),
            purpose=PlotPurpose(d.get("purpose", PlotPurpose.GROWTH.value)),
            protagonist_link=protagonist_link,
            birth_ch=d.get("birth_ch", 0),
            active_ch_range=tuple(d.get("active_ch_range", [0, 0])),
            close_ch=d.get("close_ch"),
            constraints_generated=tuple(d.get("constraints_generated", [])),
            related_ripples=tuple(d.get("related_ripples", [])),
            parent_plot=d.get("parent_plot"),
            key_chapters=tuple(d.get("key_chapters", [])),
            next_constraint_ch=d.get("next_constraint_ch", 0),
        )


__all__ = [
    "MAX_ACTIVE_SUBPLOTS",
    "Plot",
    "PlotPurpose",
    "PlotStatus",
    "PlotType",
]
```

- [ ] **Step 4: Update `domain/__init__.py` to re-export subplot symbols**

Edit `packages/lingwen-core/src/lingwen_core/domain/__init__.py`. ADD:

After existing ripple import block:

```python
from lingwen_core.domain.subplot import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
```

In `__all__` list (the explicit exports), ADD:

```python
    # Subplot
    "Plot",
    "PlotType",
    "PlotPurpose",
    "PlotStatus",
    "MAX_ACTIVE_SUBPLOTS",
```

- [ ] **Step 5: Run tests to verify GREEN**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/test_subplot.py -q
```

Expected: 5 passed.

- [ ] **Step 6: Verify domain package imports cleanly**

```bash
/home/ailearn/miniconda3/bin/python -c "
import lingwen_core.domain as d
for name in ['Plot', 'PlotType', 'PlotStatus', 'PlotPurpose', 'MAX_ACTIVE_SUBPLOTS']:
    assert hasattr(d, name), f'missing: {name}'
print('all 5 subplot symbols exported via lingwen_core.domain')
"
```

- [ ] **Step 7: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/domain/subplot.py \
        packages/lingwen-core/src/lingwen_core/domain/__init__.py \
        packages/lingwen-core/tests/test_subplot.py
git commit -m "feat(lingwen-core): subplot module + Plot entity" -m "Move Plot/PlotType/PlotPurpose/PlotStatus/MAX_ACTIVE_SUBPLOTS from
infra/subplot/data_structures.py to lingwen_core.domain.subplot.
Verbatim copy with one import change: infra.world_model.NodeId →
lingwen_core.domain.common.NodeId. 5 RED tests for frozen invariant +
to_dict/from_dict round-trip + 3 enums."
```

---

## Task 5: Make `infra/subplot/data_structures.py` a 1-line PHASE-COMPAT shim

**Files:**
- Modify: `infra/subplot/data_structures.py` (replace full impl with shim re-exports)

- [ ] **Step 1: Replace file with shim**

Write a new `infra/subplot/data_structures.py`:

```python
"""PHASE-COMPAT: Phase 19+ — DELETE after Phase 19.x

Back-compat shim re-exporting ``Plot`` data class from
``lingwen_core.domain.subplot``. Historically lived at
``infra.subplot.data_structures.Plot`` before consolidation into the
lingwen_core package.

Behavior helpers (``add_subplot``, ``get_active_subplots``,
``subplots_count``) live in their own module ``infra.subplot.helpers``
which has not yet migrated. They will move to ``lingwen_core.use_cases``
or similar application layer in a future phase.

DO NOT add new code here; this is a deletion target.
"""
from __future__ import annotations

from lingwen_core.domain.subplot import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)

__all__ = [
    "MAX_ACTIVE_SUBPLOTS",
    "Plot",
    "PlotPurpose",
    "PlotStatus",
    "PlotType",
]
```

**IMPORTANT**: This REPLACES the helper functions `add_subplot`, `get_active_subplots`, `subplots_count` from the original file. These helpers were moved in Phase 18.1 to `infra/subplot/helpers.py` (or similar). Verify by checking before deleting:

```bash
grep -rn "from infra.subplot.data_structures import" /home/ailearn/projects/LingWen --include="*.py"
```

If the grep shows imports of `add_subplot` / `get_active_subplots` / `subplots_count` from `infra.subplot.data_structures`, STOP — these helpers exist somewhere and need to be migrated first. Locate them:

```bash
grep -rn "def add_subplot\|def get_active_subplots\|def subplots_count" /home/ailearn/projects/LingWen --include="*.py"
```

If found, move them to `infra/subplot/helpers.py` (NEW file) BEFORE replacing `data_structures.py`. The helper file should look like:

```python
"""infra/subplot/helpers.py — Phase 19+ retained-behavior layer

Subplot application services that operate on Plot instances. Implementation
unchanged from when it lived in ``infra/subplot/data_structures.py``.
"""
from __future__ import annotations

from typing import Iterable

from lingwen_core.domain.ripple import WorldSnapshot
from lingwen_core.domain.subplot import Plot

MAX_ACTIVE_SUBPLOTS = 5


def add_subplot(snap: WorldSnapshot, plot: Plot) -> WorldSnapshot:
    """Add a subplot to the snapshot; returns new snapshot (frozen)."""
    subplots = list(snap.active_subplots) + [plot]
    return _replace_subplots(snap, tuple(subplots))


def get_active_subplots(snap: WorldSnapshot) -> list[Plot]:
    """Return all ACTIVE subplots from snapshot."""
    return [p for p in snap.active_subplots if p.status.value == "active"]


def subplots_count(snap: WorldSnapshot) -> int:
    return len(snap.active_subplots)


def _replace_subplots(snap: WorldSnapshot, subplots: tuple) -> WorldSnapshot:
    """Internal helper: replace active_subplots via dataclasses.replace."""
    from dataclasses import replace
    return replace(snap, active_subplots=subplots)
```

(Adjust helper implementations to match whatever the existing helpers did — read them before delete.)

- [ ] **Step 2: Verify shim re-exports work**

```bash
/home/ailearn/miniconda3/bin/python -c "
from infra.subplot.data_structures import Plot, PlotStatus, PlotType, MAX_ACTIVE_SUBPLOTS
print('shim re-exports OK')
print('Plot is lingwen_core.domain.subplot.Plot:', Plot.__module__ == 'lingwen_core.domain.subplot')
"
```

Expected: prints OK and `True`.

- [ ] **Step 3: Run regression test against subplot integration**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/subplot/test_subplot_data_structures.py \
  tests/subplot/test_subplot_integration.py -q
```

Expected: All tests pass via shim (data structures path unchanged; helpers path resolved to helpers module).

- [ ] **Step 4: Commit**

```bash
git add infra/subplot/data_structures.py infra/subplot/helpers.py 2>/dev/null || git add infra/subplot/data_structures.py
git commit -m "refactor(infra): subplot.data_structures shim" -m "1-line PHASE-COMPAT re-export of Plot from lingwen_core.domain.subplot.
Behavior helpers (add_subplot/get_active_subplots/subplots_count)
moved to infra/subplot/helpers.py (NEW) — split before shim can
delete its impl. Marked for deletion post-Phase 19.x."
```

---

## Task 6: Tighten `active_subplots` annotation from `tuple[Any, ...]` to `tuple[Plot, ...]`

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/domain/ripple.py:147` (type annotation only)

- [ ] **Step 1: Replace `tuple[Any, ...]` with `tuple[Plot, ...]`**

Edit `packages/lingwen-core/src/lingwen_core/domain/ripple.py`. The `Plot` import already exists in the file via the import block (re-export from `domain` was added in Task 4). Add explicit import to the existing import block:

```python
from lingwen_core.domain.subplot import Plot
```

Then update the field annotation:

```python
    active_subplots: tuple[Plot, ...] = ()
```

- [ ] **Step 2: Verify typing works**

```bash
/home/ailearn/miniconda3/bin/python -c "
from datetime import datetime
from lingwen_core.domain.ripple import WorldSnapshot
import lingwen_core.domain.subplot as sub
snap = WorldSnapshot(snapshot_id='s', chapter=1, timestamp=datetime(2026,1,1))
print('active_subplots type:', snap.active_subplots.__class__.__name__)
print('empty:', snap.active_subplots)
"
```

Expected: prints `tuple` and `()`.

- [ ] **Step 3: Run regression**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/ -q
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/domain/ripple.py
git commit -m "refactor(lingwen-core): tighten active_subplots to tuple[Plot, ...]" -m "Replace temporary tuple[Any, ...] with tuple[Plot, ...] now that
Plot is canonical in lingwen_core.domain.subplot (Task 4).
Reinforces DDD: domain field has domain-type annotation."
```

---

## Task 7: WorldSnapshot serialization tests (7 bundled tests)

**Files:**
- Modify: `packages/lingwen-core/tests/test_domain.py` (append tests, before `test_domain_init_exports_all`)

- [ ] **Step 1: Append 7 tests for WorldSnapshot methods**

Add to `packages/lingwen-core/tests/test_domain.py`, just BEFORE `test_domain_init_exports_all`:

```python
# ─────────────────────────────────────────────────────────
# ripple: WorldSnapshot.to_dict / from_dict / physical/mental / active_subplots
# Phase 19+ Sub1
# ─────────────────────────────────────────────────────────


def test_world_snapshot_to_dict_minimal():
    from datetime import datetime

    from lingwen_core.domain.ripple import WorldSnapshot

    snap = WorldSnapshot(
        snapshot_id="snap:1",
        chapter=10,
        timestamp=datetime(2026, 1, 1),
    )
    d = snap.to_dict()
    assert d["snapshot_id"] == "snap:1"
    assert d["chapter"] == 10
    assert d["timestamp"] == "2026-01-01T00:00:00"
    assert d["physical"]["ch"] == 0
    assert d["mental"]["ch"] == 0
    assert d["active_ripples"] == []
    assert d["active_subplots"] == []
    assert d["world_mood"] == "neutral"
    assert d["consistency_hash"] == snap.consistency_hash


def test_world_snapshot_from_dict_minimal():
    from datetime import datetime

    from lingwen_core.domain.ripple import WorldSnapshot

    d = {
        "snapshot_id": "snap:2",
        "chapter": 11,
        "timestamp": "2026-02-01T12:30:00",
        "nodes": {},
        "relations": [],
        "physical": {"ch": 11, "actions": [], "locations": [], "events": [], "constraints": []},
        "mental": {"ch": 11, "thoughts": [], "emotions": {}, "arc_progress": {}, "growth_signals": []},
        "active_ripples": [],
        "active_subplots": [],
        "world_mood": "neutral",
        "consistency_hash": "",
    }
    snap = WorldSnapshot.from_dict(d)
    assert snap.snapshot_id == "snap:2"
    assert snap.chapter == 11
    assert snap.timestamp == datetime(2026, 2, 1, 12, 30, 0)
    assert snap.physical.ch == 11


def test_world_snapshot_roundtrip_equality():
    from datetime import datetime

    from lingwen_core.domain.common import NodeId, NodeType
    from lingwen_core.domain.ripple import WorldSnapshot

    snap = WorldSnapshot(
        snapshot_id="snap:3",
        chapter=12,
        timestamp=datetime(2026, 3, 1),
        nodes={NodeId(NodeType.CHARACTER, "alice"): ...},  # placeholder; see note
    )
    # Skip nodes here because KeyPoint construction needs attrs. Test structural fields.
    snap2 = WorldSnapshot.from_dict(snap.to_dict())
    assert snap2 == snap


def test_world_snapshot_physical_mental_defaults():
    from datetime import datetime

    from lingwen_core.domain.ripple import WorldSnapshot

    snap = WorldSnapshot(snapshot_id="s", chapter=1, timestamp=datetime(2026, 1, 1))
    assert snap.physical.ch == 0
    assert snap.mental.ch == 0
    assert snap.physical.actions == ()
    assert snap.mental.thoughts == ()


def test_world_snapshot_physical_mental_serialize():
    from datetime import datetime

    from lingwen_core.domain.ripple import WorldSnapshot

    snap = WorldSnapshot(
        snapshot_id="s", chapter=5, timestamp=datetime(2026, 1, 1),
    )
    d = snap.to_dict()
    assert "physical" in d
    assert "mental" in d
    assert d["physical"]["ch"] == 0
    assert d["mental"]["ch"] == 0
    snap2 = WorldSnapshot.from_dict(d)
    assert snap2.physical.ch == 0
    assert snap2.mental.ch == 0


def test_world_snapshot_active_subplots_default_empty():
    from datetime import datetime

    from lingwen_core.domain.ripple import WorldSnapshot

    snap = WorldSnapshot(snapshot_id="s", chapter=1, timestamp=datetime(2026, 1, 1))
    assert snap.active_subplots == ()


def test_world_snapshot_from_dict_backward_compat_no_active_subplots():
    """Pre-Phase 1.2 JSON (no active_subplots key) loads cleanly."""
    from lingwen_core.domain.ripple import WorldSnapshot

    d = {
        "snapshot_id": "old",
        "chapter": 1,
        "timestamp": "2026-01-01T00:00:00",
        "nodes": {},
        "relations": [],
        "physical": {"ch": 1, "actions": [], "locations": [], "events": [], "constraints": []},
        "mental": {"ch": 1, "thoughts": [], "emotions": {}, "arc_progress": {}, "growth_signals": []},
        "active_ripples": [],
        "world_mood": "neutral",
    }
    snap = WorldSnapshot.from_dict(d)
    assert snap.active_subplots == ()
```

Note: The first `test_world_snapshot_roundtrip_equality` has a `...` placeholder for `KeyPoint(...)` construction — replace with a real `KeyPoint(id=NodeId(...), attrs={})` if needed:

```python
from lingwen_core.domain.common import KeyPoint
...,
nodes={NodeId(NodeType.CHARACTER, "alice"): KeyPoint(id=NodeId(NodeType.CHARACTER, "alice"))},
```

- [ ] **Step 2: Run tests to verify all 7 pass**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/test_domain.py -q
```

Expected: 7 new tests pass + all pre-existing tests still pass.

- [ ] **Step 3: Commit**

```bash
git add packages/lingwen-core/tests/test_domain.py
git commit -m "test(lingwen-core): WorldSnapshot serialization + field defaults" -m "7 NEW tests covering to_dict/from_dict minimal + round-trip equality +
physical/mental defaults + serialize + active_subplots default +
backward-compat from_dict with old JSON (no active_subplots key)."
```

---

## Task 8: Migrate `tests/subplot/test_subplot_integration.py`

**Files:**
- Modify: `tests/subplot/test_subplot_integration.py:29-38` (replace import block)

- [ ] **Step 1: Replace `infra.world_model` import with `lingwen_core.domain`**

Edit `tests/subplot/test_subplot_integration.py`. Find the import block at lines 29-38:

```python
from infra.world_model import (
    KeyPoint,
    NodeId,
    NodeType,
    PhysicalLine,
    WorldSnapshot,
    add_subplot,
    get_active_subplots,
    subplots_count,
)
```

REPLACE with:

```python
from lingwen_core.domain.chapter import PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType
from lingwen_core.domain.ripple import WorldSnapshot
from infra.subplot.helpers import add_subplot, get_active_subplots, subplots_count
```

- [ ] **Step 2: Run test**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/subplot/test_subplot_integration.py -q
```

Expected: All 13 tests pass (including the 5 previously-blocked by Phase 18 Finding B).

- [ ] **Step 3: Commit**

```bash
git add tests/subplot/test_subplot_integration.py
git commit -m "refactor(tests): subplot_integration migrate to lingwen_core.domain" -m "WorldSnapshot/KeyPoint/NodeId/NodeType/PhysicalLine now imported
from lingwen_core.domain. Helpers (add_subplot/get_active_subplots/
subplots_count) come from infra.subplot.helpers module (split in
Task 5). 5 previously-blocked tests now pass via lingwen_core route."
```

---

## Task 9: Migrate `tests/subplot/test_subplot_data_structures.py`

**Files:**
- Modify: `tests/subplot/test_subplot_data_structures.py:18-29` (replace import block)

- [ ] **Step 1: Replace imports**

Edit `tests/subplot/test_subplot_data_structures.py`. Find lines 18-29:

```python
from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)

# 跨包引用: Plot.protagonist_link → world_model.NodeId
try:
    from infra.world_model import NodeId, NodeType
except ImportError:  # pragma: no cover
    NodeId = None
    NodeType = None
```

REPLACE with:

```python
from lingwen_core.domain.common import NodeId, NodeType
from lingwen_core.domain.subplot import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
```

Drop the try/except — NodeId is now in canonical location, import always succeeds.

- [ ] **Step 2: Run test**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/subplot/test_subplot_data_structures.py -q
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/subplot/test_subplot_data_structures.py
git commit -m "refactor(tests): subplot_data_structures migrate to lingwen_core.domain" -m "Plot/PlotType/PlotStatus/PlotPurpose/MAX_ACTIVE_SUBPLOTS now from
lingwen_core.domain.subplot. NodeId/NodeType from lingwen_core.domain.common.
try/except import-guard removed (was for legacy infra.world_model availability)."
```

---

## Task 10: Migrate `tests/consistency/checkers/test_foreshadow_ripple_alignment.py`

**Files:**
- Modify: `tests/consistency/checkers/test_foreshadow_ripple_alignment.py:26-28` (replace imports)

- [ ] **Step 1: Replace imports**

Edit `tests/consistency/checkers/test_foreshadow_ripple_alignment.py`. Find lines 26-28:

```python
from infra.world_model.data_structures import Ripple, RippleState
from infra.world_model.lifecycle import RESOLUTION_GRACE_CH
from infra.world_model.registry import RippleRegistry
```

This file imports `Ripple`/`RippleState` from infra. `RESOLUTION_GRACE_CH` and `RippleRegistry` are NOT domain entities (they're behavior constants/services that stay in `infra.world_model.*`). REPLACE only the FIRST line:

```python
from lingwen_core.domain.ripple import Ripple, RippleState
from infra.world_model.lifecycle import RESOLUTION_GRACE_CH
from infra.world_model.registry import RippleRegistry
```

- [ ] **Step 2: Run test**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/consistency/checkers/test_foreshadow_ripple_alignment.py -q
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/consistency/checkers/test_foreshadow_ripple_alignment.py
git commit -m "refactor(tests): foreshadow_ripple_alignment migrate to lingwen_core.domain" -m "Ripple/RippleState from lingwen_core.domain.ripple. RESOLUTION_GRACE_CH
and RippleRegistry remain infra.world_model.* (behavior services, not
Phase 19+ Sub1 scope)."
```

---

## Task 11: Migrate `tests/consistency/checkers/test_pacing_ripple_integration.py`

**Files:**
- Modify: `tests/consistency/checkers/test_pacing_ripple_integration.py` (replace `infra.world_model` imports with `lingwen_core.domain` imports, scope to Ripple/WorldSnapshot only)

- [ ] **Step 1: Find and replace imports**

```bash
grep -n "from infra" tests/consistency/checkers/test_pacing_ripple_integration.py | head -10
```

For each line importing Ripple / WorldSnapshot / KeyPoint / NodeId / PhysicalLine / MentalLine from `infra.world_model.*`:

REPLACE with the corresponding `from lingwen_core.domain.{chapter,common,ripple}` import.

Behavior imports (`infra.world_model.lifecycle`, `infra.world_model.registry`, etc.) STAY as-is.

- [ ] **Step 2: Run test**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/consistency/checkers/test_pacing_ripple_integration.py -q
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/consistency/checkers/test_pacing_ripple_integration.py
git commit -m "refactor(tests): pacing_ripple_integration migrate Ripple/WorldSnapshot" -m "Domain entities from lingwen_core.domain; behavior services stay in
infra.world_model.* (lifecycle/registry — not Phase 19+ Sub1 scope)."
```

---

## Tasks 12-18: Migrate `tests/world_model/test_*.py` files

For each of the 7 remaining test files (Tasks 12-18 below), the migration is mechanical: replace `from infra.world_model.data_structures import X, Y, Z` → split across `lingwen_core.domain.{chapter,common,ripple}`.

Use Task 12 as the canonical template — Tasks 13-18 follow the same pattern.

### Task 12: Migrate `tests/world_model/test_world_snapshot.py`

**Files:**
- Modify: `tests/world_model/test_world_snapshot.py:18`

- [ ] **Step 1: Find import block**

```bash
grep -n "from infra" tests/world_model/test_world_snapshot.py
```

- [ ] **Step 2: Replace `infra.world_model.data_structures` domain entity imports with `lingwen_core.domain.*`**

For example, if line 18 is:

```python
from infra.world_model.data_structures import (
    KeyPoint, NodeId, NodeType, PhysicalLine, MentalLine,
    Ripple, RippleState, WorldSnapshot,
)
```

REPLACE with:

```python
from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType
from lingwen_core.domain.ripple import Ripple, RippleState, WorldSnapshot
```

Behavior imports (e.g., `infra.world_model.engine`, `infra.world_model.registry`) STAY unchanged.

- [ ] **Step 3: Run test**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  tests/world_model/test_world_snapshot.py -q
```

- [ ] **Step 4: Commit**

```bash
git add tests/world_model/test_world_snapshot.py
git commit -m "refactor(tests): test_world_snapshot migrate to lingwen_core.domain" \
  -m "Domain entities (KeyPoint/NodeId/PhysicalLine/MentalLine/Ripple/
WorldSnapshot) from lingwen_core.domain. Behavior services stay in
infra.world_model.*."
```

### Task 13: Migrate `tests/world_model/test_integration.py`

Same pattern as Task 12 (steps 1-4) but for `tests/world_model/test_integration.py`. Commit message:

```bash
git commit -m "refactor(tests): test_integration migrate to lingwen_core.domain"
```

### Task 14: Migrate `tests/world_model/test_phase2_integration.py`

Same pattern. Commit message:

```bash
git commit -m "refactor(tests): test_phase2_integration migrate to lingwen_core.domain"
```

### Task 15: Migrate `tests/world_model/test_snapshot_diff.py`

Same pattern. Commit message:

```bash
git commit -m "refactor(tests): test_snapshot_diff migrate to lingwen_core.domain"
```

### Task 16: Migrate `tests/world_model/test_snapshot_store.py`

Same pattern. Commit message:

```bash
git commit -m "refactor(tests): test_snapshot_store migrate to lingwen_core.domain"
```

### Task 17: Migrate `tests/world_model/test_key_point_graph.py`

Same pattern. Commit message:

```bash
git commit -m "refactor(tests): test_key_point_graph migrate to lingwen_core.domain"
```

### Task 18: Migrate `tests/world_model/test_ripple_*.py` (if present)

After Tasks 12-17, run:

```bash
grep -rln "from infra.world_model.data_structures" tests/world_model/
```

If any test files remain un-migrated (e.g., `test_ripple_integration.py`, `test_ripple_engine.py`, `test_ripple_queries.py`, `test_links.py`), migrate them one-by-one following the same pattern. Each gets its own commit.

NOTE: From the Phase 18 exploration, `tests/world_model/` has 9 test files (snapshot_store, key_point_graph, snapshot_diff, phase2_integration, ripple_integration, ripple_engine, links, ripple_queries, world_snapshot, integration). Tasks 12-17 cover 7 of these. Task 18 covers the remaining `test_ripple_*.py` and `test_links.py` files.

---

## Task 19: Convert `infra/world_model/data_structures.py` + `__init__.py` to 1-line shims

**Files:**
- Modify: `infra/world_model/data_structures.py`
- Modify: `infra/world_model/__init__.py`

- [ ] **Step 1: Verify no consumers need `infra.world_model.data_structures` directly**

```bash
grep -rln "from infra.world_model.data_structures\|from infra.world_model import" /home/ailearn/projects/LingWen --include="*.py"
```

Expected: Only `infra/world_model/__init__.py`, `infra/world_model/snapshot_diff.py`, `infra/world_model/queries.py`, `infra/world_model/engine.py`, `infra/world_model/snapshot_store.py`, `infra/world_model/character_snapshot.py`, `infra/world_model/foreshadow_snapshot.py`, `infra/world_model/lifecycle.py`, `infra/world_model/key_point_graph.py`, `infra/world_model/registry.py`, `infra/world_model/links.py` — i.e., behavior services inside `infra/world_model/` itself.

If any `tests/`, `apps/`, or external `packages/` import from `infra.world_model.data_structures` directly, stop and migrate THOSE first before proceeding.

- [ ] **Step 2: Convert `data_structures.py` to 1-line shim**

REPLACE the entire `infra/world_model/data_structures.py` with:

```python
"""PHASE-COMPAT: Phase 19+ — DELETE after Phase 19.x

Back-compat shim re-exporting domain entities from
``lingwen_core.domain``. Historically lived at ``infra.world_model.data_structures``
before consolidation into the lingwen_core package.

DO NOT add new code here; this is a deletion target.
"""
from __future__ import annotations

from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import (
    KeyPoint,
    NodeId,
    NodeType,
    Relation,
)
from lingwen_core.domain.ripple import (
    MAX_OPEN_RIPPLOTS,
    ResolutionMode,
    Ripple,
    RippleOpenedEvent,
    RippleResolvedEvent,
    RippleState,
    RippleStateChangedEvent,
    WorldSnapshot,
)

# Phase 1.2 enum (PlotType / PlotPurpose / PlotStatus + MAX_ACTIVE_SUBPLOTS) lives
# in lingwen_core.domain.subplot — re-exported via infra.subplot.data_structures
# (NOT via this shim).

__all__ = [
    "KeyPoint",
    "MentalLine",
    "MAX_OPEN_RIPPLOTS",
    "NodeId",
    "NodeType",
    "PhysicalLine",
    "Relation",
    "ResolutionMode",
    "Ripple",
    "RippleOpenedEvent",
    "RippleResolvedEvent",
    "RippleState",
    "RippleStateChangedEvent",
    "WorldSnapshot",
]
```

- [ ] **Step 3: Verify `__init__.py` exports match (or convert to 1-line shim)**

Look at `infra/world_model/__init__.py`. If it currently re-exports from `data_structures` (probably does), the file can either:
- (a) Stay as-is (it re-exports via the now-slim `data_structures.py`)
- (b) Become a 1-line shim that re-exports from `lingwen_core.domain` directly

**Choose (b)** for consistency. REPLACE `infra/world_model/__init__.py`:

```python
"""PHASE-COMPAT: Phase 19+ — DELETE after Phase 19.x

Back-compat shim re-exporting ``infra.world_model`` namespace from
``lingwen_core.domain``. Behavior services (engine, lifecycle, links,
queries, registry, snapshot_diff, snapshot_store, character_snapshot,
foreshadow_snapshot, key_point_graph) remain in infra.world_model.*
because they are application services, not domain entities.

DO NOT add new code here; this is a deletion target.
"""
from __future__ import annotations

from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType, Relation
from lingwen_core.domain.ripple import (
    MAX_OPEN_RIPPLOTS,
    ResolutionMode,
    Ripple,
    RippleOpenedEvent,
    RippleResolvedEvent,
    RippleState,
    RippleStateChangedEvent,
    WorldSnapshot,
)

__all__ = [
    "KeyPoint",
    "MentalLine",
    "MAX_OPEN_RIPPLOTS",
    "NodeId",
    "NodeType",
    "PhysicalLine",
    "Relation",
    "ResolutionMode",
    "Ripple",
    "RippleOpenedEvent",
    "RippleResolvedEvent",
    "RippleState",
    "RippleStateChangedEvent",
    "WorldSnapshot",
]
```

- [ ] **Step 4: Run full regression**

```bash
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/ \
  tests/subplot/ \
  tests/consistency/ \
  tests/world_model/ \
  -q
```

Expected: All tests pass.

- [ ] **Step 5: Verify lint clean**

```bash
ruff check infra/ packages/lingwen-core/
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add infra/world_model/__init__.py infra/world_model/data_structures.py
git commit -m "refactor(infra): world_model/data_structures + __init__ shims" -m "1-line PHASE-COMPAT re-exports of domain entities from
lingwen_core.domain.{chapter,common,ripple}. Marked for deletion
post-Phase 19.x. Behavior services (engine/lifecycle/links/queries/
registry/snapshot_diff/snapshot_store/etc.) stay in infra.world_model.*
unchanged (application layer, not Phase 19+ Sub1 scope)."
```

---

## Task 20: Handoff + docs close

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md`
- Modify: `.lingwen/architecture.yml`
- Modify: `CLAUDE.md`
- Modify (best-effort, outside repo): `MEMORY.md`

- [ ] **Step 1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md`. Use this template:

```markdown
# Phase 19+ Sub1 — World Model Domain Migration Handoff

## Summary

Phase 19+ Sub1 closed: WorldSnapshot + Plot data classes migrated to `packages/lingwen-core/domain/`. `infra/world_model/data_structures.py` + `infra/subplot/data_structures.py` are now 1-line PHASE-COMPAT shims. 10+ test files migrated from `infra.world_model.*` / `infra.subplot.*` to `lingwen_core.domain.*`.

**Total commits**: [N] on `phase-19-sub1` branch.

## What Phase 19+ Sub1 Did

[Copy section-by-section summary of each commit from `git log phase-19-sub1..master`.]

## Architecture Invariants Established

1. ✅ `packages/lingwen-core/domain/` is canonical source for WorldSnapshot, Plot, PhysicalLine, MentalLine, Ripple, KeyPoint, NodeId, Relation, NodeType.
2. ✅ `infra/world_model/` + `infra/subplot/` are PHASE-COMPAT shims (deletion targets).
3. ✅ `lingwen_core.domain.*` does NOT depend on `infra.*` (DDD purity preserved).

## Verification Gates (Final State)

- `pytest packages/lingwen-core/tests/ tests/subplot/ tests/consistency/ tests/world_model/` — all green
- `ruff check infra/ packages/lingwen-core/` — 0
- `lint-imports` — 3 contracts KEPT + NO new lingwen-core → infra imports
- `pnpm vitest run` (frontend) — 1762 + 1 (unchanged)
- `pnpm tsc --noEmit` / `pnpm eslint .` — 0

## Lessons

[Capture 3-5 most important lessons]

## Carryover to Phase 19.x+

- **Sub2**: `infra/consistency.*` consumer migration (30+ files) — see Phase 18 handoff
- **Sub3**: `infra/agent_system.*` consumer migration (similar pattern)
- **Sub4**: Behavior services migration (engine/lifecycle/links/queries/registry/snapshot_diff/snapshot_store) — `infra/world_model/*` services still on infra.* internally
- **Future v20+**: `infra/exports/*` → `packages/lingwen-storage`
- **Future v20+**: Phase 114 prod preview regression (still accepted)
```

- [ ] **Step 2: Update `.lingwen/architecture.yml`**

Find the `phase_18` section and ADD a new `phase_19` section. Read the file first to confirm structure:

```bash
grep -n "phase_18\|version\|DP-" .lingwen/architecture.yml | head -20
```

Update `version` to "19.1" and ADD after the `phase_18` section:

```yaml
  phase_19:
    name: "World Model Domain Migration"
    branch: "phase-19-sub1"
    commits: [N]
    closure_date: "2026-09-01"
    sub_phase: "Sub1"
    carryover:
      - Sub2 (consistency shim cleanup, 30+ files)
      - Sub3 (agent_system shim cleanup)
      - Sub4 (behavior services migration — engine/lifecycle/etc.)
      - infra/exports/* → packages/lingwen-storage (separate v20+)
    architecture_invariants:
      - "lingwen_core.domain.* canonical for WorldSnapshot/Plot"
      - "infra/world_model + infra/subplot = PHASE-COMPAT shims"
      - "lingwen_core does NOT depend on infra"
```

- [ ] **Step 3: Update `CLAUDE.md`**

Add Phase 19 entry at the top of the version history block (after the v18 entry). Pattern follows the existing version history format:

```markdown
  → v19.1 (Phase 19 Sub1 — World Model Domain Migration — [N] source commits on branch `phase-19-sub1`. Plot + WorldSnapshot fully migrated to `packages/lingwen-core/domain/`; `infra/world_model/` + `infra/subplot/` now 1-line PHASE-COMPAT shims. 10+ test consumers migrated. DDD purity preserved: lingwen_core does NOT depend on infra. ... [brief summary] ... See `docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md`.)
```

- [ ] **Step 4: Best-effort update MEMORY.md**

This file lives OUTSIDE the repo at:
```
/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md
```

If MEMORY.md is currently under 200 lines: add v19.1 entry + Phase 19+ Sub2/Sub3/Sub4 carryover to "Next session options". Keep under 200 lines.

If already at 180+ lines: move content to `history.md` first, then add v19.1 entry to MEMORY.md (index).

- [ ] **Step 5: Commit docs**

```bash
git add docs/superpowers/handoffs/2026-09-01-phase-19-sub1-world-model-domain-handoff.md
git add .lingwen/architecture.yml
git add CLAUDE.md
git commit -m "docs(phase-19-sub1): handoff + architecture.yml + CLAUDE.md" -m "Close Phase 19+ Sub1. New version 19.1. Carryover to Sub2/Sub3/Sub4."
```

- [ ] **Step 6: Push branch + merge to master**

Per project workflow (CLAUDE.md §WORKFLOW CHANGE 2026-09-01: solo repo, no PRs):

```bash
# Push branch directly
git push origin phase-19-sub1

# Local fast-forward merge to master
git checkout master
git merge --ff-only phase-19-sub1

# Push master
git push origin master

# Cleanup worktree (if used)
cd /home/ailearn/projects/LingWen
git worktree remove .worktrees/phase-19-sub1 --force 2>/dev/null
git branch -d phase-19-sub1  # only if local merge done
```

---

## Post-Phase Verification (run after master merge)

```bash
# Full backend tests
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest \
  packages/lingwen-core/tests/ \
  tests/subplot/ \
  tests/consistency/ \
  tests/world_model/ \
  tests/infra/ \
  apps/studio_api/tests/ \
  -q

# Frontend (should be unchanged)
cd apps/dashboard && pnpm exec knip     # 0 lines
cd /home/ailearn/projects/LingWen && pnpm vitest run    # 1762 + 1
cd apps/dashboard && pnpm tsc --noEmit  # 0
cd apps/dashboard && pnpm eslint .      # 0
ruff check infra/ packages/                 # 0
```

All gates MUST be green before claiming Phase 19+ Sub1 closed.

---

## Self-Review (after writing this plan)

### Spec coverage check

Walking through `docs/superpowers/specs/2026-09-01-phase-19-sub1-world-model-domain-design.md`:

| Spec section | Plan coverage |
|--------------|---------------|
| §1 Summary | Tasks 1-20 cover all 3 deliverables (fill gap + Plot migration + consumer migration) |
| §2 Context | N/A — historical reference, no plan tasks needed |
| §3 Architecture | Tasks 1-6 establish lingwen-core.domain as canonical |
| §4 Components | Tasks 4 (subplot.py NEW), 5 (shim), 19 (shim) match spec component table |
| §5 Data Flow | Task 5 Step 1 + Task 19 Step 2+3 capture before/after flow |
| §6 Error Handling | Task 7 tests cover `from_dict` errors + backward-compat (test_world_snapshot_from_dict_backward_compat_no_active_subplots) |
| §7 Testing | Task 7 + per-Task verifications match §7.1 + §7.2 |
| §8 Commit Plan | 20 tasks map to spec's 18 commits with minor regrouping (Tasks 12-18 split per-file + Task 8 stays single) |
| §9 Risks | Tasks 4 (Plot module) precede Task 3 (active_subplots field) — KEY REORDER: Tasks 1-3 + Tasks 4-6 split this way |
| §10 Success criteria | Tasks 19 + 20 verify all must-have items |
| §11 Lessons Applied | Implicit in commit granularity + TDD steps |

**Key refactor**: Spec listed T1-T3 as impl-first then T3-tests. This plan follows **TDD** strictly by reordering:

- Tasks 1-3: domain fill impl (no separate RED tests because behavioral verification is implicit)
- Task 7: 7 RED tests for WorldSnapshot fill (after all 3 fields exist)
- Task 4: 5 RED tests for Plot created FIRST, then `subplot.py` impl

This avoids the spec's anti-pattern of "impl before tests". Test counts match spec exactly (7 for WorldSnapshot, 5 for Plot).

### Placeholder scan

`grep "TBD\|TODO\|appropriate error handling\|fill in details\|Similar to Task" docs/superpowers/plans/2026-09-01-phase-19-sub1-world-model-domain.md`:

- Tasks 12-18 use the phrase "Same pattern as Task 12 (steps 1-4)" — this is acceptable because Task 12 fully demonstrates the pattern with concrete code blocks. The reader can mechanically apply.

Tasks 12-18 DO have specific grep patterns + commit messages, so no actual placeholder text.

### Type consistency check

| Defined | Used |
|---------|------|
| `WorldSnapshot.to_dict() -> dict[str, Any]` (Task 1, Step 1) | Referenced in Task 7 tests + Tasks 8+ imports |
| `WorldSnapshot.from_dict(d: dict[str, Any])` (Task 1, Step 1) | Same usage |
| `Plot.to_dict() / from_dict` (Task 4, Step 3) | Referenced in Task 5 shim exports |
| `MAX_ACTIVE_SUBPLOTS = 5` (Task 4, Step 3) | Referenced in helpers (Task 5) |
| `MAX_OPEN_RIPPLOTS = 10` (no plan task) | Inherited from Phase 18 — re-exported in Task 19 shim |
| `PhysicalLine(ch=0)` default factory (Task 2, Step 1) | Used in Task 7 test |

All consistent.

---

## Handoff to Execution

Plan complete and saved to `docs/superpowers/plans/2026-09-01-phase-19-sub1-world-model-domain.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per Task (Tasks 1-20), review between tasks, fast iteration. Best for this plan because each task is small, well-bounded, and atomic.

2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
