"""PHASE-COMPAT: Phase 19+ — DELETE after Phase 19.x

Back-compat shim re-exporting ``Plot`` data class from
``lingwen_core.domain.subplot``. Historically lived at
``infra.subplot.data_structures.Plot`` before consolidation into the
lingwen_core package.

Behavior helpers (``add_subplot``, ``get_active_subplots``,
``subplots_count``) live in ``infra/subplot/helpers.py`` (split during
Phase 19+ Sub1 Task 8). They will move to ``lingwen_core.use_cases``
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
