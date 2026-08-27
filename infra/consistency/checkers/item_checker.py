# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Shim re-exporting ItemChecker + ItemState from lingwen_quality."""
from lingwen_quality.consistency.checkers.item_checker import (  # noqa: F401
    ItemChecker,
    ItemState,
)
